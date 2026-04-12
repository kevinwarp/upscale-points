"""Brand Intelligence Analysis Module

Analyzes enrichment data to determine:
- Purchase model (subscription, single purchase, high repurchase)
- Estimated ad spend breakdown by channel
- Analytics/attribution maturity
- Milled email seasonal classification
- Competitor identification
"""

import logging
import re
from models.ad_models import (
    BrandIntelligence,
    CompanyEnrichment,
    DomainAdReport,
    MilledIntel,
    PurchaseModel,
    SpendEstimate,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Purchase model detection
# ---------------------------------------------------------------------------

SUBSCRIPTION_SIGNALS = [
    "subscription", "subscribe", "membership", "recurring", "monthly",
    "replenish", "auto-ship", "autoship", "refill", "renewal",
    "plan", "tier", "bundle box", "delivery service",
]

HIGH_REPURCHASE_SIGNALS = [
    "consumable", "supplement", "vitamin", "protein", "coffee", "tea",
    "snack", "food", "beverage", "drink", "skincare", "beauty",
    "pet food", "cleaning", "hygiene", "razor", "diaper", "baby formula",
    "candle", "fragrance", "essential oil",
]


def detect_purchase_model(enrichment: CompanyEnrichment | None) -> tuple[PurchaseModel, list[str]]:
    """Detect whether a brand is subscription, high-repurchase, or single-purchase."""
    if not enrichment:
        return PurchaseModel.UNKNOWN, []

    signals = []
    text = " ".join([
        enrichment.description or "",
        enrichment.industry or "",
        " ".join(enrichment.features or []),
    ]).lower()

    # Check for subscription signals
    sub_hits = [s for s in SUBSCRIPTION_SIGNALS if s in text]
    if sub_hits:
        signals.extend([f"Subscription signal: '{h}'" for h in sub_hits[:3]])
        return PurchaseModel.SUBSCRIPTION, signals

    # Check for subscription-related tech
    sub_tech = [t for t in (enrichment.technologies or [])
                if any(k in t.lower() for k in ["recharge", "bold subscriptions", "skio", "ordergroove", "yotpo subscriptions", "loop subscriptions", "smartrr", "stay.ai"])]
    if sub_tech:
        signals.extend([f"Subscription tech: {t}" for t in sub_tech])
        return PurchaseModel.SUBSCRIPTION, signals

    # Check for high-repurchase signals
    repurchase_hits = [s for s in HIGH_REPURCHASE_SIGNALS if s in text]
    if repurchase_hits:
        signals.extend([f"Repurchase signal: '{h}'" for h in repurchase_hits[:3]])
        return PurchaseModel.HIGH_REPURCHASE, signals

    # Default to single purchase
    signals.append("No subscription or repurchase signals detected")
    return PurchaseModel.SINGLE_PURCHASE, signals


# ---------------------------------------------------------------------------
# 2. Ad spend estimation
# ---------------------------------------------------------------------------

# DTC ad spend benchmarks (% of revenue by revenue tier)
# Sources: Varos, CommonThread Collective, Measured benchmarks 2024-2026
SPEND_RATES = [
    # (max_annual_revenue, ad_spend_pct, meta_share, google_share, youtube_share)
    (5_000_000,    0.28, 0.75, 0.15, 0.05),    # <$5M: 28% of rev, Meta-heavy
    (10_000_000,   0.25, 0.72, 0.17, 0.06),    # $5-10M
    (25_000_000,   0.22, 0.70, 0.18, 0.07),    # $10-25M
    (50_000_000,   0.20, 0.65, 0.20, 0.08),    # $25-50M
    (100_000_000,  0.18, 0.60, 0.22, 0.10),    # $50-100M
    (250_000_000,  0.16, 0.55, 0.22, 0.12),    # $100-250M
    (float("inf"), 0.14, 0.50, 0.23, 0.14),    # $250M+
]

# CTV test budget: 3-6% of monthly ad spend
CTV_TEST_PCT_MIN = 0.03
CTV_TEST_PCT_MAX = 0.06


def estimate_ad_spend(enrichment: CompanyEnrichment | None) -> SpendEstimate | None:
    """Estimate monthly ad spend breakdown based on revenue."""
    if not enrichment or not enrichment.estimated_annual_revenue:
        return None

    annual_rev = enrichment.estimated_annual_revenue

    # Find the right tier
    for max_rev, spend_pct, meta_share, google_share, yt_share in SPEND_RATES:
        if annual_rev <= max_rev:
            break

    monthly_ad_spend = (annual_rev * spend_pct) / 12
    meta_spend = monthly_ad_spend * meta_share
    google_spend = monthly_ad_spend * google_share
    youtube_spend = monthly_ad_spend * yt_share
    other_spend = monthly_ad_spend - meta_spend - google_spend - youtube_spend

    # CTV test recommendation: 4.5% of monthly ad spend (midpoint of 3-6%)
    ctv_test = monthly_ad_spend * 0.045
    # Round to nearest $1K for cleanliness
    ctv_test = round(ctv_test / 1000) * 1000
    ctv_test = max(ctv_test, 3000)  # Minimum $3K/mo

    return SpendEstimate(
        estimated_monthly_ad_spend=round(monthly_ad_spend),
        ad_spend_pct_of_revenue=round(spend_pct * 100, 1),
        meta_spend=round(meta_spend),
        google_search_spend=round(google_spend),
        youtube_spend=round(youtube_spend),
        ctv_spend=0,  # We don't know their current CTV spend
        other_spend=round(other_spend),
        recommended_ctv_test=ctv_test,
        recommended_ctv_pct=4.5,
    )


# ---------------------------------------------------------------------------
# 3. Analytics / Attribution maturity
# ---------------------------------------------------------------------------

ANALYTICS_TIERS = {
    "advanced": {
        "tools": [
            "google analytics 4", "ga4", "segment", "amplitude", "mixpanel",
            "heap", "fullstory", "hotjar", "lucky orange",
        ],
        "attribution": [
            "triple whale", "northbeam", "measured", "rockerbox",
            "appsflyer", "branch", "adjust", "kochava", "singular",
            "wicked reports", "hyros", "capi", "conversion api",
            "facebook pixel", "meta pixel", "tiktok pixel",
            "google tag manager", "gtm",
        ],
    },
    "intermediate": {
        "tools": [
            "google analytics", "adobe analytics", "matomo",
            "plausible", "fathom", "clicky",
        ],
        "attribution": [
            "utm", "google ads conversion", "facebook conversions api",
        ],
    },
}


def assess_analytics_maturity(enrichment: CompanyEnrichment | None) -> tuple[str, list[str], list[str], list[str]]:
    """Assess analytics/attribution maturity from tech stack.

    Returns: (maturity_level, analytics_tools, attribution_tools, notes)
    """
    if not enrichment:
        return "unknown", [], [], []

    tech_lower = [t.lower() for t in (enrichment.technologies or [])]
    tech_set = set(tech_lower)

    analytics_found = []
    attribution_found = []
    notes = []

    # Check advanced tools
    for tool in ANALYTICS_TIERS["advanced"]["tools"]:
        matches = [t for t in enrichment.technologies or [] if tool in t.lower()]
        analytics_found.extend(matches)

    for tool in ANALYTICS_TIERS["advanced"]["attribution"]:
        matches = [t for t in enrichment.technologies or [] if tool in t.lower()]
        attribution_found.extend(matches)

    # Check intermediate tools
    for tool in ANALYTICS_TIERS["intermediate"]["tools"]:
        matches = [t for t in enrichment.technologies or [] if tool in t.lower()]
        analytics_found.extend(matches)

    for tool in ANALYTICS_TIERS["intermediate"]["attribution"]:
        matches = [t for t in enrichment.technologies or [] if tool in t.lower()]
        attribution_found.extend(matches)

    # Dedupe
    analytics_found = list(dict.fromkeys(analytics_found))
    attribution_found = list(dict.fromkeys(attribution_found))

    # Determine maturity level
    has_advanced_analytics = any(
        tool in " ".join(tech_lower)
        for tool in ANALYTICS_TIERS["advanced"]["tools"]
    )
    has_attribution = any(
        tool in " ".join(tech_lower)
        for tool in ANALYTICS_TIERS["advanced"]["attribution"]
    )

    if has_attribution and has_advanced_analytics:
        maturity = "advanced"
        notes.append("Strong analytics + attribution stack detected")
        notes.append("Measurement-ready for CTV — faster onboarding")
    elif has_advanced_analytics or has_attribution:
        maturity = "intermediate"
        if has_attribution:
            notes.append("Has attribution tools but analytics could be deeper")
        else:
            notes.append("Good analytics but no dedicated attribution platform")
        notes.append("CTV attribution will provide incremental measurement clarity")
    elif analytics_found:
        maturity = "basic"
        notes.append("Basic analytics only — no attribution platform detected")
        notes.append("Upscale's built-in attribution fills a major gap")
    else:
        maturity = "basic"
        notes.append("Limited analytics visibility in tech stack")
        notes.append("Upscale provides attribution they likely don't have today")

    return maturity, analytics_found, attribution_found, notes


# ---------------------------------------------------------------------------
# 4. Milled email classification
# ---------------------------------------------------------------------------

BFCM_PATTERNS = [
    r"black\s*friday", r"cyber\s*monday", r"bfcm", r"bf/cm",
    r"biggest\s+sale", r"doorbuster",
]

SEASONAL_PATTERNS = {
    "spring_sale": [r"spring\s+sale", r"spring\s+collection", r"spring\s+launch"],
    "summer_sale": [r"summer\s+sale", r"summer\s+collection", r"memorial\s+day"],
    "back_to_school": [r"back\s+to\s+school", r"bts\s+sale"],
    "fall_sale": [r"fall\s+sale", r"fall\s+collection", r"labor\s+day"],
    "holiday": [r"holiday\s+sale", r"holiday\s+gift", r"christmas", r"gift\s+guide", r"stocking"],
    "valentines": [r"valentine", r"galentine", r"love\s+day"],
    "mothers_day": [r"mother.?s\s+day", r"mom\s+sale"],
    "fathers_day": [r"father.?s\s+day", r"dad\s+sale"],
    "new_year": [r"new\s+year", r"nye", r"resolution"],
    "4th_july": [r"4th\s+of\s+july", r"fourth\s+of\s+july", r"independence\s+day", r"july\s+4"],
}

SALE_PATTERNS = [
    r"\d+%\s*off", r"sale\s+end", r"last\s+chance", r"final\s+hours",
    r"flash\s+sale", r"clearance", r"deal", r"discount", r"save\s+\$",
    r"buy\s+one", r"bogo", r"free\s+shipping", r"limited\s+time",
    r"exclusive\s+offer", r"promo\s+code", r"coupon",
]

PRODUCT_LAUNCH_PATTERNS = [
    r"new\s+arrival", r"just\s+launched", r"introducing", r"now\s+available",
    r"meet\s+the", r"sneak\s+peek", r"first\s+look", r"dropping",
    r"new\s+collection", r"just\s+dropped", r"pre-?order",
]


def classify_email(subject: str) -> str:
    """Classify an email subject line into a promotional category."""
    s = subject.lower()

    # BFCM first (highest priority)
    for pattern in BFCM_PATTERNS:
        if re.search(pattern, s):
            return "bfcm"

    # Product launch (before seasonal — "Just Dropped: Summer Collection" is a launch)
    for pattern in PRODUCT_LAUNCH_PATTERNS:
        if re.search(pattern, s):
            return "product_launch"

    # Seasonal
    for season, patterns in SEASONAL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, s):
                return "seasonal"

    # Sale / promotion
    for pattern in SALE_PATTERNS:
        if re.search(pattern, s):
            return "sale"

    return "newsletter"


