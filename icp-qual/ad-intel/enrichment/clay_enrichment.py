"""Clay MCP Enrichment Integration

Parses Clay MCP find-and-enrich-company results and merges
them into the BrandIntelligence model for use in pitch reports.

Enrichments requested:
- Company Competitors
- Revenue Model
- Target Audience
- Investors (Crunchbase)
- Latest Funding (Crunchbase)

Can be used in two modes:
1. **Automatic** (default): The pipeline orchestrator calls ``fetch_clay_enrichment()``
   which hits the Clay API directly and returns a ``ClayEnrichment`` object.
2. **Manual override**: Pass ``--clay-json`` to ``main.py`` to load pre-fetched
   Clay JSON from disk (useful for debugging or when the API is unavailable).
"""

import asyncio
import json
import logging
import os
import re
from pathlib import Path

import httpx

from models.ad_models import BrandIntelligence, ClayEnrichment, PurchaseModel

logger = logging.getLogger(__name__)

# Clay API configuration
CLAY_API_BASE = "https://api.clay.com/v1"
CLAY_ENRICHMENTS = [
    "Company Competitors",
    "Revenue Model",
    "Target Audience",
    "Investors",
    "Latest Funding",
    "Founders",
    "Headcount Growth",
    "Recent News",
]

# Polling: Clay enrichments are async — we submit, then poll until done.
CLAY_POLL_INTERVAL = 3  # seconds between polls
CLAY_POLL_TIMEOUT = 90  # max seconds to wait for enrichments


