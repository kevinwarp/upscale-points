"""Thought Leadership & Podcast Appearance Search

Discovers podcast appearances, speaking engagements, and interview content
by company leaders (founders, CEO, CMO) via Google News RSS search.

Usage in ICP protocol:
    appearances = await fetch_thought_leadership(
        "seed.com",
        company_name="Seed",
        key_people=[{"name": "Ara Katz", "title": "Co-Founder & Co-CEO"}],
    )
    report.podcast_appearances = appearances

Returns structured PodcastAppearance records. Always returns a list (never raises).
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from urllib.parse import quote

import httpx

from models.ad_models import PodcastAppearance

logger = logging.getLogger(__name__)

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"

# Maximum results to return after deduplication
MAX_RESULTS = 15


async def fetch_thought_leadership(
    domain: str,
    company_name: str | None = None,
    key_people: list[dict] | None = None,  # [{"name": "...", "title": "..."}]
    clay_founders: list[str] | None = None,
) -> list[PodcastAppearance]:
    """Search for podcast and thought leadership appearances by company leaders.

    Builds a people list from key_people, clay_founders, or falls back to
    company-name-only search. Queries Google News RSS for podcast/interview
    mentions and returns deduplicated, structured results.

    Args:
        domain: Company domain (e.g. "seed.com")
        company_name: Human-readable company name for search queries
        key_people: List of dicts with "name" and optional "title" keys
        clay_founders: List of founder names (fallback if key_people not provided)

    Returns:
        List of PodcastAppearance (max 15). Empty list on error.
    """
    # Build list of people to search
    people: list[dict] = []
    if key_people:
        people = [
            {"name": p.get("name", ""), "title": p.get("title")}
            for p in key_people
            if p.get("name")
        ]
    elif clay_founders:
        people = [{"name": name, "title": None} for name in clay_founders if name]

    # Build search queries
    queries = _build_queries(company_name or domain, people)

    if not queries:
        logger.info(f"Thought leadership: no search queries for {domain}")
        return []

    # Execute all RSS searches
    appearances: list[PodcastAppearance] = []
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            for query, person_name, person_title in queries:
                results = await _search_rss(client, query, person_name, person_title)
                appearances.extend(results)
    except Exception as e:
        logger.error(f"Thought leadership: error for {domain}: {e}")
        return appearances[:MAX_RESULTS]

    # Deduplicate by URL and limit
    appearances = _deduplicate(appearances)
    logger.info(f"Thought leadership: found {len(appearances)} appearances for {domain}")
    return appearances[:MAX_RESULTS]


def _build_queries(
    company_name: str,
    people: list[dict],
) -> list[tuple[str, str, str | None]]:
    """Build Google News RSS search queries.

    Returns list of (query_string, person_name, person_title) tuples.
    """
    queries: list[tuple[str, str, str | None]] = []

    for person in people:
        name = person["name"]
        title = person.get("title")
        q = f'"{name}" podcast OR interview OR speaking'
        queries.append((q, name, title))

    # Company-level podcast search
    q = f'"{company_name}" podcast episode'
    queries.append((q, "", None))

    return queries


async def _search_rss(
    client: httpx.AsyncClient,
    query: str,
    person_name: str,
    person_title: str | None,
) -> list[PodcastAppearance]:
    """Execute a single Google News RSS search and parse results."""
    try:
        resp = await client.get(
            GOOGLE_NEWS_RSS,
            params={
                "q": query,
                "hl": "en-US",
                "gl": "US",
                "ceid": "US:en",
            },
        )

        if resp.status_code != 200:
            logger.debug(f"Thought leadership RSS: {resp.status_code} for query: {query[:60]}")
            return []

        return _parse_rss_items(resp.text, person_name, person_title)

    except httpx.TimeoutException:
        logger.debug(f"Thought leadership RSS: timeout for query: {query[:60]}")
        return []
    except Exception as e:
        logger.debug(f"Thought leadership RSS: error for query: {query[:60]}: {e}")
        return []


def _parse_rss_items(
    xml_text: str,
    person_name: str,
    person_title: str | None,
) -> list[PodcastAppearance]:
    """Parse Google News RSS XML into PodcastAppearance records."""
    appearances: list[PodcastAppearance] = []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.debug(f"Thought leadership: RSS parse error: {e}")
        return []

    # Google News RSS structure: rss > channel > item
    channel = root.find("channel")
    if channel is None:
        return []

    for item in channel.findall("item"):
        title_el = item.find("title")
        link_el = item.find("link")
        pub_date_el = item.find("pubDate")
        source_el = item.find("source")

        episode_title = title_el.text.strip() if title_el is not None and title_el.text else ""
        url = link_el.text.strip() if link_el is not None and link_el.text else None
        date = pub_date_el.text.strip() if pub_date_el is not None and pub_date_el.text else None

        # Try to extract show/source name from the RSS source element
        show_name = ""
        if source_el is not None:
            show_name = (source_el.text or "").strip()

        if not episode_title:
            continue

        appearances.append(
            PodcastAppearance(
                person_name=person_name,
                person_title=person_title,
                show_name=show_name,
                episode_title=episode_title,
                url=url,
                date=date,
            )
        )

    return appearances


def _deduplicate(appearances: list[PodcastAppearance]) -> list[PodcastAppearance]:
    """Remove duplicate appearances by URL, keeping first occurrence."""
    seen_urls: set[str] = set()
    unique: list[PodcastAppearance] = []

    for a in appearances:
        if a.url and a.url in seen_urls:
            continue
        if a.url:
            seen_urls.add(a.url)
        unique.append(a)

    return unique