def classify_milled_emails(milled: MilledIntel) -> MilledIntel:
    """Classify all emails and update seasonal flags."""
    if not milled or not milled.emails:
        return milled

    categories: dict[str, int] = {}
    for email in milled.emails:
        cat = classify_email(email.subject)
        email.category = cat
        categories[cat] = categories.get(cat, 0) + 1

    milled.promo_categories = categories
    milled.has_bfcm = categories.get("bfcm", 0) > 0
    milled.has_seasonal_sales = categories.get("seasonal", 0) > 0 or categories.get("sale", 0) > 2

    return milled


# ---------------------------------------------------------------------------
# 5. Full analysis runner
# ---------------------------------------------------------------------------

def analyze_brand_intelligence(report: DomainAdReport) -> BrandIntelligence:
    """Run all brand intelligence analyses and return combined results."""
    intel = BrandIntelligence()

    # Purchase model
    model, signals = detect_purchase_model(report.enrichment)
    intel.purchase_model = model
    intel.purchase_model_signals = signals

    # Spend estimation
    intel.spend_estimate = estimate_ad_spend(report.enrichment)

    # Analytics maturity
    maturity, analytics, attribution, notes = assess_analytics_maturity(report.enrichment)
    intel.analytics_maturity = maturity
    intel.analytics_tools = analytics
    intel.attribution_tools = attribution
    intel.maturity_notes = notes

    # Classify Milled emails
    if report.milled_intel and report.milled_intel.found:
        report.milled_intel = classify_milled_emails(report.milled_intel)

    return intel
