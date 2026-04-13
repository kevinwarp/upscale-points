import logging
import re
import time
from datetime import datetime

from models.ad_models import MilledEmail, MilledIntel
from scraping.browser_agent import BrowserAgent

logger = logging.getLogger(__name__)


def _slug_candidates(domain: str, company_name: str | None = None) -> list[str]:
    """Generate slug candidates from a domain and optional company name.

    Tries multiple strategies (highest-confidence first):
    1. Hyphenated company name (e.g. 'Summer Fridays' → 'summer-fridays')
    2. Concatenated company name (e.g. 'Summer Fridays' → 'summerfridays')
    3. Raw domain name (e.g. 'summerfridays')
    4. Common suffix splits (e.g. 'jonesroad-beauty')
    5. Known word boundary splits (e.g. 'jones-road-beauty')
    6. Full domain with .com (some Milled pages index this way)
    """
    name = domain.lower().replace("www.", "").split(".")[0]
    candidates = []

    # --- Company-name-derived slugs (most reliable when available) ---
    if company_name:
        # Normalise: lowercase, strip non-alphanumeric except spaces/hyphens
        cn = re.sub(r"[^a-z0-9\s-]", "", company_name.lower()).strip()
        if cn:
            # Hyphenated form: "Summer Fridays" → "summer-fridays"
            hyphenated = re.sub(r"[\s-]+", "-", cn)
            candidates.append(hyphenated)
            # Concatenated form: "Summer Fridays" → "summerfridays"
            concatenated = re.sub(r"[\s-]+", "", cn)
            if concatenated != hyphenated:
                candidates.append(concatenated)

    # --- Domain-derived slug ---
    candidates.append(name)

    # If the domain already has hyphens, also try without
    if "-" in name:
        candidates.append(name.replace("-", ""))
    else:
        # Try suffix-based splits
        _SUFFIXES = [
            "rugs", "baby", "health", "beauty", "home", "shop", "store",
            "wear", "labs", "goods", "co", "brand", "life", "skin",
            "care", "food", "pets", "fit", "gear", "supply", "club",
        ]
        for suffix in _SUFFIXES:
            if name.endswith(suffix) and name != suffix:
                candidates.append(name[:-len(suffix)] + "-" + suffix)

        # Try splitting at known word boundaries using a dictionary approach
        # For multi-word brands like 'jonesroadbeauty' → 'jones-road-beauty'
        _WORDS = [
            "jones", "road", "beauty", "seed", "wild", "grain", "green",
            "blue", "red", "black", "white", "gold", "silver", "sun",
            "moon", "star", "day", "night", "city", "bay", "lake",
            "new", "old", "big", "little", "good", "best", "true",
            "pure", "fresh", "clean", "bright", "clear", "smart",
            "native", "natural", "organic", "modern", "simple", "bold",
            "royal", "urban", "coastal", "mountain", "river", "ocean",
            "made", "born", "bred", "grown", "craft", "arte", "luxe",
            "summer", "winter", "spring", "friday", "fridays",
        ]
        # Greedy word split from left
        def _try_split(s: str) -> list[str] | None:
            if not s:
                return []
            for w in sorted(_WORDS, key=len, reverse=True):
                if s.startswith(w) and len(w) < len(s):
                    rest = _try_split(s[len(w):])
                    if rest is not None:
                        return [w] + rest
            # If remaining string is a known suffix, accept it
            if s in _SUFFIXES or len(s) >= 3:
                return [s]
            return None

        parts = _try_split(name)
        if parts and len(parts) > 1:
            candidates.append("-".join(parts))

    # Also try the full domain (some Milled pages use it)
    candidates.append(domain.lower())

    return list(dict.fromkeys(candidates))  # dedupe


def _parse_email_date(raw: str, page_year: int | None = None) -> str:
    """Normalise a Milled date string like 'Apr 10' or 'Apr 10, 2025' to ISO."""
    raw = raw.strip()
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    year = page_year or datetime.now().year
    for fmt in ("%b %d", "%B %d"):
        try:
            dt = datetime.strptime(raw, fmt).replace(year=year)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw


