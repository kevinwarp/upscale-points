"""Slack Delivery Module

Posts ICP qualification results to #gtm-icp-qualification via Slack webhook.
Main message is a concise summary; details go in a thread reply.
"""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

SLACK_CHANNEL_ID = "C08U7N6KZV4"  # #gtm-icp-qualification


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

    # ── Main message (concise) ──
    main = (
        f":dart: *ICP Qualification Complete: {company}*\n"
        f"`{domain}` · {industry} · {platform}\n"
        f"\n"
        f"*Upscale Fit Score: {total_score}/100 ({grade})*\n"
        f"> {recommendation}"
        f"{competitor_line}\n"
        f"\n"
        f":page_facing_up: {links_line}\n"
        f"_Pipeline completed in {report.pipeline_duration_seconds or 0:.0f}s_"
    )

    # ── Thread message (details) ──
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

    thread = (
        f":bar_chart: *Key Metrics*\n"
        f"• Revenue: *{_fmt_money(monthly_rev)}/mo* ({_fmt_money(annual_rev)} annual)\n"
        f"• Employees: {employees or '—'}\n"
        f"• Monthly visits: {_fmt_number(visits)}\n"
        f"• Reviews: {review_str}\n"
        f"\n"
        f":tv: *Ad Discovery* — {mix.total_ads_found} ads found\n"
        f"• iSpot (Linear TV): {ispot_count} ads{ispot_note}\n"
        f"• YouTube: {yt_count} ads\n"
        f"• Meta: {meta_count} ads\n"
        f"\n"
        f":office: *CRM Status*: {crm_line}\n"
        f":busts_in_silhouette: *Contacts Discovered*: {contacts_count} new contacts found\n"
        f":mag: *Brand Trend*: {trend.title()} · Promotions: {report.wayback_intel.promotional_intensity if report.wayback_intel else 'unknown'}\n"
        f":bulb: *Social*: {social_line}"
        f"{creative_line}"
    )

    # Build thread messages list
    thread_messages = [thread]

    # Add external call log as follow-up thread message
    if call_tracker:
        call_thread = call_tracker.to_slack_thread()
        thread_messages.extend(call_thread)

    return main, thread_messages


async def post_to_slack(
    main_message: str,
    thread_messages: list[str],
    channel: str = SLACK_CHANNEL_ID,
) -> str | None:
    """Post the main message and threaded replies to Slack.

    Uses SLACK_BOT_TOKEN env var with chat.postMessage API so we can
    retrieve thread_ts for threaded replies.

    Returns the message permalink URL, or None on failure.
    """
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        logger.warning("SLACK_BOT_TOKEN not set — skipping Slack delivery")
        return None

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

        # Get permalink for the main message
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
