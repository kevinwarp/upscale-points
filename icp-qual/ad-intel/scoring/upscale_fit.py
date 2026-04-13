"""Upscale Fit Scoring Engine

Scores a DTC brand 0-100 across 6 categories to determine how well they fit
as an Upscale.ai CTV + YouTube streaming customer.

Categories (weights):
  1. Revenue Scale      (25%) — Monthly DTC revenue band
  2. Ad Platform Presence (20%) — How many ad channels they already run
  3. Industry Fit        (20%) — DTC ecommerce in target verticals
  4. Digital Maturity     (15%) — Tech stack, analytics, attribution readiness
  5. Social Audience      (10%) — Social following + engagement signals
  6. Brand Health         (10%) — Reviews, rating, email marketing cadence
"""

from __future__ import annotations

from dataclasses import dataclass, field
from models.ad_models import DomainAdReport


@dataclass
class CategoryScore:
    name: str
    score: float  # 0-100
    weight: float  # 0-1
    notes: list[str] = field(default_factory=list)

    @property
    def weighted(self) -> float:
        return round(self.score * self.weight, 2)


@dataclass
class UpscaleFitResult:
    total_score: float
    grade: str
    categories: list[CategoryScore]
    recommendation: str

    def to_dict(self) -> dict:
        return {
            "total_score": self.total_score,
            "grade": self.grade,
            "recommendation": self.recommendation,
            "categories": [
                {
                    "name": c.name,
                    "score": c.score,
                    "weight": c.weight,
                    "weighted_score": c.weighted,
                    "notes": c.notes,
                }
                for c in self.categories
            ],
        }


# ---------------------------------------------------------------------------
# Target industries for Upscale CTV/YouTube
# ---------------------------------------------------------------------------
TARGET_INDUSTRIES = {
    "health", "nutrition", "supplements", "vitamins", "beauty", "skincare",
    "cosmetics", "wellness", "fitness", "food", "beverage", "fashion",
    "apparel", "home", "furniture", "decor", "baby", "kids", "pet",
    "outdoor", "sports", "personal care", "haircare", "fragrance",
    "jewelry", "accessories", "cleaning", "household",
}

# Tech signals that indicate attribution / analytics readiness
MATURITY_TECH = {
    "google analytics", "ga4", "segment", "mixpanel", "amplitude",
    "facebook pixel", "meta pixel", "tiktok pixel", "snapchat pixel",
    "google tag manager", "gtm", "hotjar", "fullstory", "heap",
    "klaviyo", "attentive", "postscript", "yotpo", "okendo",
    "triple whale", "northbeam", "rockerbox", "measured", "tatari",
    "optimizely", "vwo", "convert", "onetrust", "cookiebot",
    "recharge", "bold subscriptions", "shopify flow",
}


def score_revenue(report: DomainAdReport) -> CategoryScore:
    """Score 0-100 based on monthly DTC revenue."""
    cat = CategoryScore(name="Revenue Scale", score=0, weight=0.25)
    e = report.enrichment
    if not e or not e.estimated_monthly_revenue:
        cat.notes.append("No revenue data available")
        return cat

    monthly = e.estimated_monthly_revenue
    annual = e.estimated_annual_revenue or monthly * 12

    # Scoring bands (monthly)
    if monthly >= 5_000_000:
        cat.score = 100
        cat.notes.append(f"${monthly/1e6:.1f}M/mo estimated monthly DTC revenue, ideal CTV scale")
    elif monthly >= 2_000_000:
        cat.score = 90
        cat.notes.append(f"${monthly/1e6:.1f}M/mo estimated monthly DTC revenue, ready for streaming")
    elif monthly >= 1_000_000:
        cat.score = 80
        cat.notes.append(f"${monthly/1e6:.1f}M/mo estimated monthly DTC revenue, CTV-ready budget")
    elif monthly >= 500_000:
        cat.score = 65
        cat.notes.append(f"${monthly/1e3:.0f}K/mo estimated monthly DTC revenue, YouTube-first opportunity")
    elif monthly >= 200_000:
        cat.score = 45
        cat.notes.append(f"${monthly/1e3:.0f}K/mo estimated monthly DTC revenue, test budget potential")
    elif monthly >= 50_000:
        cat.score = 25
        cat.notes.append(f"${monthly/1e3:.0f}K/mo estimated monthly DTC revenue, pre-scale prospect")
    else:
        cat.score = 10
        cat.notes.append(f"${monthly/1e3:.0f}K/mo — too early for streaming media")

    cat.notes.append(f"${annual/1e6:.1f}M estimated annual DTC revenue")
    return cat


