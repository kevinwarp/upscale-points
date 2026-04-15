import asyncio
import logging
import time
from datetime import datetime, timezone

from models.ad_models import (
    BrandIntelligence,
    ChannelMix,
    ClayEnrichment,
    CompetitorDetection,
    CTV_COMPETITOR_TAGS,
    DomainAdReport,
    EnrichedCompetitor,
    MilledIntel,
    Platform,
    PlatformResult,
    WaybackEventHit,
    WaybackIntelModel,
)
from enrichment.clay_enrichment import fetch_clay_enrichment, merge_clay_into_intel
from enrichment.company_pulse import fetch_company_pulse
from enrichment.contact_search import fetch_contacts_for_domain
from enrichment.creative_pipeline import generate_creative, CreativeResult
from enrichment.voiceover_gen import generate_voiceover
from models.ad_models import CreativePipelineResult
from enrichment.storeleads_client import enrich_domain
from scoring.brand_intel import analyze_brand_intelligence
from scraping.browser_agent import managed_browser
from scraping.ispot_scraper import scrape_ispot
from scraping.youtube_transparency_scraper import scrape_youtube_ads
from scraping.meta_ad_scraper import scrape_meta_ads
from scraping.milled_scraper import scrape_milled
from scraping.google_trends_scraper import scrape_google_trends
from scraping.competitor_scraper import scrape_competitor_landscape
from scraping.wayback_scraper import scrape_wayback
from utils.call_tracker import CallTracker, CallStatus
from utils.domain_utils import domain_to_brand_guess, normalize_domain
from utils.status_reporter import StatusReporter

logger = logging.getLogger(__name__)

RATE_LIMIT_SECONDS = 10
HEARTBEAT_INTERVAL = 30  # seconds between progress updates


class TrackedStep:
    """Async context manager that emits heartbeat updates every 30s and catches errors.

    Usage:
        async with TrackedStep(status, "storeleads", "Enriching...", progress=5):
            result = await some_call()
    On success: emits step_complete. On error: emits step_error.
    While running: emits step_progress every 30s.
    """

    def __init__(
        self,
        status: StatusReporter,
        step: str,
        label: str,
        progress: int = 0,
        timeout: float | None = None,
    ):
        self.status = status
        self.step = step
        self.label = label
        self.progress = progress
        self.timeout = timeout
        self._heartbeat_task: asyncio.Task | None = None
        self._elapsed = 0

    async def _heartbeat_loop(self):
        """Emit progress updates every HEARTBEAT_INTERVAL seconds."""
        try:
            while True:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                self._elapsed += HEARTBEAT_INTERVAL
                mins = self._elapsed // 60
                secs = self._elapsed % 60
                time_str = f"{mins}m {secs}s" if mins else f"{secs}s"
                self.status.step_progress(
                    self.step,
                    f"{self.label} ({time_str} elapsed...)",
                    progress=self.progress,
                )
        except asyncio.CancelledError:
            pass

    async def __aenter__(self):
        self.status.step_start(self.step, self.label, progress=self.progress)
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        if exc_type is not None:
            self.status.step_error(
                self.step,
                f"{self.label} — failed",
                error=str(exc_val),
                progress=self.progress,
            )
            logger.warning(f"Step {self.step} failed: {exc_val}")
            return True  # suppress the exception
        return False


async def _heartbeat_monitor(status: StatusReporter):
    """Background task that emits progress updates for all running steps every 30s."""
    try:
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            # Emit heartbeat for every step that has an active timer (started but not completed)
            for step, start_t in list(status._step_timers.items()):
                elapsed = time.monotonic() - start_t
                mins = int(elapsed) // 60
                secs = int(elapsed) % 60
                time_str = f"{mins}m {secs}s" if mins else f"{secs}s"
                status.step_progress(step, f"Still running... ({time_str} elapsed)")
    except asyncio.CancelledError:
        pass


