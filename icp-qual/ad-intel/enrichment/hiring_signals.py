"""Hiring & Growth Signals Enrichment

Fetches open-job and headcount-growth data for a brand domain, then
flags marketing-related roles.  Uses Clay API data when available
(either pre-fetched or fetched on demand) and falls back to lightweight
scraping when Clay is unavailable.

Enrichments consumed from Clay:
- Open Jobs
- Headcount Growth
"""

import asyncio
import json
import logging
import os
import re
from typing import Optional

import httpx

from models.ad_models import HiringIntel, JobPosting

logger = logging.getLogger(__name__)

# Clay API configuration (mirrors clay_enrichment.py)
CLAY_API_BASE = "https://api.clay.com/v1"
CLAY_HIRING_ENRICHMENTS = ["Open Jobs", "Headcount Growth"]

# Polling: Clay enrichments are async — we submit, then poll until done.
CLAY_POLL_INTERVAL = 3  # seconds between polls
CLAY_POLL_TIMEOUT = 90  # max seconds to wait for enrichments

# Keywords used to flag a job posting as marketing-related
MARKETING_KEYWORDS = [
    "marketing", "growth", "paid", "media", "performance", "creative",
    "brand", "acquisition", "demand gen", "ctv", "tv", "streaming",
    "video", "social media", "content", "seo", "sem", "ppc",
    "digital marketing", "advertising", "campaign",
]

# Lightweight scraping config
SCRAPE_TIMEOUT = 15  # seconds
SCRAPE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def fetch_hiring_intel(
    domain: str,
    company_name: str | None = None,
    clay_data: dict | None = None,
) -> HiringIntel:
    """Fetch hiring & growth signals for *domain*.

    Args:
        domain: Company domain (e.g. ``"seed.com"``).
        company_name: Optional human-readable company name (used for scrape
            fallback queries).
        clay_data: Optional pre-fetched Clay response dict.  When provided
            the Clay API is **not** called again — the data is parsed directly.

    Returns:
        ``HiringIntel`` populated with whatever data was available.
        Never raises; errors are captured in ``HiringIntel.error``.
    """
    try:
        # 1. Try Clay data (pre-fetched or on-demand)
        if clay_data is not None:
            logger.info(f"Parsing pre-fetched Clay data for {domain}")
            return _parse_clay_response(clay_data, domain)

        api_key = os.getenv("CLAY_API_KEY")
        if api_key:
            logger.info(f"Fetching hiring signals from Clay API for {domain}")
            result = await _fetch_from_clay(domain, api_key)
            if result.found:
                return result
            logger.info(f"Clay returned no hiring data for {domain} — falling back to scrape")

        # 2. Fallback: lightweight scrape
        logger.info(f"Scraping hiring signals for {domain}")
        return await _scrape_hiring_signals(domain, company_name)

    except Exception as e:
        logger.warning(f"Hiring signals error for {domain}: {e}")
        return HiringIntel(error=str(e))


# ---------------------------------------------------------------------------
# Clay API helpers
# ---------------------------------------------------------------------------

async def _fetch_from_clay(domain: str, api_key: str) -> HiringIntel:
    """Hit Clay API directly for Open Jobs + Headcount Growth."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Submit enrichment request
            payload = {
                "domain": domain,
                "enrichments": CLAY_HIRING_ENRICHMENTS,
            }
            resp = await client.post(
                f"{CLAY_API_BASE}/find-and-enrich-company",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            initial = resp.json()

            # Synchronous result (cached)
            task_id = initial.get("task_id")
            if not task_id:
                return _parse_clay_response(initial, domain)

            # Poll for completion
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
                    return _parse_clay_response(task_data, domain)
                elif status in ("failed", "error"):
                    logger.warning(
                        f"Clay hiring enrichment failed for {domain}: "
                        f"{task_data.get('error', status)}"
                    )
                    return HiringIntel(error=f"Clay task failed: {task_data.get('error', status)}")

            logger.warning(f"Clay hiring enrichment timed out after {CLAY_POLL_TIMEOUT}s for {domain}")
            return HiringIntel(error="Clay enrichment timed out")

    except httpx.HTTPStatusError as e:
        logger.warning(f"Clay API HTTP error for {domain}: {e.response.status_code} {e.response.text[:200]}")
        return HiringIntel(error=f"Clay HTTP {e.response.status_code}")
    except Exception as e:
        logger.warning(f"Clay hiring enrichment error for {domain}: {e}")
        return HiringIntel(error=str(e))


# ---------------------------------------------------------------------------
# Clay response parsing
# ---------------------------------------------------------------------------

def _parse_clay_response(clay_data: dict, domain: str) -> HiringIntel:
    """Parse a Clay API response into a ``HiringIntel`` object."""
    companies = clay_data.get("companies", {})
    company = companies.get(domain, {})
    enrichments = company.get("enrichments", {})

    all_jobs: list[JobPosting] = []
    growth_12m: float | None = None
    growth_24m: float | None = None

    for _id, enrichment in enrichments.items():
        name = enrichment.get("name", "")
        value = enrichment.get("value")
        state = enrichment.get("state", "")

        if state != "completed" or not value:
            continue

        if name == "Open Jobs":
            all_jobs = _parse_open_jobs(value)

        elif name == "Headcount Growth":
            growth_12m, growth_24m = _parse_headcount_growth(value)

    marketing_jobs = [j for j in all_jobs if j.is_marketing]
    velocity = _determine_velocity(growth_12m)

    return HiringIntel(
        found=bool(all_jobs or growth_12m is not None),
        open_jobs_count=len(all_jobs),
        marketing_jobs=marketing_jobs,
        all_jobs=all_jobs,
        hiring_velocity=velocity,
        headcount_growth_12m=growth_12m,
        headcount_growth_24m=growth_24m,
    )


def _parse_open_jobs(value) -> list[JobPosting]:
    """Parse Clay's Open Jobs enrichment value into ``JobPosting`` objects."""
    try:
        jobs_raw = json.loads(value) if isinstance(value, str) else value
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"Could not parse Open Jobs value: {str(value)[:200]}")
        return []

    if not isinstance(jobs_raw, list):
        # Sometimes the value is a single dict or a summary string
        if isinstance(jobs_raw, dict):
            jobs_raw = [jobs_raw]
        else:
            return []

    postings: list[JobPosting] = []
    for raw in jobs_raw:
        if isinstance(raw, str):
            # Plain title string
            postings.append(_make_job_posting(title=raw))
        elif isinstance(raw, dict):
            postings.append(
                _make_job_posting(
                    title=raw.get("title") or raw.get("job_title") or raw.get("name", ""),
                    department=raw.get("department") or raw.get("team"),
                    location=raw.get("location") or raw.get("city"),
                    url=raw.get("url") or raw.get("link") or raw.get("apply_url"),
                )
            )
    return postings


