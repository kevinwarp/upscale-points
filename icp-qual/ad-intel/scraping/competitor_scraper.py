"""Competitor discovery and CTV/YouTube check scraper.

Finds competitors using Clay enrichment candidates, validates them via
StoreLeads API (same platform, similar revenue, similar category), then
checks iSpot.tv and YouTube Ads Transparency for validated competitors.
"""

import logging
import re
import time

from enrichment.storeleads_client import enrich_domain
from models.ad_models import CompanyEnrichment
from scraping.browser_agent import BrowserAgent

logger = logging.getLogger(__name__)

# Revenue proximity threshold for competitor validation
REVENUE_THRESHOLD = 10_000_000  # $10M annual revenue


def _name_to_domain_guesses(name: str) -> list[str]:
    """Convert a brand name to a list of likely domain guesses.

    E.g. "RMS Beauty" -> ["rmsbeauty.com", "rms-beauty.com", "rms.com"]
    """
    clean = name.strip()
    lower = clean.lower()
    # Remove common suffixes that wouldn't be in domain
    for suffix in [" inc", " llc", " co", " ltd"]:
        if lower.endswith(suffix):
            lower = lower[: -len(suffix)].strip()

    domains = []
    # No spaces
    domains.append(f"{lower.replace(' ', '')}.com")
    # Hyphenated
    if " " in lower:
        domains.append(f"{lower.replace(' ', '-')}.com")
    # First word only (e.g. "Kosas" from "Kosas Cosmetics")
    words = lower.split()
    if len(words) > 1:
        domains.append(f"{words[0]}.com")

    return domains


def _categories_overlap(cats_a: list[str] | None, cats_b: list[str] | None) -> bool:
    """Check if two category lists share any category or related category."""
    if not cats_a or not cats_b:
        return True  # If we can't compare, don't penalize

    set_a = {c.lower() for c in cats_a}
    set_b = {c.lower() for c in cats_b}

    # Direct overlap
    if set_a & set_b:
        return True

    # Check for substring matches (e.g. "beauty" in "health & beauty")
    for a in set_a:
        for b in set_b:
            if a in b or b in a:
                return True

    return False


def _validate_competitor(
    candidate: CompanyEnrichment,
    brand: CompanyEnrichment,
) -> tuple[bool, str]:
    """Validate a competitor candidate against the target brand.

    Returns (is_valid, reason).
    """
    # Must have data
    if not candidate.company_name and not candidate.ecommerce_platform:
        return False, "no StoreLeads data"

    # Platform match
    if (
        brand.ecommerce_platform
        and candidate.ecommerce_platform
        and brand.ecommerce_platform.lower() != candidate.ecommerce_platform.lower()
    ):
        return False, f"different platform ({candidate.ecommerce_platform} vs {brand.ecommerce_platform})"

    # Revenue proximity
    if brand.estimated_annual_revenue and candidate.estimated_annual_revenue:
        diff = abs(brand.estimated_annual_revenue - candidate.estimated_annual_revenue)
        if diff > REVENUE_THRESHOLD:
            return False, f"revenue too different (${candidate.estimated_annual_revenue:,.0f} vs ${brand.estimated_annual_revenue:,.0f})"

    # Category similarity
    brand_cats = [brand.industry] if brand.industry else None
    candidate_cats = [candidate.industry] if candidate.industry else None
    if not _categories_overlap(brand_cats, candidate_cats):
        return False, f"different category ({candidate.industry} vs {brand.industry})"

    return True, "validated"


async def find_competitors(
    brand_domain: str,
    brand_enrichment: CompanyEnrichment | None,
    clay_competitors: list[str] | None = None,
) -> list[dict]:
    """Find and validate competitors using Clay candidates + StoreLeads.

    For each Clay competitor name, converts to likely domain(s) and calls
    StoreLeads to validate platform, revenue proximity, and category match.

    Returns up to 5 validated competitor dicts with StoreLeads data.
    """
    if not clay_competitors:
        logger.info("Competitors: no Clay competitor candidates provided")
        return []

    validated = []

    for name in clay_competitors:
        if len(validated) >= 5:
            break

        domain_guesses = _name_to_domain_guesses(name)
        enrichment = None

        # Try each domain guess until one returns real data
        for guess in domain_guesses:
            logger.info(f"Competitors: trying {name} -> {guess}")
            result = await enrich_domain(guess)
            if result and (result.company_name or result.ecommerce_platform):
                enrichment = result
                break

        if not enrichment:
            logger.info(f"Competitors: no StoreLeads data for {name} (tried {domain_guesses})")
            validated.append({
                "name": name,
                "domain": domain_guesses[0] if domain_guesses else None,
                "platform": None,
                "revenue": None,
                "category": None,
                "validated": False,
                "reason": "not found in StoreLeads",
            })
            continue

        # Validate against brand
        is_valid, reason = (
            _validate_competitor(enrichment, brand_enrichment)
            if brand_enrichment
            else (True, "no brand data to compare")
        )

        comp = {
            "name": enrichment.company_name or name,
            "domain": enrichment.domain,
            "platform": enrichment.ecommerce_platform,
            "revenue": enrichment.estimated_annual_revenue,
            "category": enrichment.industry,
            "validated": is_valid,
            "reason": reason,
        }
        validated.append(comp)
        logger.info(
            f"Competitors: {name} -> {comp['domain']} "
            f"({'VALID' if is_valid else 'INVALID'}: {reason})"
        )

    valid_count = sum(1 for c in validated if c["validated"])
    logger.info(
        f"Competitors: {valid_count}/{len(validated)} validated "
        f"out of {len(clay_competitors)} candidates"
    )
    return validated