async def run_pipeline(
    domain: str,
    headless: bool = True,
    status: StatusReporter | None = None,
) -> tuple[DomainAdReport, CallTracker]:
    """Run the full ad intelligence pipeline for a domain.

    Returns:
        Tuple of (DomainAdReport, CallTracker) — report data and external call log.
    """
    start_time = time.monotonic()
    domain = normalize_domain(domain)
    tracker = CallTracker(domain=domain)

    report = DomainAdReport(
        domain=domain,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )

    # Initialize status reporter if not provided
    if status is None:
        status = StatusReporter(domain)
    status.pipeline_start()

    # Start heartbeat monitor — emits progress for all running steps every 30s
    heartbeat_task = asyncio.create_task(_heartbeat_monitor(status))

    # Step 1: Store Leads enrichment
    status.step_start("storeleads", f"Enriching {domain} via Store Leads...", progress=5)
    tracker.start("storeleads")
    enrichment = await enrich_domain(domain)
    if enrichment:
        report.enrichment = enrichment
        # Prefer StoreLeads merchant_name for brand display
        report.company_name = enrichment.merchant_name or enrichment.company_name

        # Detect CTV competitor tags in tech stack
        report.competitor_detection = _detect_ctv_competitors(enrichment.technologies)
        competitor_info = ""
        if report.competitor_detection.found:
            competitor_info = f" | COMPETITOR DETECTED: {', '.join(report.competitor_detection.competitors_detected)}"
            logger.warning(f"CTV competitor tags detected: {report.competitor_detection.competitors_detected}")

        tracker.record("StoreLeads API", "storeleads", data_summary=f"{enrichment.company_name}, ${enrichment.estimated_monthly_revenue or 0:,.0f}/mo")
        status.step_complete("storeleads", f"Store Leads: {enrichment.company_name or domain}{competitor_info}", progress=10, data={
            "company_name": enrichment.company_name,
            "revenue": enrichment.estimated_monthly_revenue,
            "employees": enrichment.employee_count,
            "platform": enrichment.ecommerce_platform,
            "competitors_detected": report.competitor_detection.competitors_detected,
        })
    else:
        tracker.record("StoreLeads API", "storeleads", status=CallStatus.ERROR, error="No data returned")
        status.step_complete("storeleads", "Store Leads: no data found", progress=10)

    # Determine brand name for scraping
    brand_name = report.company_name or domain_to_brand_guess(domain)

    # Step 1b: Company Pulse CRM lookup (runs in parallel with browser scrapers)
    status.step_start("company_pulse", f"Fetching CRM data for {domain}...", progress=12)
    pulse_task = asyncio.create_task(fetch_company_pulse(domain))

    # Step 1c: Contact Search discovery + DB lookup (runs in parallel)
    status.step_start("contact_search", f"Discovering contacts for {domain}...", progress=14)
    contacts_task = asyncio.create_task(fetch_contacts_for_domain(domain))

    # Step 1c2: Clay enrichment — competitors, founders, investors, funding (runs in parallel)
    status.step_start("clay_enrichment", f"Fetching Clay enrichment for {domain}...", progress=14)
    tracker.start("clay_enrichment")
    clay_task = asyncio.create_task(_safe_clay(fetch_clay_enrichment(domain)))

    # Step 1d: Creative Pipeline — AI ad creative generation (10-20 min, start early)
    status.step_start("creative_pipeline", f"Starting AI creative generation for {domain}...", progress=15)
    creative_task = asyncio.create_task(
        _safe_creative("CreativePipeline", generate_creative(domain))
    )

    # Step 1e: Voiceover Generation — AI voiceover audio (3-5 min, runs in parallel)
    status.step_start("voiceover", f"Starting AI voiceover generation for {domain}...", progress=16)
    voiceover_task = asyncio.create_task(generate_voiceover(domain))

    # Step 2: Launch browser
    status.step_start("browser", f"Launching browser (headless={headless})...", progress=16)
    async with managed_browser(headless=headless) as agent:
        status.step_complete("browser", "Browser ready", progress=18)

        # Step 3: Run all scrapers concurrently (ads + Milled email intel)
        tracker.start("ispot")
        tracker.start("youtube")
        tracker.start("meta")
        tracker.start("milled")
        status.step_start("scrapers", "Scraping iSpot, YouTube, Meta, Milled in parallel...", progress=20)
        ispot_task = asyncio.create_task(
            _safe_scrape("iSpot", scrape_ispot(agent, brand_name))
        )
        youtube_task = asyncio.create_task(
            _safe_scrape(
                "YouTube",
                scrape_youtube_ads(agent, brand_name, domain),
            )
        )
        meta_task = asyncio.create_task(
            _safe_scrape("Meta", scrape_meta_ads(agent, brand_name))
        )
        milled_task = asyncio.create_task(
            _safe_milled("Milled", scrape_milled(agent, domain, brand_name))
        )

        ad_results = await asyncio.gather(ispot_task, youtube_task, meta_task)
        report.ispot_ads = ad_results[0]
        report.youtube_ads = ad_results[1]
        report.meta_ads = ad_results[2]

        report.milled_intel = await milled_task

        # Track scraper results
        for name, step, result in [
            ("iSpot Scraper", "ispot", ad_results[0]),
            ("YouTube Ads Transparency", "youtube", ad_results[1]),
            ("Meta Ad Library", "meta", ad_results[2]),
        ]:
            if result.error:
                tracker.record(name, step, status=CallStatus.ERROR, error=result.error, data_summary=f"{len(result.ads)} ads")
            else:
                tracker.record(name, step, data_summary=f"{len(result.ads)} ads found")

        if report.milled_intel.error:
            tracker.record("Milled Email Intel", "milled", status=CallStatus.ERROR, error=report.milled_intel.error)
        else:
            tracker.record("Milled Email Intel", "milled", data_summary=f"{'found' if report.milled_intel.found else 'not found'}")

        status.step_complete("scrapers", f"Scraping complete: {len(ad_results[0].ads)}+{len(ad_results[1].ads)}+{len(ad_results[2].ads)} ads", progress=45, data={
            "ispot": len(ad_results[0].ads),
            "youtube": len(ad_results[1].ads),
            "meta": len(ad_results[2].ads),
            "milled": report.milled_intel.found,
        })

        # Step 4: Compute channel mix (needed for subsequent steps)
        status.step_start("analysis", "Computing channel mix & brand intelligence...", progress=48)
        report.channel_mix = _compute_channel_mix(report)
        report.running_any_ads = report.channel_mix.total_ads_found > 0

        # Step 5: Brand intelligence analysis (non-browser tasks)
        report.brand_intel = analyze_brand_intelligence(report)
        status.step_complete("analysis", f"Analysis complete: {report.channel_mix.total_platforms} platforms, {report.channel_mix.total_ads_found} ads", progress=50)

        # Step 5b: Collect Clay enrichment (needed before competitor scraper)
        clay_result = await clay_task
        if clay_result and clay_result.enriched:
            report.clay = clay_result
            # Merge key Clay fields into brand_intel
            merge_clay_into_intel(report.brand_intel, {
                "competitors": clay_result.competitors,
                "revenue_model": clay_result.revenue_model,
                "target_audience": clay_result.target_audience,
                "target_demographics": None,
                "logo_url": clay_result.logo_url,
                "headquarters": clay_result.headquarters,
                "founders": clay_result.founders,
                "investors": clay_result.investors,
                "total_funding": clay_result.latest_funding,
                "recent_funding_round": clay_result.latest_funding,
                "headcount_growth": None,
                "recent_news": None,
            })
            tracker.record("Clay Enrichment", "clay_enrichment", data_summary=(
                f"{len(clay_result.competitors)} competitors, "
                f"{len(clay_result.founders)} founders, "
                f"HQ={clay_result.headquarters}"
            ))
            status.step_complete("clay_enrichment", (
                f"Clay: {len(clay_result.competitors)} competitors, "
                f"{len(clay_result.founders)} founders, "
                f"HQ={clay_result.headquarters or 'n/a'}"
            ), progress=52, data={
                "competitors": clay_result.competitors,
                "founders": clay_result.founders,
                "headquarters": clay_result.headquarters,
                "revenue_model": clay_result.revenue_model,
            })
        else:
            tracker.record("Clay Enrichment", "clay_enrichment", status=CallStatus.ERROR,
                           error="No data returned or CLAY_API_KEY not set")
            status.step_complete("clay_enrichment", "Clay: no data (API key missing or error)", progress=52)

        # Step 6: Run extended scrapers (trends + competitor check)
        tracker.start("trends")
        tracker.start("competitors")
        tracker.start("wayback")
        status.step_start("extended_scrapers", "Running Google Trends + competitor landscape...", progress=52)
        industry = enrichment.industry if enrichment else None

        trends_task = asyncio.create_task(
            _safe_dict("GoogleTrends", scrape_google_trends(agent, brand_name))
        )
        # Gather Clay competitor names if available
        clay_competitors = (
            report.clay.competitors if report.clay and report.clay.enriched else None
        )

        competitor_task = asyncio.create_task(
            _safe_dict(
                "Competitors",
                scrape_competitor_landscape(
                    agent, brand_name, domain, industry,
                    clay_competitors=clay_competitors,
                    enrichment=enrichment,
                ),
            )
        )

        # Wayback Machine: runs without browser, parallel with trends + competitors
        wayback_task = asyncio.create_task(
            _safe_wayback("Wayback", scrape_wayback(domain))
        )

        trends_result, competitor_result, wayback_result = await asyncio.gather(
            trends_task, competitor_task, wayback_task
        )

        # Track extended scraper results
        if trends_result:
            tracker.record("Google Trends", "trends", data_summary=f"trend: {trends_result.get('trend', 'n/a')}")
        else:
            tracker.record("Google Trends", "trends", status=CallStatus.ERROR, error="No data returned")

        if competitor_result:
            tracker.record("Competitor Landscape", "competitors", data_summary=f"{len(competitor_result.get('competitors', []))} competitors")
        else:
            tracker.record("Competitor Landscape", "competitors", status=CallStatus.ERROR, error="No data returned")

        if wayback_result and wayback_result.found:
            tracker.record("Wayback Machine", "wayback", data_summary=f"{wayback_result.active_events} active events, {wayback_result.promotional_intensity} intensity")
        elif wayback_result and wayback_result.error:
            tracker.record("Wayback Machine", "wayback", status=CallStatus.ERROR, error=wayback_result.error)
        else:
            tracker.record("Wayback Machine", "wayback", data_summary="no data")

        # Merge extended results into brand_intel
        if trends_result:
            report.brand_intel.brand_search_trend = trends_result.get("trend")
            report.brand_intel.monthly_search_volume = trends_result.get("search_volume")

        if competitor_result:
            report.brand_intel.competitors = competitor_result.get("competitors", [])
            report.brand_intel.competitors_on_ctv = competitor_result.get("competitors_on_ctv", [])
            report.brand_intel.competitors_on_youtube = competitor_result.get("competitors_on_youtube", [])

        # Merge Wayback results
        if wayback_result:
            events = []
            for ea in wayback_result.events_with_activity:
                if ea.activity_detected:
                    events.append(WaybackEventHit(
                        event_name=ea.event.name,
                        event_date=ea.event_date.isoformat(),
                        category=ea.event.category,
                        activity_score=ea.activity_score,
                        unique_versions=ea.unique_versions,
                        snapshots_count=ea.snapshots_in_window,
                        archive_url=ea.snapshots[0].archive_url if ea.snapshots else None,
                    ))
            report.wayback_intel = WaybackIntelModel(
                domain=domain,
                total_snapshots_checked=wayback_result.total_snapshots_checked,
                total_events_checked=wayback_result.total_events_checked,
                active_events=wayback_result.active_events,
                promotional_intensity=wayback_result.promotional_intensity,
                years_analyzed=wayback_result.years_analyzed,
                events=events,
                found=wayback_result.found,
                error=wayback_result.error,
                scrape_duration_seconds=wayback_result.scrape_duration_seconds,
            )

        status.step_complete("extended_scrapers", f"Trends: {trends_result.get('trend', 'unknown') if trends_result else 'n/a'}, Competitors: {len(competitor_result.get('competitors', [])) if competitor_result else 0}, Wayback: {wayback_result.promotional_intensity if wayback_result else 'n/a'}", progress=65)

    # Step 7: Enrich competitors via StoreLeads (runs outside browser context)
    all_competitor_names = list(dict.fromkeys(
        report.brand_intel.competitors
        + (report.clay.competitors if report.clay else [])
    ))
    tracker.start("competitor_enrichment")
    if all_competitor_names:
        status.step_start("competitor_enrichment", f"Enriching {len(all_competitor_names)} competitors via StoreLeads...", progress=66)
        try:
            report.enriched_competitors = await _enrich_competitors(
                all_competitor_names,
                report.brand_intel.competitors_on_ctv,
                report.brand_intel.competitors_on_youtube,
            )
            tracker.record("StoreLeads (Competitors)", "competitor_enrichment", data_summary=f"{len(report.enriched_competitors)}/{len(all_competitor_names)} enriched")
            status.step_complete("competitor_enrichment", f"Enriched {len(report.enriched_competitors)} competitors", progress=70, data={
                "enriched": len(report.enriched_competitors),
                "total_candidates": len(all_competitor_names),
            })
        except Exception as exc:
            logger.warning(f"Competitor enrichment failed: {exc}")
            status.step_complete("competitor_enrichment", f"Error: {exc}", progress=70)
    else:
        status.step_start("competitor_enrichment", "No competitors to enrich", progress=66)
        status.step_complete("competitor_enrichment", "No competitors found", progress=70, data={"enriched": 0, "total_candidates": 0})

    # Collect Company Pulse (may already be done — it ran in parallel)
    tracker.start("company_pulse")
    report.company_pulse = await pulse_task
    if report.company_pulse.found:
        tracker.record("Company Pulse (HubSpot)", "company_pulse", data_summary=f"{report.company_pulse.health_status}, {len(report.company_pulse.contacts)} contacts")
        status.step_complete("company_pulse", f"CRM: {report.company_pulse.health_status} ({report.company_pulse.health_score}/100), {len(report.company_pulse.contacts)} contacts, {len(report.company_pulse.opportunities)} deals", progress=68, data={
            "health_score": report.company_pulse.health_score,
            "health_status": report.company_pulse.health_status,
            "contacts": len(report.company_pulse.contacts),
            "deals": len(report.company_pulse.opportunities),
        })
    else:
        tracker.record("Company Pulse (HubSpot)", "company_pulse", data_summary="not in CRM")
        status.step_complete("company_pulse", f"CRM: {domain} not in CRM", progress=68)

    # Collect Contact Search results
    from models.ad_models import ContactIntel, TargetContact

    contact_result = await contacts_task
    target_contacts: list[TargetContact] = []

    # Merge discovered contacts
    for c in contact_result.discovered:
        target_contacts.append(TargetContact(
            first_name=c.first_name,
            last_name=c.last_name,
            title=c.title,
            email=c.email,
            linkedin_url=c.linkedin_url,
            confidence_score=c.confidence_score,
            email_sources=c.email_sources.split(", ") if c.email_sources else [],
        ))

    # Merge existing contacts (add outreach status for those already in DB)
    existing_emails = {c.best_email for c in contact_result.existing}
    for c in contact_result.existing:
        # Check if already added from discovery
        match = next((t for t in target_contacts if t.email == c.best_email), None)
        if match:
            match.outreach_status = c.outreach_status
            match.replied_at = c.replied_at
        else:
            target_contacts.append(TargetContact(
                first_name=c.first_name,
                last_name=c.last_name,
                title=c.title,
                email=c.best_email,
                linkedin_url=c.linkedin_url,
                confidence_score=c.confidence_score,
                email_sources=c.email_sources,
                outreach_status=c.outreach_status,
                replied_at=c.replied_at,
            ))

    report.contact_intel = ContactIntel(
        found=len(target_contacts) > 0,
        discovered_count=len(contact_result.discovered),
        existing_count=contact_result.total_existing,
        contacts=target_contacts,
        error=contact_result.error,
    )
    tracker.record("Contact Search (Apollo)", "contact_search", data_summary=f"{len(target_contacts)} contacts ({len(contact_result.discovered)} new)")
    status.step_complete("contact_search", f"Contacts: {len(target_contacts)} total ({len(contact_result.discovered)} discovered, {contact_result.total_existing} existing)", progress=72, data={
        "discovered": len(contact_result.discovered),
        "existing": contact_result.total_existing,
        "total": len(target_contacts),
    })

    # ── Phase 2: Deep Research (runs in parallel) ───────────────
    from enrichment.hiring_signals import fetch_hiring_intel
    from enrichment.news_search import fetch_news_intel
    from enrichment.thought_leadership import fetch_thought_leadership
    from enrichment.case_study_search import fetch_case_studies

    company_name = report.company_name or domain

    # Prepare people list for thought leadership search
    key_people: list[dict] = []
    for tc in target_contacts[:5]:
        name = f"{tc.first_name or ''} {tc.last_name or ''}".strip()
        if name:
            key_people.append({"name": name, "title": tc.title or ""})

    # Launch Phase 2 tasks in parallel
    status.step_start("news_search", f"Searching news & media for {company_name}...", progress=73)
    status.step_start("thought_leadership", f"Searching podcasts & thought leadership...", progress=73)
    status.step_start("case_study_search", f"Searching platform case studies...", progress=73)

    phase2_tasks = await asyncio.gather(
        fetch_hiring_intel(domain, company_name=company_name, clay_data=report.clay.raw_data if report.clay and report.clay.enriched else None),
        fetch_news_intel(domain, company_name=company_name, clay_news=report.clay.recent_news if report.clay else None),
        fetch_thought_leadership(domain, company_name=company_name, key_people=key_people or None, clay_founders=report.brand_intel.founders or None),
        fetch_case_studies(domain, company_name=company_name),
        return_exceptions=True,
    )

    # Collect hiring intel
    hiring_result = phase2_tasks[0]
    if isinstance(hiring_result, Exception):
        logger.warning(f"Hiring intel failed: {hiring_result}")
    else:
        report.hiring_intel = hiring_result
        tracker.record("Hiring Intel (Clay)", "hiring_signals", data_summary=f"{hiring_result.open_jobs_count} jobs, {len(hiring_result.marketing_jobs)} marketing")
        detail_parts = [f"{hiring_result.open_jobs_count} open jobs"]
        if hiring_result.marketing_jobs:
            detail_parts.append(f"{len(hiring_result.marketing_jobs)} marketing roles")
        if hiring_result.hiring_velocity:
            detail_parts.append(f"velocity: {hiring_result.hiring_velocity}")

    # Collect news intel
    news_result = phase2_tasks[1]
    if isinstance(news_result, Exception):
        logger.warning(f"News search failed: {news_result}")
        status.step_complete("news_search", "News: error", progress=76)
    else:
        report.recent_news = news_result
        cats = {}
        for n in news_result:
            cats[n.category] = cats.get(n.category, 0) + 1
        cat_str = ", ".join(f"{v} {k}" for k, v in sorted(cats.items(), key=lambda x: x[1], reverse=True))
        tracker.record("News Search", "news_search", data_summary=f"{len(news_result)} articles")
        status.step_complete("news_search", f"News: {len(news_result)} articles ({cat_str})", progress=76, data={
            "detail": f"{len(news_result)} articles found" + (f" · {cat_str}" if cat_str else ""),
            "articles": len(news_result),
            "categories": cats,
        })

    # Collect thought leadership
    podcast_result = phase2_tasks[2]
    if isinstance(podcast_result, Exception):
        logger.warning(f"Thought leadership search failed: {podcast_result}")
        status.step_complete("thought_leadership", "Podcasts: error", progress=78)
    else:
        report.podcasts = podcast_result
        tracker.record("Thought Leadership", "thought_leadership", data_summary=f"{len(podcast_result)} appearances")
        status.step_complete("thought_leadership", f"Podcasts: {len(podcast_result)} appearances found", progress=78, data={
            "detail": f"{len(podcast_result)} podcast/thought leadership appearances" if podcast_result else "No podcast appearances found",
            "podcasts": len(podcast_result),
        })

    # Collect case studies
    case_result = phase2_tasks[3]
    if isinstance(case_result, Exception):
        logger.warning(f"Case study search failed: {case_result}")
        status.step_complete("case_study_search", "Case studies: error", progress=80)
    else:
        report.case_studies = case_result
        platforms = list(dict.fromkeys(cs.platform for cs in case_result))
        tracker.record("Case Study Search", "case_study_search", data_summary=f"{len(case_result)} studies")
        status.step_complete("case_study_search", f"Case studies: {len(case_result)} found ({', '.join(platforms)})", progress=80, data={
            "detail": f"{len(case_result)} case studies from {', '.join(platforms)}" if case_result else "No platform case studies found",
            "studies": len(case_result),
            "platforms": platforms,
        })

    # ── End Phase 2 ───────────────────────────────────────────

    # Collect Creative Pipeline result (may still be running — await it)
    tracker.start("creative_pipeline")
    status.step_start("creative_pipeline", "Waiting for AI creative generation...", progress=75)
    creative_result = await creative_task
    has_creative_data = creative_result and (creative_result.brand_brief or creative_result.script)
    if has_creative_data:
        report.creative_pipeline = CreativePipelineResult(
            found=True,
            job_id=creative_result.job_id,
            status=creative_result.status,
            brand_name=creative_result.brand_name,
            brand_url=creative_result.brand_url,
            brand_brief=creative_result.brand_brief,
            script=creative_result.script,
            image_urls=creative_result.image_urls,
            video_urls=creative_result.video_urls,
            voiceover_url=creative_result.voiceover_url,
            docx_url=creative_result.docx_url,
            zip_url=creative_result.zip_url,
            elapsed_seconds=creative_result.elapsed_seconds,
        )
        total_videos = sum(len(v) for v in creative_result.video_urls.values())
        tracker.record("Creative Pipeline", "creative_pipeline", data_summary=f"{len(creative_result.image_urls)} images, {total_videos} videos")
        status.step_complete("creative_pipeline", f"Creative Pipeline: {len(creative_result.image_urls)} images, {total_videos} videos ({creative_result.elapsed_seconds}s)", progress=90, data={
            "images": len(creative_result.image_urls),
            "videos": total_videos,
            "elapsed": creative_result.elapsed_seconds,
        })
    else:
        error_msg = creative_result.error if creative_result else "No result"
        report.creative_pipeline = CreativePipelineResult(
            found=False,
            job_id=creative_result.job_id if creative_result else "",
            status=creative_result.status if creative_result else "error",
            error=error_msg,
            elapsed_seconds=creative_result.elapsed_seconds if creative_result else 0,
        )
        tracker.record("Creative Pipeline", "creative_pipeline", status=CallStatus.ERROR, error=error_msg)
        status.step_complete("creative_pipeline", f"Creative Pipeline: {error_msg}", progress=90)

    # Collect Voiceover result
    tracker.start("voiceover")
    try:
        vo_result = await voiceover_task
        if vo_result["status"] == "complete" and vo_result["audio_files"]:
            report.audio_files = vo_result["audio_files"]
            report.audio_run_id = vo_result["run_id"]
            tracker.record("Voiceover Generation", "voiceover", data_summary=f"{len(vo_result['audio_files'])} audio files")
            status.step_complete("voiceover", f"Voiceover: {len(vo_result['audio_files'])} audio files generated", progress=95, data={
                "audio_count": len(vo_result["audio_files"]),
                "run_id": vo_result["run_id"],
            })
        else:
            error_msg = vo_result.get("error", vo_result["status"])
            tracker.record("Voiceover Generation", "voiceover", status=CallStatus.ERROR, error=error_msg)
            status.step_complete("voiceover", f"Voiceover: {error_msg}", progress=95)
    except Exception as e:
        logger.error(f"Voiceover task failed: {e}")
        tracker.record("Voiceover Generation", "voiceover", status=CallStatus.ERROR, error=str(e))
        status.step_complete("voiceover", f"Voiceover: error — {e}", progress=95)

    # Stop heartbeat monitor
    heartbeat_task.cancel()
    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass

    # Finalize
    report.pipeline_duration_seconds = round(time.monotonic() - start_time, 2)
    logger.info(f"Pipeline complete in {report.pipeline_duration_seconds}s — {tracker.summary_text()}")

    return report, tracker