async def scrape_milled(
    agent: BrowserAgent,
    domain: str,
    company_name: str | None = None,
) -> MilledIntel:
    """Scrape Milled.com for a brand's email newsletter history.

    Uses Google search to find the Milled brand page and extract email
    listings from the cached/indexed data, since Milled uses Cloudflare
    bot protection that blocks direct Playwright access.

    Args:
        agent: Browser agent for running Playwright.
        domain: Brand domain (e.g. "seed.com").
        company_name: Optional company name for better search matching.
    """
    start = time.monotonic()
    result = MilledIntel()
    slugs = _slug_candidates(domain, company_name)
    brand_name = company_name or domain.replace("www.", "").split(".")[0]
    logger.info(f"Milled: slug candidates for {domain} (company={company_name!r}): {slugs}")

    try:
        async with agent.new_page() as page:
            # Strategy: Use Google to search for milled.com brand page
            # Google caches Milled pages and we can extract email data
            # from the search results themselves
            search_query = f"site:milled.com {brand_name} emails"
            search_url = f"https://www.google.com/search?q={search_query}&num=10"
            logger.info(f"Milled: searching Google for '{search_query}'")

            await page.goto(search_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)

            # Extract milled.com links from Google results
            google_links = await page.query_selector_all("a[href*='milled.com/']")
            milled_brand_url = None
            milled_email_urls = []

            for link in google_links:
                href = await link.get_attribute("href")
                if not href:
                    continue
                # Clean Google redirect URLs
                if "/url?q=" in href:
                    href = href.split("/url?q=")[1].split("&")[0]
                if "milled.com" not in href:
                    continue

                # Check if it's a brand index page
                for slug in slugs:
                    if f"milled.com/{slug}" in href:
                        if href.rstrip("/").endswith(f"/{slug}") or f"/{slug}?" in href:
                            milled_brand_url = href
                        elif f"/{slug}/" in href:
                            # Individual email page
                            text = (await link.inner_text()).strip()
                            milled_email_urls.append((href, text))

            # Also try to extract snippet text from Google results
            # which often contains email subjects and dates
            snippets = await page.query_selector_all(".VwiC3b, .IsZvec, [data-sncf]")
            snippet_texts = []
            for s in snippets:
                text = (await s.inner_text()).strip()
                if text and "milled" in text.lower():
                    snippet_texts.append(text)

            # Try a second search specifically for recent emails
            search_query2 = f"site:milled.com/{slugs[0]}/ 2026 OR 2025"
            await page.goto(
                f"https://www.google.com/search?q={search_query2}&num=20",
                wait_until="domcontentloaded",
            )
            await page.wait_for_timeout(2000)

            google_links2 = await page.query_selector_all("a[href*='milled.com/']")
            for link in google_links2:
                href = await link.get_attribute("href")
                if not href:
                    continue
                if "/url?q=" in href:
                    href = href.split("/url?q=")[1].split("&")[0]
                for slug in slugs:
                    if f"milled.com/{slug}/" in href and href not in [
                        u for u, _ in milled_email_urls
                    ]:
                        text = (await link.inner_text()).strip()
                        milled_email_urls.append((href, text))

            # If Google search failed, try direct navigation as fallback
            if not milled_brand_url and not milled_email_urls:
                logger.info(f"Milled: Google search returned nothing, trying direct URLs...")
                for slug in slugs:
                    direct_url = f"https://milled.com/{slug}"
                    logger.info(f"Milled: trying direct URL {direct_url}")
                    try:
                        resp = await page.goto(direct_url, wait_until="domcontentloaded", timeout=15000)
                        await page.wait_for_timeout(2000)

                        # Check if page loaded (not a 404 or Cloudflare block)
                        title = await page.title()
                        content = await page.content()

                        # Look for signs of a valid Milled brand page
                        if resp and resp.status == 200 and "milled" in title.lower():
                            milled_brand_url = direct_url
                            result.brand_slug = slug
                            result.milled_url = direct_url
                            result.found = True

                            # Try to extract email links from the page
                            email_links = await page.query_selector_all(f"a[href*='milled.com/{slug}/']")
                            for link in email_links:
                                href = await link.get_attribute("href")
                                text = (await link.inner_text()).strip()
                                if href and text and len(text) > 4:
                                    milled_email_urls.append((href, text))

                            logger.info(f"Milled: found brand page at {direct_url} with {len(milled_email_urls)} email links")
                            break
                        elif "challenge" in content.lower() or "cloudflare" in content.lower():
                            logger.info(f"Milled: Cloudflare challenge at {direct_url}, trying next slug")
                            continue
                    except Exception as e:
                        logger.debug(f"Milled: direct URL {direct_url} failed: {e}")
                        continue

            if not milled_brand_url and not milled_email_urls:
                logger.warning(
                    f"Milled: no results found for {domain} "
                    f"(company_name={company_name!r}, tried slugs: {slugs}). "
                    f"Google search and direct URL navigation both returned nothing. "
                    f"Possible causes: wrong slug, Cloudflare blocking, or brand not on Milled."
                )
                return result

            # Populate result from what we found
            if milled_brand_url:
                result.milled_url = milled_brand_url
                # Extract slug from URL
                parts = milled_brand_url.rstrip("/").split("/")
                result.brand_slug = parts[-1] if parts else slugs[0]
            else:
                result.brand_slug = slugs[0]
                result.milled_url = f"https://milled.com/{slugs[0]}"

            # --- Try to scrape dates from a Milled brand page directly ---
            # Navigate to the brand page to get dates for email listings
            email_dates: dict[str, str] = {}  # url -> ISO date
            brand_page_url = milled_brand_url or f"https://milled.com/{slugs[0]}"
            try:
                logger.info(f"Milled: fetching brand page {brand_page_url} for dates...")
                resp = await page.goto(brand_page_url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(3000)

                if resp and resp.status == 200:
                    page_content = await page.content()
                    if "cloudflare" not in page_content.lower() or "challenge" not in page_content.lower():
                        # Extract date + link pairs from the Milled brand page
                        # Milled uses <time> tags or date-like text near email links
                        time_els = await page.query_selector_all("time[datetime]")
                        for tel in time_els:
                            dt_val = await tel.get_attribute("datetime")
                            # Find closest link sibling/parent
                            parent = await tel.evaluate_handle("el => el.closest('a') || el.parentElement?.querySelector('a')")
                            if parent:
                                href = await parent.get_attribute("href")
                                if href and dt_val:
                                    full_url = href if href.startswith("http") else f"https://milled.com{href}"
                                    email_dates[full_url] = dt_val[:10]

                        # Fallback: look for date patterns in text near links
                        if not email_dates:
                            email_cards = await page.query_selector_all("[class*='email'], [class*='card'], [class*='item'], article, li")
                            for card in email_cards[:40]:
                                card_text = (await card.inner_text()).strip()
                                card_link = await card.query_selector("a[href*='/']")
                                if not card_link:
                                    continue
                                href = await card_link.get_attribute("href")
                                if not href:
                                    continue
                                full_url = href if href.startswith("http") else f"https://milled.com{href}"
                                # Look for date patterns: "Apr 10, 2025", "04/10/2025", "Apr 10"
                                date_match = re.search(
                                    r'([A-Z][a-z]{2}\s+\d{1,2},?\s*\d{4}|'
                                    r'\d{1,2}/\d{1,2}/\d{4}|'
                                    r'[A-Z][a-z]{2}\s+\d{1,2})',
                                    card_text,
                                )
                                if date_match:
                                    email_dates[full_url] = _parse_email_date(date_match.group(0))

                        logger.info(f"Milled: extracted {len(email_dates)} dates from brand page")
            except Exception as e:
                logger.debug(f"Milled: brand page date extraction failed: {e}")

            # Also try to extract dates from Google search result metadata
            # Google often shows dates like "Apr 10, 2025" in .LEwnzc, .f, or span elements
            if not email_dates:
                try:
                    # Go back to the Google search results
                    search_query_dates = f"site:milled.com/{slugs[0]}/"
                    await page.goto(
                        f"https://www.google.com/search?q={search_query_dates}&num=20",
                        wait_until="domcontentloaded",
                    )
                    await page.wait_for_timeout(2000)

                    # Each search result container usually has a date span
                    results_els = await page.query_selector_all(".g, [data-sokoban-container]")
                    for res_el in results_els:
                        link_el = await res_el.query_selector("a[href*='milled.com/']")
                        if not link_el:
                            continue
                        href = await link_el.get_attribute("href")
                        if not href:
                            continue
                        if "/url?q=" in href:
                            href = href.split("/url?q=")[1].split("&")[0]

                        # Look for date text in the result snippet
                        res_text = (await res_el.inner_text()).strip()
                        date_match = re.search(
                            r'([A-Z][a-z]{2}\s+\d{1,2},\s*\d{4})',
                            res_text,
                        )
                        if date_match and href:
                            email_dates[href] = _parse_email_date(date_match.group(1))

                    logger.info(f"Milled: extracted {len(email_dates)} dates from Google metadata")
                except Exception as e:
                    logger.debug(f"Milled: Google date extraction failed: {e}")

            # Parse email data from Google search results
            # Filter out junk: nav items, short strings, non-email titles
            JUNK_TITLES = {
                "read more", "sign in", "ai mode", "images", "shopping",
                "videos", "news", "maps", "books", "flights", "finance",
                "all", "more", "tools", "settings", "search", "about",
                "cached", "similar", "milled", "brands",
            }

            seen = set()
            for url, title in milled_email_urls:
                if url in seen:
                    continue
                seen.add(url)

                # Must actually be an individual email URL with a path segment
                # Pattern: milled.com/{slug}/{email-slug}
                url_parts = url.rstrip("/").split("/")
                if len(url_parts) < 5:  # https://milled.com/slug/email-slug
                    continue

                # Google result titles from Milled follow patterns like:
                # "Subject Line - Brand Name | Milled"
                # But link text can include breadcrumbs:
                # "Subject Line\nMilled\nhttps://milled.com ›"
                subject = title.strip()

                # Strip everything after first \n (Google breadcrumb noise)
                if "\n" in subject:
                    subject = subject.split("\n")[0].strip()

                if " | Milled" in subject:
                    subject = subject.split(" | Milled")[0].strip()
                if " - Milled" in subject:
                    subject = subject.split(" - Milled")[0].strip()

                # Remove brand name suffix if present
                brand_lower = brand_name.lower()
                for sep in [" - ", " — ", " | ", ": "]:
                    if sep + brand_lower in subject.lower():
                        idx = subject.lower().rfind(sep + brand_lower)
                        subject = subject[:idx].strip()
                    elif brand_lower + sep in subject.lower():
                        idx = subject.lower().find(brand_lower + sep)
                        subject = subject[idx + len(brand_lower) + len(sep):].strip()

                # Skip junk entries
                if not subject or len(subject) < 4:
                    continue
                if subject.lower().strip(".,!? ") in JUNK_TITLES:
                    continue
                # Skip if it looks like Google navigation (usually 1-2 words, all lowercase)
                if len(subject.split()) <= 2 and subject.islower() and len(subject) < 15:
                    continue

                # Look up date from our extracted dates
                date_str = email_dates.get(url, "")
                # Also try without trailing slash / query variations
                if not date_str:
                    clean_url = url.rstrip("/").split("?")[0].split("#")[0]
                    for dated_url, d in email_dates.items():
                        if dated_url.rstrip("/").split("?")[0].split("#")[0] == clean_url:
                            date_str = d
                            break

                result.emails.append(
                    MilledEmail(
                        date=date_str,
                        subject=subject[:200],
                        subheading=None,
                        url=url,
                    )
                )

            # Extract stats from snippets
            for text in snippet_texts:
                total_match = re.search(
                    r"([\d,]+)\s+emails?\s+archived", text, re.IGNORECASE
                )
                if total_match:
                    result.total_emails = int(
                        total_match.group(1).replace(",", "")
                    )
                last12_match = re.search(
                    r"([\d,]+)\s+emails?\s+found", text, re.IGNORECASE
                )
                if last12_match:
                    result.emails_last_12_months = int(
                        last12_match.group(1).replace(",", "")
                    )

            if result.emails_last_12_months > 0:
                result.emails_per_week = round(
                    result.emails_last_12_months / 52, 1
                )

            result.found = len(result.emails) > 0
            elapsed = round(time.monotonic() - start, 2)
            logger.info(
                f"Milled: found {len(result.emails)} emails for "
                f"{result.brand_slug} via Google ({elapsed}s)"
            )

    except Exception as e:
        elapsed = round(time.monotonic() - start, 2)
        logger.warning(
            f"Milled: error searching for {domain} after {elapsed}s "
            f"(company_name={company_name!r}, slugs={slugs}): {type(e).__name__}: {e}",
            exc_info=True,
        )

    return result