async def check_competitor_ctv(
    agent: BrowserAgent,
    competitor_name: str,
) -> dict:
    """Check if a competitor is running CTV ads on iSpot.tv.

    Returns dict with: name, has_ctv (bool), ad_count (int), error
    """
    result = {"name": competitor_name, "has_ctv": False, "ad_count": 0, "error": None}

    try:
        async with agent.new_page() as page:
            query = competitor_name.replace(" ", "+")
            url = f"https://www.ispot.tv/search?term={query}"
            logger.info(f"Competitor CTV check: {competitor_name} on iSpot")

            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)

            # Check if any results found
            page_text = await page.inner_text("body")

            # Look for ad counts or brand page links
            if "no results" in page_text.lower() or "0 results" in page_text.lower():
                result["has_ctv"] = False
            else:
                # Try to find ad count
                count_match = re.search(r'(\d+)\s+ads?', page_text.lower())
                if count_match:
                    result["ad_count"] = int(count_match.group(1))
                    result["has_ctv"] = result["ad_count"] > 0

                # Also check for brand page links
                brand_links = await page.query_selector_all("a[href*='/brand/']")
                if brand_links:
                    result["has_ctv"] = True
                    if not result["ad_count"]:
                        result["ad_count"] = len(brand_links)

    except Exception as e:
        logger.warning(f"Competitor CTV check failed for {competitor_name}: {e}")
        result["error"] = str(e)

    return result


async def check_competitor_youtube(
    agent: BrowserAgent,
    competitor_name: str,
) -> dict:
    """Check if a competitor is running YouTube ads via Google Ads Transparency.

    Returns dict with: name, has_youtube (bool), ad_count (int), error
    """
    result = {"name": competitor_name, "has_youtube": False, "ad_count": 0, "error": None}

    try:
        async with agent.new_page() as page:
            query = competitor_name.replace(" ", "+")
            url = f"https://adstransparency.google.com/?search={query}&region=US"
            logger.info(f"Competitor YouTube check: {competitor_name}")

            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)

            page_text = await page.inner_text("body")

            # Check for video ad indicators
            if "video" in page_text.lower() or "youtube" in page_text.lower():
                result["has_youtube"] = True
                # Try to count ads
                ad_elements = await page.query_selector_all("[class*='ad-card'], [class*='creative']")
                result["ad_count"] = len(ad_elements) if ad_elements else 1

    except Exception as e:
        logger.warning(f"Competitor YouTube check failed for {competitor_name}: {e}")
        result["error"] = str(e)

    return result


async def scrape_competitor_landscape(
    agent: BrowserAgent,
    brand_name: str,
    domain: str,
    industry: str | None = None,
    clay_competitors: list[str] | None = None,
    enrichment: CompanyEnrichment | None = None,
) -> dict:
    """Full competitive landscape analysis.

    Validates Clay competitor candidates via StoreLeads, then checks each
    validated competitor for CTV and YouTube ad presence.

    Returns dict with:
        competitors: list of competitor dicts (with validation data)
        competitors_on_ctv: list of names with CTV ads
        competitors_on_youtube: list of names with YouTube ads
        details: list of per-competitor result dicts
    """
    start = time.monotonic()
    result = {
        "competitors": [],
        "competitors_on_ctv": [],
        "competitors_on_youtube": [],
        "details": [],
        "error": None,
    }

    try:
        # Step 1: Find and validate competitors via StoreLeads
        competitors = await find_competitors(domain, enrichment, clay_competitors)
        result["competitors"] = [c["name"] for c in competitors]

        # Only check CTV/YouTube for validated competitors
        validated = [c for c in competitors if c.get("validated")]

        if not validated:
            logger.info(f"Competitors: no validated competitors for {brand_name}")
            # Still include unvalidated ones in details
            result["details"] = competitors
            return result

        # Step 2: Check each validated competitor for CTV + YouTube
        for comp in validated:
            comp_name = comp["name"]
            ctv = await check_competitor_ctv(agent, comp_name)
            yt = await check_competitor_youtube(agent, comp_name)

            detail = {
                **comp,
                "has_ctv": ctv["has_ctv"],
                "ctv_ads": ctv["ad_count"],
                "has_youtube": yt["has_youtube"],
                "youtube_ads": yt["ad_count"],
            }
            result["details"].append(detail)

            if ctv["has_ctv"]:
                result["competitors_on_ctv"].append(comp_name)
            if yt["has_youtube"]:
                result["competitors_on_youtube"].append(comp_name)

        # Include unvalidated ones in details too (without CTV/YouTube data)
        for comp in competitors:
            if not comp.get("validated"):
                result["details"].append(comp)

        elapsed = round(time.monotonic() - start, 2)
        logger.info(
            f"Competitors: {len(validated)} validated, "
            f"{len(result['competitors_on_ctv'])} on CTV, "
            f"{len(result['competitors_on_youtube'])} on YouTube ({elapsed}s)"
        )

    except Exception as e:
        logger.warning(f"Competitors: landscape check failed: {e}")
        result["error"] = str(e)

    return result
