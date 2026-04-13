import logging
import re
import time
from urllib.parse import quote_plus

from models.ad_models import Ad, Platform, PlatformResult
from scraping.browser_agent import BrowserAgent

logger = logging.getLogger(__name__)


def _brand_slug(brand_name: str) -> str:
    """Convert a brand name to an iSpot URL slug: lowercase, hyphens, no special chars."""
    slug = brand_name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


async def scrape_ispot(agent: BrowserAgent, brand_name: str) -> PlatformResult:
    """Search iSpot.tv for CTV ads matching the brand name.

    Strategy order:
    1. Search page (/search/{brand}) — quick if it works
    2. Google fallback (site:ispot.tv/brands brand) — finds brand page slug
    3. Extract ads from brand page or search results
    """
    start_time = time.monotonic()
    result = PlatformResult(platform=Platform.ISPOT)

    try:
        async with agent.new_page() as page:
            brand_page_found = False

            # --- Strategy 1: iSpot search page ---
            search_url = f"https://www.ispot.tv/search/{quote_plus(brand_name)}"
            logger.info(f"iSpot: navigating to {search_url}")
            await page.goto(search_url, wait_until="domcontentloaded")

            try:
                await page.wait_for_selector(
                    "a.card-container, .top-results, article.search-page, a[href*='/ad/']",
                    timeout=8000,
                )
            except Exception:
                logger.info("iSpot: first load timeout, retrying...")
                await page.reload(wait_until="domcontentloaded")
                try:
                    await page.wait_for_selector(
                        "a.card-container, .top-results, article.search-page, a[href*='/ad/']",
                        timeout=8000,
                    )
                except Exception:
                    logger.info("iSpot: search page empty, trying Google fallback")

            # Check for captcha
            if await page.query_selector(
                "[class*='captcha'], [id*='captcha'], [class*='Captcha']"
            ):
                result.error = "captcha_detected"
                result.scrape_duration_seconds = round(
                    time.monotonic() - start_time, 2
                )
                return result

            # Try to find and navigate to the brand page from search results
            brand_links = await page.query_selector_all(
                "a.card-container[href*='/brands/'], a[href*='/brands/']"
            )
            for bl in brand_links:
                href = await bl.get_attribute("href")
                if href and "/brands/" in href:
                    brand_url = (
                        f"https://www.ispot.tv{href}"
                        if href.startswith("/")
                        else href
                    )
                    logger.info(f"iSpot: navigating to brand page {brand_url}")
                    await page.goto(brand_url, wait_until="domcontentloaded")
                    await page.wait_for_timeout(2000)
                    brand_page_found = True
                    break

            # --- Strategy 2: Google fallback if search didn't find brand page ---
            if not brand_page_found:
                ad_links_check = await page.query_selector_all('a[href*="/ad/"]')
                has_ads = any(
                    "/top-" not in (await a.get_attribute("href") or "")
                    for a in ad_links_check[:5]
                ) if ad_links_check else False

                if not has_ads:
                    brand_page_found = await _google_brand_fallback(
                        page, brand_name
                    )

            # --- Extract ads ---
            ads = await _extract_ads(page)
            result.ads = ads
            result.found = len(ads) > 0
            logger.info(f"iSpot: found {len(ads)} ads")

            # --- Extract video URL from first ad detail page ---
            if result.ads and result.ads[0].ad_page_url:
                try:
                    await _enrich_first_ad_video(page, result.ads[0])
                except Exception as e:
                    logger.debug(f"iSpot: video extraction failed: {e}")

    except Exception as e:
        logger.error(f"iSpot scraper error: {e}")
        result.error = str(e)

    result.scrape_duration_seconds = round(time.monotonic() - start_time, 2)
    return result


