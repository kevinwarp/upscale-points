"""News & Media Mentions Search

Fetches recent news coverage for a brand from two sources:
1. Clay "Recent News" enrichment (pre-fetched text summaries)
2. Google News RSS feed (live search)

Items are auto-categorized by type (funding, product_launch, partnership,
m_and_a, press) and deduplicated by headline similarity.

Usage in ICP protocol:
    news = await fetch_news_intel("seed.com", company_name="Seed Health")
    report.news_items = news
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

import httpx

from models.ad_models import NewsItem

logger = logging.getLogger(__name__)

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"
MAX_ITEMS = 20
REQUEST_TIMEOUT = 15

# ── Category keyword rules ──────────────────────────────────────────

_CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("funding", ["funding", "raised", "series", "investment"]),
    ("product_launch", ["launch", "new product", "introduces", "unveils"]),
    ("partnership", ["partner", "partnership", "collaboration", "integration"]),
    ("m_and_a", ["acquir", "merger", "bought"]),
]


def _categorize(headline: str) -> str:
    """Assign a category based on keyword matching in the headline."""
    lower = headline.lower()
    for category, keywords in _CATEGORY_RULES:
        if any(kw in lower for kw in keywords):
            return category
    return "press"


# ── Clay news parsing ───────────────────────────────────────────────

def _parse_clay_news(clay_news: list[str]) -> list[NewsItem]:
    """Parse Clay's 'Recent News' enrichment strings into NewsItem objects.

    Clay returns news as free-text summaries, e.g.:
        "Seed Health launches new probiotic line (TechCrunch, 2024-03-15)"
        "Seed Health raises $40M Series B"

    We extract what we can and categorize each item.
    """
    items: list[NewsItem] = []
    for raw in clay_news:
        raw = raw.strip()
        if not raw:
            continue

        # Try to extract source and date from parenthetical at end
        # e.g. "(TechCrunch, 2024-03-15)" or "(Forbes, Jan 2024)"
        source = None
        date = None
        paren_match = re.search(r"\(([^)]+)\)\s*$", raw)
        if paren_match:
            paren_text = paren_match.group(1)
            parts = [p.strip() for p in paren_text.split(",")]
            if len(parts) >= 2:
                source = parts[0]
                date = parts[-1]
            elif len(parts) == 1:
                # Could be source or date
                if re.search(r"\d{4}", parts[0]):
                    date = parts[0]
                else:
                    source = parts[0]
            # Use text before parenthetical as headline
            headline = raw[: paren_match.start()].strip()
        else:
            headline = raw

        if not headline:
            continue

        items.append(
            NewsItem(
                headline=headline,
                source=source,
                date=date,
                category=_categorize(headline),
            )
        )

    return items


# ── Google News RSS parsing ─────────────────────────────────────────

async def _search_google_news(query: str, client: httpx.AsyncClient) -> list[NewsItem]:
    """Fetch and parse Google News RSS results for a query."""
    items: list[NewsItem] = []
    params = {
        "q": query,
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en",
    }

    try:
        resp = await client.get(GOOGLE_NEWS_RSS, params=params)
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.warning(f"Google News RSS HTTP error for query '{query}': {e.response.status_code}")
        return items
    except httpx.RequestError as e:
        logger.warning(f"Google News RSS request error for query '{query}': {e}")
        return items

    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError as e:
        logger.warning(f"Google News RSS XML parse error for query '{query}': {e}")
        return items

    for item_el in root.findall(".//item"):
        headline = (item_el.findtext("title") or "").strip()
        if not headline:
            continue

        # Google News titles often end with " - Source Name"
        source = None
        if " - " in headline:
            parts = headline.rsplit(" - ", 1)
            headline = parts[0].strip()
            source = parts[1].strip()

        link = (item_el.findtext("link") or "").strip() or None
        pub_date = (item_el.findtext("pubDate") or "").strip() or None

        items.append(
            NewsItem(
                headline=headline,
                source=source,
                url=link,
                date=pub_date,
                category=_categorize(headline),
            )
        )

    return items


# ── Deduplication ───────────────────────────────────────────────────

def _deduplicate(items: list[NewsItem]) -> list[NewsItem]:
    """Remove near-duplicate items using simple substring matching on headlines."""
    seen: list[str] = []
    unique: list[NewsItem] = []

    for item in items:
        lower = item.headline.lower().strip()
        if not lower:
            continue

        is_dup = False
        for prev in seen:
            # Check if one headline is a substring of the other
            if lower in prev or prev in lower:
                is_dup = True
                break

        if not is_dup:
            seen.append(lower)
            unique.append(item)

    return unique


# ── Public API ──────────────────────────────────────────────────────

async def fetch_news_intel(
    domain: str,
    company_name: str | None = None,
    clay_news: list[str] | None = None,
) -> list[NewsItem]:
    """Fetch recent news and media mentions for a brand.

    Combines Clay pre-fetched news (if available) with live Google News
    RSS results.  Items are categorized, deduplicated, and capped at 20.

    Args:
        domain: Company domain (e.g. "seed.com")
        company_name: Company name for search queries (falls back to domain)
        clay_news: Optional pre-fetched Clay "Recent News" strings

    Returns:
        list[NewsItem] — always returns a list, never raises.
    """
    all_items: list[NewsItem] = []

    # ── 1. Parse Clay news if provided ──────────────────────────────
    if clay_news:
        try:
            clay_items = _parse_clay_news(clay_news)
            all_items.extend(clay_items)
            logger.info(f"Parsed {len(clay_items)} news items from Clay for {domain}")
        except Exception as e:
            logger.warning(f"Error parsing Clay news for {domain}: {e}")

    # ── 2. Search Google News RSS ───────────────────────────────────
    name = company_name or domain.split(".")[0].capitalize()

    queries = [
        f'"{name}" news',
        f'"{name}" product launch OR partnership OR acquisition',
    ]

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            for query in queries:
                try:
                    rss_items = await _search_google_news(query, client)
                    all_items.extend(rss_items)
                    logger.info(f"Fetched {len(rss_items)} items from Google News for query: {query}")
                except Exception as e:
                    logger.warning(f"Google News search failed for query '{query}': {e}")
    except Exception as e:
        logger.warning(f"Failed to create HTTP client for news search ({domain}): {e}")

    # ── 3. Deduplicate and limit ────────────────────────────────────
    unique = _deduplicate(all_items)
    result = unique[:MAX_ITEMS]

    logger.info(f"News search for {domain}: {len(all_items)} raw -> {len(unique)} unique -> {len(result)} returned")
    return result
