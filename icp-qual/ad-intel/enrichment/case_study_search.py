"""Case Study Search

Searches ad/tech platform case study pages (Meta, Google, TikTok, Shopify, etc.)
for mentions of a brand, extracts key metrics, and returns structured results.

Usage in ICP protocol:
    studies = await fetch_case_studies("seed.com", "Seed")
    report.case_studies = studies

Searches Google News RSS for platform-specific case study URLs, then fetches
each page to extract performance metrics (ROAS, CPA, conversion, revenue, etc.).
"""

from __future__ import annotations

import asyncio
import logging
import re
from urllib.parse import quote_plus
from xml.etree import ElementTree

import httpx

from models.ad_models import PlatformCaseStudy

logger = logging.getLogger(__name__)

# Platform-specific search queries — {company} is replaced at runtime
PLATFORM_SEARCHES: list[tuple[str, str]] = [
    ("Meta", 'site:facebook.com/business "{company}" case study'),
    ("Meta", 'site:meta.com/business "{company}" success story'),
    ("Google", 'site:thinkwithgoogle.com "{company}"'),
    ("Google", 'site:blog.google "{company}" case study'),
    ("TikTok", 'site:tiktok.com/business "{company}" case study'),
    ("Shopify", 'site:shopify.com "{company}" success story OR case study'),
    ("Klaviyo", 'site:klaviyo.com "{company}" case study'),
    ("Triple Whale", 'site:triplewhale.com "{company}" case study'),
    ("YouTube", 'site:youtube.com/ads "{company}" case study'),
]

# Regex patterns for extracting key metrics from case study pages
_METRIC_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\d+(?:\.\d+)?x\s*ROAS", re.IGNORECASE),
    re.compile(r"\d+(?:\.\d+)?%\s*(?:increase|improvement|growth|lift|higher|boost)", re.IGNORECASE),
    re.compile(r"\d+(?:\.\d+)?%\s*(?:lower|decrease|reduction|drop)\s*(?:CPA|CPM|CAC|cost)", re.IGNORECASE),
    re.compile(r"\$\d+(?:\.\d+)?[MBK]?\s*(?:revenue|sales|spend|budget)", re.IGNORECASE),
    re.compile(r"\d+(?:\.\d+)?%\s*(?:conversion|CTR|click-through|open rate)", re.IGNORECASE),
    re.compile(r"\d+(?:\.\d+)?x\s*(?:return|increase|growth|improvement)", re.IGNORECASE),
]

_GOOGLE_RSS_URL = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
_MAX_RESULTS = 10
_MAX_METRICS_PER_STUDY = 5


async def _search_platform(
    platform: str,
    query: str,
    client: httpx.AsyncClient,
) -> list[PlatformCaseStudy]:
    """Search Google News RSS for a single platform query.

    Returns a list of PlatformCaseStudy with title and URL populated.
    """
    rss_url = _GOOGLE_RSS_URL.format(query=quote_plus(query))

    try:
        resp = await client.get(rss_url)
        resp.raise_for_status()
    except Exception as e:
        logger.debug(f"Case study search: RSS fetch failed for {platform!r}: {e}")
        return []

    results: list[PlatformCaseStudy] = []
    try:
        root = ElementTree.fromstring(resp.text)
        for item in root.iter("item"):
            title_el = item.find("title")
            link_el = item.find("link")
            title = title_el.text.strip() if title_el is not None and title_el.text else ""
            url = link_el.text.strip() if link_el is not None and link_el.text else None

            if not title and not url:
                continue

            results.append(PlatformCaseStudy(
                platform=platform,
                title=title,
                url=url,
            ))
    except ElementTree.ParseError as e:
        logger.debug(f"Case study search: RSS parse error for {platform!r}: {e}")

    return results


def _extract_metrics(html: str) -> list[str]:
    """Extract up to _MAX_METRICS_PER_STUDY key metrics from page HTML."""
    metrics: list[str] = []
    seen: set[str] = set()

    for pattern in _METRIC_PATTERNS:
        for match in pattern.finditer(html):
            metric = match.group(0).strip()
            normalized = metric.lower()
            if normalized not in seen:
                seen.add(normalized)
                metrics.append(metric)
                if len(metrics) >= _MAX_METRICS_PER_STUDY:
                    return metrics

    return metrics


async def _enrich_case_study(
    study: PlatformCaseStudy,
    client: httpx.AsyncClient,
) -> PlatformCaseStudy:
    """Fetch the case study page and extract key metrics."""
    if not study.url:
        return study

    try:
        resp = await client.get(study.url, timeout=10, follow_redirects=True)
        resp.raise_for_status()
        study.key_metrics = _extract_metrics(resp.text)
    except Exception as e:
        logger.debug(f"Case study search: page fetch failed for {study.url}: {e}")

    return study


async def fetch_case_studies(
    domain: str,
    company_name: str | None = None,
) -> list[PlatformCaseStudy]:
    """Search ad/tech platforms for case studies mentioning the brand.

    Searches Meta, Google, TikTok, Shopify, Klaviyo, Triple Whale, and
    YouTube case study pages via Google News RSS, then fetches each page
    to extract key performance metrics.

    Args:
        domain: Company domain (e.g. "seed.com")
        company_name: Optional company name — falls back to domain stem.

    Returns:
        List of PlatformCaseStudy (max 10, deduplicated by URL). Never raises.
    """
    company = company_name or domain.split(".")[0]
    logger.info(f"Case study search: starting for {company!r} ({domain})")

    async with httpx.AsyncClient(
        timeout=15,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; UpscaleBot/1.0)"},
    ) as client:
        # Build queries and search all platforms concurrently
        tasks = [
            _search_platform(platform, query.replace("{company}", company), client)
            for platform, query in PLATFORM_SEARCHES
        ]
        platform_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten and deduplicate by URL
        seen_urls: set[str] = set()
        studies: list[PlatformCaseStudy] = []

        for result in platform_results:
            if isinstance(result, Exception):
                logger.debug(f"Case study search: platform task failed: {result}")
                continue
            for study in result:
                url_key = study.url or study.title
                if url_key in seen_urls:
                    continue
                seen_urls.add(url_key)
                studies.append(study)

        # Limit before enrichment to avoid excessive fetches
        studies = studies[:_MAX_RESULTS]

        # Enrich each case study with key metrics concurrently
        if studies:
            enriched = await asyncio.gather(
                *[_enrich_case_study(s, client) for s in studies],
                return_exceptions=True,
            )
            studies = [
                s for s in enriched
                if isinstance(s, PlatformCaseStudy)
            ]

    logger.info(f"Case study search: found {len(studies)} case studies for {company!r}")
    return studies
