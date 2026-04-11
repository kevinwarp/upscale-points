import logging
import time
from urllib.parse import quote_plus

from models.ad_models import Ad, Platform, PlatformResult
from scraping.browser_agent import BrowserAgent

logger = logging.getLogger(__name__)


async def scrape_ispot(agent: BrowserAgent, brand_name: str) -> PlatformResult:
    """Search iSpot.tv for CTV ads matching the brand name."""
    start_time = time.monotonic()
    result = PlatformResult(platform=Platform.ISPOT)

    try:
        async with agent.new_page() as page:
            # iSpot uses /search/{query} URL format
            search_url = f"https://www.ispot.tv/search/{quote_plus(brand_name)}"
            logger.info(f"iSpot: navigating to {search_url}")
            await page.goto(search_url, wait_until="domcontentloaded")

            # Wait for card containers to appear
            try:
                await page.wait_for_selector(
                    "a.card-container, .top-results, article.search-page",
                    timeout=8000,
                )
            except Exception:
                # Retry once on timeout per spec
                logger.info("iSpot: first load timeout, retrying...")
                await page.reload(wait_until="domcontentloaded")
                try:
                    await page.wait_for_selector(
                        "a.card-container, .top-results, article.search-page",
                        timeout=8000,
                    )
                except Exception:
                    result.error = "timeout_after_retry"
                    result.scrape_duration_seconds = round(
                        time.monotonic() - start_time, 2
                    )
                    return result

            # Check for captcha
            if await page.query_selector(
                "[class*='captcha'], [id*='captcha'], [class*='Captcha']"
            ):
                result.error = "captcha_detected"
                result.scrape_duration_seconds = round(
                    time.monotonic() - start_time, 2
                )
                return result

            # Try to find and navigate to the brand page for complete results
            brand_links = await page.query_selector_all(
                "a.card-container[href*='/brands/']"
            )
            if brand_links:
                href = await brand_links[0].get_attribute("href")
                if href:
                    brand_url = (
                        f"https://www.ispot.tv{href}"
                        if href.startswith("/")
                        else href
                    )
                    logger.info(f"iSpot: navigating to brand page {brand_url}")
                    await page.goto(brand_url, wait_until="domcontentloaded")
                    await page.wait_for_timeout(2000)

            # Extract ads — use multiple strategies depending on page type
            # Strategy 1: card-container links (search results page)
            cards = await page.query_selector_all("a.card-container")
            # Strategy 2: all a[href*="/ad/"] links (brand page)
            ad_links = await page.query_selector_all('a[href*="/ad/"]')

            all_candidates = cards + ad_links
            seen_urls = set()

            for el in all_candidates[:60]:
                try:
                    href = await el.get_attribute("href")
                    if not href:
                        continue

                    # Only include actual ad detail pages
                    if "/ad/" not in href:
                        continue
                    # Skip nav links like /ad/top-commercials
                    if href in ("/ad/top-commercials", "/ad/top-spenders"):
                        continue
                    if href in seen_urls:
                        continue

                    ad_url = (
                        f"https://www.ispot.tv{href}"
                        if href.startswith("/")
                        else href
                    )

                    # Get title: prefer HTML title attribute (always set on
                    # brand page links), then child heading, then inner text
                    title = await el.get_attribute("title")

                    if not title:
                        title_el = await el.query_selector(
                            "h5.card-title, .card-title, h5, h4"
                        )
                        if title_el:
                            title = (await title_el.inner_text()).strip()

                    if not title:
                        raw_text = (await el.inner_text()).strip()
                        title = raw_text if raw_text else None

                    if title:
                        seen_urls.add(href)
                        result.ads.append(
                            Ad(
                                title=title[:200],
                                ad_page_url=ad_url,
                            )
                        )
                except Exception as e:
                    logger.debug(f"iSpot card extraction error: {e}")
                    continue

            result.found = len(result.ads) > 0
            logger.info(f"iSpot: found {len(result.ads)} ads")

    except Exception as e:
        logger.error(f"iSpot scraper error: {e}")
        result.error = str(e)

    result.scrape_duration_seconds = round(time.monotonic() - start_time, 2)
    return result