async def _safe_scrape(name: str, coro) -> PlatformResult:
    """Wrap a scraper coroutine so it never crashes the pipeline."""
    try:
        return await coro
    except Exception as e:
        logger.error(f"{name} scraper crashed: {e}")
        platform_map = {
            "iSpot": Platform.ISPOT,
            "YouTube": Platform.YOUTUBE,
            "Meta": Platform.META,
        }
        return PlatformResult(
            platform=platform_map.get(name, Platform.ISPOT),
            found=False,
            error=f"crash: {str(e)}",
        )


async def _safe_milled(name: str, coro) -> MilledIntel:
    """Wrap the Milled scraper so it never crashes the pipeline."""
    try:
        return await coro
    except Exception as e:
        logger.error(f"{name} scraper crashed: {e}")
        return MilledIntel(found=False)


async def _safe_dict(name: str, coro) -> dict:
    """Wrap a scraper that returns a dict so it never crashes the pipeline."""
    try:
        return await coro
    except Exception as e:
        logger.error(f"{name} scraper crashed: {e}")
        return {}


async def _safe_clay(coro) -> ClayEnrichment:
    """Wrap the Clay enrichment call so it never crashes the pipeline."""
    try:
        return await coro
    except Exception as e:
        logger.error(f"Clay enrichment crashed: {e}")
        return ClayEnrichment()


