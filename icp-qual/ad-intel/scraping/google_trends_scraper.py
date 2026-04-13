"""Google Trends scraper for brand search volume trends.

Fetches Google Trends data for the brand name to determine if brand
search interest is rising, stable, or declining. This is a leading
indicator of brand awareness and helps project CTV halo effect.
"""

import logging
import re
import time

from scraping.browser_agent import BrowserAgent

logger = logging.getLogger(__name__)


async def scrape_google_trends(
    agent: BrowserAgent,
    brand_name: str,
) -> dict:
    """Scrape Google Trends for brand search interest.

    Returns:
        dict with keys: trend (rising/stable/declining), search_volume (int or None),
        trend_pct_change (float), error (str or None)
    """
    result = {
        "trend": None,
        "search_volume": None,
        "trend_pct_change": None,
        "error": None,
    }

    start = time.monotonic()

    try:
        async with agent.new_page() as page:
            # Use Google Trends explore page with 12-month timeframe
            query = brand_name.replace(" ", "+")
            url = f"https://trends.google.com/trends/explore?q={query}&date=today+12-m&geo=US"
            logger.info(f"Google Trends: fetching trends for '{brand_name}'")

            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)

            # Look for the "Interest over time" widget which shows trend data
            # Google Trends shows a comparison widget with % change
            page_text = await page.inner_text("body")

            # Try to extract the trend summary
            # Google Trends sometimes shows "+X%" or "-X%" or "Breakout"
            change_match = re.search(r'([+-]?\d+)\s*%', page_text)
            if change_match:
                pct = int(change_match.group(1))
                result["trend_pct_change"] = pct
                if pct > 10:
                    result["trend"] = "rising"
                elif pct < -10:
                    result["trend"] = "declining"
                else:
                    result["trend"] = "stable"

            # Try to extract related queries or interest values
            # Look for the average interest value from the chart
            interest_matches = re.findall(r'interest.*?(\d+)', page_text.lower())
            if interest_matches:
                try:
                    result["search_volume"] = int(interest_matches[-1])
                except (ValueError, IndexError):
                    pass

            # Fallback: try to read SVG chart data points
            if not result["trend"]:
                # Check for the trend line widget header text
                try:
                    widget = await page.query_selector('[class*="comparison-item"]')
                    if widget:
                        widget_text = await widget.inner_text()
                        if "%" in widget_text:
                            match = re.search(r'([+-]?\d+)%', widget_text)
                            if match:
                                pct = int(match.group(1))
                                result["trend_pct_change"] = pct
                                result["trend"] = (
                                    "rising" if pct > 10
                                    else "declining" if pct < -10
                                    else "stable"
                                )
                except Exception:
                    pass

            if not result["trend"]:
                result["trend"] = "stable"  # default if we can't determine

            elapsed = round(time.monotonic() - start, 2)
            logger.info(
                f"Google Trends: {brand_name} trend={result['trend']} "
                f"change={result['trend_pct_change']}% ({elapsed}s)"
            )

    except Exception as e:
        logger.warning(f"Google Trends: error for '{brand_name}': {e}")
        result["error"] = str(e)
        result["trend"] = "unknown"

    return result