def score_ad_presence(report: DomainAdReport) -> CategoryScore:
    """Score based on current ad platform activity."""
    cat = CategoryScore(name="Ad Platform Presence", score=0, weight=0.20)
    mix = report.channel_mix

    # Base score from platform count
    if mix.total_platforms >= 3:
        cat.score = 90
        cat.notes.append("Active on all 3 platforms — omnichannel advertiser")
    elif mix.total_platforms == 2:
        cat.score = 70
        cat.notes.append(f"Active on {mix.total_platforms} platforms")
    elif mix.total_platforms == 1:
        cat.score = 45
        cat.notes.append("Single platform — expansion opportunity")
    else:
        cat.score = 15
        cat.notes.append("No ads detected — greenfield or stealth advertiser")

    # Bonus for linear TV (indicates streaming readiness)
    if mix.has_linear:
        cat.score = min(100, cat.score + 10)
        cat.notes.append("Already running linear TV — natural CTV transition")

    # Volume bonus
    if mix.total_ads_found >= 50:
        cat.score = min(100, cat.score + 5)
        cat.notes.append(f"{mix.total_ads_found} total ads — high creative velocity")
    elif mix.total_ads_found >= 20:
        cat.notes.append(f"{mix.total_ads_found} total ads — active creative output")

    # Platform-specific notes
    if not mix.has_linear and not mix.has_youtube:
        cat.notes.append("No video advertising detected — full CTV+YouTube upside")
    elif not mix.has_linear:
        cat.notes.append("No linear/CTV presence — prime expansion channel")
    if not mix.has_youtube:
        cat.notes.append("No YouTube presence — untapped video opportunity")

    return cat


def score_industry(report: DomainAdReport) -> CategoryScore:
    """Score based on industry fit for DTC streaming advertising."""
    cat = CategoryScore(name="Industry Fit", score=0, weight=0.20)
    e = report.enrichment
    if not e or not e.industry:
        cat.notes.append("No industry data")
        cat.score = 30  # Unknown — could be anything
        return cat

    industry_lower = e.industry.lower()
    matches = [t for t in TARGET_INDUSTRIES if t in industry_lower]

    if matches:
        cat.score = 90
        cat.notes.append(f"Target vertical: {e.industry}")
        cat.notes.append(f"Matched: {', '.join(matches)}")
    elif any(kw in industry_lower for kw in ("ecommerce", "e-commerce", "retail", "shopping")):
        cat.score = 70
        cat.notes.append(f"General ecommerce: {e.industry}")
    else:
        cat.score = 35
        cat.notes.append(f"Non-target vertical: {e.industry}")

    # Bonus for Shopify / ecommerce platform
    if e.ecommerce_platform:
        platform = e.ecommerce_platform.lower()
        if "shopify" in platform:
            cat.score = min(100, cat.score + 10)
            plan_note = f" ({e.ecommerce_plan})" if e.ecommerce_plan else ""
            cat.notes.append(f"Shopify store{plan_note} — core DTC platform")
        elif platform in ("bigcommerce", "woocommerce", "magento"):
            cat.score = min(100, cat.score + 5)
            cat.notes.append(f"{e.ecommerce_platform} store — DTC capable")

    return cat


def score_digital_maturity(report: DomainAdReport) -> CategoryScore:
    """Score based on tech stack sophistication and attribution readiness."""
    cat = CategoryScore(name="Digital Maturity", score=0, weight=0.15)
    e = report.enrichment
    if not e:
        cat.notes.append("No enrichment data")
        return cat

    tech_lower = [t.lower() for t in (e.technologies or [])]
    features = [f.lower() for f in (e.features or [])]

    # Count maturity signals
    maturity_hits = []
    for tech in tech_lower:
        for signal in MATURITY_TECH:
            if signal in tech:
                maturity_hits.append(tech)
                break

    hit_count = len(maturity_hits)
    total_tech = len(tech_lower)

    if hit_count >= 8:
        cat.score = 95
        cat.notes.append(f"{hit_count} attribution/analytics tools — highly sophisticated")
    elif hit_count >= 5:
        cat.score = 80
        cat.notes.append(f"{hit_count} attribution/analytics tools — strong stack")
    elif hit_count >= 3:
        cat.score = 60
        cat.notes.append(f"{hit_count} attribution/analytics tools — moderate")
    elif hit_count >= 1:
        cat.score = 35
        cat.notes.append(f"{hit_count} attribution/analytics tools — basic")
    else:
        cat.score = 15
        cat.notes.append("No recognizable analytics/attribution tools")

    # Bonus for headless / advanced ecommerce
    if "headless" in features or "storefront api" in features:
        cat.score = min(100, cat.score + 10)
        cat.notes.append("Headless commerce — advanced engineering team")

    cat.notes.append(f"{total_tech} total technologies detected")
    return cat


