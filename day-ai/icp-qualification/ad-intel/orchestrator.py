import asyncio
import logging
import time
from datetime import datetime, timezone

from models.ad_models import (
    ChannelMix,
    DomainAdReport,
    Platform,
    PlatformResult,
)
from enrichment.storeleads_client import enrich_domain
from scraping.browser_agent import managed_browser
from scraping.ispot_scraper import scrape_ispot
from scraping.youtube_transparency_scraper import scrape_youtube_ads
from scraping.meta_ad_scraper import scrape_meta_ads
from utils.domain_utils import domain_to_brand_guess, normalize_domain

logger = logging.getLogger(__name__)

RATE_LIMIT_SECONDS = 10


async def run_pipeline(
    domain: str,
    headless: bool = True,
) -> DomainAdReport:
    """Run the full ad intelligence pipeline for a domain."""
    start_time = time.monotonic()
    domain = normalize_domain(domain)

    report = DomainAdReport(
        domain=domain,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )

    # Step 1: Store Leads enrichment
    logger.info(f"[1/5] Enriching {domain} via Store Leads...")
    enrichment = await enrich_domain(domain)
    if enrichment:
        report.enrichment = enrichment
        report.company_name = enrichment.company_name

    # Determine brand name for scraping
    brand_name = report.company_name or domain_to_brand_guess(domain)
    logger.info(f"Using brand name: '{brand_name}' for scraping")

    # Step 2: Launch browser
    logger.info(f"[2/5] Launching browser (headless={headless})...")
    async with managed_browser(headless=headless) as agent:

        # Step 3: Run all three scrapers concurrently
        logger.info("[3/5] Scraping iSpot, YouTube, Meta in parallel...")
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

        results = await asyncio.gather(ispot_task, youtube_task, meta_task)
        report.ispot_ads = results[0]
        report.youtube_ads = results[1]
        report.meta_ads = results[2]

    # Step 4: Compute channel mix
    logger.info("[4/5] Computing channel mix...")
    report.channel_mix = _compute_channel_mix(report)
    report.running_any_ads = report.channel_mix.total_ads_found > 0

    # Finalize
    report.pipeline_duration_seconds = round(time.monotonic() - start_time, 2)
    logger.info(f"[5/5] Pipeline complete in {report.pipeline_duration_seconds}s")

    return report


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