def _parse_headcount_growth(value) -> tuple[float | None, float | None]:
    """Parse Clay's Headcount Growth enrichment value."""
    try:
        hc = json.loads(value) if isinstance(value, str) else value
    except (json.JSONDecodeError, TypeError):
        return None, None

    if not isinstance(hc, dict):
        return None, None

    growth_12m = hc.get("percent_employee_growth_over_last_12_months")
    growth_24m = hc.get("percent_employee_growth_over_last_24_months")

    # Coerce to float if present
    try:
        growth_12m = float(growth_12m) if growth_12m is not None else None
    except (ValueError, TypeError):
        growth_12m = None
    try:
        growth_24m = float(growth_24m) if growth_24m is not None else None
    except (ValueError, TypeError):
        growth_24m = None

    return growth_12m, growth_24m


# ---------------------------------------------------------------------------
# Scrape fallback
# ---------------------------------------------------------------------------

async def _scrape_hiring_signals(
    domain: str,
    company_name: str | None = None,
) -> HiringIntel:
    """Lightweight scrape of the brand's careers page to count open roles."""
    careers_urls = [
        f"https://{domain}/careers",
        f"https://{domain}/jobs",
        f"https://careers.{domain}",
    ]

    all_jobs: list[JobPosting] = []

    async with httpx.AsyncClient(
        timeout=SCRAPE_TIMEOUT,
        headers=SCRAPE_HEADERS,
        follow_redirects=True,
    ) as client:
        for url in careers_urls:
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    continue
                page_jobs = _extract_jobs_from_html(resp.text, url)
                if page_jobs:
                    all_jobs.extend(page_jobs)
                    break  # found a working careers page
            except httpx.HTTPError:
                continue

    marketing_jobs = [j for j in all_jobs if j.is_marketing]

    return HiringIntel(
        found=bool(all_jobs),
        open_jobs_count=len(all_jobs),
        marketing_jobs=marketing_jobs,
        all_jobs=all_jobs,
    )


def _extract_jobs_from_html(html: str, base_url: str) -> list[JobPosting]:
    """Best-effort extraction of job titles from a careers HTML page.

    Looks for common patterns: ``<h2>``, ``<h3>``, ``<a>`` elements inside
    containers that look like job listings.  This is intentionally simple —
    Clay is the preferred data source.
    """
    postings: list[JobPosting] = []

    # Pattern 1: JSON-LD structured data (most reliable)
    ld_pattern = re.compile(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.DOTALL)
    for match in ld_pattern.finditer(html):
        try:
            data = json.loads(match.group(1))
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get("@type") == "JobPosting":
                    postings.append(
                        _make_job_posting(
                            title=item.get("title", ""),
                            location=(
                                item.get("jobLocation", {}).get("address", {}).get("addressLocality")
                                if isinstance(item.get("jobLocation"), dict)
                                else None
                            ),
                            url=item.get("url"),
                        )
                    )
        except (json.JSONDecodeError, TypeError, AttributeError):
            continue

    if postings:
        return postings

    # Pattern 2: common heading patterns inside job-listing containers
    title_pattern = re.compile(
        r'<(?:h[23]|a)[^>]*class="[^"]*(?:job|position|role|opening|title)[^"]*"[^>]*>'
        r'\s*([^<]{3,80})\s*</(?:h[23]|a)>',
        re.IGNORECASE,
    )
    for match in title_pattern.finditer(html):
        title = match.group(1).strip()
        if title:
            postings.append(_make_job_posting(title=title))

    return postings


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_job_posting(
    title: str,
    department: Optional[str] = None,
    location: Optional[str] = None,
    url: Optional[str] = None,
) -> JobPosting:
    """Create a ``JobPosting`` and auto-flag ``is_marketing``."""
    return JobPosting(
        title=title,
        department=department,
        location=location,
        url=url,
        is_marketing=_is_marketing_role(title, department),
    )


def _is_marketing_role(title: str, department: str | None = None) -> bool:
    """Return True if the title (or department) matches a marketing keyword."""
    text = (title + " " + (department or "")).lower()
    return any(kw in text for kw in MARKETING_KEYWORDS)


def _determine_velocity(growth_12m: float | None) -> str | None:
    """Classify 12-month headcount growth into a velocity label."""
    if growth_12m is None:
        return None
    if growth_12m > 20:
        return "accelerating"
    if growth_12m >= 5:
        return "stable"
    return "slowing"