async def _google_brand_fallback(page, brand_name: str) -> bool:
    """Use Google to find the iSpot brand page when search fails.

    Strategy: search Google for iSpot ad pages for this brand, navigate to
    one, then discover the brand page link from the ad detail page.  iSpot
    brand pages use opaque 3-letter codes (/brands/SBT/slug) that can't be
    guessed — but every ad page links back to the brand page.
    """
    try:
        slug = _brand_slug(brand_name)

        # Search for ad pages OR brand pages
        google_url = (
            f"https://www.google.com/search?q="
            f"site:ispot.tv+%22{quote_plus(brand_name)}%22"
        )
        logger.info(f"iSpot: Google fallback — {google_url}")
        await page.goto(google_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        # Collect all ispot.tv links from Google results
        ispot_urls: list[str] = []
        links = await page.query_selector_all("a")
        for link in links[:30]:
            href = await link.get_attribute("href") or ""
            # Clean Google redirect URLs
            if "/url?" in href:
                match = re.search(r"q=(https?://[^&]+)", href)
                if match:
                    href = match.group(1)
            if "ispot.tv" not in href or not href.startswith("http"):
                continue
            # Must contain brand slug to be relevant
            if slug not in href.lower() and brand_name.lower().replace(" ", "-") not in href.lower():
                continue
            ispot_urls.append(href)

        # Prefer brand pages, then ad pages
        brand_urls = [u for u in ispot_urls if "/brands/" in u]
        ad_urls = [u for u in ispot_urls if "/ad/" in u]

        if brand_urls:
            logger.info(f"iSpot: Google found brand page {brand_urls[0]}")
            await page.goto(brand_urls[0], wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            # Validate we're on the right brand page
            title = await page.title()
            if brand_name.lower().split()[0] in title.lower():
                return True

        if ad_urls:
            # Navigate to an ad page, then find the brand link
            logger.info(f"iSpot: Google found ad page {ad_urls[0]}, extracting brand link")
            await page.goto(ad_urls[0], wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)

            # Ad pages link back to the brand page
            brand_links = await page.query_selector_all('a[href*="/brands/"]')
            for bl in brand_links:
                bl_href = await bl.get_attribute("href") or ""
                if slug in bl_href.lower():
                    brand_url = (
                        f"https://www.ispot.tv{bl_href}"
                        if bl_href.startswith("/")
                        else bl_href
                    )
                    logger.info(f"iSpot: discovered brand page from ad — {brand_url}")
                    await page.goto(brand_url, wait_until="domcontentloaded")
                    await page.wait_for_timeout(2000)
                    return True

    except Exception as e:
        logger.debug(f"iSpot Google fallback error: {e}")

    return False


async def _extract_ads(page) -> list[Ad]:
    """Extract ads from the current iSpot page (search results or brand page)."""
    # Strategy 1: card-container links (search results page)
    cards = await page.query_selector_all("a.card-container")
    # Strategy 2: all a[href*="/ad/"] links (brand page)
    ad_links = await page.query_selector_all('a[href*="/ad/"]')

    all_candidates = cards + ad_links
    seen_urls: set[str] = set()
    ads: list[Ad] = []

    for el in all_candidates[:60]:
        try:
            href = await el.get_attribute("href")
            if not href:
                continue

            # Only include actual ad detail pages
            if "/ad/" not in href:
                continue
            # Skip nav links
            if "/top-commercials" in href or "/top-spenders" in href:
                continue
            if href in seen_urls:
                continue

            ad_url = (
                f"https://www.ispot.tv{href}"
                if href.startswith("/")
                else href
            )

            # Get title: prefer HTML title attribute, then child heading, then text
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
                ads.append(
                    Ad(
                        title=title[:200],
                        ad_page_url=ad_url,
                    )
                )
        except Exception as e:
            logger.debug(f"iSpot card extraction error: {e}")
            continue

    return ads


async def _enrich_first_ad_video(page, ad: Ad) -> None:
    """Navigate to the first ad's detail page to extract video URL and thumbnail.

    iSpot ad detail pages embed a <video> element directly, or sometimes
    an iframe with a video player. We grab the source and poster (thumbnail).
    """
    logger.info(f"iSpot: fetching video from {ad.ad_page_url}")
    await page.goto(ad.ad_page_url, wait_until="domcontentloaded")
    await page.wait_for_timeout(3000)

    # Try <video> tag first
    video_data = await page.evaluate("""() => {
  const video = document.querySelector('video');
  if (video) {
    const src = video.src || (video.querySelector('source') || {}).src || '';
    const poster = video.poster || '';
    return { src, poster };
  }
  // Try iframe with video embed
  const iframe = document.querySelector('iframe[src*="video"], iframe[src*="player"]');
  if (iframe) return { src: iframe.src, poster: '' };
  return null;
}""")

    if video_data:
        src = video_data.get("src", "")
        poster = video_data.get("poster", "")
        if src and src.startswith("http"):
            ad.video_url = src
            logger.info(f"iSpot: captured video URL ({len(src)} chars)")
        if poster and poster.startswith("http"):
            ad.thumbnail_url = poster
            logger.info(f"iSpot: captured thumbnail URL")

    # Also try to extract duration from the page
    duration_text = await page.evaluate("""() => {
  const el = document.querySelector('[class*="duration"], .ad-duration, .video-duration');
  return el ? el.innerText.trim() : null;
}""")
    if duration_text:
        # Parse "0:30" or "30s" format
        try:
            if ":" in duration_text:
                parts = duration_text.split(":")
                ad.duration_seconds = int(parts[0]) * 60 + int(parts[1])
            elif duration_text.endswith("s"):
                ad.duration_seconds = int(duration_text[:-1])
        except (ValueError, IndexError):
            pass
