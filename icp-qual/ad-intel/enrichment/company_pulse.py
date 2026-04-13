"""Company Pulse API Client

Fetches CRM intelligence from the Company Pulse API — relationship health,
contacts, deals, meetings, outreach history, and AI-generated status summaries.

Usage in ICP protocol:
    pulse = await fetch_company_pulse("seed.com")
    report.company_pulse = pulse

The API aggregates data from Day AI + HubSpot in real time (30-90s typical).
A 404 means the brand isn't tracked yet — that's normal and non-blocking.
"""

from __future__ import annotations

import logging
import os

import httpx

from models.ad_models import (
    CompanyPulse,
    CrmContact,
    CrmDeal,
    CrmMeeting,
    CrmOutreach,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://company-pulse-695873346148.us-central1.run.app"


async def fetch_company_pulse(
    domain: str,
    api_key: str | None = None,
    base_url: str | None = None,
) -> CompanyPulse:
    """Fetch Company Pulse report for a domain.

    Args:
        domain: Company domain (e.g. "seed.com")
        api_key: API key (falls back to COMPANY_PULSE_API_KEY env var)
        base_url: Override base URL

    Returns:
        CompanyPulse with CRM data, or empty CompanyPulse with error if failed.
    """
    api_key = api_key or os.getenv(
        "COMPANY_PULSE_API_KEY",
        "xuuuAaVl/GFsez0vyis269sa0S3mZMcsz6P4S4r6A/o=",
    )
    base_url = base_url or os.getenv("COMPANY_PULSE_API_URL", BASE_URL)

    if not api_key:
        logger.warning("COMPANY_PULSE_API_KEY not set — skipping Company Pulse")
        return CompanyPulse(found=False, error="No API key configured")

    url = f"{base_url.rstrip('/')}/api/v1/company-status"

    try:
        # API takes 30-90s to aggregate data from multiple sources
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.get(
                url,
                params={"domain": domain},
                headers={"x-api-key": api_key},
            )

            if resp.status_code == 404:
                logger.info(f"Company Pulse: {domain} not found in CRM (normal for new brands)")
                return CompanyPulse(found=False, error="Not found in CRM")

            resp.raise_for_status()
            data = resp.json()

        return _parse_pulse_response(data)

    except httpx.TimeoutException:
        logger.warning(f"Company Pulse: timeout for {domain} (API can take 30-90s)")
        return CompanyPulse(found=False, error="Request timed out")
    except Exception as e:
        logger.error(f"Company Pulse: error for {domain}: {e}")
        return CompanyPulse(found=False, error=str(e))


def _parse_pulse_response(data: dict) -> CompanyPulse:
    """Parse the raw Company Pulse API response into our model."""
    org = data.get("organization", {})

    pulse = CompanyPulse(
        found=True,
        report_id=data.get("reportId"),
        # Organization
        current_status=org.get("currentStatus"),
        status_summary=org.get("statusSummary", []),
        next_steps=org.get("nextSteps"),
        owner_email=org.get("ownerEmail"),
        # Health
        health_score=data.get("healthScore"),
        health_status=data.get("healthStatus"),
        health_signals=data.get("healthSignals", []),
        # Timeline
        days_since_first_contact=data.get("daysSinceFirstContact"),
        outreach_summary=data.get("outreachSummary"),
        # CRM tier
        crm_tier=(data.get("upscaleScore") or {}).get("tier"),
    )

    # Parse contacts
    for c in data.get("contacts", []):
        outreach = [
            CrmOutreach(
                provider=o.get("provider"),
                sent=o.get("sent", False),
                opened=o.get("opened", False),
                clicked=o.get("clicked", False),
                confidence=o.get("confidence"),
                campaign_name=o.get("campaignName"),
            )
            for o in c.get("outreach", [])
        ]
        pulse.contacts.append(
            CrmContact(
                email=c.get("email"),
                first_name=c.get("firstName"),
                last_name=c.get("lastName"),
                title=c.get("title"),
                lifecycle_stage=c.get("lifecycleStage"),
                last_conversation_date=c.get("lastConversationDate"),
                outreach=outreach,
            )
        )

    # Parse deals/opportunities
    for opp in data.get("opportunities", []):
        pulse.opportunities.append(
            CrmDeal(
                title=opp.get("title"),
                stage=opp.get("stage"),
                deal_size=opp.get("dealSize"),
                probability=opp.get("probability"),
                days_in_stage=opp.get("daysInStage"),
                close_date=opp.get("closeDate"),
                pipeline=opp.get("hubspotPipeline"),
            )
        )

    # Parse meetings
    for m in data.get("meetings", []):
        pulse.meetings.append(
            CrmMeeting(
                title=m.get("title"),
                date=m.get("date"),
                attendees=m.get("attendees", []),
                summary=m.get("summaryShort"),
                key_points=m.get("keyPoints", []),
                action_items=m.get("actionItems", []),
            )
        )

    return pulse
