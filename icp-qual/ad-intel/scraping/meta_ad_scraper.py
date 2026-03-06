import logging
import time
from urllib.parse import quote_plus

from models.ad_models import Ad, Platform, PlatformResult
from scraping.browser_agent import BrowserAgent

logger = logging.getLogger(__name__)

META_AD_LIBRARY_URL = "https://www.facebook.com/ads/library/"


async def scrape_meta_ads(
    agent: BrowserAgent, brand_name: str
) -> PlatformResult:
    """Search Meta Ad Library for video ads from the last 30 days."""
    start_time = time.monotonic()
    result = PlatformResult(platform=Platform.META)

    try:
        async with agent.new_page() as page:
            # Construct URL with filters pre-applied via query params
            params = (
                f"?active_status=active"
                f"&ad_type=all"
                f"&country=US"
                f"&media_type=video"
                f"&search_type=keyword_unordered"
                f"&q={quote_plus(brand_name)}"
            )
            url = META_AD_LIBRARY_URL + params
            logger.info(f"Meta: navigating to {url}")
            await page.goto(url, wait_until="domcontentloaded")

            # Wait for ad content to load — look for "Library ID" text
            # which appears in each ad card
            try:
                await page.wait_for_function(
                    "() => document.body.innerText.includes('Library ID:')",
                    timeout=12000,
                )
            except Exception:
                # Retry once on timeout
                logger.info("Meta: first load timeout, retrying...")
                await page.reload(wait_until="domcontentloaded")
                try:
                    await page.wait_for_function(
                        "() => document.body.innerText.includes('Library ID:')",
                        timeout=12000,
                    )
                except Exception:
                    result.error = "timeout_after_retry"
                    result.scrape_duration_seconds = round(
                        time.monotonic() - start_time, 2
                    )
                    return result

            # Captcha / login wall check
            if await page.query_selector(
                "[id*='captcha'], [class*='captcha']"
            ):
                result.error = "captcha_or_login_required"
                result.scrape_duration_seconds = round(
                    time.monotonic() - start_time, 2
                )
                return result

            # Scroll to load more ads (Meta uses infinite scroll)
            await _scroll_for_content(page, max_scrolls=3)

            # Extract ads by parsing page text — split on "Library ID:" delimiters
            # NOTE: Regex for zero-width chars uses String.fromCharCode to avoid
            # Python/JS Unicode escape conflicts.
            js_code = """() => {
  const results = [];
  const body = document.body.innerText;
  const sections = body.split('Library ID:');
  const zwsp = new RegExp('[' + String.fromCharCode(0x200B, 0x200C, 0x200D, 0xFEFF) + ']', 'g');
  for (let i = 1; i < sections.length && i <= 30; i++) {
    const section = sections[i];
    const lines = section.split('\\n')
      .map(l => l.replace(zwsp, '').trim())
      .filter(l => l.length > 0);
    const libraryId = lines[0] || null;
    let startDate = null;
    for (const line of lines) {
      if (line.includes('Started running on')) {
        startDate = line.replace('Started running on', '').trim();
        break;
      }
    }
    let advertiser = null;
    let adText = null;
    let foundSummary = false;
    for (const line of lines) {
      if (line.includes('See summary details') ||
          line.includes('See ad details')) {
        foundSummary = true;
        continue;
      }
      if (foundSummary && !advertiser && line !== 'Sponsored') {
        advertiser = line;
        continue;
      }
      if (foundSummary && advertiser && line === 'Sponsored') continue;
      if (foundSummary && advertiser && !adText &&
          line !== 'Sponsored' && !line.startsWith('0:')) {
        adText = line.substring(0, 200);
        break;
      }
    }
    if (libraryId) {
      results.push({
        library_id: libraryId,
        advertiser: advertiser,
        ad_text: adText,
        start_date: startDate
      });
    }
  }
  return results;
}"""
            ads_data = await page.evaluate(js_code)

            for ad_data in ads_data[:30]:
                library_id = ad_data.get("library_id")
                advertiser = ad_data.get("advertiser")
                ad_text = ad_data.get("ad_text")
                start_date = ad_data.get("start_date")

                title = advertiser or ad_text
                ad_page_url = (
                    f"https://www.facebook.com/ads/library/?id={library_id}"
                    if library_id
                    else None
                )

                if title or library_id:
                    result.ads.append(
                        Ad(
                            title=title,
                            ad_page_url=ad_page_url,
                            start_date=start_date,
                            format="video",
                        )
                    )

            result.found = len(result.ads) > 0
            logger.info(f"Meta: found {len(result.ads)} ads")

    except Exception as e:
        logger.error(f"Meta Ad Library scraper error: {e}")
        result.error = str(e)

    result.scrape_duration_seconds = round(time.monotonic() - start_time, 2)
    return result


async def _scroll_for_content(page, max_scrolls: int = 3) -> None:
    """Scroll down to trigger lazy-loading of more ad cards."""
    for i in range(max_scrolls):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1500)
        at_bottom = await page.evaluate(
            "(window.innerHeight + window.scrollY) >= document.body.scrollHeight - 100"
        )
        if at_bottom:
            break