async def fetch_clay_enrichment(
    domain: str,
    api_key: str | None = None,
) -> ClayEnrichment:
    """Fetch Clay enrichment data for a domain via the Clay API.

    Calls Clay's find-and-enrich-company endpoint, polls for completion,
    then parses results into a ``ClayEnrichment`` model.

    Args:
        domain: Company domain (e.g. "seed.com")
        api_key: Clay API key (falls back to CLAY_API_KEY env var)

    Returns:
        ClayEnrichment with parsed data, or empty ClayEnrichment on failure.
    """
    api_key = api_key or os.getenv("CLAY_API_KEY")
    if not api_key:
        logger.warning("CLAY_API_KEY not set — skipping Clay enrichment")
        return ClayEnrichment()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Step 1: Submit enrichment request
            payload = {
                "domain": domain,
                "enrichments": CLAY_ENRICHMENTS,
            }
            resp = await client.post(
                f"{CLAY_API_BASE}/find-and-enrich-company",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            initial = resp.json()

            # If all enrichments are already completed (cached), parse immediately
            task_id = initial.get("task_id")
            if not task_id:
                # No task_id means results came back synchronously
                parsed = parse_clay_enrichments(initial, domain)
                return _parsed_to_clay_enrichment(parsed, raw_data=initial)

            # Step 2: Poll for completion
            elapsed = 0
            while elapsed < CLAY_POLL_TIMEOUT:
                await asyncio.sleep(CLAY_POLL_INTERVAL)
                elapsed += CLAY_POLL_INTERVAL

                poll_resp = await client.get(
                    f"{CLAY_API_BASE}/get-task/{task_id}",
                    headers=headers,
                )
                poll_resp.raise_for_status()
                task_data = poll_resp.json()

                status = task_data.get("status", "")
                if status == "completed":
                    parsed = parse_clay_enrichments(task_data, domain)
                    return _parsed_to_clay_enrichment(parsed, raw_data=task_data)
                elif status in ("failed", "error"):
                    logger.warning(f"Clay enrichment failed for {domain}: {task_data.get('error', status)}")
                    return ClayEnrichment()

            logger.warning(f"Clay enrichment timed out after {CLAY_POLL_TIMEOUT}s for {domain}")
            return ClayEnrichment()

    except httpx.HTTPStatusError as e:
        logger.warning(f"Clay API HTTP error for {domain}: {e.response.status_code} {e.response.text[:200]}")
        return ClayEnrichment()
    except Exception as e:
        logger.warning(f"Clay enrichment error for {domain}: {e}")
        return ClayEnrichment()


def _parsed_to_clay_enrichment(parsed: dict, raw_data: dict | None = None) -> ClayEnrichment:
    """Convert the parsed dict from ``parse_clay_enrichments`` to a ``ClayEnrichment`` model."""
    has_data = any([
        parsed.get("competitors"),
        parsed.get("founders"),
        parsed.get("investors"),
        parsed.get("revenue_model"),
        parsed.get("target_audience"),
        parsed.get("headquarters"),
    ])
    return ClayEnrichment(
        enriched=has_data,
        logo_url=parsed.get("logo_url"),
        headquarters=parsed.get("headquarters"),
        competitors=parsed.get("competitors", []),
        revenue_model=parsed.get("revenue_model"),
        target_audience=parsed.get("target_audience"),
        founders=parsed.get("founders", []),
        investors=parsed.get("investors", []),
        latest_funding=parsed.get("recent_funding_round") or parsed.get("total_funding"),
        headcount_growth=(
            f"{parsed['headcount_growth']['growth_12m']}% (12mo)"
            if parsed.get("headcount_growth") and parsed["headcount_growth"].get("growth_12m")
            else None
        ),
        recent_news=[parsed["recent_news"]] if parsed.get("recent_news") else [],
        raw_data=raw_data,
    )


def parse_clay_enrichments(clay_data: dict, domain: str) -> dict:
    """Parse Clay MCP response into a clean dict for BrandIntelligence.

    Args:
        clay_data: Raw Clay MCP response (from find-and-enrich-company or get-task)
        domain: The company domain (e.g. "seed.com")

    Returns:
        dict with keys: competitors, revenue_model, target_audience,
        target_demographics, headcount_growth, recent_news
    """
    result = {
        "competitors": [],
        "revenue_model": None,
        "target_audience": None,
        "target_demographics": None,
        "headcount_growth": None,
        "recent_news": None,
        # Company info from base response
        "logo_url": None,
        # Crunchbase enrichments
        "headquarters": None,
        "founders": [],
        "investors": [],
        "total_funding": None,
        "recent_funding_round": None,
    }

    # Find the company data
    companies = clay_data.get("companies", {})
    company = companies.get(domain, {})

    # Extract base company fields (logo, HQ, funding from base response)
    result["logo_url"] = company.get("logo_url") or company.get("logo")
    result["headquarters"] = company.get("headquarters") or company.get("hq_location")

    # Total funding from base response (e.g. "$10M - $50M" range or exact)
    funding_range = company.get("total_funding_amount_range_usd")
    if funding_range:
        result["total_funding"] = funding_range

    enrichments = company.get("enrichments", {})

    for _id, enrichment in enrichments.items():
        name = enrichment.get("name", "")
        value = enrichment.get("value")
        state = enrichment.get("state", "")

        if state != "completed" or not value:
            continue

        if name == "Company Competitors":
            # Value is comma-separated: "Garden of Life, Renew Life, Culturelle"
            result["competitors"] = [c.strip() for c in value.split(",") if c.strip()]

        elif name == "Revenue Model":
            # Value: "Subscription, Transactional"
            result["revenue_model"] = value.strip()

        elif name == "Target Audience":
            # Value is markdown with #### Key Results and #### Research Summary
            result["target_audience"] = _extract_key_results(value)
            result["target_demographics"] = _extract_demographics(value)

        elif name == "Headcount Growth":
            try:
                hc = json.loads(value) if isinstance(value, str) else value
                result["headcount_growth"] = {
                    "current": hc.get("employee_count"),
                    "growth_12m": hc.get("percent_employee_growth_over_last_12_months"),
                    "growth_24m": hc.get("percent_employee_growth_over_last_24_months"),
                }
            except (json.JSONDecodeError, TypeError):
                pass

        elif name == "Recent News":
            result["recent_news"] = value

        elif name == "Investors":
            # Value may be comma-separated names or JSON list
            try:
                investors = json.loads(value) if isinstance(value, str) and value.startswith("[") else None
                if isinstance(investors, list):
                    result["investors"] = [str(i).strip() for i in investors if i]
                else:
                    result["investors"] = [i.strip() for i in value.split(",") if i.strip()]
            except (json.JSONDecodeError, TypeError):
                result["investors"] = [i.strip() for i in value.split(",") if i.strip()]

        elif name == "Latest Funding":
            # Value may be JSON with round info or plain text
            try:
                funding = json.loads(value) if isinstance(value, str) else value
                if isinstance(funding, dict):
                    round_name = funding.get("round_name") or funding.get("series") or ""
                    amount = funding.get("amount") or funding.get("money_raised") or ""
                    date = funding.get("date") or funding.get("announced_on") or ""
                    parts = [p for p in [round_name, str(amount), date] if p]
                    result["recent_funding_round"] = " - ".join(parts) if parts else value
                    # Also update total funding if we have a better number
                    total = funding.get("total_funding") or funding.get("total_funding_usd")
                    if total:
                        result["total_funding"] = str(total)
                else:
                    result["recent_funding_round"] = str(value).strip()
            except (json.JSONDecodeError, TypeError):
                result["recent_funding_round"] = str(value).strip()

        elif name == "Founders":
            # Value is comma-separated names
            result["founders"] = [f.strip() for f in value.split(",") if f.strip()]

    return result


def _extract_key_results(text: str) -> str:
    """Extract the Key Results line from Clay's markdown response."""
    # Pattern: #### Key Results\n<content>
    match = re.search(r"####\s*Key\s*Results\s*\n(.+?)(?:\n####|\Z)", text, re.DOTALL)
    if match:
        return match.group(1).strip().split("\n")[0].strip()
    return text[:200] if text else ""


def _extract_demographics(text: str) -> str:
    """Extract age range and demographic info from Clay's target audience."""
    # Look for age range patterns
    age_match = re.search(r"(\d{2})\s*[-–]\s*(\d{2})\s*(?:years?)?", text)
    age_range = f"{age_match.group(1)}-{age_match.group(2)}" if age_match else None

    # Look for the research summary
    match = re.search(r"####\s*Research\s*Summary\s*\n(.+?)(?:\n####|\Z)", text, re.DOTALL)
    summary = match.group(1).strip()[:300] if match else ""

    if age_range:
        return f"Age {age_range}. {summary}"
    return summary


def merge_clay_into_intel(intel: BrandIntelligence, clay_parsed: dict) -> BrandIntelligence:
    """Merge parsed Clay data into an existing BrandIntelligence object."""

    # Competitors (Clay is more reliable than Google scraping)
    if clay_parsed.get("competitors"):
        intel.competitors = clay_parsed["competitors"]

    # Revenue model → purchase model
    rev_model = (clay_parsed.get("revenue_model") or "").lower()
    if "subscription" in rev_model:
        intel.purchase_model = PurchaseModel.SUBSCRIPTION
        intel.purchase_model_signals.insert(0, f"Clay: Revenue model = {clay_parsed['revenue_model']}")
    elif any(w in rev_model for w in ["transactional", "one-time", "single"]):
        if intel.purchase_model == PurchaseModel.UNKNOWN:
            intel.purchase_model = PurchaseModel.SINGLE_PURCHASE
            intel.purchase_model_signals.insert(0, f"Clay: Revenue model = {clay_parsed['revenue_model']}")

    # Target audience
    if clay_parsed.get("target_audience"):
        intel.target_audience = clay_parsed["target_audience"]
    if clay_parsed.get("target_demographics"):
        intel.target_demographics = clay_parsed["target_demographics"]

    # Logo
    if clay_parsed.get("logo_url"):
        intel.logo_url = clay_parsed["logo_url"]

    # Crunchbase / company info
    if clay_parsed.get("headquarters"):
        intel.headquarters = clay_parsed["headquarters"]
    if clay_parsed.get("founders"):
        intel.founders = clay_parsed["founders"]
    if clay_parsed.get("investors"):
        intel.investors = clay_parsed["investors"]
    if clay_parsed.get("total_funding"):
        intel.total_funding = clay_parsed["total_funding"]
    if clay_parsed.get("recent_funding_round"):
        intel.recent_funding_round = clay_parsed["recent_funding_round"]

    return intel


def load_and_merge(report_path: str, clay_path: str) -> None:
    """Load report JSON and Clay JSON, merge, and save."""
    report_data = json.loads(Path(report_path).read_text())
    clay_data = json.loads(Path(clay_path).read_text())

    domain = report_data.get("domain", "")
    parsed = parse_clay_enrichments(clay_data, domain)

    # Merge into brand_intel section
    brand_intel = report_data.get("brand_intel", {})
    if parsed["competitors"]:
        brand_intel["competitors"] = parsed["competitors"]
    if parsed["target_audience"]:
        brand_intel["target_audience"] = parsed["target_audience"]
    if parsed["target_demographics"]:
        brand_intel["target_demographics"] = parsed["target_demographics"]

    rev_model = (parsed.get("revenue_model") or "").lower()
    if "subscription" in rev_model:
        brand_intel["purchase_model"] = "subscription"
    elif "transactional" in rev_model:
        brand_intel["purchase_model"] = "single_purchase"

    # Crunchbase / company info
    if parsed.get("logo_url"):
        brand_intel["logo_url"] = parsed["logo_url"]
    if parsed.get("headquarters"):
        brand_intel["headquarters"] = parsed["headquarters"]
    if parsed.get("founders"):
        brand_intel["founders"] = parsed["founders"]
    if parsed.get("investors"):
        brand_intel["investors"] = parsed["investors"]
    if parsed.get("total_funding"):
        brand_intel["total_funding"] = parsed["total_funding"]
    if parsed.get("recent_funding_round"):
        brand_intel["recent_funding_round"] = parsed["recent_funding_round"]

    report_data["brand_intel"] = brand_intel

    # Save updated report
    Path(report_path).write_text(json.dumps(report_data, indent=2, default=str))
    logger.info(f"Merged Clay data into {report_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", required=True)
    parser.add_argument("--clay-json", help="Path to Clay JSON file")
    parser.add_argument("--report-dir", default="output/reports")
    args = parser.parse_args()

    report_path = f"{args.report_dir}/{args.domain}.json"
    clay_path = args.clay_json or f"output/clay/{args.domain}.json"

    logging.basicConfig(level=logging.INFO)
    load_and_merge(report_path, clay_path)
    print(f"Done: merged Clay enrichment into {report_path}")
