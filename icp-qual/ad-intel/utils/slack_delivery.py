"""Slack Delivery Module

Posts ICP qualification results to #gtm-icp-qualification.
Main message is a concise summary; details go in thread replies.

Delivery strategy:
  1. If SLACK_BOT_TOKEN is set, posts directly via Slack API
  2. Otherwise, saves messages to output/slack_pending/ for MCP-based delivery
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

SLACK_CHANNEL_ID = "C08U7N6KZV4"  # #gtm-icp-qualification
SLACK_PENDING_DIR = Path(__file__).resolve().parent.parent / "output" / "slack_pending"


def _fmt_money(val: float | None) -> str:
    if val is None:
        return "—"
    if val >= 1_000_000:
        return f"${val / 1_000_000:.1f}M"
    if val >= 1_000:
        return f"${val / 1_000:.0f}K"
    return f"${val:,.0f}"


def _fmt_number(val: int | None) -> str:
    if val is None:
        return "—"
    if val >= 1_000_000:
        return f"{val / 1_000_000:.1f}M"
    if val >= 1_000:
        return f"{val / 1_000:.0f}K"
    return f"{val:,}"


def build_slack_messages(
    report,
    fit,
    internal_url: str | None = None,
    pitch_url: str | None = None,
    call_tracker=None,
    pitch_failed_sections: list[dict] | None = None,
) -> tuple[str, list[str]]:
    """Build the main message and thread detail messages.

    Returns (main_message, thread_messages) where thread_messages is a list
    of strings to post as thread replies — first is the detail summary,
    then the external call log.
    """
    e = report.enrichment
    company = report.company_name or report.domain
    domain = report.domain
    industry = e.industry.split("/")[-1].strip() if e and e.industry else "E-Commerce"
    platform = e.ecommerce_platform or "—" if e else "—"

    # Fit score
    grade = fit.grade
    total_score = fit.total_score
    recommendation = fit.recommendation

    # Competitor alert
    competitor_line = ""
    if report.competitor_detection and report.competitor_detection.found:
        comps = ", ".join(report.competitor_detection.competitors_detected)
        tags = ", ".join(report.competitor_detection.tags_matched)
        competitor_line = f"\n:warning: *COMPETITOR DETECTED: {comps}* ({tags} in tech stack)"

    # Report links
    links = []
    if internal_url:
        links.append(f"<{internal_url}|Internal Report>")
    if pitch_url:
        links.append(f"<{pitch_url}|Pitch Report>")
    links_line = " | ".join(links) if links else "_Reports pending upload_"

    # ── Metrics ──
    monthly_rev = e.estimated_monthly_revenue if e else None
    annual_rev = e.estimated_annual_revenue if e else None
    employees = e.employee_count if e else None
    visits = e.estimated_monthly_visits if e else None

    # Reviews
    review_str = "—"
    if e and e.review_rating and e.review_count:
        source = e.review_source or ""
        review_str = f"{e.review_rating}★ / {_fmt_number(e.review_count)} reviews" + (f" ({source})" if source else "")

    # Ads
    mix = report.channel_mix
    ispot_count = len(report.ispot_ads.ads)
    yt_count = len(report.youtube_ads.ads)
    meta_count = len(report.meta_ads.ads)

    ispot_note = ""
    if not report.ispot_ads.found:
        ispot_note = " — *No CTV presence, prime expansion channel*"

    # CRM
    crm_line = "Not in CRM"
    if report.company_pulse and report.company_pulse.found:
        p = report.company_pulse
        crm_line = f"{p.health_status} ({p.health_score}/100) · {len(p.contacts)} contacts · {len(p.opportunities)} deals"

    # Contacts
    contacts_count = report.contact_intel.discovered_count if report.contact_intel else 0

    # Social
    social_parts = []
    if e and e.social_profiles:
        for sp in e.social_profiles:
            if sp.followers and sp.followers > 1000:
                social_parts.append(f"{sp.platform.title()} {_fmt_number(sp.followers)}")
    social_line = " · ".join(social_parts[:5]) if social_parts else "—"

    # Brand trend
    trend = report.brand_intel.brand_search_trend or "unknown"

    # Creative pipeline
    creative_line = ""
    cp = report.creative_pipeline
    if cp and cp.found:
        creative_line = f"\n:sparkles: *Creative Pipeline*: Brief ({len(cp.brand_brief)} chars) + Script ({len(cp.script)} chars)"
        if cp.image_urls:
            creative_line += f" + {len(cp.image_urls)} images"

    # ── 1. Main message: Full report summary ──
    main = (
        f":dart: *ICP Qualification Complete: {company}*\n"
        f"`{domain}` · {industry} · {platform}\n"
        f"\n"
        f"*Upscale Fit Score: {total_score}/100 ({grade})*\n"
        f"> {recommendation}"
        f"{competitor_line}\n"
        f"\n"
        f":bar_chart: *Company Snapshot*\n"
        f"• Revenue: *{_fmt_money(monthly_rev)}/mo* ({_fmt_money(annual_rev)} annual)\n"
        f"• Employees: {employees or '—'}\n"
        f"• Monthly visits: {_fmt_number(visits)}\n"
        f"• Reviews: {review_str}\n"
        f"• Social: {social_line}\n"
        f"\n"
        f":tv: *Ad Discovery* — {mix.total_ads_found} ads found\n"
        f"• iSpot (Linear TV): {ispot_count} ads{ispot_note}\n"
        f"• YouTube: {yt_count} ads\n"
        f"• Meta: {meta_count} ads\n"
        f"\n"
        f":office: *CRM*: {crm_line}\n"
        f":busts_in_silhouette: *Contacts*: {contacts_count} new contacts found\n"
        f":mag: *Brand Trend*: {trend.title()} · Promotions: {report.wayback_intel.promotional_intensity if report.wayback_intel else 'unknown'}"
        f"{creative_line}\n"
        f"\n"
        f"_Pipeline completed in {report.pipeline_duration_seconds or 0:.0f}s_"
    )

    thread_messages = []

    # ── 2. Thread 1: Status of all pipeline calls ──
    if call_tracker:
        call_threads = call_tracker.to_slack_thread()
        thread_messages.extend(call_threads)

    # ── 3. Thread 2: Internal report summary + link ──
    internal_thread = ":memo: *Internal Report*\n"
    if internal_url:
        internal_thread += f"<{internal_url}|:link: Open Internal Report>\n\n"
    else:
        internal_thread += "_Report not generated_\n\n"

    # Add key internal data points
    internal_details = []
    if report.enriched_competitors:
        comp_names = [c.company_name or c.domain for c in report.enriched_competitors[:5]]
        internal_details.append(f"• *Competitors*: {', '.join(comp_names)}")
    if report.recent_news:
        internal_details.append(f"• *News*: {len(report.recent_news)} articles found")
    if report.podcasts:
        internal_details.append(f"• *Podcasts*: {len(report.podcasts)} appearances")
    if report.case_studies:
        internal_details.append(f"• *Case Studies*: {len(report.case_studies)} found")
    if report.milled_intel and report.milled_intel.total_emails:
        internal_details.append(f"• *Email Intel*: {report.milled_intel.total_emails} promotional emails ({report.milled_intel.emails_per_week or 0:.1f}/wk)")
    if report.brand_intel and report.brand_intel.brand_search_trend:
        internal_details.append(f"• *Google Trends*: {report.brand_intel.brand_search_trend}")

    # Tech stack highlights
    if e and e.technologies:
        tech_cats = {}
        for t in e.technologies[:20]:
            cat = t.category if hasattr(t, 'category') and t.category else "Other"
            tech_cats.setdefault(cat, []).append(t.name if hasattr(t, 'name') else str(t))
        top_cats = sorted(tech_cats.items(), key=lambda x: -len(x[1]))[:4]
        tech_lines = [f"{cat}: {', '.join(techs[:3])}" for cat, techs in top_cats]
        if tech_lines:
            internal_details.append(f"• *Tech Stack*: {' · '.join(tech_lines)}")

    if internal_details:
        internal_thread += "\n".join(internal_details)
    else:
        internal_thread += "_No additional details available_"

    thread_messages.append(internal_thread)

    # ── 4. Thread 3: Pitch summary + link ──
    pitch_thread = ":dart: *Pitch Report*\n"
    if pitch_url:
        pitch_thread += f"<{pitch_url}|:link: Open Pitch Report>\n\n"
    else:
        pitch_thread += "_Report not generated_\n\n"

    # Pitch-relevant summary
    pitch_details = []
    pitch_details.append(f"• *Industry*: {industry}")
    pitch_details.append(f"• *Platform*: {platform}")
    if monthly_rev:
        from reports.pitch_report import _budget_tier, _detect_shopify, _detect_klaviyo
        try:
            intel = report.brand_intel
            budget = _budget_tier(monthly_rev, intel)
            has_shopify = _detect_shopify(report)
            has_klaviyo = _detect_klaviyo(report)
            pitch_details.append(f"• *Recommended Budget*: {_fmt_money(budget['m1'])}/mo → {_fmt_money(budget['m3'])}/mo (3-month ramp)")
            if has_shopify:
                pitch_details.append("• :white_check_mark: *Shopify* — native integration ready")
            if has_klaviyo:
                pitch_details.append("• :white_check_mark: *Klaviyo* — email journey sync ready")
        except Exception:
            pass

    if not report.ispot_ads.found:
        pitch_details.append("• :star: *CTV Greenfield* — no current streaming TV presence")
    elif ispot_count > 0:
        pitch_details.append(f"• :tv: *Active on CTV* — {ispot_count} linear TV ads found, expansion opportunity")

    if fit:
        # Top scoring dimensions
        try:
            top_scores = sorted(
                [(d.dimension, d.score, d.max_score) for d in fit.dimensions],
                key=lambda x: x[1] / max(x[2], 1),
                reverse=True,
            )[:3]
            strengths = [f"{d[0]} ({d[1]}/{d[2]})" for d in top_scores]
            pitch_details.append(f"• *Top Strengths*: {', '.join(strengths)}")
        except Exception:
            pass

    pitch_thread += "\n".join(pitch_details)
    thread_messages.append(pitch_thread)

    # ── 5. Thread: Failed pitch sections (if any) ──
    if pitch_failed_sections:
        fail_lines = [f"• `{s['section']}` — {s['error']}" for s in pitch_failed_sections]
        fail_thread = (
            f":warning: *{len(pitch_failed_sections)} Pitch Section(s) Failed* — excluded from final report\n"
            + "\n".join(fail_lines)
        )
        thread_messages.append(fail_thread)

    return main, thread_messages


async def post_to_slack(
    main_message: str,
    thread_messages: list[str],
    channel: str = SLACK_CHANNEL_ID,
) -> str | None:
    """Post the main message and threaded replies to Slack.

    Strategy:
      1. If SLACK_BOT_TOKEN env var is set, post directly via Slack API
      2. Otherwise, save to output/slack_pending/ for MCP-based delivery

    Returns the message permalink URL, or None on failure/pending.
    """
    token = os.getenv("SLACK_BOT_TOKEN")

    if token:
        return await _post_via_api(main_message, thread_messages, channel, token)
    else:
        return _save_for_mcp_delivery(main_message, thread_messages, channel)


async def _post_via_api(
    main_message: str,
    thread_messages: list[str],
    channel: str,
    token: str,
) -> str | None:
    """Post directly via Slack Bot API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    api_url = "https://slack.com/api/chat.postMessage"

    async with httpx.AsyncClient(timeout=30) as client:
        # Post main message
        resp = await client.post(
            api_url,
            headers=headers,
            json={"channel": channel, "text": main_message, "unfurl_links": False},
        )
        resp.raise_for_status()
        data = resp.json()

        if not data.get("ok"):
            logger.error(f"Slack chat.postMessage failed: {data.get('error')}")
            return None

        thread_ts = data["ts"]
        channel_id = data["channel"]

        # Post each thread reply
        for msg in thread_messages:
            try:
                reply_resp = await client.post(
                    api_url,
                    headers=headers,
                    json={
                        "channel": channel_id,
                        "text": msg,
                        "thread_ts": thread_ts,
                        "unfurl_links": False,
                    },
                )
                reply_resp.raise_for_status()
                reply_data = reply_resp.json()
                if not reply_data.get("ok"):
                    logger.warning(f"Slack thread reply failed: {reply_data.get('error')}")
            except Exception as e:
                logger.warning(f"Failed to post Slack thread reply: {e}")

        # Get permalink
        permalink = None
        try:
            link_resp = await client.get(
                "https://slack.com/api/chat.getPermalink",
                headers=headers,
                params={"channel": channel_id, "message_ts": thread_ts},
            )
            link_data = link_resp.json()
            if link_data.get("ok"):
                permalink = link_data["permalink"]
        except Exception as e:
            logger.debug(f"Could not fetch permalink: {e}")

        logger.info(f"Slack message posted to #{channel_id} (ts={thread_ts})")
        return permalink


def _save_for_mcp_delivery(
    main_message: str,
    thread_messages: list[str],
    channel: str,
) -> str | None:
    """Save Slack messages to disk for MCP-based delivery.

    The API server exposes GET /api/slack/pending which returns these,
    and POST /api/slack/send/{filename} to mark as sent.
    """
    SLACK_PENDING_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    payload = {
        "channel_id": channel,
        "main_message": main_message,
        "thread_messages": thread_messages,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
    }

    filename = f"slack_{ts}.json"
    filepath = SLACK_PENDING_DIR / filename
    filepath.write_text(json.dumps(payload, indent=2))

    logger.info(f"Slack message saved to {filepath} (no SLACK_BOT_TOKEN — awaiting MCP delivery)")
    return None