def score_social_audience(report: DomainAdReport) -> CategoryScore:
    """Score based on social media following and presence."""
    cat = CategoryScore(name="Social Audience", score=0, weight=0.10)
    e = report.enrichment
    if not e or not e.social_profiles:
        cat.notes.append("No social profiles found")
        return cat

    total_followers = 0
    platforms_with_data = 0

    for sp in e.social_profiles:
        if sp.followers and sp.followers > 0:
            total_followers += sp.followers
            platforms_with_data += 1
            cat.notes.append(f"{sp.platform}: {sp.followers:,} followers")

    if total_followers >= 1_000_000:
        cat.score = 95
        cat.notes.append("Major social presence — large retargeting pool")
    elif total_followers >= 500_000:
        cat.score = 85
    elif total_followers >= 100_000:
        cat.score = 70
    elif total_followers >= 25_000:
        cat.score = 50
    elif total_followers >= 5_000:
        cat.score = 30
    elif platforms_with_data > 0:
        cat.score = 15
    else:
        cat.score = 20  # Have profiles but no follower data
        cat.notes.append("Social profiles exist but follower counts unavailable")

    return cat


def score_brand_health(report: DomainAdReport) -> CategoryScore:
    """Score based on reviews, ratings, and email marketing cadence."""
    cat = CategoryScore(name="Brand Health", score=0, weight=0.10)
    e = report.enrichment
    base = 50  # Start neutral

    # Reviews
    if e and e.review_count and e.review_rating:
        if e.review_rating >= 4.0 and e.review_count >= 100:
            base += 25
            cat.notes.append(
                f"{e.review_rating} stars / {e.review_count:,} reviews on {e.review_source} — strong"
            )
        elif e.review_rating >= 3.5:
            base += 15
            cat.notes.append(
                f"{e.review_rating} stars / {e.review_count:,} reviews — decent"
            )
        elif e.review_rating >= 2.5:
            base += 0
            cat.notes.append(
                f"{e.review_rating} stars — mixed reviews, reputation risk"
            )
        else:
            base -= 15
            cat.notes.append(
                f"{e.review_rating} stars — poor reviews, may limit CTV effectiveness"
            )
    else:
        cat.notes.append("No review data available")

    # Email marketing cadence (from Milled)
    milled = report.milled_intel
    if milled and milled.found:
        if milled.emails_per_week >= 3:
            base += 25
            cat.notes.append(
                f"{milled.emails_per_week}/wk email cadence — aggressive marketer"
            )
        elif milled.emails_per_week >= 1.5:
            base += 15
            cat.notes.append(
                f"{milled.emails_per_week}/wk email cadence — consistent marketer"
            )
        elif milled.emails_per_week >= 0.5:
            base += 5
            cat.notes.append(
                f"{milled.emails_per_week}/wk email cadence — light email program"
            )
        else:
            cat.notes.append("Minimal email activity")
    else:
        cat.notes.append("Not tracked on Milled")

    # Web traffic as health signal
    if e and e.estimated_monthly_visits:
        visits = e.estimated_monthly_visits
        if visits >= 1_000_000:
            base += 10
            cat.notes.append(f"{visits:,} monthly visits — major traffic")
        elif visits >= 200_000:
            base += 5
            cat.notes.append(f"{visits:,} monthly visits — solid traffic")

    cat.score = max(0, min(100, base))
    return cat


def _grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _recommendation(score: float, report: DomainAdReport) -> str:
    mix = report.channel_mix
    has_tv = mix.has_linear if mix else False

    if score >= 85:
        if has_tv:
            return (
                "Prime Upscale prospect. Already running linear TV — position CTV "
                "as the performance upgrade with measurable attribution. "
                "Pitch full CTV + YouTube package with 3-month ramp."
            )
        return (
            "Strong Upscale fit. High revenue, active advertiser, DTC-native. "
            "Lead with CTV awareness + YouTube mid-funnel. "
            "Recommend $30K/mo launch expanding to $60K by month 3."
        )
    if score >= 70:
        return (
            "Good fit for Upscale. Recommend YouTube-first entry point to prove "
            "streaming ROI, then expand into CTV once baseline is established. "
            "Start at $15-20K/mo test budget."
        )
    if score >= 55:
        return (
            "Moderate fit. Brand has growth potential but may need to scale "
            "digital advertising first. Recommend YouTube-only pilot at "
            "$8-12K/mo with clear ROAS targets before CTV expansion."
        )
    if score >= 40:
        return (
            "Early-stage prospect. Nurture with educational content on streaming "
            "TV ROI for DTC brands. Revisit when monthly revenue exceeds $500K."
        )
    return (
        "Not ready for streaming media. Brand needs to build core digital "
        "advertising foundation first. Add to long-term nurture list."
    )


def calculate_upscale_fit(report: DomainAdReport) -> UpscaleFitResult:
    """Run the full Upscale Fit scoring for a DomainAdReport."""
    categories = [
        score_revenue(report),
        score_ad_presence(report),
        score_industry(report),
        score_digital_maturity(report),
        score_social_audience(report),
        score_brand_health(report),
    ]

    total = round(sum(c.weighted for c in categories))
    grade = _grade(total)
    rec = _recommendation(total, report)

    return UpscaleFitResult(
        total_score=total,
        grade=grade,
        categories=categories,
        recommendation=rec,
    )