async def _safe_wayback(name: str, coro):
    """Wrap the Wayback scraper so it never crashes the pipeline."""
    try:
        return await coro
    except Exception as e:
        logger.error(f"{name} scraper crashed: {e}")
        return None


async def _enrich_competitors(
    competitor_names: list[str],
    competitors_on_ctv: list[str],
    competitors_on_youtube: list[str],
) -> list[EnrichedCompetitor]:
    """Enrich competitor names via StoreLeads to get revenue, category, domain, etc."""
    from scraping.competitor_scraper import _name_to_domain_guesses

    ctv_set = {c.lower() for c in (competitors_on_ctv or [])}
    yt_set = {c.lower() for c in (competitors_on_youtube or [])}
    enriched: list[EnrichedCompetitor] = []

    for name in competitor_names[:8]:  # Cap at 8 to avoid API abuse
        domain_guesses = _name_to_domain_guesses(name)
        result = None

        for guess in domain_guesses:
            try:
                data = await enrich_domain(guess)
                if data and (data.company_name or data.ecommerce_platform):
                    result = data
                    break
            except Exception as e:
                logger.warning(f"Competitor enrichment failed for {guess}: {e}")

        ec = EnrichedCompetitor(
            name=name,
            on_ctv=name.lower() in ctv_set,
            on_youtube=name.lower() in yt_set,
        )

        if result:
            ec.domain = result.domain
            ec.industry = result.industry
            ec.estimated_annual_revenue = result.estimated_annual_revenue
            ec.ecommerce_platform = result.ecommerce_platform
            ec.employee_count = result.employee_count
            ec.logo_url = result.logo_url
            ec.validated = True
            logger.info(
                f"Competitor enriched: {name} -> {result.domain} "
                f"(${result.estimated_annual_revenue or 0:,.0f}/yr, {result.industry})"
            )
        else:
            ec.domain = domain_guesses[0] if domain_guesses else ""
            logger.info(f"Competitor not found in StoreLeads: {name} (tried {domain_guesses})")

        enriched.append(ec)

    return enriched


