import logging
import time

from models.ad_models import Ad, Platform, PlatformResult
from scraping.browser_agent import BrowserAgent

logger = logging.getLogger(__name__)

TRANSPARENCY_URL = "https://adstransparency.google.com/"


async def scrape_youtube_ads(
    agent: BrowserAgent, brand_name: str, domain: str
) -> PlatformResult:
    """Search Google Ads Transparency Center for YouTube video ads."""
    start_time = time.monotonic()
    result = PlatformResult(platform=Platform.YOUTUBE)

    try:
        async with agent.new_page() as page:
            # Step 1: Navigate to Transparency Center
            logger.info("YouTube: navigating to Ads Transparency Center")
            await page.goto(TRANSPARENCY_URL, wait_until="networkidle")

            # Step 2: Type brand name into the search input
            search_input = await page.wait_for_selector(
                "input[type='text']",
                timeout=8000,
            )
            if not search_input:
                result.error = "search_input_not_found"
                result.scrape_duration_seconds = round(
                    time.monotonic() - start_time, 2
                )
                return result

            await search_input.click()
            await search_input.fill(brand_name)
            await page.wait_for_timeout(1500)

            # Step 3: Click the first autocomplete suggestion (material-select-item)
            suggestion = await page.query_selector("material-select-item")
            if not suggestion:
                # Retry with domain root
                logger.info(
                    "YouTube: no suggestions for brand name, trying domain root"
                )
                domain_root = domain.split(".")[0]
                await search_input.fill("")
                await search_input.fill(domain_root)
                await page.wait_for_timeout(1500)
                suggestion = await page.query_selector("material-select-item")

            if not suggestion:
                result.found = False
                result.error = "no_advertiser_suggestions"
                result.scrape_duration_seconds = round(
                    time.monotonic() - start_time, 2
                )
                return result

            await suggestion.click()
            await page.wait_for_timeout(3000)
            logger.info(f"YouTube: navigated to advertiser page at {page.url}")

            # Step 4: Apply platform filter → YouTube
            await _apply_platform_filter(page, "YouTube")

            # Step 5: Apply date filter → Last 30 days
            await _apply_date_filter(page)

            # Wait for creatives to reload after filtering
            await page.wait_for_timeout(2000)

            # Step 6: Extract ad creatives from .creative-bounding-box elements
            boxes = await page.query_selector_all(".creative-bounding-box")
            logger.info(f"YouTube: found {len(boxes)} creative boxes")

            for box in boxes[:30]:
                try:
                    # The href attribute on the bounding box contains the ad detail URL
                    href = await box.get_attribute("href")
                    ad_url = None
                    if href:
                        ad_url = f"https://adstransparency.google.com{href}"

                    # Get the aria-label from the creative element for ad numbering
                    creative_el = await box.query_selector(
                        "creative[aria-label]"
                    )
                    aria = (
                        await creative_el.get_attribute("aria-label")
                        if creative_el
                        else None
                    )

                    result.ads.append(
                        Ad(
                            title=aria or f"Ad creative",
                            ad_page_url=ad_url,
                            format="video",
                        )
                    )
                except Exception as e:
                    logger.debug(f"YouTube creative extraction error: {e}")

            result.found = len(result.ads) > 0
            logger.info(f"YouTube: found {len(result.ads)} ads")

    except Exception as e:
        logger.error(f"YouTube Transparency scraper error: {e}")
        result.error = str(e)

    result.scrape_duration_seconds = round(time.monotonic() - start_time, 2)
    return result


async def _apply_platform_filter(page, platform_name: str) -> None:
    """Click the platform-filter element and select a specific platform."""
    try:
        pf = await page.query_selector("platform-filter")
        if not pf:
            logger.warning("YouTube: platform-filter element not found")
            return

        await pf.click()
        await page.wait_for_timeout(500)

        # Find the option matching the platform name
        options = await page.query_selector_all("material-select-item")
        for opt in options:
            text = (await opt.inner_text()).strip()
            if platform_name.lower() in text.lower():
                await opt.click()
                logger.info(f"YouTube: selected platform filter '{text}'")
                await page.wait_for_timeout(500)
                return

        logger.warning(f"YouTube: '{platform_name}' not found in platform options")
    except Exception as e:
        logger.warning(f"YouTube: could not apply platform filter: {e}")


async def _apply_date_filter(page) -> None:
    """Click the date-range-filter and select 'Last 30 days'."""
    try:
        df = await page.query_selector("date-range-filter")
        if not df:
            logger.warning("YouTube: date-range-filter element not found")
            return

        await df.click()
        await page.wait_for_timeout(500)

        # Look for date range options
        options = await page.query_selector_all(
            "material-select-item, [role='option']"
        )
        for opt in options:
            text = (await opt.inner_text()).strip().lower()
            if "30" in text or "last 30" in text:
                await opt.click()
                logger.info(f"YouTube: selected date filter '{text}'")
                await page.wait_for_timeout(500)
                return

        logger.warning("YouTube: 'Last 30 days' not found in date options")
    except Exception as e:
        logger.warning(f"YouTube: could not apply date filter: {e}")