async def _safe_creative(name: str, coro) -> CreativeResult:
    """Wrap the Creative Pipeline so it never crashes the pipeline."""
    try:
        return await coro
    except Exception as e:
        logger.error(f"{name} crashed: {e}")
        return CreativeResult(status="error", error=f"crash: {str(e)}")


def _detect_ctv_competitors(technologies: list[str]) -> CompetitorDetection:
    """Scan a brand's tech stack for CTV competitor tags.

    If a brand uses Tatari, MNTN/SteelHouse, tvScientific, Vibe, or
    Universal Ads, they are likely working with a competitor.
    """
    result = CompetitorDetection()
    competitors_found: set[str] = set()
    tags_matched: list[str] = []

    for tech in technologies:
        tech_lower = tech.lower().strip()
        for tag_pattern, competitor_name in CTV_COMPETITOR_TAGS.items():
            if tag_pattern in tech_lower:
                competitors_found.add(competitor_name)
                tags_matched.append(tech)
                break

    if competitors_found:
        result.found = True
        result.competitors_detected = sorted(competitors_found)
        result.tags_matched = tags_matched
        names = ", ".join(result.competitors_detected)
        result.warning = f"Brand is using {names} — active CTV competitor client"

    return result


def _compute_channel_mix(report: DomainAdReport) -> ChannelMix:
    """Derive channel mix from platform results."""
    has_linear = report.ispot_ads.found
    has_youtube = report.youtube_ads.found
    has_meta = report.meta_ads.found
    return ChannelMix(
        has_linear=has_linear,
        has_youtube=has_youtube,
        has_meta=has_meta,
        total_platforms=sum([has_linear, has_youtube, has_meta]),
        total_ads_found=(
            len(report.ispot_ads.ads)
            + len(report.youtube_ads.ads)
            + len(report.meta_ads.ads)
        ),
    )
