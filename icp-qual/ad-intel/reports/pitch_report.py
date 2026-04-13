"""External Pitch Report Generator

Generates a branded Upscale.ai streaming proposal HTML for sending to brands.
Incorporates competitive positioning from Upscale collateral:
  - "The Problem" framing (TV as performance channel)
  - Native Shopify + Klaviyo integration (conditional)
  - End-to-End Platform (Creative System + ML + Measurement)
  - Creative as a System (velocity stats, case studies)
  - CTV Impact (47% streaming stat, 95% completion)
  - YouTube Impact (12.5% stat, unified platform)
  - Proven Results (case studies matched to brand vertical)
  - Why Upscale Wins (vs traditional approaches)
  - Transparent Pricing
  - 3-Month Campaign Plan with eCommerce tactics
  - Promotional Calendar (Milled data)
  - Streaming Inventory Partners
  - Next Steps CTA
"""

from __future__ import annotations

import html as html_mod
import calendar as cal_mod
from datetime import date, datetime, timedelta

from models.ad_models import BrandIntelligence, DomainAdReport
from data.competitive_intel import MARKET_STATS
from data.ecommerce_calendar import get_events_for_year
from scoring.upscale_fit import UpscaleFitResult


def _esc(val) -> str:
    if val is None:
        return ""
    return html_mod.escape(str(val))


def _fmt_money(val: float | None, short: bool = True) -> str:
    if val is None:
        return "—"
    if short:
        if val >= 1_000_000:
            return f"${val / 1_000_000:.1f}M"
        if val >= 1_000:
            return f"${val / 1_000:.0f}K"
    return f"${val:,.0f}"


def _fmt_number(val: int | None) -> str:
    if val is None:
        return "—"
    return f"{val:,}"


def _budget_tier(monthly_rev: float | None, intel=None) -> dict:
    """Calculate recommended budget tiers as % of estimated monthly ad spend.

    Month 1 (Launch):  5% of estimated total monthly ad spend
    Month 2 (Scale):   7.5% of estimated total monthly ad spend
    Month 3 (Expand):  10% of estimated total monthly ad spend

    Falls back to revenue-based estimation if no spend estimate available.
    """
    # Try to use estimated monthly ad spend if available
    monthly_ad_spend = None
    if intel and intel.spend_estimate:
        monthly_ad_spend = intel.spend_estimate.estimated_monthly_ad_spend

    if monthly_ad_spend and monthly_ad_spend > 0:
        m1 = round(monthly_ad_spend * 0.05, -2)  # 5%, round to nearest $100
        m2 = round(monthly_ad_spend * 0.075, -2)  # 7.5%
        m3 = round(monthly_ad_spend * 0.10, -2)   # 10%
    elif monthly_rev and monthly_rev > 0:
        # Fallback: estimate ad spend as ~15% of revenue, then apply %s
        est_ad_spend = monthly_rev * 0.15
        m1 = round(est_ad_spend * 0.05, -2)
        m2 = round(est_ad_spend * 0.075, -2)
        m3 = round(est_ad_spend * 0.10, -2)
    else:
        # Absolute minimum
        m1 = 5_000
        m2 = 7_500
        m3 = 10_000

    # Enforce minimums ($3K/mo minimum for meaningful results)
    m1 = max(m1, 3_000)
    m2 = max(m2, 4_500)
    m3 = max(m3, 6_000)

    daily = round(m1 / 30)

    # Label based on spend level
    if m1 >= 75_000:
        label = "Premier"
    elif m1 >= 40_000:
        label = "Enterprise"
    elif m1 >= 20_000:
        label = "Performance"
    elif m1 >= 10_000:
        label = "Scale"
    elif m1 >= 5_000:
        label = "Growth"
    else:
        label = "Starter"

    return {"m1": m1, "m2": m2, "m3": m3, "daily": daily, "label": label}


def _spend_strategy(intel: BrandIntelligence | None, budget: dict) -> dict:
    """Determine channel strategy based on estimated annual ad spend.

    Tiers:
      <$5M ad spend  → YouTube-only, skip CTV
      $5M-$10M       → CTV-led, 40% retargeting / 60% acquisition
      $10M+          → CTV + YouTube, 80% acquisition / 20% retargeting

    Returns dict with:
      tier: "youtube_only" | "ctv_led" | "full_funnel"
      lead_channel: "YouTube" | "CTV" | "CTV + YouTube"
      yt_pct: float (0-1)
      ctv_rt_pct: float (0-1)
      ctv_acq_pct: float (0-1)
      annual_ad_spend: float
      description: str
    """
    annual_ad_spend = 0.0
    if intel and intel.spend_estimate:
        annual_ad_spend = intel.spend_estimate.estimated_monthly_ad_spend * 12

    if annual_ad_spend < 5_000_000:
        # <$5M — YouTube-only
        return {
            "tier": "youtube_only",
            "lead_channel": "YouTube",
            "yt_pct": 1.0,
            "ctv_rt_pct": 0.0,
            "ctv_acq_pct": 0.0,
            "annual_ad_spend": annual_ad_spend,
            "description": "YouTube-first strategy — the most efficient path to streaming TV performance at this spend level. Scale into CTV as results prove out.",
        }
    elif annual_ad_spend < 10_000_000:
        # $5M-$10M — CTV-led, 40% RT / 60% ACQ
        return {
            "tier": "ctv_led",
            "lead_channel": "CTV",
            "yt_pct": 0.30,
            "ctv_rt_pct": 0.28,  # 40% of 70% CTV allocation
            "ctv_acq_pct": 0.42,  # 60% of 70% CTV allocation
            "annual_ad_spend": annual_ad_spend,
            "description": "CTV-led with YouTube support. 40% retargeting to prove ROI fast, 60% acquisition to grow the funnel. YouTube extends reach and captures mid-funnel intent.",
        }
    else:
        # $10M+ — Full funnel, 80% ACQ
        return {
            "tier": "full_funnel",
            "lead_channel": "CTV + YouTube",
            "yt_pct": 0.25,
            "ctv_rt_pct": 0.15,  # 20% of 75% CTV allocation
            "ctv_acq_pct": 0.60,  # 80% of 75% CTV allocation
            "annual_ad_spend": annual_ad_spend,
            "description": "Full-funnel CTV + YouTube. 80% acquisition to drive new customer growth at scale. Retargeting captures intent, YouTube fills the mid-funnel.",
        }


def _campaign_start_date() -> datetime:
    """Return the Monday that is 2 weeks from today."""
    today = datetime.now()
    # Days until next Monday (0=Mon … 6=Sun)
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7  # if today is Monday, go to next week
    next_monday = today + timedelta(days=days_until_monday)
    # Two Mondays from now
    return next_monday + timedelta(weeks=1)


def _compute_daily_spend(budget_m1: float, strategy: dict) -> list[dict]:
    """Compute 30-day daily spend schedule with ramp-up in week 1.

    Returns list of 30 dicts: {day, date, label, yt, ctv_rt, ctv_acq, total}
    """
    daily_target = budget_m1 / 30
    start = _campaign_start_date()
    days = []

    for d in range(1, 31):
        if d <= 7:
            ramp = 0.30 + (0.70 * (d - 1) / 6)
        else:
            ramp = 1.0

        daily = daily_target * ramp
        dt = start + timedelta(days=d - 1)
        days.append({
            "day": d,
            "date": dt,
            "label": dt.strftime("%b %d"),  # e.g. "Apr 28"
            "yt": round(daily * strategy["yt_pct"]),
            "ctv_rt": round(daily * strategy["ctv_rt_pct"]),
            "ctv_acq": round(daily * strategy["ctv_acq_pct"]),
            "total": round(daily),
        })

    return days


def _compute_weekly_spend(budget: dict, strategy: dict) -> list[dict]:
    """Compute 12-week spend schedule across 3 months.

    Returns list of 12 dicts: {week, start_date, label, yt, ctv_rt, ctv_acq, total}
    """
    monthly_budgets = [budget["m1"], budget["m2"], budget["m3"]]
    start = _campaign_start_date()
    weeks = []

    for w in range(1, 13):
        month_idx = min((w - 1) // 4, 2)
        weekly = monthly_budgets[month_idx] / 4.33

        week_start = start + timedelta(weeks=w - 1)
        weeks.append({
            "week": w,
            "start_date": week_start,
            "label": f"Wk {w} ({week_start.strftime('%b %d')})",  # e.g. "Wk 1 (Apr 28)"
            "yt": round(weekly * strategy["yt_pct"]),
            "ctv_rt": round(weekly * strategy["ctv_rt_pct"]),
            "ctv_acq": round(weekly * strategy["ctv_acq_pct"]),
            "total": round(weekly),
        })

    return weeks


# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------

def _detect_shopify(report: DomainAdReport) -> bool:
    e = report.enrichment
    if not e:
        return False
    return bool(e.ecommerce_platform and "shopify" in e.ecommerce_platform.lower())


def _detect_klaviyo(report: DomainAdReport) -> bool:
    e = report.enrichment
    if not e:
        return False
    return any("klaviyo" in t.lower() for t in (e.technologies or []))


# ---------------------------------------------------------------------------
# Case studies matched by industry vertical
# ---------------------------------------------------------------------------

CASE_STUDIES = {
    "canopy": {
        "name": "Canopy",
        "vertical": "Home / Health",
        "stats": [
            ("79%", "Lower CPV"),
            ("53%", "Lower CPA"),
            ("2x", "ROAS"),
        ],
        "quote": "Modular production and structured iteration drove compounding performance gains across 30+ creatives.",
        "url": "https://upscale.ai/case-studies/scaled-creative-velocity-and-streaming-roi",
    },
    "branch": {
        "name": "Branch",
        "vertical": "Furniture",
        "stats": [
            ("$50K", "Creative Savings"),
            ("6.2x", "ROAS"),
            ("500+", "Purchases/Month"),
        ],
        "quote": "Upscale delivered 500+ attributable purchases per month with a 6.2x blended ROAS.",
        "url": "https://upscale.ai/case-studies/branch",
    },
    "newton": {
        "name": "Newton Baby",
        "vertical": "Baby",
        "stats": [
            ("80+", "Creatives Produced"),
            ("40%", "Lower CPA"),
            ("<$2", "Per Visitor"),
        ],
        "quote": "Newton scaled to 80+ streaming creatives and drove 40% lower CPA through always-on creative testing.",
        "url": "https://upscale.ai/case-studies/over-80-creatives-for-bfcm",
    },
    "lalo": {
        "name": "Lalo",
        "vertical": "Baby / Kids",
        "stats": [
            ("2.46x", "iROAS (verified)"),
            ("45", "Unique Creatives"),
            ("8x", "Faster Production"),
        ],
        "quote": "Lalo launched 45 unique CTV creatives across 6 marketing initiatives with third-party verified incrementality.",
        "url": "https://upscale.ai/case-studies/lalo",
    },
    "fatty15": {
        "name": "fatty15",
        "vertical": "Supplements",
        "stats": [
            ("3.65x", "Blended ROAS"),
            ("69%", "First-Time Buyers"),
            ("53", "Creatives Produced"),
        ],
        "quote": "fatty15 achieved 3.65x blended ROAS with 69% of attributed conversions from first-time buyers.",
        "url": "https://upscale.ai/case-studies/turning-storytelling-into-a-growth-engine",
    },
}

# Map industry keywords to case study keys (best match first)
INDUSTRY_CASE_MAP = {
    "supplement": ["fatty15", "canopy"],
    "vitamin": ["fatty15", "canopy"],
    "health": ["fatty15", "canopy"],
    "nutrition": ["fatty15", "canopy"],
    "wellness": ["fatty15", "canopy"],
    "probiotic": ["fatty15", "canopy"],
    "baby": ["newton", "lalo"],
    "kids": ["lalo", "newton"],
    "furniture": ["branch", "canopy"],
    "home": ["canopy", "branch"],
    "decor": ["canopy", "branch"],
    "beauty": ["fatty15", "canopy"],
    "skincare": ["fatty15", "canopy"],
    "cosmetic": ["fatty15", "canopy"],
    "apparel": ["lalo", "branch"],
    "fashion": ["lalo", "branch"],
    "pet": ["newton", "fatty15"],
    "food": ["fatty15", "lalo"],
    "beverage": ["fatty15", "lalo"],
    "fitness": ["fatty15", "branch"],
    "sport": ["fatty15", "branch"],
    "air": ["canopy", "branch"],
    "humidifier": ["canopy", "branch"],
}


def _match_case_studies(industry: str | None) -> list[dict]:
    """Return 2-3 case studies best matched to the brand's industry."""
    if not industry:
        return [CASE_STUDIES["branch"], CASE_STUDIES["fatty15"], CASE_STUDIES["canopy"]]

    industry_lower = industry.lower()
    for keyword, keys in INDUSTRY_CASE_MAP.items():
        if keyword in industry_lower:
            result = [CASE_STUDIES[k] for k in keys]
            # Add a third if we only matched 2
            for fallback in ["canopy", "lalo", "branch", "newton", "fatty15"]:
                if fallback not in keys and len(result) < 3:
                    result.append(CASE_STUDIES[fallback])
            return result[:3]

    # Default mix
    return [CASE_STUDIES["branch"], CASE_STUDIES["fatty15"], CASE_STUDIES["canopy"]]


# ---------------------------------------------------------------------------
# Brand trait reasoning engine
# ---------------------------------------------------------------------------

def _detect_brand_traits(report: DomainAdReport) -> list[dict]:
    """Analyze enrichment + brand_intel data to identify brand traits and map to Upscale arguments."""
    e = report.enrichment
    mix = report.channel_mix
    intel = report.brand_intel
    traits = []

    if e:
        # High AOV
        if e.avg_product_price:
            try:
                price = float(str(e.avg_product_price).replace("$", "").replace(",", ""))
                if price >= 100:
                    traits.append({
                        "trait": "High AOV",
                        "icon": "&#x1f4b0;",
                        "why": f"At ${price:,.0f} average order value, streaming TV's premium environment and high completion rates drive efficient conversion economics. Every attributed purchase carries meaningful revenue.",
                    })
            except (ValueError, TypeError):
                pass

        # Purchase model — use brand_intel detection if available
        from models.ad_models import PurchaseModel
        if intel and intel.purchase_model == PurchaseModel.SUBSCRIPTION:
            traits.append({
                "trait": "Subscription Model",
                "icon": "&#x1f504;",
                "why": "Subscription brands benefit from streaming TV's retargeting and reactivation capabilities. CTV drives first subscriptions while retargeting re-engages lapsed subscribers — maximizing LTV.",
            })
        elif intel and intel.purchase_model == PurchaseModel.HIGH_REPURCHASE:
            traits.append({
                "trait": "High Repurchase Rate",
                "icon": "&#x1f504;",
                "why": "Consumable products with repeat purchase behavior are ideal for CTV. First-purchase acquisition via streaming TV, then retargeting to drive repurchase. Streaming exposure keeps your brand top-of-mind between purchases.",
            })
        else:
            # Fallback to text-based detection
            industry_lower = (e.industry or "").lower()
            desc_lower = (e.description or "").lower()
            if any(w in desc_lower or w in industry_lower for w in ["subscription", "subscribe", "membership"]):
                traits.append({
                    "trait": "Subscription Model",
                    "icon": "&#x1f504;",
                    "why": "Subscription brands benefit from streaming TV's retargeting and reactivation capabilities. CTV drives first subscriptions while retargeting re-engages lapsed subscribers — maximizing LTV.",
                })

        # Venture-backed / funded (check early — strong pitch signal)
        if intel and (intel.total_funding or intel.investors):
            investor_note = ""
            if intel.investors:
                investor_note = f" Backed by {', '.join(intel.investors[:2])}."
            traits.append({
                "trait": "Venture-Backed Growth",
                "icon": "&#x1f680;",
                "why": f"Funded brands need marketing channels that prove ROI to investors.{investor_note} Streaming TV + YouTube with built-in attribution provides the measurable performance data boards and investors demand — not just reach metrics.",
            })

        # Strong visuals / demonstrable product
        industry_lower = (e.industry or "").lower()
        if any(w in industry_lower for w in ["beauty", "cosmetic", "skincare", "fashion", "apparel", "furniture", "home", "decor", "food", "beverage"]):
            traits.append({
                "trait": "Visually Demonstrable",
                "icon": "&#x1f3ac;",
                "why": "Visually rich products thrive on the big screen. Upscale's AI creative engine can generate dozens of product-focused video variations — showcasing textures, transformations, and lifestyle context that static social ads can't match.",
            })

        # Existing paid social / search + spend context
        if mix and (mix.has_meta or mix.has_youtube):
            channels = []
            if mix.has_meta:
                channels.append("Meta")
            if mix.has_youtube:
                channels.append("YouTube")
            spend_note = ""
            if intel and intel.spend_estimate:
                s = intel.spend_estimate
                spend_note = f" We estimate ~{_fmt_money(s.meta_spend)}/mo on Meta alone. "
            traits.append({
                "trait": f"Active on {' + '.join(channels)}",
                "icon": "&#x1f4e1;",
                "why": f"You're already investing in {' and '.join(channels)}.{spend_note} Streaming TV provides incremental reach beyond social audiences, and cross-channel lift studies show CTV exposure increases social ad performance and brand search volume.",
            })

        # No TV / CTV presence — with competitor context
        if mix and not mix.has_linear:
            comp_note = ""
            if intel and intel.competitors_on_ctv:
                comp_note = f" Your competitors ({', '.join(intel.competitors_on_ctv)}) are already there."
            traits.append({
                "trait": "Untapped TV Opportunity",
                "icon": "&#x1f4fa;",
                "why": f"47% of TV is now streaming, and you're not on it.{comp_note} That's the largest premium screen in the house, reaching audiences that don't see social ads.",
            })

        # Brand search trend
        if intel and intel.brand_search_trend == "rising":
            traits.append({
                "trait": "Rising Brand Interest",
                "icon": "&#x1f4c8;",
                "why": "Google Trends shows rising search interest for your brand. CTV amplifies this momentum — streaming TV exposure is proven to drive incremental brand search volume, accelerating organic growth.",
            })
        elif intel and intel.brand_search_trend == "declining":
            traits.append({
                "trait": "Brand Awareness Gap",
                "icon": "&#x1f4c9;",
                "why": "Google Trends shows declining search interest for your brand. CTV is the proven channel for reversing this — streaming TV drives measurable brand search lift and re-introduces your brand to lapsed audiences on the biggest screen in the house.",
            })

        # Analytics maturity
        if intel and intel.analytics_maturity == "advanced":
            traits.append({
                "trait": "Measurement-Ready",
                "icon": "&#x1f4ca;",
                "why": f"Your tech stack ({', '.join(intel.attribution_tools[:3])}) shows strong analytics maturity. You're well-positioned to see clear, attributable CTV results from day one. Upscale's built-in attribution layers on top of your existing measurement stack.",
            })
        elif intel and intel.analytics_maturity == "basic":
            traits.append({
                "trait": "Attribution Gap",
                "icon": "&#x1f4ca;",
                "why": "Your current analytics stack has limited attribution visibility. Upscale's built-in measurement — IP-based attribution, incrementality testing, SKU-level insight — fills a critical gap and gives you attribution you likely don't have today.",
            })

        # Strong email / seasonal
        milled = report.milled_intel
        if milled and milled.found and milled.emails_per_week > 1.0:
            traits.append({
                "trait": "Active Email Marketer",
                "icon": "&#x1f4e7;",
                "why": f"You send ~{milled.emails_per_week:.0f} emails/week — you already have a promotional rhythm. Streaming flights timed 3-5 days before your biggest email drops prime audiences and increase open rates and purchase intent.",
            })

        # UGC / social content
        desc_lower = (e.description or "").lower()
        has_social = bool(e.social_profiles and len(e.social_profiles) > 2)
        if has_social or any(w in desc_lower for w in ["community", "social", "ugc", "creator", "influencer"]):
            traits.append({
                "trait": "Strong Social Presence",
                "icon": "&#x1f4f8;",
                "why": "Your existing social and UGC content is a goldmine. Upscale can turn your best-performing organic and creator content into widescreen, TV-ready creative — no new production shoot required.",
            })

    # Always include at most 5 traits
    return traits[:5]


def _build_why_brand(company, traits: list[dict]) -> str:
    """Build the personalized 'Why Upscale for [Brand]' section."""
    if not traits:
        return ""

    items = []
    for t in traits:
        items.append(f"""<div style="display:flex;gap:14px;align-items:flex-start;padding:20px;background:white;border:1px solid var(--border);border-radius:12px">
    <span style="font-size:1.6rem;flex-shrink:0">{t['icon']}</span>
    <div>
      <h4 style="font-size:.95rem;color:var(--navy);margin-bottom:4px">{_esc(t['trait'])}</h4>
      <p style="font-size:.85rem;color:#475467;line-height:1.6">{t['why']}</p>
    </div>
  </div>""")

    return f"""<div class="section">
  <h2>Why Upscale for {company}</h2>
  <p class="section-sub">Based on your brand's profile, here's why streaming TV + YouTube with Upscale is the right move right now.</p>
  <div class="grid-2">{"".join(items)}</div>
</div>"""


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

class PitchConfig:
    """Overridable pitch report configuration.

    Any field left as None uses the auto-detected default.
    """
    def __init__(
        self,
        company_name: str | None = None,
        industry: str | None = None,
        monthly_budget_m1: float | None = None,
        monthly_budget_m2: float | None = None,
        monthly_budget_m3: float | None = None,
        total_creatives: int | None = None,
        strategy_tier: str | None = None,  # "youtube_only", "ctv_led", "full_funnel"
        include_ctv: bool | None = None,
        include_youtube: bool | None = None,
        campaign_start_date: str | None = None,
    ):
        self.company_name = company_name
        self.industry = industry
        self.monthly_budget_m1 = monthly_budget_m1
        self.monthly_budget_m2 = monthly_budget_m2
        self.monthly_budget_m3 = monthly_budget_m3
        self.total_creatives = total_creatives
        self.strategy_tier = strategy_tier
        self.include_ctv = include_ctv
        self.include_youtube = include_youtube
        self.campaign_start_date = campaign_start_date

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

    @classmethod
    def from_dict(cls, d: dict) -> "PitchConfig":
        return cls(**{k: v for k, v in d.items() if k in cls.__init__.__code__.co_varnames})


def generate_pitch_report(
    report: DomainAdReport,
    fit: UpscaleFitResult,
    config: PitchConfig | None = None,
) -> str:
    """Generate the external-facing pitch HTML."""
    cfg = config or PitchConfig()
    e = report.enrichment
    company = _esc(cfg.company_name or report.company_name or report.domain)
    domain = _esc(report.domain)
    industry = _esc(cfg.industry or (e.industry.split("/")[-1].strip() if e and e.industry else "E-Commerce"))
    description = _esc(e.description) if e and e.description else ""

    monthly_rev = e.estimated_monthly_revenue if e else None
    intel = report.brand_intel
    budget = _budget_tier(monthly_rev, intel)

    # Apply budget overrides from config
    if cfg.monthly_budget_m1 is not None:
        budget["m1"] = cfg.monthly_budget_m1
    if cfg.monthly_budget_m2 is not None:
        budget["m2"] = cfg.monthly_budget_m2
    if cfg.monthly_budget_m3 is not None:
        budget["m3"] = cfg.monthly_budget_m3
    budget["daily"] = round(budget["m1"] / 30)

    has_shopify = _detect_shopify(report)
    has_klaviyo = _detect_klaviyo(report)

    logo_html = ""

    # Detect brand traits for personalization
    brand_traits = _detect_brand_traits(report)

    # Determine spend strategy based on annual ad spend tier
    strategy = _spend_strategy(intel, budget)

    # Apply strategy tier override from config
    if cfg.strategy_tier and cfg.strategy_tier in ("youtube_only", "ctv_led", "full_funnel"):
        strategy["tier"] = cfg.strategy_tier

    # Build sections — each wrapped so one failure doesn't kill the report
    import logging as _log
    _plog = _log.getLogger("pitch_report")

    def _safe(name, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            _plog.warning(f"Pitch section '{name}' failed: {exc}")
            return f'<!-- section {name} failed: {_esc(str(exc))} -->'

    hero = _safe("hero", _build_hero, company, domain, industry, description, logo_html, budget, strategy)
    exec_summary = _safe("exec_summary", _build_exec_summary, company, report, budget, intel, has_shopify, has_klaviyo, strategy)
    toc = _safe("toc", _build_toc, company, report, intel, strategy)
    problem = _safe("problem", _build_problem, company, report, budget)
    overview = _safe("overview", _build_overview, company, budget, monthly_rev, intel, strategy)
    company_snapshot = _safe("company_snapshot", _build_company_snapshot, company, report, intel)
    why_brand = _safe("why_brand", _build_why_brand, company, brand_traits)
    integration = _safe("integration", _build_integration, company, has_shopify, has_klaviyo)
    platform = _safe("platform", _build_platform)
    creative_system = _safe("creative_system", _build_creative_system, company, report, budget)
    spend_charts = _safe("spend_charts", _build_spend_charts, company, budget, strategy)
    campaign_plan = _safe("campaign_plan", _build_campaign_plan, company, budget, has_shopify, has_klaviyo, strategy, report)
    # For YouTube-only tier, skip CTV impact section
    if strategy["tier"] == "youtube_only":
        ctv_impact = ""
    else:
        ctv_impact = _safe("ctv_impact", _build_ctv_impact, company, report, budget, has_shopify)
    youtube_impact = _safe("youtube_impact", _build_youtube_impact, company, report, budget)
    optimization = _safe("optimization", _build_optimization_engine, company)
    attribution = _safe("attribution", _build_attribution_system, company, has_shopify)
    promo_cal = ""  # Now embedded inside campaign plan
    competitive = _safe("competitive", _build_competitive_landscape, company, intel)
    roi_projection = _safe("roi_projection", _build_roi_projection, company, budget, monthly_rev, intel, strategy, has_shopify, e)
    audience_strategy = _safe("audience_strategy", _build_audience_strategy, company, report, intel, strategy, has_shopify, has_klaviyo)
    objection_killer = _safe("objection_killer", _build_objection_killer, company, report, budget, strategy)
    results = _safe("results", _build_proven_results, company, e.industry if e else None)
    creative_preview = _safe("creative_preview", _build_creative_preview, company, report)
    audio_demos = _safe("audio_demos", _build_audio_demos, company, report)
    creative_showcase = _safe("creative_showcase", _build_creative_showcase, report)
    ad_discovery_video = _safe("ad_discovery_video", _build_ad_discovery_video, company, report)
    inventory = "" if strategy["tier"] == "youtube_only" else _safe("inventory", _build_inventory)
    next_steps = _safe("next_steps", _build_next_steps, company, budget)

    generated = datetime.utcnow().strftime("%B %d, %Y")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Streaming Proposal — {company} + Upscale.ai</title>
<meta name="description" content="Custom CTV and YouTube streaming proposal for {company} by Upscale.ai">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2"></script>
<script src="https://player.vimeo.com/api/player.js"></script>
<style>
:root {{
  --pink: #831F80;
  --pink-light: #F6EBF6;
  --pink-glow: #FF3AF9;
  --navy: #021A20;
  --teal: #0A6D86;
  --teal-light: #E6F5F8;
  --white: #FFFFFF;
  --border: #D7D7D7;
  --muted: #838383;
  --bg: #F6F6F6;
  --success: #027A48;
  --success-light: #ECFDF3;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  color: var(--navy);
  background: var(--white);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}}
.page {{ max-width: 1080px; margin: 0 auto; }}

/* ── Site-style Header ── */
.site-header {{
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--white);
  border-bottom: 1px solid var(--border);
  padding: 0 40px;
}}
.site-header-inner {{
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
}}
.site-header .logo-link {{
  display: flex;
  align-items: center;
  text-decoration: none;
}}
.site-header .logo-link {{ flex-direction: column; gap: 2px; }}
.site-header .logo-link svg {{ height: 28px; width: auto; }}
.logo-tagline {{ font-size: .58rem; color: var(--muted); letter-spacing: .04em; font-weight: 500; white-space: nowrap; }}
.site-header-nav {{
  display: flex;
  gap: 28px;
  align-items: center;
}}
.site-header-nav a {{
  color: var(--navy);
  text-decoration: none;
  font-size: .85rem;
  font-weight: 500;
  transition: color .15s;
}}
.site-header-nav a:hover {{ color: #831F80; }}
.header-actions {{
  display: flex;
  align-items: center;
  gap: 12px;
}}
.header-brand {{
  color: var(--muted);
  font-size: .8rem;
  font-weight: 500;
}}
.header-cta {{
  display: inline-flex;
  align-items: center;
  padding: 8px 20px;
  background: var(--navy);
  color: var(--white);
  font-size: .82rem;
  font-weight: 600;
  border-radius: 8px;
  text-decoration: none;
  transition: background .15s;
}}
.header-cta:hover {{ background: #0a3a48; }}

/* Hero */
.hero {{
  background: linear-gradient(135deg, var(--navy) 0%, #0d3a47 50%, var(--pink) 100%);
  color: white;
  padding: 80px 40px 60px;
  position: relative;
  overflow: hidden;
}}
.hero::before {{
  content: '';
  position: absolute;
  top: -40%;
  right: -10%;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(131,31,128,.3), transparent 70%);
  border-radius: 50%;
}}
.hero-eyebrow {{
  display: inline-block;
  background: rgba(255,255,255,.12);
  backdrop-filter: blur(8px);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .12em;
  text-transform: uppercase;
  padding: 6px 14px;
  border-radius: 999px;
  margin-bottom: 20px;
  border: 1px solid rgba(255,255,255,.15);
}}
.hero h1 {{
  font-size: clamp(2.4rem, 5vw, 3.8rem);
  line-height: 1.08;
  letter-spacing: -0.04em;
  font-weight: 800;
  max-width: 780px;
  margin-bottom: 16px;
}}
.hero h1 .highlight {{ color: var(--pink-glow); }}
.hero-sub {{
  font-size: 1.1rem;
  color: rgba(255,255,255,.78);
  max-width: 640px;
  margin-bottom: 28px;
}}
.hero-stats {{
  display: flex;
  gap: 32px;
  flex-wrap: wrap;
}}
.hero-stat {{
  text-align: center;
}}
.hero-stat .num {{
  font-size: 2rem;
  font-weight: 800;
}}
.hero-stat .lbl {{
  font-size: .75rem;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: rgba(255,255,255,.6);
}}
.brand-logo {{
  width: 220px;
  height: 220px;
  border-radius: 16px;
  object-fit: contain;
  background: white;
  padding: 12px;
  margin-bottom: 16px;
}}

/* Sections */
.section {{
  padding: 56px 40px;
  border-bottom: 1px solid var(--border);
}}
.section.alt {{ background: var(--bg); }}
.section.dark {{
  background: var(--navy);
  color: white;
  border-bottom-color: #0d3a47;
}}
.section h2 {{
  font-size: 1.8rem;
  letter-spacing: -0.03em;
  margin-bottom: 8px;
}}
.section .section-sub {{
  font-size: 1rem;
  color: var(--muted);
  margin-bottom: 28px;
  max-width: 640px;
}}
.section.dark .section-sub {{ color: rgba(255,255,255,.6); }}
.section.dark h2 {{ color: white; }}

/* Cards grid */
.grid-3 {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}}
.grid-2 {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}}
.grid-4 {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}}
.card {{
  background: white;
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 28px;
  transition: transform .2s ease, box-shadow .2s ease;
}}
.card:hover {{
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(2,26,32,.1);
}}
.card.dark {{
  background: rgba(255,255,255,.06);
  border-color: rgba(255,255,255,.12);
  color: white;
}}
.card h3 {{
  font-size: 1.1rem;
  margin-bottom: 10px;
}}
.card .icon {{
  font-size: 2rem;
  margin-bottom: 12px;
}}
.card p, .card li {{
  font-size: .9rem;
  color: #475467;
  line-height: 1.65;
}}
.card.dark p, .card.dark li {{
  color: rgba(255,255,255,.7);
}}

/* Stat highlight */
.stat-big {{
  font-size: 2.4rem;
  font-weight: 800;
  color: var(--pink);
  line-height: 1;
  margin-bottom: 4px;
}}
.stat-label {{
  font-size: .78rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: .05em;
}}

/* Integration cards */
.integration-card {{
  background: white;
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 28px;
  border-top: 4px solid var(--teal);
}}
.integration-card.active {{
  border-top-color: var(--success);
  background: var(--success-light);
}}
.integration-card h3 {{
  font-size: 1.1rem;
  margin-bottom: 12px;
}}
.integration-card .badge {{
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: .72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .06em;
  margin-bottom: 12px;
}}
.integration-card .badge.connected {{
  background: var(--success-light);
  color: var(--success);
}}
.integration-card .badge.available {{
  background: var(--pink-light);
  color: var(--pink);
}}
.check-list {{
  list-style: none;
  padding: 0;
}}
.check-list li {{
  font-size: .88rem;
  padding: 5px 0;
  padding-left: 22px;
  position: relative;
  color: #475467;
}}
.check-list li::before {{
  content: '\\2713';
  position: absolute;
  left: 0;
  color: var(--success);
  font-weight: 700;
}}

/* Phase cards */
.phase-card {{
  background: white;
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 24px;
  position: relative;
  overflow: hidden;
}}
.phase-card::before {{
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 4px;
}}
.phase-card.p1::before {{ background: var(--teal); }}
.phase-card.p2::before {{ background: var(--pink); }}
.phase-card.p3::before {{ background: var(--navy); }}
.phase-card .phase-label {{
  font-size: .72rem;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 6px;
}}
.phase-card .phase-budget {{
  font-size: 1.8rem;
  font-weight: 800;
  color: var(--navy);
  margin-bottom: 4px;
}}
.phase-card h3 {{
  font-size: 1rem;
  margin-bottom: 10px;
}}
.phase-card ul {{
  list-style: none;
  padding: 0;
}}
.phase-card li {{
  font-size: .85rem;
  color: #475467;
  padding: 4px 0;
  padding-left: 18px;
  position: relative;
}}
.phase-card li::before {{
  content: '\\2713';
  position: absolute;
  left: 0;
  color: var(--success);
  font-weight: 700;
}}

/* Impact section */
.impact-grid {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-top: 20px;
}}
.impact-stat {{
  text-align: center;
  padding: 20px;
  background: var(--bg);
  border-radius: 12px;
  transition: transform .2s ease, box-shadow .2s ease;
  cursor: default;
}}
.impact-stat:hover {{
  transform: scale(1.05);
  box-shadow: 0 4px 16px rgba(2,26,32,.08);
}}
.impact-stat .num {{
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--navy);
}}
.impact-stat .lbl {{
  font-size: .72rem;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: var(--muted);
  margin-top: 4px;
}}
.section.dark .impact-stat {{
  background: rgba(255,255,255,.08);
}}
.section.dark .impact-stat .num {{
  color: white;
}}
.section.dark .impact-stat .lbl {{
  color: rgba(255,255,255,.6);
}}

/* Case study cards */
.case-card {{
  background: white;
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 28px;
  text-align: center;
  transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
}}
.case-card:hover {{
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(131,31,128,.1);
  border-color: var(--pink);
}}
.case-card .case-name {{
  font-size: 1.2rem;
  font-weight: 800;
  color: var(--navy);
  margin-bottom: 4px;
}}
.case-card .case-vertical {{
  font-size: .75rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: .06em;
  margin-bottom: 16px;
}}
.case-stats {{
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 14px;
}}
.case-stat {{
  text-align: center;
}}
.case-stat .val {{
  font-size: 1.4rem;
  font-weight: 800;
  color: var(--pink);
  line-height: 1;
}}
.case-stat .lbl {{
  font-size: .68rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: .04em;
  margin-top: 4px;
}}
.case-card .case-quote {{
  font-size: .85rem;
  color: #475467;
  font-style: italic;
  border-top: 1px solid #f0f0f0;
  padding-top: 12px;
  margin-top: 4px;
}}

/* Why Upscale wins */
.win-grid {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}}
.win-item {{
  display: flex;
  gap: 14px;
  align-items: flex-start;
  padding: 16px;
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 10px;
}}
.win-check {{
  color: var(--pink-glow);
  font-size: 1.2rem;
  font-weight: 700;
  flex-shrink: 0;
  margin-top: 2px;
}}
.win-item h4 {{
  font-size: .92rem;
  color: white;
  margin-bottom: 4px;
}}
.win-item p {{
  font-size: .82rem;
  color: rgba(255,255,255,.6);
  line-height: 1.5;
}}

/* Calendar */
.cal-month {{ margin-bottom: 14px; }}
.cal-month h4 {{
  font-size: .85rem;
  font-weight: 700;
  color: var(--navy);
  padding-bottom: 6px;
  border-bottom: 1px solid #eee;
  margin-bottom: 6px;
}}
.cal-row {{
  display: grid;
  grid-template-columns: 70px 1fr;
  gap: 8px;
  padding: 4px 0;
  font-size: .82rem;
  border-bottom: 1px solid #fafafa;
}}
.cal-date {{ color: var(--muted); font-weight: 500; }}
.cal-subj {{ color: var(--navy); }}

/* Spend bar chart */
.spend-chart {{
  display: flex;
  align-items: flex-end;
  gap: 32px;
  height: 220px;
  margin: 28px auto 0;
  max-width: 600px;
  padding: 0 24px;
}}
.spend-month-group {{
  flex: 1;
  display: flex;
  gap: 6px;
  align-items: flex-end;
  height: 100%;
  position: relative;
  padding-bottom: 24px;
}}
.spend-month-group .spend-bar {{
  flex: 1;
}}
.spend-bar {{
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  height: 100%;
  justify-content: flex-end;
}}
.spend-bar-fill {{
  width: 100%;
  border-radius: 10px 10px 4px 4px;
  position: relative;
  transition: transform .25s ease, box-shadow .25s ease;
  cursor: default;
  min-height: 24px;
}}
.spend-bar-fill:hover {{
  transform: scaleY(1.06);
  transform-origin: bottom;
  box-shadow: 0 -4px 20px rgba(131,31,128,.25);
}}
.spend-bar-fill .bar-tooltip {{
  position: absolute;
  top: -36px;
  left: 50%;
  transform: translateX(-50%) scale(.85);
  background: var(--navy);
  color: white;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: .72rem;
  font-weight: 600;
  white-space: nowrap;
  opacity: 0;
  transition: opacity .2s ease, transform .2s ease;
  pointer-events: none;
}}
.spend-bar-fill:hover .bar-tooltip {{
  opacity: 1;
  transform: translateX(-50%) scale(1);
}}
.spend-bar-val {{
  font-size: .85rem;
  font-weight: 800;
  color: var(--navy);
}}
.section.dark .spend-bar-val {{
  color: white;
}}
.spend-bar-label {{
  font-size: .72rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: .04em;
  font-weight: 600;
}}
.section.dark .spend-bar-label {{
  color: rgba(255,255,255,.6);
}}
/* Dark section bar hover */
.section.dark .spend-bar-fill:hover {{
  box-shadow: 0 -4px 20px rgba(255,255,255,.15);
}}

/* Inventory logos */
.logo-grid {{
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  justify-content: center;
  padding: 20px 0;
}}
.logo-pill {{
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px 20px;
  font-size: .85rem;
  font-weight: 600;
  color: var(--navy);
  transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
  cursor: default;
}}
.logo-pill:hover {{
  transform: translateY(-2px);
  border-color: var(--teal);
  box-shadow: 0 4px 12px rgba(10,98,104,.12);
}}

/* CTA */
.cta {{
  background: linear-gradient(135deg, var(--pink) 0%, var(--navy) 100%);
  color: white;
  padding: 60px 40px;
  text-align: center;
}}
.cta h2 {{
  font-size: 2rem;
  margin-bottom: 12px;
  color: white;
}}
.cta p {{
  font-size: 1.05rem;
  color: rgba(255,255,255,.8);
  max-width: 560px;
  margin: 0 auto 28px;
}}
.cta-steps {{
  display: flex;
  justify-content: center;
  gap: 24px;
  flex-wrap: wrap;
  margin-top: 24px;
}}
.cta-step {{
  background: rgba(255,255,255,.1);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,.15);
  border-radius: 20px;
  padding: 24px;
  width: 180px;
  text-align: center;
  transition: transform .2s ease, background .2s ease;
}}
.cta-step:hover {{
  transform: translateY(-4px);
  background: rgba(255,255,255,.18);
}}
.cta-step .step-num {{
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--pink-glow);
}}
.cta-step .step-label {{
  font-size: .82rem;
  margin-top: 6px;
  color: rgba(255,255,255,.85);
}}

/* Transparency */
.transparency-grid {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}}
.transparency-item {{
  text-align: center;
  padding: 24px;
  background: var(--bg);
  border-radius: 12px;
  transition: transform .2s ease, box-shadow .2s ease;
}}
.transparency-item:hover {{
  transform: translateY(-3px);
  box-shadow: 0 6px 18px rgba(2,26,32,.06);
}}
.transparency-item .icon {{
  font-size: 1.8rem;
  margin-bottom: 10px;
}}
.transparency-item h4 {{
  font-size: .95rem;
  margin-bottom: 6px;
}}
.transparency-item p {{
  font-size: .82rem;
  color: #475467;
}}

/* Table of contents */
.toc-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
  margin-top: 20px;
}}
.toc-item {{
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: white;
  border: 1px solid var(--border);
  border-radius: 8px;
  text-decoration: none;
  color: var(--navy);
  font-size: .85rem;
  font-weight: 500;
  transition: all .2s ease;
}}
.toc-item:hover {{
  border-color: var(--pink);
  box-shadow: 0 2px 12px rgba(131,31,128,.1);
  text-decoration: none;
}}
.toc-num {{
  font-weight: 800;
  color: var(--pink);
  font-size: 1rem;
  flex-shrink: 0;
  width: 24px;
}}

/* Collapsible sections */
details.collapsible {{
  border: none;
}}
details.collapsible > summary {{
  cursor: pointer;
  list-style: none;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: .82rem;
  font-weight: 600;
  color: var(--teal);
  padding: 10px 0;
  user-select: none;
}}
details.collapsible > summary::-webkit-details-marker {{ display: none; }}
details.collapsible > summary::before {{
  content: '\\25B6';
  font-size: .65rem;
  transition: transform .2s;
  flex-shrink: 0;
}}
details.collapsible[open] > summary::before {{
  transform: rotate(90deg);
}}
details.collapsible > .collapse-content {{
  animation: slideDown .3s ease;
  padding-top: 8px;
}}
@keyframes slideDown {{
  from {{ opacity: 0; transform: translateY(-8px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

/* Exec summary */
.exec-summary {{
  padding: 40px;
  border-bottom: 1px solid var(--border);
  background: var(--bg);
}}
.exec-kpi-strip {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  margin-top: 24px;
}}
.exec-kpi {{
  text-align: center;
  padding: 16px 12px;
  background: white;
  border: 1px solid var(--border);
  border-radius: 10px;
  transition: transform .2s ease, box-shadow .2s ease;
  cursor: default;
}}
.exec-kpi:hover {{
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(2,26,32,.08);
}}
.exec-kpi .val {{
  font-size: 1.4rem;
  font-weight: 800;
  color: var(--navy);
}}
.exec-kpi .lbl {{
  font-size: .68rem;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: var(--muted);
  margin-top: 2px;
}}

/* ── Creative Showcase ── */
.showcase-section {{ padding: 80px 0; background: var(--bg); }}
.showcase-header {{ text-align: center; margin-bottom: 40px; }}
.showcase-header .kicker {{ font-size: .75rem; text-transform: uppercase; letter-spacing: .12em; color: var(--teal); font-weight: 700; margin-bottom: 8px; }}
.showcase-header h2 {{ font-size: 2.2rem; font-weight: 800; letter-spacing: -.02em; margin-bottom: 12px; }}
.showcase-header p {{ color: var(--muted); max-width: 600px; margin: 0 auto; font-size: .95rem; }}
.showcase-filters {{ display: flex; justify-content: center; flex-wrap: wrap; gap: 8px; margin-bottom: 32px; padding: 0 24px; }}
.showcase-filter {{ padding: 7px 18px; border-radius: 100px; border: 1px solid var(--border); background: white; font-size: .8rem; font-weight: 600; color: var(--navy); cursor: pointer; transition: all .15s; font-family: inherit; }}
.showcase-filter:hover {{ border-color: var(--pink); color: var(--pink); }}
.showcase-filter.active {{ background: var(--navy); color: white; border-color: var(--navy); }}
.showcase-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; max-width: 1080px; margin: 0 auto; padding: 0 40px; }}
.showcase-card {{ position: relative; border-radius: 14px; overflow: hidden; cursor: pointer; background: #000; aspect-ratio: 16/9; }}
.showcase-card[data-cats] {{ }}
.showcase-card.hidden {{ display: none; }}
.showcase-card.showcase-collapsed {{ display: none; }}
.showcase-thumb {{ width: 100%; height: 100%; object-fit: cover; transition: transform .3s, opacity .3s; display: block; }}
.showcase-card:hover .showcase-thumb {{ transform: scale(1.05); opacity: .85; }}
.showcase-overlay {{ position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; pointer-events: none; }}
.showcase-play {{ width: 56px; height: 56px; background: rgba(255,255,255,.92); border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 20px rgba(0,0,0,.25); transition: transform .2s; }}
.showcase-card:hover .showcase-play {{ transform: scale(1.1); }}
.showcase-play svg {{ width: 22px; height: 22px; margin-left: 3px; fill: var(--navy); }}
.showcase-tag {{ position: absolute; top: 12px; left: 12px; padding: 4px 12px; background: rgba(131,31,128,.88); color: white; font-size: .65rem; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; border-radius: 6px; backdrop-filter: blur(4px); }}
.showcase-brand {{ position: absolute; bottom: 12px; left: 12px; color: white; font-size: .8rem; font-weight: 700; text-shadow: 0 1px 6px rgba(0,0,0,.5); }}
/* Lightbox modal */
.showcase-modal {{ position: fixed; inset: 0; z-index: 9999; background: rgba(0,0,0,.88); display: none; align-items: center; justify-content: center; backdrop-filter: blur(4px); }}
.showcase-modal.open {{ display: flex; }}
.showcase-modal-inner {{ width: 80vw; aspect-ratio: 16/9; position: relative; border-radius: 14px; overflow: hidden; background: #000; box-shadow: 0 20px 60px rgba(0,0,0,.5); }}
.showcase-modal-inner iframe {{ width: 100%; height: 100%; border: 0; }}
.showcase-modal-close {{ position: absolute; top: -48px; right: 0; width: 40px; height: 40px; background: rgba(255,255,255,.15); border: none; border-radius: 50%; color: white; font-size: 1.4rem; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background .15s; }}
.showcase-modal-close:hover {{ background: rgba(255,255,255,.3); }}
@media (max-width: 900px) {{
  .showcase-grid {{ grid-template-columns: repeat(2, 1fr); gap: 16px; padding: 0 20px; }}
}}
@media (max-width: 640px) {{
  .showcase-grid {{ grid-template-columns: 1fr; }}
  .showcase-header h2 {{ font-size: 1.6rem; }}
}}

/* ── Site-style Footer ── */
.site-footer {{
  margin-top: 80px;
}}
.footer-cta {{
  background: var(--navy);
  border-radius: 20px;
  padding: 48px 32px;
  text-align: center;
  margin: 0 40px 32px;
}}
.footer-cta h3 {{
  color: var(--white);
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 8px;
}}
.footer-cta p {{
  color: rgba(255,255,255,.65);
  font-size: .95rem;
  margin-bottom: 20px;
}}
.footer-cta .cta-btn {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 28px;
  background: var(--white);
  color: var(--navy);
  font-size: .9rem;
  font-weight: 600;
  border-radius: 10px;
  text-decoration: none;
  transition: transform .15s, box-shadow .15s;
}}
.footer-cta .cta-btn:hover {{ transform: translateY(-1px); box-shadow: 0 4px 16px rgba(0,0,0,.2); }}
.footer-bottom {{
  padding: 24px 40px 12px;
  text-align: center;
}}
.footer-nav {{
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-bottom: 20px;
}}
.footer-nav a {{
  color: var(--navy);
  text-decoration: none;
  font-size: .82rem;
  font-weight: 500;
}}
.footer-nav a:hover {{ color: #831F80; }}
.footer-social {{
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-bottom: 20px;
}}
.footer-social a {{
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #F6F6F6;
  color: var(--navy);
  text-decoration: none;
  transition: background .15s;
}}
.footer-social a:hover {{ background: #F6EBF6; }}
.footer-social a svg {{ width: 16px; height: 16px; }}
.footer-wordmark {{
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}}
.footer-wordmark svg {{ height: 22px; width: auto; opacity: .5; }}
.footer-legal {{
  display: flex;
  justify-content: center;
  gap: 18px;
  margin-bottom: 8px;
}}
.footer-legal a {{
  color: var(--muted);
  text-decoration: none;
  font-size: .75rem;
}}
.footer-legal a:hover {{ color: var(--navy); }}
.footer-meta {{
  color: var(--muted);
  font-size: .72rem;
  margin-top: 6px;
}}

@media (max-width: 900px) {{
  .grid-3, .grid-4, .transparency-grid {{ grid-template-columns: 1fr; }}
  .grid-2, .win-grid {{ grid-template-columns: 1fr; }}
  .impact-grid {{ grid-template-columns: 1fr 1fr; }}
  .hero {{ padding: 48px 24px 40px; }}
  .section {{ padding: 40px 24px; }}
}}
@media (max-width: 640px) {{
  .site-header {{ padding: 0 16px; }}
  .site-header-nav {{ display: none; }}
  .footer-cta {{ margin: 0 20px 24px; padding: 32px 20px; }}
  .footer-bottom {{ padding: 20px 20px 12px; }}
  .cta-steps {{ flex-direction: column; align-items: center; }}
  .hero-stats {{ gap: 20px; }}
  .case-stats {{ flex-direction: column; gap: 8px; }}
}}
</style>
</head>
<body>
<div class="page">
  <header class="site-header">
    <div class="site-header-inner">
      <a href="https://upscale.ai" class="logo-link" target="_blank" rel="noopener">
        <svg width="136" height="35" viewBox="0 0 136 35" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M10.7512 9.8282H14.7971V12.5491L14.2694 13.4635L12.7793 16.0451H14.7971V25.5127H10.7512V23.7557C9.76786 25.22 8.2103 25.952 6.07706 25.952C4.36255 25.952 2.94576 25.3771 1.82679 24.2264C0.707924 23.0762 0.148438 21.4869 0.148438 19.4588V9.8282H4.19487V18.9564C4.19487 20.0027 4.47724 20.8022 5.04188 21.3564C5.60652 21.9107 6.35943 22.1878 7.30032 22.1878C8.34591 22.1878 9.18251 21.8632 9.81022 21.2149C10.4371 20.5666 10.7512 19.5944 10.7512 18.2977V9.8282ZM88.2742 2.61377L84.2277 4.95011V25.5127H88.2742V2.61377ZM94.4343 19.3327C94.978 21.2986 96.4518 22.2819 98.857 22.2819C100.404 22.2819 101.576 21.7588 102.37 20.7132L105.633 22.5954C104.085 24.8331 101.805 25.952 98.7941 25.952C96.2015 25.952 94.1207 25.1674 92.5521 23.5995C90.9835 22.0308 90.1995 20.0546 90.1995 17.6709C90.1995 15.3077 90.9732 13.3366 92.5208 11.7577C94.068 10.1787 96.0548 9.3894 98.4807 9.3894C100.781 9.3894 102.678 10.1839 104.174 11.7732C105.669 13.3628 106.417 15.3286 106.417 17.6709C106.417 18.1931 106.365 18.7474 106.26 19.3327H94.4343ZM94.3713 16.1963H102.37C102.14 15.13 101.665 14.335 100.943 13.8124C100.221 13.2894 99.401 13.0277 98.4807 13.0277C97.393 13.0277 96.4942 13.3049 95.7828 13.8592C95.0723 14.4135 94.6016 15.1922 94.3713 16.1963ZM78.2562 9.8282H82.3027V25.5127H78.2562V23.6617C77.0433 25.1888 75.3388 25.952 73.1433 25.952C71.0524 25.952 69.259 25.1518 67.7638 23.552C66.2685 21.9521 65.5208 19.9916 65.5208 17.6709C65.5208 15.3492 66.2685 13.3885 67.7638 11.7887C69.259 10.1891 71.0524 9.3894 73.1433 9.3894C75.3388 9.3894 77.0433 10.1526 78.2562 11.6792V9.8282ZM70.7907 20.8548C71.6064 21.6803 72.6417 22.0937 73.8963 22.0937C75.1507 22.0937 76.1909 21.6803 77.0172 20.8548C77.8434 20.0285 78.2562 18.9675 78.2562 17.6709C78.2562 16.3739 77.8434 15.3129 77.0172 14.4868C76.1909 13.6606 75.1507 13.2478 73.8963 13.2478C72.6417 13.2478 71.6064 13.6606 70.7907 14.4868C69.9748 15.3129 69.5675 16.3739 69.5675 17.6709C69.5675 18.9675 69.9748 20.0285 70.7907 20.8548ZM57.4253 25.952C55.0622 25.952 53.0913 25.1569 51.5121 23.5674C49.9332 21.9781 49.144 20.0131 49.144 17.6709C49.144 15.3286 49.9332 13.3628 51.5121 11.7732C53.0913 10.1839 55.0622 9.3894 57.4253 9.3894C58.9518 9.3894 60.3425 9.75566 61.597 10.4869C62.8523 11.2189 63.8037 12.2022 64.4515 13.436L60.9701 15.4746C60.6561 14.8268 60.1803 14.3141 59.5422 13.9377C58.9051 13.5614 58.1885 13.3731 57.3941 13.3731C56.1811 13.3731 55.1771 13.7755 54.3828 14.5809C53.5878 15.3854 53.1906 16.4155 53.1906 17.6709C53.1906 18.9044 53.5878 19.9242 54.3828 20.7288C55.1771 21.5344 56.1811 21.9366 57.3941 21.9366C58.2092 21.9366 58.9361 21.7537 59.574 21.3874C60.2115 21.0215 60.6878 20.5147 61.0014 19.8663L64.5142 21.8735C63.8246 23.1074 62.8523 24.0959 61.597 24.8382C60.3425 25.5808 58.9518 25.952 57.4253 25.952ZM39.503 14.2831C39.503 14.7009 39.7802 15.0409 40.3344 15.3026C40.8888 15.5634 41.5629 15.7938 42.3579 15.9924C43.1524 16.1911 43.9467 16.4421 44.7418 16.7453C45.5362 17.0483 46.2104 17.5559 46.7647 18.2664C47.3189 18.9778 47.5962 19.8663 47.5962 20.9325C47.5962 22.5428 46.995 23.7823 45.7925 24.6502C44.5898 25.5178 43.0894 25.952 41.2909 25.952C38.0707 25.952 35.8753 24.7073 34.7036 22.2189L38.2175 20.2427C38.6775 21.6018 39.7017 22.2819 41.2909 22.2819C42.7345 22.2819 43.4554 21.8322 43.4554 20.9325C43.4554 20.5147 43.1783 20.1745 42.624 19.9139C42.0705 19.6522 41.3955 19.4166 40.6012 19.2077C39.8059 18.9987 39.0117 18.7371 38.2175 18.4235C37.4224 18.1095 36.748 17.6129 36.1937 16.9334C35.6395 16.2541 35.3622 15.4019 35.3622 14.377C35.3622 12.829 35.932 11.6109 37.0719 10.7224C38.2123 9.8342 39.629 9.3894 41.3229 9.3894C42.5981 9.3894 43.7584 9.67682 44.8047 10.2521C45.8503 10.827 46.6759 11.6479 47.2826 12.7145L43.8318 14.5963C43.3301 13.5301 42.4935 12.9967 41.3229 12.9967C40.7996 12.9967 40.3654 13.1114 40.0208 13.3419C39.6758 13.5717 39.503 13.8858 39.503 14.2831ZM25.8503 9.3894C27.9621 9.3894 29.7658 10.1891 31.261 11.7887C32.7564 13.3885 33.5041 15.3492 33.5041 17.6709C33.5041 19.9916 32.7564 21.9521 31.261 23.552C29.7658 25.1518 27.9621 25.952 25.8503 25.952C23.6541 25.952 21.9601 25.1888 20.7686 23.6617V31.7867H16.7222V16.0451H18.7397L17.2496 13.4635L16.7222 12.5491V9.8282H20.7686V11.6792C21.9601 10.1526 23.6541 9.3894 25.8503 9.3894ZM21.9919 20.8548C22.807 21.6803 23.8423 22.0937 25.0973 22.0937C26.3519 22.0937 27.3924 21.6803 28.2187 20.8548C29.0439 20.0285 29.4574 18.9675 29.4574 17.6709C29.4574 16.3739 29.0439 15.3129 28.2187 14.4868C27.3924 13.6606 26.3519 13.2478 25.0973 13.2478C23.8423 13.2478 22.807 13.6606 21.9919 14.4868C21.1762 15.3129 20.7686 16.3739 20.7686 17.6709C20.7686 18.9675 21.1762 20.0285 21.9919 20.8548Z" fill="#2B2731"/>
          <path d="M111.441 24.1096C110.98 24.5707 110.427 24.8014 109.781 24.8014C109.136 24.8014 108.582 24.5707 108.121 24.1096C107.66 23.6485 107.43 23.0953 107.43 22.4496C107.43 21.8039 107.66 21.2506 108.121 20.7896C108.582 20.3285 109.136 20.0978 109.781 20.0978C110.427 20.0978 110.98 20.3285 111.441 20.7896C111.903 21.2506 112.133 21.8039 112.133 22.4496C112.133 23.0953 111.903 23.6485 111.441 24.1096ZM132.624 7.42658C131.978 7.42658 131.418 7.18931 130.944 6.71519C130.47 6.24096 130.233 5.68095 130.233 5.03516C130.233 4.38947 130.47 3.82452 130.944 3.3402C131.418 2.85598 131.978 2.61377 132.624 2.61377C133.29 2.61377 133.86 2.85598 134.334 3.3402C134.809 3.82452 135.046 4.38947 135.046 5.03516C135.046 5.68095 134.809 6.24096 134.334 6.71519C133.86 7.18931 133.29 7.42658 132.624 7.42658ZM130.687 24.3775V9.24275H134.592V24.3775H130.687ZM125.294 9.24275H129.199V24.3775H125.294V22.5918C124.124 24.0648 122.479 24.8014 120.36 24.8014C118.342 24.8014 116.612 24.0296 115.169 22.4859C113.726 20.9419 113.005 19.0501 113.005 16.8101C113.005 14.5702 113.726 12.6784 115.169 11.1347C116.612 9.59072 118.342 8.81888 120.36 8.81888C122.479 8.81888 124.124 9.5555 125.294 11.0285V9.24275ZM118.09 19.8824C118.877 20.6795 119.876 21.0781 121.087 21.0781C122.297 21.0781 123.301 20.6795 124.098 19.8824C124.896 19.0855 125.294 18.0613 125.294 16.8101C125.294 15.559 124.896 14.5348 124.098 13.7379C123.301 12.9408 122.297 12.5422 121.087 12.5422C119.876 12.5422 118.877 12.9408 118.09 13.7379C117.303 14.5348 116.909 15.559 116.909 16.8101C116.909 18.0613 117.303 19.0855 118.09 19.8824Z" fill="url(#paint0_linear_pnav)"/>
          <defs><linearGradient id="paint0_linear_pnav" x1="108.121" y1="24.1096" x2="135.174" y2="2.43389" gradientUnits="userSpaceOnUse"><stop stop-color="#B72BB3"/><stop offset="1" stop-color="#60B1E3"/></linearGradient></defs>
        </svg>
        <span class="logo-tagline">AI Creative + Media + Measurement &mdash; One Platform</span>
      </a>
      <nav class="site-header-nav">
        <a href="https://upscale.ai/how-it-works" target="_blank" rel="noopener">Platform</a>
        <a href="https://upscale.ai/solutions" target="_blank" rel="noopener">Solutions</a>
        <a href="https://upscale.ai/solutions#case-studies" target="_blank" rel="noopener">Case Studies</a>
        <a href="https://upscale.ai/about" target="_blank" rel="noopener">About</a>
        <a href="https://upscale.ai/careers" target="_blank" rel="noopener">Careers</a>
      </nav>
      <div class="header-actions">
        <span class="header-brand">Proposal for {company}</span>
        <a href="https://upscale.ai/contact" class="header-cta" target="_blank" rel="noopener">Get Demo</a>
      </div>
    </div>
  </header>

  {hero}
  {exec_summary}
  {toc}
  <div id="s-spend-plan">{spend_charts}</div>
  <div id="s-campaign">{campaign_plan}</div>
  <div id="s-overview">{overview}</div>
  <div id="s-creative">{creative_system}</div>
  {creative_preview}
  {audio_demos}
  <div id="s-showcase">{creative_showcase}</div>
  {roi_projection}
  <div id="s-snapshot">{company_snapshot}</div>
  {ad_discovery_video}
  <div id="s-why-brand">{why_brand}</div>
  <div id="s-problem">{problem}</div>
  {objection_killer}
  <div id="s-audience">{audience_strategy}</div>
  <div id="s-integration">{integration}</div>
  <div id="s-platform">{platform}</div>
  <div id="s-ctv">{ctv_impact}</div>
  <div id="s-youtube">{youtube_impact}</div>
  <div id="s-optimization">{optimization}</div>
  <div id="s-attribution">{attribution}</div>
  <div id="s-competitive">{competitive}</div>
  <div id="s-results">{results}</div>
  <div id="s-inventory">{inventory}</div>
  <div id="s-next-steps">{next_steps}</div>

  <footer class="site-footer">
    <div class="footer-cta">
      <h3>Ready to unlock the power of AI advertising on Streaming TV?</h3>
      <p>See how Upscale.ai drives measurable performance for eCommerce brands.</p>
      <a href="https://upscale.ai/contact" class="cta-btn" target="_blank" rel="noopener">Get Demo &rarr;</a>
    </div>
    <div class="footer-bottom">
      <nav class="footer-nav">
        <a href="https://upscale.ai/how-it-works" target="_blank" rel="noopener">Platform</a>
        <a href="https://upscale.ai/solutions" target="_blank" rel="noopener">Solutions</a>
        <a href="https://upscale.ai/about" target="_blank" rel="noopener">About</a>
        <a href="https://upscale.ai/careers" target="_blank" rel="noopener">Careers</a>
        <a href="https://upscale.ai/contact" target="_blank" rel="noopener">Get Demo</a>
      </nav>
      <div class="footer-social">
        <a href="https://www.instagram.com/upscaleaihq" target="_blank" rel="noopener" title="Instagram"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg></a>
        <a href="https://www.linkedin.com/company/upscaleaihq/" target="_blank" rel="noopener" title="LinkedIn"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg></a>
        <a href="https://x.com/upscaleaiHQ" target="_blank" rel="noopener" title="X"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg></a>
        <a href="https://www.facebook.com/upscaleaihq" target="_blank" rel="noopener" title="Facebook"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg></a>
        <a href="https://www.youtube.com/@TVAdsAI" target="_blank" rel="noopener" title="YouTube"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg></a>
        <a href="https://vimeo.com/upscaleai" target="_blank" rel="noopener" title="Vimeo"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M23.977 6.416c-.105 2.338-1.739 5.543-4.894 9.609-3.268 4.247-6.026 6.37-8.29 6.37-1.409 0-2.578-1.294-3.553-3.881L5.322 11.4C4.603 8.816 3.834 7.522 3.01 7.522c-.179 0-.806.378-1.881 1.132L0 7.197c1.185-1.044 2.351-2.084 3.501-3.128C5.08 2.701 6.266 1.984 7.055 1.91c1.867-.18 3.016 1.1 3.447 3.838.465 2.953.789 4.789.971 5.507.539 2.45 1.131 3.674 1.776 3.674.502 0 1.256-.796 2.265-2.385 1.004-1.589 1.54-2.797 1.612-3.628.144-1.371-.395-2.061-1.614-2.061-.574 0-1.167.121-1.777.391 1.186-3.868 3.434-5.757 6.762-5.637 2.473.06 3.628 1.664 3.493 4.797l-.013.01z"/></svg></a>
      </div>
      <div class="footer-wordmark">
        <svg width="136" height="35" viewBox="0 0 136 35" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M10.7512 9.8282H14.7971V12.5491L14.2694 13.4635L12.7793 16.0451H14.7971V25.5127H10.7512V23.7557C9.76786 25.22 8.2103 25.952 6.07706 25.952C4.36255 25.952 2.94576 25.3771 1.82679 24.2264C0.707924 23.0762 0.148438 21.4869 0.148438 19.4588V9.8282H4.19487V18.9564C4.19487 20.0027 4.47724 20.8022 5.04188 21.3564C5.60652 21.9107 6.35943 22.1878 7.30032 22.1878C8.34591 22.1878 9.18251 21.8632 9.81022 21.2149C10.4371 20.5666 10.7512 19.5944 10.7512 18.2977V9.8282ZM88.2742 2.61377L84.2277 4.95011V25.5127H88.2742V2.61377ZM94.4343 19.3327C94.978 21.2986 96.4518 22.2819 98.857 22.2819C100.404 22.2819 101.576 21.7588 102.37 20.7132L105.633 22.5954C104.085 24.8331 101.805 25.952 98.7941 25.952C96.2015 25.952 94.1207 25.1674 92.5521 23.5995C90.9835 22.0308 90.1995 20.0546 90.1995 17.6709C90.1995 15.3077 90.9732 13.3366 92.5208 11.7577C94.068 10.1787 96.0548 9.3894 98.4807 9.3894C100.781 9.3894 102.678 10.1839 104.174 11.7732C105.669 13.3628 106.417 15.3286 106.417 17.6709C106.417 18.1931 106.365 18.7474 106.26 19.3327H94.4343ZM94.3713 16.1963H102.37C102.14 15.13 101.665 14.335 100.943 13.8124C100.221 13.2894 99.401 13.0277 98.4807 13.0277C97.393 13.0277 96.4942 13.3049 95.7828 13.8592C95.0723 14.4135 94.6016 15.1922 94.3713 16.1963ZM78.2562 9.8282H82.3027V25.5127H78.2562V23.6617C77.0433 25.1888 75.3388 25.952 73.1433 25.952C71.0524 25.952 69.259 25.1518 67.7638 23.552C66.2685 21.9521 65.5208 19.9916 65.5208 17.6709C65.5208 15.3492 66.2685 13.3885 67.7638 11.7887C69.259 10.1891 71.0524 9.3894 73.1433 9.3894C75.3388 9.3894 77.0433 10.1526 78.2562 11.6792V9.8282ZM70.7907 20.8548C71.6064 21.6803 72.6417 22.0937 73.8963 22.0937C75.1507 22.0937 76.1909 21.6803 77.0172 20.8548C77.8434 20.0285 78.2562 18.9675 78.2562 17.6709C78.2562 16.3739 77.8434 15.3129 77.0172 14.4868C76.1909 13.6606 75.1507 13.2478 73.8963 13.2478C72.6417 13.2478 71.6064 13.6606 70.7907 14.4868C69.9748 15.3129 69.5675 16.3739 69.5675 17.6709C69.5675 18.9675 69.9748 20.0285 70.7907 20.8548ZM57.4253 25.952C55.0622 25.952 53.0913 25.1569 51.5121 23.5674C49.9332 21.9781 49.144 20.0131 49.144 17.6709C49.144 15.3286 49.9332 13.3628 51.5121 11.7732C53.0913 10.1839 55.0622 9.3894 57.4253 9.3894C58.9518 9.3894 60.3425 9.75566 61.597 10.4869C62.8523 11.2189 63.8037 12.2022 64.4515 13.436L60.9701 15.4746C60.6561 14.8268 60.1803 14.3141 59.5422 13.9377C58.9051 13.5614 58.1885 13.3731 57.3941 13.3731C56.1811 13.3731 55.1771 13.7755 54.3828 14.5809C53.5878 15.3854 53.1906 16.4155 53.1906 17.6709C53.1906 18.9044 53.5878 19.9242 54.3828 20.7288C55.1771 21.5344 56.1811 21.9366 57.3941 21.9366C58.2092 21.9366 58.9361 21.7537 59.574 21.3874C60.2115 21.0215 60.6878 20.5147 61.0014 19.8663L64.5142 21.8735C63.8246 23.1074 62.8523 24.0959 61.597 24.8382C60.3425 25.5808 58.9518 25.952 57.4253 25.952ZM39.503 14.2831C39.503 14.7009 39.7802 15.0409 40.3344 15.3026C40.8888 15.5634 41.5629 15.7938 42.3579 15.9924C43.1524 16.1911 43.9467 16.4421 44.7418 16.7453C45.5362 17.0483 46.2104 17.5559 46.7647 18.2664C47.3189 18.9778 47.5962 19.8663 47.5962 20.9325C47.5962 22.5428 46.995 23.7823 45.7925 24.6502C44.5898 25.5178 43.0894 25.952 41.2909 25.952C38.0707 25.952 35.8753 24.7073 34.7036 22.2189L38.2175 20.2427C38.6775 21.6018 39.7017 22.2819 41.2909 22.2819C42.7345 22.2819 43.4554 21.8322 43.4554 20.9325C43.4554 20.5147 43.1783 20.1745 42.624 19.9139C42.0705 19.6522 41.3955 19.4166 40.6012 19.2077C39.8059 18.9987 39.0117 18.7371 38.2175 18.4235C37.4224 18.1095 36.748 17.6129 36.1937 16.9334C35.6395 16.2541 35.3622 15.4019 35.3622 14.377C35.3622 12.829 35.932 11.6109 37.0719 10.7224C38.2123 9.8342 39.629 9.3894 41.3229 9.3894C42.5981 9.3894 43.7584 9.67682 44.8047 10.2521C45.8503 10.827 46.6759 11.6479 47.2826 12.7145L43.8318 14.5963C43.3301 13.5301 42.4935 12.9967 41.3229 12.9967C40.7996 12.9967 40.3654 13.1114 40.0208 13.3419C39.6758 13.5717 39.503 13.8858 39.503 14.2831ZM25.8503 9.3894C27.9621 9.3894 29.7658 10.1891 31.261 11.7887C32.7564 13.3885 33.5041 15.3492 33.5041 17.6709C33.5041 19.9916 32.7564 21.9521 31.261 23.552C29.7658 25.1518 27.9621 25.952 25.8503 25.952C23.6541 25.952 21.9601 25.1888 20.7686 23.6617V31.7867H16.7222V16.0451H18.7397L17.2496 13.4635L16.7222 12.5491V9.8282H20.7686V11.6792C21.9601 10.1526 23.6541 9.3894 25.8503 9.3894ZM21.9919 20.8548C22.807 21.6803 23.8423 22.0937 25.0973 22.0937C26.3519 22.0937 27.3924 21.6803 28.2187 20.8548C29.0439 20.0285 29.4574 18.9675 29.4574 17.6709C29.4574 16.3739 29.0439 15.3129 28.2187 14.4868C27.3924 13.6606 26.3519 13.2478 25.0973 13.2478C23.8423 13.2478 22.807 13.6606 21.9919 14.4868C21.1762 15.3129 20.7686 16.3739 20.7686 17.6709C20.7686 18.9675 21.1762 20.0285 21.9919 20.8548Z" fill="#2B2731"/>
          <path d="M111.441 24.1096C110.98 24.5707 110.427 24.8014 109.781 24.8014C109.136 24.8014 108.582 24.5707 108.121 24.1096C107.66 23.6485 107.43 23.0953 107.43 22.4496C107.43 21.8039 107.66 21.2506 108.121 20.7896C108.582 20.3285 109.136 20.0978 109.781 20.0978C110.427 20.0978 110.98 20.3285 111.441 20.7896C111.903 21.2506 112.133 21.8039 112.133 22.4496C112.133 23.0953 111.903 23.6485 111.441 24.1096ZM132.624 7.42658C131.978 7.42658 131.418 7.18931 130.944 6.71519C130.47 6.24096 130.233 5.68095 130.233 5.03516C130.233 4.38947 130.47 3.82452 130.944 3.3402C131.418 2.85598 131.978 2.61377 132.624 2.61377C133.29 2.61377 133.86 2.85598 134.334 3.3402C134.809 3.82452 135.046 4.38947 135.046 5.03516C135.046 5.68095 134.809 6.24096 134.334 6.71519C133.86 7.18931 133.29 7.42658 132.624 7.42658ZM130.687 24.3775V9.24275H134.592V24.3775H130.687ZM125.294 9.24275H129.199V24.3775H125.294V22.5918C124.124 24.0648 122.479 24.8014 120.36 24.8014C118.342 24.8014 116.612 24.0296 115.169 22.4859C113.726 20.9419 113.005 19.0501 113.005 16.8101C113.005 14.5702 113.726 12.6784 115.169 11.1347C116.612 9.59072 118.342 8.81888 120.36 8.81888C122.479 8.81888 124.124 9.5555 125.294 11.0285V9.24275ZM118.09 19.8824C118.877 20.6795 119.876 21.0781 121.087 21.0781C122.297 21.0781 123.301 20.6795 124.098 19.8824C124.896 19.0855 125.294 18.0613 125.294 16.8101C125.294 15.559 124.896 14.5348 124.098 13.7379C123.301 12.9408 122.297 12.5422 121.087 12.5422C119.876 12.5422 118.877 12.9408 118.09 13.7379C117.303 14.5348 116.909 15.559 116.909 16.8101C116.909 18.0613 117.303 19.0855 118.09 19.8824Z" fill="url(#paint0_linear_pfooter)"/>
          <defs><linearGradient id="paint0_linear_pfooter" x1="108.121" y1="24.1096" x2="135.174" y2="2.43389" gradientUnits="userSpaceOnUse"><stop stop-color="#B72BB3"/><stop offset="1" stop-color="#60B1E3"/></linearGradient></defs>
        </svg>
      </div>
      <div class="footer-legal">
        <a href="https://upscale.ai/privacy" target="_blank" rel="noopener">Privacy</a>
        <a href="https://upscale.ai/terms" target="_blank" rel="noopener">Terms of Use</a>
      </div>
      <p class="footer-meta">Prepared {generated} &middot; Custom streaming proposal for {company} &middot; Confidential</p>
    </div>
  </footer>
</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _build_exec_summary(
    company: str, report: DomainAdReport, budget: dict,
    intel: BrandIntelligence | None, has_shopify: bool, has_klaviyo: bool,
    strategy: dict | None = None,
) -> str:
    """Build an executive summary section at the top of the proposal."""
    e = report.enrichment
    mix = report.channel_mix

    # Revenue context
    rev_line = ""
    if e and e.estimated_annual_revenue:
        rev_line = f" With an estimated {_fmt_money(e.estimated_annual_revenue)}/yr in DTC revenue,"

    # Channel gap — customize based on strategy
    channel_gap = ""
    if strategy and strategy["tier"] == "youtube_only":
        channel_gap = " — YouTube is the highest-ROI streaming channel at this spend level"
    elif not mix.has_linear:
        channel_gap = " — yet you're not on streaming TV, where 47% of all viewing now happens"
    elif mix.has_meta and mix.has_youtube:
        channel_gap = " across Meta and YouTube"

    # Integration advantage
    integration_note = ""
    if has_shopify and has_klaviyo:
        integration_note = " Your Shopify + Klaviyo stack connects natively for first-party attribution and audience sync."
    elif has_shopify:
        integration_note = " Your Shopify store connects directly for purchase-level attribution."

    # Spend context
    spend_note = ""
    if intel and intel.spend_estimate:
        s = intel.spend_estimate
        if strategy and strategy["tier"] == "youtube_only":
            spend_note = f" We estimate ~{_fmt_money(s.estimated_monthly_ad_spend)}/mo in total ad spend."
        else:
            spend_note = f" We estimate ~{_fmt_money(s.estimated_monthly_ad_spend)}/mo in total ad spend — a CTV test at {_fmt_money(s.recommended_ctv_test)}/mo would be {s.recommended_ctv_pct}% of that."

    # Build KPI strip
    total_3mo = budget["m1"] + budget["m2"] + budget["m3"]
    ctv_3mo = int(total_3mo * 0.6)
    yt_3mo = int(total_3mo * 0.4)
    kpis = []
    kpis.append((_fmt_money(budget["m1"]), "Month 1 Launch Spend"))
    kpis.append((_fmt_money(total_3mo), "Proposed Spend — 3-Month Total"))
    kpis.append((_fmt_money(ctv_3mo), "CTV Spend"))
    kpis.append((_fmt_money(yt_3mo), "YouTube Spend"))

    kpi_html = "".join(
        f'<div class="exec-kpi"><div class="val">{v}</div><div class="lbl">{l}</div></div>'
        for v, l in kpis
    )

    return f"""<div class="exec-summary">
  <h2 style="font-size:1.3rem;margin-bottom:8px">Executive Summary</h2>
  <p style="font-size:.95rem;color:#475467;line-height:1.7;max-width:800px">
    {company} is a strong fit for Upscale's streaming TV + YouTube platform.{rev_line} you're actively advertising{channel_gap}.{integration_note}{spend_note}
    This proposal outlines a {_fmt_money(budget['m1'])}/mo launch plan with $0 monthly management fee, AI-generated creative included, and built-in attribution — live in 14 days.
  </p>
  <div class="exec-kpi-strip">{kpi_html}</div>
</div>"""


def _build_toc(company: str, report: DomainAdReport, intel: BrandIntelligence | None, strategy: dict | None = None) -> str:
    """Build a clickable table of contents."""
    milled = report.milled_intel
    tier = strategy["tier"] if strategy else "full_funnel"

    sections = [
        ("s-snapshot", "Company Profile"),
        ("s-why-brand", f"Why {company}"),
        ("s-problem", "The Problem"),
        ("s-myths", "Myth vs. Reality"),
        ("s-overview", "Campaign Overview"),
        ("s-audience", "Audience Strategy"),
        ("s-creative", "Creative System"),
        ("s-spend-plan", "Spend Plan"),
        ("s-roi", "ROI Projection"),
        ("s-campaign", "3-Month Plan"),
    ]

    # Only include CTV section if not YouTube-only
    if tier != "youtube_only":
        sections.append(("s-ctv", "CTV Impact"))

    sections.extend([
        ("s-youtube", "YouTube Opportunity"),
        ("s-optimization", "Real-Time Optimization"),
        ("s-attribution", "Attribution System"),
    ])

    if intel and intel.competitors:
        sections.append(("s-competitive", "Competitive Landscape"))

    sections.extend([
        ("s-results", "Proven Results"),
        ("s-inventory", "Streaming Inventory"),
        ("s-next-steps", "Next Steps"),
    ])

    items = "".join(
        f'<a href="#{anchor}" class="toc-item"><span class="toc-num">{i+1:02d}</span> {label}</a>'
        for i, (anchor, label) in enumerate(sections)
    )

    return f"""<div class="section" style="padding:32px 40px">
  <h2 style="font-size:1.1rem;margin-bottom:4px">What's Inside</h2>
  <p class="section-sub" style="margin-bottom:0">Jump to any section of this proposal.</p>
  <div class="toc-grid">{items}</div>
</div>"""


def _build_optimization_engine(company: str) -> str:
    """Build the Real-Time Optimization section from Upscale's optimization guide."""
    loops = [
        ("&#x1f4b0;", "Budget & Bids",
         "Adjusts budgets and CPM bids at the line item level daily to correct pacing and reward top-performing segments."),
        ("&#x23f0;", "Dayparting",
         "Weights spend by hour and day of week based on live performance — spending more during peak response windows, less during low-engagement periods."),
        ("&#x1f3ac;", "Creative Weighting",
         "After a learning window, shifts spend toward winning creatives and tapers underperformers by KPI. 70% of campaign performance is driven by creative."),
        ("&#x1f4f1;", "Supply / App Bundles",
         "Analyzes performance by streaming app and reallocates budget — scaling top-performing apps, throttling weak ones. Direct publisher integrations reduce intermediary fees."),
        ("&#x1f3af;", "Campaign Type",
         "Optimizes differently across acquisition, retargeting, and remarketing based on distinct performance profiles."),
        ("&#x1f4cd;", "Geo / Zip Targeting",
         "Reallocates spend across zip codes — leaning into high-converting geos, pulling back from weak ones. CTV geo-targeting goes down to zip code level vs. DMA-only on linear."),
    ]

    loop_cards = "".join(
        f"""<div class="card" style="text-align:center">
      <div style="font-size:1.6rem;margin-bottom:8px">{icon}</div>
      <h4 style="font-size:.9rem;margin-bottom:6px">{name}</h4>
      <p style="font-size:.8rem;color:#475467;margin:0">{desc}</p>
    </div>"""
        for icon, name, desc in loops
    )

    return f"""<div class="section alt">
  <h2>Real-Time Optimization Engine</h2>
  <p class="section-sub">Upscale's Agentic Ad Ops system optimizes {company}'s campaigns autonomously — adjusting creatives, supply, dayparts, geo targeting, and bids multiple times per day.</p>

  <div class="grid-3">{loop_cards}</div>

  <details class="collapsible" style="margin-top:20px">
    <summary>How the AI/ML Engine Works</summary>
    <div class="collapse-content">
      <div class="grid-2">
        <div class="card">
          <h3 style="font-size:.95rem">Bid Optimization Model</h3>
          <p style="font-size:.85rem;color:#475467">Ingests bid, impression, and conversion data alongside creative attributes and competitive landscape signals. Outputs optimized bid prices and click/conversion predictions for every auction — operating thousands of times per second.</p>
        </div>
        <div class="card">
          <h3 style="font-size:.95rem">Creative Optimization Model</h3>
          <p style="font-size:.85rem;color:#475467">Uses LLMs and genetic optimization algorithms to analyze creative attributes against performance data. Selects the highest-performing creative variant for each impression — a closed-loop intelligence cycle where every campaign makes the next one smarter.</p>
        </div>
      </div>
      <div class="card" style="margin-top:12px;background:var(--teal-light);border-color:var(--teal)">
        <h3 style="color:var(--teal);font-size:.95rem">&#x1f504; Design Philosophy: Gradual Decay, Not Hard Cutoffs</h3>
        <p style="font-size:.85rem;color:#475467">Underperforming creatives, apps, geos, and line items get reduced spend over time — with room to recover — before a decisive shutoff once data is clear. <strong>Patience</strong> for new variables, <strong>urgency</strong> when data is clear, and a <strong>compounding advantage</strong> that widens with every campaign cycle.</p>
      </div>
    </div>
  </details>
</div>"""


def _build_attribution_system(company: str, has_shopify: bool) -> str:
    """Build the Attribution System section from Upscale's attribution guide."""
    shopify_note = ""
    if has_shopify:
        shopify_note = " With Shopify connected, this includes order-level and SKU-level attribution."

    layers = [
        ("01", "IP-Based Attribution", "DETERMINISTIC", "var(--teal)",
         f"Impression-level data matched via IP address with strict recency windows — connecting the TV screen to the checkout. Deterministic match within a household network, no modeling required.{shopify_note}"),
        ("02", "Household Graph", "PROBABILISTIC + DETERMINISTIC", "var(--pink)",
         "Cross-device resolution via Beeswax and Comcast Household Graph + LiveRamp Identity Network. Devices — CTV, mobile, desktop — are mapped to a shared household ID, capturing the real path from TV exposure to purchase."),
        ("03", "Google Identity (CM360)", "DETERMINISTIC", "var(--navy)",
         "Logged-in Google identity matching via Campaign Manager 360. When users are signed into Google services, impressions are tied to authenticated accounts — the highest-confidence signal available. Cross-platform: YouTube, Android TV, web."),
        ("04", "Incrementality Testing", "CAUSAL", "var(--success)",
         "Randomized 20% holdout control group receives no ads. The difference in conversion rates is the true incremental lift. Always-on and free to run — no separate budget required. Eliminates bias from retargeting and organic demand."),
    ]

    layer_cards = "".join(
        f"""<div class="card" style="border-left:4px solid {color}">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
        <span style="font-size:1.4rem;font-weight:800;color:{color}">{num}</span>
        <div>
          <h3 style="font-size:1rem;margin-bottom:2px">{name}</h3>
          <span style="font-size:.6rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;padding:2px 8px;border-radius:4px;background:{color};color:white">{tag}</span>
        </div>
      </div>
      <p style="font-size:.85rem;color:#475467;margin:0">{desc}</p>
    </div>"""
        for num, name, tag, color, desc in layers
    )

    return f"""<div class="section">
  <h2>Four-Layer Attribution System</h2>
  <p class="section-sub">Upscale delivers high-fidelity CTV attribution by combining deterministic signals, probabilistic identity graphs, and controlled experimentation into a unified measurement system.</p>

  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0;margin-bottom:24px;border:1px solid var(--border);border-radius:12px;overflow:hidden">
    <div style="padding:16px;text-align:center;border-right:1px solid var(--border)">
      <div style="font-size:1.4rem;font-weight:800;color:var(--pink)">01</div>
      <div style="font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)">IP Matching</div>
      <div style="font-size:.75rem;color:var(--teal);font-weight:600;margin-top:2px">Deterministic Spine</div>
    </div>
    <div style="padding:16px;text-align:center;border-right:1px solid var(--border)">
      <div style="font-size:1.4rem;font-weight:800;color:var(--pink)">02</div>
      <div style="font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)">Household Graph</div>
      <div style="font-size:.75rem;color:var(--teal);font-weight:600;margin-top:2px">Cross-Device</div>
    </div>
    <div style="padding:16px;text-align:center;border-right:1px solid var(--border)">
      <div style="font-size:1.4rem;font-weight:800;color:var(--pink)">03</div>
      <div style="font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)">Google Identity</div>
      <div style="font-size:.75rem;color:var(--teal);font-weight:600;margin-top:2px">Login-Based</div>
    </div>
    <div style="padding:16px;text-align:center">
      <div style="font-size:1.4rem;font-weight:800;color:var(--pink)">04</div>
      <div style="font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)">Incrementality</div>
      <div style="font-size:.75rem;color:var(--teal);font-weight:600;margin-top:2px">Causal Truth</div>
    </div>
  </div>

  <div class="grid-2">{layer_cards}</div>

  <details class="collapsible" style="margin-top:20px">
    <summary>Why Multi-Layer Attribution Matters</summary>
    <div class="collapse-content">
      <div class="grid-2">
        <div class="card">
          <h4 style="font-size:.85rem;color:var(--pink)">Single-Method Blind Spots</h4>
          <ul style="list-style:none;padding:0;font-size:.82rem;color:#475467">
            <li style="padding:4px 0">&#x26a0; IP-only misses cross-device behavior</li>
            <li style="padding:4px 0">&#x26a0; Graph-only lacks deterministic grounding</li>
            <li style="padding:4px 0">&#x26a0; Platform-only sees limited scope</li>
            <li style="padding:4px 0">&#x26a0; No incrementality overstates performance</li>
          </ul>
        </div>
        <div class="card" style="background:var(--success-light);border-color:var(--success)">
          <h4 style="font-size:.85rem;color:var(--success)">Upscale's Solution</h4>
          <ul style="list-style:none;padding:0;font-size:.82rem;color:#475467">
            <li style="padding:4px 0">&#x2713; Household Graph resolves cross-device</li>
            <li style="padding:4px 0">&#x2713; IP + CM360 validate with hard signals</li>
            <li style="padding:4px 0">&#x2713; Multiple identity systems span platforms</li>
            <li style="padding:4px 0">&#x2713; Always-on holdouts prove true lift</li>
          </ul>
        </div>
      </div>
      <p style="font-size:.85rem;color:#475467;margin-top:12px;text-align:center"><strong>The closed loop:</strong> Impressions &rarr; Visits &rarr; Revenue &rarr; True Lift &mdash; every step measured and validated.</p>
    </div>
  </details>
</div>"""


def _build_company_snapshot(company: str, report: DomainAdReport, intel: BrandIntelligence | None) -> str:
    """Build a Company Snapshot section with Crunchbase/Clay data — HQ, founders, investors, funding."""
    if not intel:
        return ""

    # Only show if we have meaningful data
    has_funding = intel.total_funding or intel.recent_funding_round
    has_investors = bool(intel.investors)
    has_founders = bool(intel.founders)
    has_hq = bool(intel.headquarters)
    has_audience = bool(intel.target_audience)

    if not any([has_funding, has_investors, has_founders, has_hq, has_audience]):
        return ""

    e = report.enrichment

    # Build detail items
    details = []

    if has_hq:
        details.append(("&#x1f4cd;", "Headquarters", _esc(intel.headquarters)))

    if has_founders:
        details.append(("&#x1f464;", "Founded By", _esc(", ".join(intel.founders[:4]))))

    if e and e.employee_count:
        growth_note = ""
        details.append(("&#x1f465;", "Team Size", f"{_fmt_number(e.employee_count)} employees{growth_note}"))

    if e and e.estimated_annual_revenue:
        details.append(("&#x1f4b5;", "Est. Revenue", f"{_fmt_money(e.estimated_annual_revenue)}/yr"))

    # Note: Funding, investors, and latest round are shown in the internal report only.

    if has_audience:
        details.append(("&#x1f3af;", "Target Audience", _esc(intel.target_audience)))

    if intel.target_demographics:
        details.append(("&#x1f4ca;", "Demographics", _esc(intel.target_demographics[:200])))

    # Ecommerce details
    if e and e.ecommerce_platform:
        plan = f" ({e.ecommerce_plan})" if e.ecommerce_plan else ""
        details.append(("&#x1f6d2;", "Platform", f"{_esc(e.ecommerce_platform)}{plan}"))

    if e and e.product_count:
        price_note = f" &middot; Avg {_esc(e.avg_product_price)}" if e.avg_product_price else ""
        range_note = f" &middot; Range: {_esc(e.price_range)}" if e.price_range else ""
        details.append(("&#x1f4e6;", "Products", f"{_fmt_number(e.product_count)} products{price_note}{range_note}"))

    if e and e.estimated_monthly_visits:
        details.append(("&#x1f310;", "Monthly Traffic", f"{_fmt_number(e.estimated_monthly_visits)} visits/mo"))

    if e and e.review_count:
        rating = f" &middot; {e.review_rating} stars" if e.review_rating else ""
        source = f" on {_esc(e.review_source)}" if e.review_source else ""
        details.append(("&#x2b50;", "Reviews", f"{_fmt_number(e.review_count)} reviews{rating}{source}"))

    if not details:
        return ""

    items_html = ""
    for icon, label, value in details:
        items_html += f"""<div style="display:flex;gap:12px;align-items:flex-start;padding:14px 0;border-bottom:1px solid var(--border)">
      <span style="font-size:1.2rem;flex-shrink:0;width:28px;text-align:center">{icon}</span>
      <div>
        <div style="font-size:.75rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-bottom:2px">{label}</div>
        <div style="font-size:.9rem;color:var(--navy);line-height:1.5">{value}</div>
      </div>
    </div>"""

    # Growth signal callout if funded
    growth_callout = ""
    if has_funding or has_investors:
        growth_callout = f"""<div style="margin-top:20px;padding:16px 20px;background:var(--teal-light);border-radius:10px;border-left:4px solid var(--teal)">
      <p style="font-size:.88rem;color:var(--teal);line-height:1.6;margin:0">
        <strong>Growth Signal:</strong> Backed by institutional investors, {company} is positioned for scale.
        Streaming TV + YouTube is the performance channel that converts brand awareness into measurable revenue — exactly what growth-stage brands need.
      </p>
    </div>"""

    # Tech stack collapsible
    tech_html = ""
    if e and e.technologies and len(e.technologies) > 3:
        tech_pills = "".join(
            f'<span style="display:inline-block;padding:4px 10px;margin:3px;font-size:.75rem;background:var(--bg);border:1px solid var(--border);border-radius:6px;color:var(--navy)">{_esc(t)}</span>'
            for t in e.technologies[:30]
        )
        tech_html = f"""<details class="collapsible" style="margin-top:16px">
      <summary>Tech Stack ({len(e.technologies)} technologies detected)</summary>
      <div class="collapse-content">
        <div style="padding:12px 0">{tech_pills}</div>
      </div>
    </details>"""

    # Social profiles collapsible
    social_html = ""
    if e and e.social_profiles:
        social_rows = ""
        for sp in e.social_profiles:
            followers = _fmt_number(sp.followers) if sp.followers else "—"
            social_rows += f"""<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #f0f0f0;font-size:.82rem">
          <span style="font-weight:600">{_esc(sp.platform)}</span>
          <span style="color:var(--muted)">{followers} followers</span>
        </div>"""
        social_html = f"""<details class="collapsible">
      <summary>Social Profiles ({len(e.social_profiles)} platforms)</summary>
      <div class="collapse-content">
        <div style="max-width:400px">{social_rows}</div>
      </div>
    </details>"""

    return f"""<div class="section alt">
  <h2>{company} at a Glance</h2>
  <p class="section-sub">Company intelligence from public sources and enrichment data.</p>
  <div style="max-width:680px">
    {items_html}
  </div>
  {growth_callout}
  {tech_html}
  {social_html}
</div>"""


def _build_hero(company, domain, industry, description, logo_html, budget, strategy: dict | None = None) -> str:
    # Customize headline based on strategy tier
    if strategy and strategy["tier"] == "youtube_only":
        headline = f'Upscale Can Help <span class="highlight">{company}</span> Scale Performance Across YouTube'
        eyebrow = "AI Creative + Media + Measurement — One Platform"
    elif strategy and strategy["tier"] == "ctv_led":
        headline = f'Upscale Can Help <span class="highlight">{company}</span> Scale Performance Across Streaming TV'
        eyebrow = "AI Creative + Media + Measurement — One Platform"
    else:
        headline = f'Upscale Can Help <span class="highlight">{company}</span> Scale Performance Across Streaming (CTV) & YouTube'
        eyebrow = "AI Creative + Media + Measurement — One Platform"

    # Strategy-specific stat
    streaming_stat = '<div class="hero-stat"><div class="num">&#x1f4fa;</div><div class="lbl">Streaming is the Future of TV</div></div>'
    if strategy and strategy["tier"] == "youtube_only":
        streaming_stat = '<div class="hero-stat"><div class="num">2.7B</div><div class="lbl">YouTube MAU</div></div>'

    return f"""<div class="hero">
  <span class="hero-eyebrow">{eyebrow}</span>
  {logo_html}
  <h1>{headline}</h1>
  <div class="hero-stats">
    <div class="hero-stat"><div class="num">{_fmt_money(budget['m1'])}</div><div class="lbl">Launch Budget</div></div>
    <div class="hero-stat"><div class="num">14 days</div><div class="lbl">To Launch</div></div>
    {streaming_stat}
  </div>
</div>"""


def _build_problem(company, report: DomainAdReport, budget: dict) -> str:
    mix = report.channel_mix
    m1 = budget["m1"]

    # Agency breakdown — they take 60% off the top
    agency_mgmt = int(m1 * 0.10)
    agency_creative = int(m1 * 0.50)
    agency_media = m1 - agency_mgmt - agency_creative
    agency_pct = round(agency_media / m1 * 100)

    # Personalize pain points
    pain_points = []
    if not mix.has_linear:
        pain_points.append("You're missing the biggest screen in the house — 47% of TV is streaming")
    if mix.has_meta and not mix.has_linear:
        pain_points.append("Social ads alone can't reach cord-cutters on their TVs")
    if mix.total_ads_found > 30:
        pain_points.append("High creative volume needs a system, not one-off production rounds")
    if not pain_points:
        pain_points.append("Generic CTV/YouTube vendors aren't built for eCommerce results")
    pain_points.append("Agencies charge fees and mark up creative — less budget goes to actual media")

    pain_html = "".join(
        f'<li style="padding:6px 0;font-size:.92rem;color:rgba(255,255,255,.75)">{p}</li>'
        for p in pain_points
    )

    return f"""<div class="section dark">
  <h2>The Problem</h2>
  <p class="section-sub">Traditional agencies and vendors weren't built for YouTube and streaming TV performance. They charge too much and deliver too little.</p>
  <div class="grid-2">
    <div>
      <h3 style="font-size:.82rem;color:rgba(255,255,255,.45);text-transform:uppercase;letter-spacing:.1em;margin-bottom:16px">Where {_fmt_money(m1)}/mo goes with a typical agency</h3>
      <div style="margin-bottom:10px">
        <div style="display:flex;justify-content:space-between;font-size:.85rem;color:rgba(255,255,255,.7);margin-bottom:4px"><span>Management fee (10%)</span><span style="color:var(--pink-glow)">{_fmt_money(agency_mgmt)}</span></div>
        <div style="height:8px;background:rgba(255,255,255,.08);border-radius:4px;overflow:hidden"><div style="width:10%;height:100%;background:var(--pink-glow);border-radius:4px"></div></div>
      </div>
      <div style="margin-bottom:10px">
        <div style="display:flex;justify-content:space-between;font-size:.85rem;color:rgba(255,255,255,.7);margin-bottom:4px"><span>Creative production</span><span style="color:var(--pink-glow)">{_fmt_money(agency_creative)}+</span></div>
        <div style="height:8px;background:rgba(255,255,255,.08);border-radius:4px;overflow:hidden"><div style="width:50%;height:100%;background:var(--pink-glow);border-radius:4px"></div></div>
      </div>
      <div style="margin-bottom:16px">
        <div style="display:flex;justify-content:space-between;font-size:.85rem;color:rgba(255,255,255,.7);margin-bottom:4px"><span>Actual media spend</span><span style="color:#4ADE80">{_fmt_money(agency_media)}</span></div>
        <div style="height:8px;background:rgba(255,255,255,.08);border-radius:4px;overflow:hidden"><div style="width:{agency_pct}%;height:100%;background:#4ADE80;border-radius:4px"></div></div>
      </div>
      <p style="font-size:1.1rem;font-weight:700;color:var(--pink-glow)">Only {agency_pct}% of your budget actually runs as ads.</p>
      <div style="margin-top:20px;padding:16px;background:rgba(74,222,128,.08);border:1px solid rgba(74,222,128,.2);border-radius:10px">
        <p style="font-size:.92rem;color:rgba(255,255,255,.85)">With <strong style="color:#4ADE80">Upscale</strong>: $0 monthly management fee. Creative included. <strong style="color:#4ADE80">100% of your budget goes to media.</strong></p>
      </div>
    </div>
    <div>
      <h3 style="font-size:.82rem;color:rgba(255,255,255,.45);text-transform:uppercase;letter-spacing:.1em;margin-bottom:16px">Three structural problems</h3>
      <div style="margin-bottom:16px">
        <div style="display:flex;gap:12px;align-items:flex-start">
          <span style="background:var(--pink-glow);color:white;font-weight:800;font-size:.78rem;width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0">1</span>
          <div><h4 style="color:white;font-size:.95rem;margin-bottom:2px">Misaligned incentives</h4><p style="font-size:.82rem;color:rgba(255,255,255,.6)">They earn more when you spend more — regardless of performance.</p></div>
        </div>
      </div>
      <div style="margin-bottom:16px">
        <div style="display:flex;gap:12px;align-items:flex-start">
          <span style="background:var(--pink-glow);color:white;font-weight:800;font-size:.78rem;width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0">2</span>
          <div><h4 style="color:white;font-size:.95rem;margin-bottom:2px">Creative bottleneck</h4><p style="font-size:.82rem;color:rgba(255,255,255,.6)">2-4 creatives per quarter. $5K-$50K per round. Weeks of waiting.</p></div>
        </div>
      </div>
      <div style="margin-bottom:16px">
        <div style="display:flex;gap:12px;align-items:flex-start">
          <span style="background:var(--pink-glow);color:white;font-weight:800;font-size:.78rem;width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0">3</span>
          <div><h4 style="color:white;font-size:.95rem;margin-bottom:2px">Inflated measurement</h4><p style="font-size:.82rem;color:rgba(255,255,255,.6)">Platform-reported metrics overcount. No one proves incrementality.</p></div>
        </div>
      </div>
      <h3 style="font-size:.82rem;color:rgba(255,255,255,.45);text-transform:uppercase;letter-spacing:.1em;margin-bottom:10px;margin-top:24px">Why {company} needs this now</h3>
      <ul style="list-style:none;padding:0">{pain_html}</ul>
    </div>
  </div>
</div>"""


def _build_overview(company, budget, monthly_rev, intel: BrandIntelligence | None = None, strategy: dict | None = None) -> str:
    total = budget["m1"] + budget["m2"] + budget["m3"]
    rev_context = ""
    spend_context = ""

    if monthly_rev:
        pct = round(budget["m1"] / monthly_rev * 100, 1)
        rev_context = f" This represents approximately {pct}% of current monthly DTC revenue."

    # Strategy-specific channel description
    channel_desc = "CTV and YouTube"
    if strategy:
        if strategy["tier"] == "youtube_only":
            channel_desc = "YouTube"
        elif strategy["tier"] == "ctv_led":
            channel_desc = "CTV (40% RT / 60% ACQ) + YouTube"
        else:
            channel_desc = "CTV + YouTube (80% acquisition)"

    # Strategy badge
    strategy_badge = ""
    if strategy:
        badge_color = {"youtube_only": "var(--pink)", "ctv_led": "var(--teal)", "full_funnel": "var(--navy)"}
        badge_label = {"youtube_only": "YouTube-First", "ctv_led": "CTV-Led", "full_funnel": "Full Funnel"}
        c = badge_color.get(strategy["tier"], "var(--teal)")
        l = badge_label.get(strategy["tier"], "")
        strategy_badge = f'<span style="display:inline-block;padding:4px 12px;border-radius:6px;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;background:{c};color:white;margin-bottom:12px">{l} Strategy</span>'

    # Add spend estimate context if available
    if intel and intel.spend_estimate:
        s = intel.spend_estimate
        spend_context = f"""<div class="card" style="margin-top:20px;background:var(--teal-light);border-color:var(--teal)">
    <h3 style="color:var(--teal)">&#x1f4ca; Estimated Current Ad Spend</h3>
    <p style="font-size:.88rem;color:#475467">Based on {company}'s estimated revenue, we project ~<strong>{_fmt_money(s.estimated_monthly_ad_spend)}/mo</strong> in total advertising ({s.ad_spend_pct_of_revenue}% of revenue). That's roughly <strong>{_fmt_money(s.meta_spend)}/mo on Meta</strong>, {_fmt_money(s.google_search_spend)}/mo on Google, and {_fmt_money(s.youtube_spend)}/mo on YouTube. A recommended CTV test at {s.recommended_ctv_pct}% of ad spend = <strong>{_fmt_money(s.recommended_ctv_test)}/mo</strong>.</p>
  </div>"""

    return f"""<div class="section">
  <h2>Campaign Overview</h2>
  {strategy_badge}
  <p class="section-sub">A phased streaming strategy designed specifically for {company}'s growth trajectory.{rev_context}</p>
  <div class="grid-3">
    <div class="card">
      <div class="icon">&#x1f680;</div>
      <h3>Launch Investment</h3>
      <p>{_fmt_money(budget['m1'])}/month starting budget with ~{_fmt_money(budget['daily'])}/day across {channel_desc}. <strong>$0 monthly management fee</strong> — 100% of this goes to media.</p>
    </div>
    <div class="card">
      <div class="icon">&#x1f4ca;</div>
      <h3>KPIs We Track</h3>
      <p>CPVisit, CPA, ROAS, Brand Search Lift, and Incremental Revenue — measured through built-in attribution with Google's deterministic ID graph, not modeled estimates.</p>
    </div>
    <div class="card">
      <div class="icon">&#x1f3af;</div>
      <h3>3-Month Commitment</h3>
      <p>{_fmt_money(total)} total investment over 3 months with progressive scaling: {_fmt_money(budget['m1'])} &rarr; {_fmt_money(budget['m2'])} &rarr; {_fmt_money(budget['m3'])} as performance proves out. Creative included.</p>
    </div>
  </div>
  {spend_context}
</div>"""


def _build_integration(company, has_shopify, has_klaviyo) -> str:
    shopify_badge = '<span class="badge connected">&#x2713; Your Store Connected</span>' if has_shopify else '<span class="badge available">Available</span>'
    shopify_class = "integration-card active" if has_shopify else "integration-card"
    shopify_intro = f"{company}'s Shopify store connects directly to Upscale for real-time purchase data." if has_shopify else "Connect your Shopify store for deterministic purchase attribution and ML-powered targeting."

    klaviyo_badge = '<span class="badge connected">&#x2713; Detected in Your Stack</span>' if has_klaviyo else '<span class="badge available">Available</span>'
    klaviyo_class = "integration-card active" if has_klaviyo else "integration-card"
    klaviyo_intro = f"We detected Klaviyo in {company}'s tech stack — this unlocks unified TV + email customer journeys." if has_klaviyo else "Add Klaviyo integration to unlock post-view email flows and suppress existing purchasers."

    return f"""<div class="section alt">
  <h2>Native eCommerce Integrations</h2>
  <p class="section-sub">Upscale is deeply integrated with Shopify and Klaviyo — no manual data connections, no CSV uploads, no guesswork.</p>
  <div class="grid-2">
    <div class="{shopify_class}">
      {shopify_badge}
      <h3>Shopify</h3>
      <p style="font-size:.88rem;color:#475467;margin-bottom:12px">{shopify_intro}</p>
      <ul class="check-list">
        <li>First-party purchase data feeds ML targeting</li>
        <li>Pixel-level deterministic attribution</li>
        <li>Real-time conversion tracking</li>
        <li>Product catalog sync for dynamic creative</li>
        <li>Audience suppression of existing purchasers</li>
      </ul>
    </div>
    <div class="{klaviyo_class}">
      {klaviyo_badge}
      <h3>Klaviyo</h3>
      <p style="font-size:.88rem;color:#475467;margin-bottom:12px">{klaviyo_intro}</p>
      <ul class="check-list">
        <li>Email + SMS journey data enriches targeting</li>
        <li>Suppression of existing purchasers</li>
        <li>Post-view email flows triggered by TV exposure</li>
        <li>Unified customer journey: TV + email + SMS</li>
        <li>Klaviyo audience sync for retargeting</li>
      </ul>
    </div>
  </div>
</div>"""


def _build_platform() -> str:
    return """<div class="section">
  <h2>End-to-End Platform</h2>
  <p class="section-sub">Three integrated systems that work together — not three separate vendors you have to manage.</p>
  <div class="grid-3">
    <div class="card">
      <div class="stat-big" style="font-size:1.4rem">Creative</div>
      <div class="stat-label">Included in CTV Campaign</div>
      <h3 style="margin-top:16px">Creative as a System</h3>
      <p>Always-on performance creative engine that generates 2-20+ variations per month. From brief to first ad in <strong>6 days</strong> — vs. 6-7 weeks with traditional production. $500 per creative vs. $10,000+ industry average.</p>
    </div>
    <div class="card">
      <div class="stat-big">1st</div>
      <div class="stat-label">Party Data ML</div>
      <h3 style="margin-top:16px">Purchase-Optimized Targeting</h3>
      <p>ML models trained on your Shopify first-party purchase data — not generic demographic reach. Optimizes toward actual views, sign-ups, and purchases across Streaming TV + YouTube simultaneously.</p>
    </div>
    <div class="card">
      <div class="stat-big">Built-in</div>
      <div class="stat-label">Not an add-on</div>
      <h3 style="margin-top:16px">Measurement & Incrementality</h3>
      <p>Attribution + incrementality testing is native to the platform. Path-to-purchase mapping with clear attribution windows: 3-day full credit, 4-day partial, 7-day max. No third-party measurement tool required.</p>
    </div>
  </div>
</div>"""


def _build_creative_system(company, report: DomainAdReport, budget: dict | None = None) -> str:
    # Determine total creatives based on monthly spend tier
    monthly_spend = budget.get("m3", 0) if budget else 0
    if monthly_spend >= 30_000:
        total_creatives = 24
        cadence = "3+"
    elif monthly_spend >= 15_000:
        total_creatives = 18
        cadence = "2-3"
    else:
        total_creatives = 12
        cadence = "2+"

    has_ads = report.channel_mix.total_ads_found > 0 if report.channel_mix else False
    ad_count = report.channel_mix.total_ads_found if report.channel_mix else 0

    repurpose = ""
    if has_ads:
        repurpose = f"""<div class="card" style="margin-top:20px;background:var(--teal-light);border-color:var(--teal)">
    <h3 style="color:var(--teal)">&#x267b; Repurpose {company}'s Existing Creative</h3>
    <p>We detected <strong>{ad_count} active ads</strong> across your channels. Our AI creative platform can adapt your best-performing social and digital video into CTV-optimized 15s and 30s formats — no new production required. This gets you on streaming TV <em>this week</em>.</p>
  </div>"""

    return f"""<div class="section alt">
  <h2>Creative That Scales</h2>
  <p class="section-sub">Agencies produce 2-4 creatives per quarter for $5K-$50K per round. Upscale runs a continuous creative flywheel — dozens of variations, tested continuously, included in your plan.</p>
  <div class="grid-4">
    <div style="text-align:center;padding:20px">
      <div class="stat-big" style="font-size:1.6rem">Included</div>
      <div class="stat-label">Creative Production</div>
      <p style="font-size:.78rem;color:var(--muted);margin-top:6px">vs. $10,000+ at agencies</p>
    </div>
    <div style="text-align:center;padding:20px">
      <div class="stat-big">6 days</div>
      <div class="stat-label">Brief to Launch</div>
      <p style="font-size:.78rem;color:var(--muted);margin-top:6px">vs. 6-7 weeks traditional</p>
    </div>
    <div style="text-align:center;padding:20px">
      <div class="stat-big">{total_creatives}</div>
      <div class="stat-label">Total Creatives</div>
      <p style="font-size:.78rem;color:var(--muted);margin-top:6px">Included in your plan</p>
    </div>
    <div style="text-align:center;padding:20px">
      <div class="stat-big">{cadence}</div>
      <div class="stat-label">New Creative</div>
      <p style="font-size:.78rem;color:var(--muted);margin-top:6px">every 2-3 weeks</p>
    </div>
  </div>

  <!-- Creative Flywheel — Circular -->
  <div style="margin-top:28px;background:white;border:1px solid var(--border);border-radius:20px;padding:28px">
    <div style="position:relative;width:540px;height:540px;margin:0 auto">
      <!-- Circular ring (SVG) — no dashed lines or icons -->
      <svg viewBox="0 0 540 540" style="position:absolute;top:0;left:0;width:100%;height:100%">
        <circle cx="270" cy="270" r="200" fill="none" stroke="#E8F4F7" stroke-width="32" />
      </svg>
      <!-- Step nodes positioned evenly around the circle -->
      <!-- 01 Research — top center -->
      <div style="position:absolute;top:4px;left:50%;transform:translateX(-50%);text-align:center;background:var(--teal-light);border-radius:12px;padding:10px 14px;min-width:108px;border:2px solid var(--teal)">
        <div style="font-size:1.1rem;font-weight:800;color:var(--teal)">01</div>
        <div style="font-size:.72rem;font-weight:600;color:var(--navy)">Research</div>
        <div style="font-size:.62rem;color:var(--muted)">Audience &amp; data</div>
      </div>
      <!-- 02 Concept — top-right -->
      <div style="position:absolute;top:72px;right:8px;text-align:center;background:var(--teal-light);border-radius:12px;padding:10px 14px;min-width:108px;border:1.5px solid var(--teal)">
        <div style="font-size:1.1rem;font-weight:800;color:var(--teal)">02</div>
        <div style="font-size:.72rem;font-weight:600;color:var(--navy)">Concept</div>
        <div style="font-size:.62rem;color:var(--muted)">Hooks &amp; scripts</div>
      </div>
      <!-- 03 Generate — right -->
      <div style="position:absolute;top:236px;right:-12px;text-align:center;background:var(--teal-light);border-radius:12px;padding:10px 14px;min-width:108px;border:1.5px solid var(--teal)">
        <div style="font-size:1.1rem;font-weight:800;color:var(--teal)">03</div>
        <div style="font-size:.72rem;font-weight:600;color:var(--navy)">Generate</div>
        <div style="font-size:.62rem;color:var(--muted)">16:9, 9:16, 6s</div>
      </div>
      <!-- 04 Evaluate — bottom-right -->
      <div style="position:absolute;bottom:72px;right:28px;text-align:center;background:var(--pink-light);border-radius:12px;padding:10px 14px;min-width:108px;border:2px solid var(--pink)">
        <div style="font-size:1.1rem;font-weight:800;color:var(--pink)">04</div>
        <div style="font-size:.72rem;font-weight:600;color:var(--navy)">Evaluate</div>
        <div style="font-size:.62rem;color:var(--muted)">Brand-safe review</div>
      </div>
      <!-- 05 Deploy — bottom center -->
      <div style="position:absolute;bottom:4px;left:50%;transform:translateX(-50%);text-align:center;background:var(--teal-light);border-radius:12px;padding:10px 14px;min-width:108px;border:1.5px solid var(--teal)">
        <div style="font-size:1.1rem;font-weight:800;color:var(--teal)">05</div>
        <div style="font-size:.72rem;font-weight:600;color:var(--navy)">Deploy</div>
        <div style="font-size:.62rem;color:var(--muted)">CTV + YouTube</div>
      </div>
      <!-- 06 Measure — bottom-left -->
      <div style="position:absolute;bottom:72px;left:28px;text-align:center;background:var(--teal-light);border-radius:12px;padding:10px 14px;min-width:108px;border:1.5px solid var(--teal)">
        <div style="font-size:1.1rem;font-weight:800;color:var(--teal)">06</div>
        <div style="font-size:.72rem;font-weight:600;color:var(--navy)">Measure</div>
        <div style="font-size:.62rem;color:var(--muted)">MTA + incrementality</div>
      </div>
      <!-- 07 Optimize — left -->
      <div style="position:absolute;top:236px;left:-12px;text-align:center;background:#ECFDF5;border-radius:12px;padding:10px 14px;min-width:108px;border:2px solid var(--success)">
        <div style="font-size:1.1rem;font-weight:800;color:var(--success)">07</div>
        <div style="font-size:.72rem;font-weight:600;color:var(--navy)">Optimize</div>
        <div style="font-size:.62rem;color:var(--muted)">Feed winners back</div>
      </div>
      <!-- Center label — title -->
      <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center">
        <div style="font-size:1rem;font-weight:800;color:var(--navy);line-height:1.3">The Creative</div>
        <div style="font-size:1rem;font-weight:800;color:var(--navy);line-height:1.3">Flywheel</div>
      </div>
    </div>
    <p style="text-align:center;font-size:.82rem;color:var(--muted);margin-top:20px">Performance data from Step 07 feeds directly back into Step 01. The flywheel gets smarter with every iteration.</p>
  </div>

  <!-- Always-On Creative Pipeline — Kanban Board -->
  <div style="margin-top:32px;background:white;border:1px solid var(--border);border-radius:20px;padding:28px;overflow:hidden">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px">
      <div>
        <h3 style="margin-bottom:4px">Always-On Creative Pipeline</h3>
        <p style="font-size:.85rem;color:var(--muted)">4+ new ads added to your account every 2 weeks. No briefs to write, no rounds of revision, no production delays.</p>
      </div>
      <div style="text-align:right;flex-shrink:0;padding-left:20px">
        <div style="font-size:2rem;font-weight:900;color:var(--pink)">24+</div>
        <div style="font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)">Creatives in 90 Days</div>
      </div>
    </div>

    <!-- Formats -->
    <div style="margin-bottom:20px">
      <div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:8px">Formats</div>
      <div style="display:flex;flex-wrap:wrap;gap:6px">
        <span style="padding:4px 12px;border-radius:6px;font-size:.75rem;font-weight:600;background:var(--teal-light);color:var(--teal);border:1px solid var(--teal)">16:9 CTV &amp; In-Stream</span>
        <span style="padding:4px 12px;border-radius:6px;font-size:.75rem;font-weight:600;background:var(--pink-light);color:var(--pink);border:1px solid var(--pink)">9:16 YouTube Shorts</span>
        <span style="padding:4px 12px;border-radius:6px;font-size:.75rem;font-weight:600;background:#E8EDF0;color:var(--navy);border:1px solid var(--navy)">6s Bumper Ads</span>
        <span style="padding:4px 12px;border-radius:6px;font-size:.75rem;font-weight:600;background:#FEF3C7;color:#92400E;border:1px solid #D97706">15s Non-Skip</span>
        <span style="padding:4px 12px;border-radius:6px;font-size:.75rem;font-weight:600;background:#ECFDF5;color:var(--success);border:1px solid var(--success)">30s Lean-Back TV</span>
      </div>
    </div>

    <!-- Creative Types -->
    <div style="margin-bottom:20px">
      <div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:8px">Creative Types</div>
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px">
        <div style="padding:12px;background:var(--teal-light);border-radius:10px;border-left:3px solid var(--teal)">
          <div style="font-size:.78rem;font-weight:700;color:var(--teal)">Performance</div>
          <div style="font-size:.68rem;color:var(--muted);margin-top:2px">Direct response, CTA-driven</div>
        </div>
        <div style="padding:12px;background:var(--pink-light);border-radius:10px;border-left:3px solid var(--pink)">
          <div style="font-size:.78rem;font-weight:700;color:var(--pink)">Testimonial / UGC</div>
          <div style="font-size:.68rem;color:var(--muted);margin-top:2px">Social proof &amp; reviews</div>
        </div>
        <div style="padding:12px;background:#E8EDF0;border-radius:10px;border-left:3px solid var(--navy)">
          <div style="font-size:.78rem;font-weight:700;color:var(--navy)">Branding (inc. Full Line)</div>
          <div style="font-size:.68rem;color:var(--muted);margin-top:2px">Brand awareness &amp; catalog</div>
        </div>
        <div style="padding:12px;background:#FEF3C7;border-radius:10px;border-left:3px solid #D97706">
          <div style="font-size:.78rem;font-weight:700;color:#92400E">Event Specific</div>
          <div style="font-size:.68rem;color:var(--muted);margin-top:2px">BFCM, launches, seasonal</div>
        </div>
      </div>
    </div>

    <!-- Kanban Board — 6 columns (bi-weekly sprints) -->
    <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:8px;overflow-x:auto">
      <!-- Sprint 1: Wk 1-2 -->
      <div style="background:#F8FAFB;border-radius:10px;padding:10px;min-width:120px">
        <div style="font-size:.65rem;font-weight:700;color:var(--teal);text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px;text-align:center">Wk 1-2 &middot; Launch</div>
        <div style="background:white;border:1px solid #E5E7EB;border-radius:6px;padding:8px;margin-bottom:6px;border-left:3px solid var(--teal)">
          <div style="font-size:.7rem;font-weight:600;color:var(--navy)">Perf. 30s CTV</div>
          <div style="font-size:.6rem;color:var(--muted)">16:9</div>
        </div>
        <div style="background:white;border:1px solid #E5E7EB;border-radius:6px;padding:8px;margin-bottom:6px;border-left:3px solid var(--teal)">
          <div style="font-size:.7rem;font-weight:600;color:var(--navy)">Perf. 15s Non-Skip</div>
          <div style="font-size:.6rem;color:var(--muted)">16:9</div>
        </div>
        <div style="background:white;border:1px solid #E5E7EB;border-radius:6px;padding:8px;margin-bottom:6px;border-left:3px solid var(--pink)">
          <div style="font-size:.7rem;font-weight:600;color:var(--navy)">UGC Short</div>
          <div style="font-size:.6rem;color:var(--muted)">9:16</div>
        </div>
        <div style="background:white;border:1px solid #E5E7EB;border-radius:6px;padding:8px;border-left:3px solid var(--teal)">
          <div style="font-size:.7rem;font-weight:600;color:var(--navy)">Bumper 6s</div>
          <div style="font-size:.6rem;color:var(--muted)">16:9</div>
        </div>
        <div style="text-align:center;margin-top:8px;font-size:1rem;font-weight:800;color:var(--teal)">4</div>
      </div>
      <!-- Sprint 2: Wk 3-4 -->
      <div style="background:#F8FAFB;border-radius:10px;padding:10px;min-width:120px">
        <div style="font-size:.65rem;font-weight:700;color:var(--teal);text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px;text-align:center">Wk 3-4</div>
        <div style="background:white;border:1px solid #E5E7EB;border-radius:6px;padding:8px;margin-bottom:6px;border-left:3px solid var(--navy)">
          <div style="font-size:.7rem;font-weight:600;color:var(--navy)">Brand 30s</div>
          <div style="font-size:.6rem;color:var(--muted)">Full line</div>
        </div>
        <div style="background:white;border:1px solid #E5E7EB;border-radius:6px;padding:8px;margin-bottom:6px;border-left:3px solid var(--teal)">
          <div style="font-size:.7rem;font-weight:600;color:var(--navy)">Perf. Variation A</div>
          <div style="font-size:.6rem;color:var(--muted)">New hook</div>
        </div>
        <div style="background:white;border:1px solid #E5E7EB;border-radius:6px;padding:8px;margin-bottom:6px;border-left:3px solid var(--pink)">
          <div style="font-size:.7rem;font-weight:600;color:var(--navy)">UGC Testimonial</div>
          <div style="font-size:.6rem;color:var(--muted)">9:16</div>
        </div>
        <div style="background:white;border:1px solid #E5E7EB;border-radius:6px;padding:8px;border-left:3px solid var(--teal)">
          <div style="font-size:.7rem;font-weight:600;color:var(--navy)">Bumper Var.</div>
          <div style="font-size:.6rem;color:var(--muted)">6s</div>
        </div>
        <div style="text-align:center;margin-top:8px;font-size:1rem;font-weight:800;color:var(--teal)">+4</div>
      </div>
      <!-- Sprint 3: Wk 5-6 -->
      <div style="background:#F8FAFB;border-radius:10px;padding:10px;min-width:120px">
        <div style="font-size:.65rem;font-weight:700;color:var(--pink);text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px;text-align:center">Wk 5-6</div>
        <div style="background:white;border:1px solid #E5E7EB;border-radius:6px;padding:8px;margin-bottom:6px;border-left:3px solid var(--teal)">
          <div style="font-size:.7rem;font-weight:600;color:var(--navy)">Top Hook Remix</div>
          <div style="font-size:.6rem;color:var(--muted)">30s + 15s</div>
        </div>
        <div style="background:white;border:1px solid #E5E7EB;border-radius:6px;padding:8px;margin-bottom:6px;border-left:3px solid var(--pink)">
          <div style="font-size:.7rem;font-weight:600;color:var(--navy)">UGC Short x2</div>
          <div style="font-size:.6rem;color:var(--muted)">9:16</div>
        </div>
        <div style="background:white;border:1px solid #E5E7EB;border-radius:6px;padding:8px;border-left:3px solid var(--navy)">
          <div style="font-size:.7rem;font-weight:600;color:var(--navy)">Brand Lean-Back</div>
          <div style="font-size:.6rem;color:var(--muted)">30s CTV</div>
        </div>
        <div style="text-align:center;margin-top:8px;font-size:1rem;font-weight:800;color:var(--pink)">+4</div>
      </div>
      <!-- Sprint 4: Wk 7-8 -->
      <div style="background:#F8FAFB;border-radius:10px;padding:10px;min-width:120px">
        <div style="font-size:.65rem;font-weight:700;color:var(--pink);text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px;text-align:center">Wk 7-8</div>
        <div style="background:white;border:1px solid #E5E7EB;border-radius:6px;padding:8px;margin-bottom:6px;border-left:3px solid #D97706">
          <div style="font-size:.7rem;font-weight:600;color:var(--navy)">Event: Seasonal</div>
          <div style="font-size:.6rem;color:var(--muted)">30s + 15s</div>
        </div>
        <div style="background:white;border:1px solid #E5E7EB;border-radius:6px;padding:8px;margin-bottom:6px;border-left:3px solid var(--teal)">
          <div style="font-size:.7rem;font-weight:600;color:var(--navy)">Perf. Winner Scale</div>
          <div style="font-size:.6rem;color:var(--muted)">Angle B</div>
        </div>
        <div style="background:white;border:1px solid #E5E7EB;border-radius:6px;padding:8px;border-left:3px solid var(--pink)">
          <div style="font-size:.7rem;font-weight:600;color:var(--navy)">UGC Product</div>
          <div style="font-size:.6rem;color:var(--muted)">9:16</div>
        </div>
        <div style="text-align:center;margin-top:8px;font-size:1rem;font-weight:800;color:var(--pink)">+4</div>
      </div>
      <!-- Sprint 5: Wk 9-10 -->
      <div style="background:#F8FAFB;border-radius:10px;padding:10px;min-width:120px">
        <div style="font-size:.65rem;font-weight:700;color:var(--navy);text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px;text-align:center">Wk 9-10</div>
        <div style="background:white;border:1px solid #E5E7EB;border-radius:6px;padding:8px;margin-bottom:6px;border-left:3px solid var(--teal)">
          <div style="font-size:.7rem;font-weight:600;color:var(--navy)">Perf. New Angle</div>
          <div style="font-size:.6rem;color:var(--muted)">30s + 15s</div>
        </div>
        <div style="background:white;border:1px solid #E5E7EB;border-radius:6px;padding:8px;margin-bottom:6px;border-left:3px solid var(--navy)">
          <div style="font-size:.7rem;font-weight:600;color:var(--navy)">Brand Refresh</div>
          <div style="font-size:.6rem;color:var(--muted)">Updated CTA</div>
        </div>
        <div style="background:white;border:1px solid #E5E7EB;border-radius:6px;padding:8px;border-left:3px solid var(--pink)">
          <div style="font-size:.7rem;font-weight:600;color:var(--navy)">UGC Before/After</div>
          <div style="font-size:.6rem;color:var(--muted)">9:16</div>
        </div>
        <div style="text-align:center;margin-top:8px;font-size:1rem;font-weight:800;color:var(--navy)">+4</div>
      </div>
      <!-- Sprint 6: Wk 11-12 -->
      <div style="background:#F8FAFB;border-radius:10px;padding:10px;min-width:120px">
        <div style="font-size:.65rem;font-weight:700;color:var(--navy);text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px;text-align:center">Wk 11-12</div>
        <div style="background:white;border:1px solid #E5E7EB;border-radius:6px;padding:8px;margin-bottom:6px;border-left:3px solid #D97706">
          <div style="font-size:.7rem;font-weight:600;color:var(--navy)">Event: BFCM Prep</div>
          <div style="font-size:.6rem;color:var(--muted)">30s + 15s + 6s</div>
        </div>
        <div style="background:white;border:1px solid #E5E7EB;border-radius:6px;padding:8px;margin-bottom:6px;border-left:3px solid var(--teal)">
          <div style="font-size:.7rem;font-weight:600;color:var(--navy)">Perf. Best-Of</div>
          <div style="font-size:.6rem;color:var(--muted)">Top performers</div>
        </div>
        <div style="background:white;border:1px solid #E5E7EB;border-radius:6px;padding:8px;border-left:3px solid var(--navy)">
          <div style="font-size:.7rem;font-weight:600;color:var(--navy)">Brand Full Line</div>
          <div style="font-size:.6rem;color:var(--muted)">Catalog showcase</div>
        </div>
        <div style="text-align:center;margin-top:8px;font-size:1rem;font-weight:800;color:var(--navy)">+4</div>
      </div>
    </div>
    <div style="text-align:center;margin-top:12px;font-size:.72rem;color:var(--muted)">Every 2-week sprint adds 4+ new ads to your library. The pipeline never stops.</div>
  </div>

  <div style="margin-top:20px;display:flex;gap:12px;flex-wrap:wrap;justify-content:center">
    <span style="background:var(--navy);color:white;padding:6px 16px;border-radius:999px;font-size:.78rem;font-weight:600">16:9 CTV &amp; In-Stream</span>
    <span style="background:var(--navy);color:white;padding:6px 16px;border-radius:999px;font-size:.78rem;font-weight:600">9:16 YouTube Shorts</span>
    <span style="background:var(--navy);color:white;padding:6px 16px;border-radius:999px;font-size:.78rem;font-weight:600">6s Bumper Ads</span>
    <span style="background:var(--navy);color:white;padding:6px 16px;border-radius:999px;font-size:.78rem;font-weight:600">15s Non-Skip</span>
    <span style="background:var(--navy);color:white;padding:6px 16px;border-radius:999px;font-size:.78rem;font-weight:600">30s Lean-Back TV</span>
  </div>

  <div class="grid-2" style="margin-top:20px">
    <div class="card">
      <h3>&#x1f4f1; Product-Focused</h3>
      <p>Clean, benefit-driven product spots that highlight your key differentiators. Optimized for CTV 15s non-skip and YouTube TrueView formats. SKU-level creative for product launches and seasonal promos.</p>
    </div>
    <div class="card">
      <h3>&#x1f4f8; Social Montage / UGC</h3>
      <p>Authentic, testimonial-style creative compiled from social content and customer reviews. We can turn your existing social and digital assets into widescreen, TV-ready creative — no new shoot required.</p>
    </div>
  </div>
  {repurpose}
</div>"""


def _md_to_html(text: str) -> str:
    """Convert basic markdown inline formatting to HTML."""
    import re
    # Escape HTML first
    text = html_mod.escape(text)
    # Bold: **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    # Italic: *text* or _text_ (but not inside strong tags)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    # Inline code: `text`
    text = re.sub(r'`(.+?)`', r'<code style="background:rgba(0,0,0,.06);padding:1px 4px;border-radius:3px;font-size:.8em">\1</code>', text)
    return text


def _build_creative_preview(company: str, report: DomainAdReport) -> str:
    """Build a preview section showing AI-generated brand brief + script from Creative Pipeline.

    Script is rendered as 2-column scene cards with keyframe images on the left
    and script content on the right. Brand brief shows key highlights with
    proper markdown rendering.
    """
    cp = report.creative_pipeline
    if not cp or not cp.found:
        return ""

    # ── Brand brief (show key highlights, properly formatted) ──
    brief_html = ""
    if cp.brand_brief:
        brief_paras = [p.strip() for p in cp.brand_brief.split("\n") if p.strip()]
        brief_content = ""
        for p in brief_paras:
            # Skip separator lines
            if p.strip() == "---" or p.strip() == "***":
                continue
            # Convert markdown-style headers
            if p.startswith("#"):
                heading = p.lstrip("#").strip()
                brief_content += f'<p style="font-weight:700;color:var(--navy);margin-top:14px;margin-bottom:4px;font-size:.9rem">{_md_to_html(heading)}</p>'
            # Bullet points
            elif p.startswith("- ") or p.startswith("* "):
                item = p[2:].strip()
                brief_content += f'<div style="display:flex;gap:6px;padding:2px 0 2px 12px;font-size:.82rem;color:#444"><span style="color:var(--teal);flex-shrink:0">•</span><span>{_md_to_html(item)}</span></div>'
            else:
                brief_content += f'<p style="font-size:.84rem;color:#444;margin-bottom:6px;line-height:1.6">{_md_to_html(p)}</p>'

        brief_html = f"""<div class="card" style="margin-bottom:24px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
        <span style="font-size:1.2rem">&#x1f4cb;</span>
        <h3 style="margin:0">Brand Intelligence Brief</h3>
      </div>
      <div style="max-height:320px;overflow-y:auto;padding-right:8px">
        {brief_content}
      </div>
    </div>"""

    # ── Script — parse into scenes, render as 2-column cards with keyframe images ──
    script_html = ""
    if cp.script:
        import re
        script_lines = cp.script.split("\n")
        scenes = []  # list of (scene_title, duration, visual_desc, vo_text, other_content)
        current_scene = None
        current_section = ""  # "visual", "vo", "copy", "notes", "other"
        current_data = {"title": "", "duration": "", "visual": [], "vo": [], "copy": [], "notes": [], "other": []}

        for raw_line in script_lines:
            line = raw_line.strip()
            if not line or line == "---" or line == "***":
                continue

            # Detect scene headings
            is_scene = False
            if re.match(r'^(\*\*)?SCENE\s+\d', line, re.IGNORECASE):
                is_scene = True
            elif re.match(r'^#{1,3}\s+.*scene', line, re.IGNORECASE):
                is_scene = True
            elif re.match(r'^(\*\*)?Scene\s+\d', line):
                is_scene = True

            if is_scene:
                # Save previous scene
                if current_data["title"]:
                    scenes.append(dict(current_data))
                current_data = {"title": "", "duration": "", "visual": [], "vo": [], "copy": [], "notes": [], "other": []}
                title = line.lstrip("#* ").strip().rstrip("*")
                current_data["title"] = title
                current_section = "other"
                continue

            # Detect duration
            if line.upper().startswith("**DURATION:") or line.upper().startswith("DURATION:"):
                dur = line.split(":", 1)[1].strip().rstrip("*")
                current_data["duration"] = dur
                continue

            # Detect section labels
            upper = line.upper().replace("**", "")
            if upper.startswith("MEDIA/VISUAL") or upper.startswith("VISUAL"):
                current_section = "visual"
                continue
            elif upper.startswith("VOICEOVER") or upper.startswith("VO:"):
                current_section = "vo"
                # Check if VO content is on same line
                if ":" in line:
                    vo_text = line.split(":", 1)[1].strip().strip("*\"")
                    if vo_text:
                        current_data["vo"].append(vo_text)
                continue
            elif upper.startswith("ON-SCREEN COPY") or upper.startswith("COPY:"):
                current_section = "copy"
                continue
            elif upper.startswith("DIRECTOR NOTES") or upper.startswith("NOTES:"):
                current_section = "notes"
                continue

            # Skip meta lines before first scene
            if not current_data["title"]:
                continue

            # Add content to current section
            clean = line.lstrip("*- ").strip().rstrip("*")
            if clean and clean not in ("(None)", "(None, visuals tell the story.)", "(None in this scene, allowing visuals to dominate. Critical elements within 95% safe zone.)"):
                if current_section == "visual":
                    current_data["visual"].append(clean)
                elif current_section == "vo":
                    current_data["vo"].append(clean.strip('"'))
                elif current_section == "copy":
                    current_data["copy"].append(clean)
                elif current_section == "notes":
                    current_data["notes"].append(clean)
                else:
                    current_data["other"].append(clean)

        # Save last scene
        if current_data["title"]:
            scenes.append(dict(current_data))

        # Build scene cards — 2 columns: keyframe image (left) + script content (right)
        images = cp.image_urls or []
        scene_cards = ""
        for i, scene in enumerate(scenes):
            title = _md_to_html(scene["title"])
            duration = scene["duration"]

            # Left column: keyframe image
            if i < len(images):
                img_html = f'<img src="{_esc(images[i])}" alt="Scene {i+1} keyframe" style="width:100%;border-radius:10px;aspect-ratio:16/9;object-fit:cover;box-shadow:0 2px 8px rgba(0,0,0,.15)">'
            else:
                # Placeholder keyframe
                scene_num = i + 1
                img_html = f'''<div style="width:100%;aspect-ratio:16/9;border-radius:10px;background:linear-gradient(135deg,var(--navy) 0%,var(--teal) 100%);display:flex;flex-direction:column;align-items:center;justify-content:center;color:white">
                  <div style="font-size:2rem;font-weight:800;opacity:.8">SCENE {scene_num}</div>
                  <div style="font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;opacity:.5;margin-top:4px">{duration or "Keyframe"}</div>
                </div>'''

            # Right column: script content
            content_parts = ""

            # Duration badge
            if duration:
                content_parts += f'<div style="margin-bottom:8px"><span style="background:var(--teal);color:white;padding:2px 10px;border-radius:999px;font-size:.68rem;font-weight:600">{_md_to_html(duration)}</span></div>'

            # Visual direction
            if scene["visual"]:
                content_parts += '<div style="margin-bottom:10px">'
                content_parts += '<div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--teal);margin-bottom:4px">Visual</div>'
                for v in scene["visual"]:
                    content_parts += f'<p style="font-size:.8rem;color:#444;margin-bottom:3px;line-height:1.5">{_md_to_html(v)}</p>'
                content_parts += '</div>'

            # Voiceover
            if scene["vo"]:
                vo_text = " ".join(scene["vo"])
                content_parts += f'''<div style="margin-bottom:10px;background:var(--teal-light);border-left:3px solid var(--teal);border-radius:0 8px 8px 0;padding:10px 12px">
                  <div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--teal);margin-bottom:3px">&#x1f399; Voiceover</div>
                  <p style="font-size:.82rem;color:var(--navy);margin:0;font-style:italic;line-height:1.5">"{_md_to_html(vo_text)}"</p>
                </div>'''

            # On-screen copy
            if scene["copy"]:
                content_parts += '<div style="margin-bottom:8px">'
                content_parts += '<div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--pink);margin-bottom:3px">On-Screen Copy</div>'
                for c in scene["copy"]:
                    content_parts += f'<p style="font-size:.8rem;color:#444;margin-bottom:2px">{_md_to_html(c)}</p>'
                content_parts += '</div>'

            scene_cards += f"""<div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;background:white;border:1px solid var(--border);border-radius:14px;padding:20px;margin-bottom:14px">
          <div style="display:flex;flex-direction:column;justify-content:center">
            {img_html}
          </div>
          <div>
            <h4 style="font-size:.95rem;color:var(--navy);margin-bottom:8px">{title}</h4>
            {content_parts}
          </div>
        </div>"""

        if scene_cards:
            script_html = f"""<div style="margin-top:4px">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px">
          <span style="font-size:1.2rem">&#x1f3ac;</span>
          <h3 style="margin:0">AI-Generated Production Script</h3>
          <span style="margin-left:auto;font-size:.72rem;background:var(--teal);color:white;padding:3px 10px;border-radius:999px">30s CTV</span>
        </div>
        {scene_cards}
      </div>"""
        else:
            # Fallback: render as formatted text
            script_text = _md_to_html(cp.script[:3000])
            script_html = f'<div class="card" style="font-size:.82rem;color:#444;white-space:pre-wrap;line-height:1.6">{script_text}</div>'

    return f"""<div class="section" style="background:linear-gradient(180deg, #F6EBF6 0%, white 40%)">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
    <span style="font-size:1.4rem">&#x2728;</span>
    <h2 style="margin:0">Your Custom Ad — AI-Generated for {company}</h2>
  </div>
  <p class="section-sub">Our AI creative pipeline researched your brand, built a creative brief, and generated a production-ready script with scene stills — all automated. This is what Upscale's creative system produces for every campaign.</p>
  {brief_html}
  {script_html}
</div>"""


def _build_video_card(ad, source_platform: str) -> str:
    """Build a single MP4 video card for an ad."""
    title = _esc(ad.title or "Untitled Ad")
    duration_html = ""
    if ad.duration_seconds:
        secs = ad.duration_seconds % 60
        duration_html = f'<span style="background:var(--teal);color:white;padding:2px 8px;border-radius:4px;font-size:.72rem;font-weight:600">:{secs:02d}</span>'

    start_date_html = ""
    if ad.start_date:
        start_date_html = f'<span style="font-size:.78rem;color:var(--muted)">Running since {_esc(ad.start_date)}</span>'

    link_html = ""
    if ad.ad_page_url:
        link_html = f'<a href="{_esc(ad.ad_page_url)}" target="_blank" style="font-size:.78rem;color:var(--teal);font-weight:600">View on {_esc(source_platform)} &rarr;</a>'

    poster_attr = f'poster="{_esc(ad.thumbnail_url)}"' if ad.thumbnail_url else ""

    return f"""<div style="background:var(--navy);border-radius:16px;overflow:hidden;box-shadow:0 8px 32px rgba(0,0,0,.15)">
    <video controls preload="metadata" style="width:100%;display:block;aspect-ratio:16/9;background:#000" {poster_attr}>
      <source src="{_esc(ad.video_url)}" type="video/mp4">
    </video>
    <div style="padding:16px 20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px">
      <div>
        <div style="color:white;font-weight:600;font-size:.9rem">{title} {duration_html}</div>
        <div style="display:flex;gap:12px;align-items:center;margin-top:4px">
          <span style="font-size:.72rem;color:rgba(255,255,255,.5);text-transform:uppercase;letter-spacing:.04em">via {_esc(source_platform)}</span>
          {start_date_html}
        </div>
      </div>
      {link_html}
    </div>
  </div>"""


def _extract_youtube_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats."""
    import re
    if not url:
        return None
    # adstransparency.google.com URLs don't have video IDs
    if "adstransparency.google.com" in url:
        return None
    # youtube.com/watch?v=ID
    m = re.search(r'[?&]v=([a-zA-Z0-9_-]{11})', url)
    if m:
        return m.group(1)
    # youtu.be/ID
    m = re.search(r'youtu\.be/([a-zA-Z0-9_-]{11})', url)
    if m:
        return m.group(1)
    # youtube.com/embed/ID
    m = re.search(r'youtube\.com/embed/([a-zA-Z0-9_-]{11})', url)
    if m:
        return m.group(1)
    return None


def _build_youtube_embed(ad, index: int) -> str:
    """Build a YouTube iframe embed card."""
    # Try to extract video ID from ad_page_url or video_url
    vid_id = _extract_youtube_video_id(ad.ad_page_url or "") or _extract_youtube_video_id(ad.video_url or "")

    title = _esc(ad.title or f"YouTube Ad {index + 1}")
    start_date_html = ""
    if ad.start_date:
        start_date_html = f' &middot; Running since {_esc(ad.start_date)}'

    if vid_id:
        return f"""<div style="background:white;border:1px solid var(--border);border-radius:14px;overflow:hidden">
    <div style="position:relative;padding-bottom:56.25%;height:0">
      <iframe src="https://www.youtube.com/embed/{vid_id}" style="position:absolute;top:0;left:0;width:100%;height:100%;border:0" allow="accelerometer;autoplay;clipboard-write;encrypted-media;gyroscope;picture-in-picture" allowfullscreen></iframe>
    </div>
    <div style="padding:12px 16px">
      <div style="font-weight:600;font-size:.85rem">{title}</div>
      <div style="font-size:.75rem;color:var(--muted)">YouTube{start_date_html}</div>
    </div>
  </div>"""

    # Fallback: link card if no embeddable video ID
    link_url = _esc(ad.ad_page_url or "")
    return f"""<div style="background:white;border:1px solid var(--border);border-radius:14px;overflow:hidden;padding:20px;display:flex;align-items:center;gap:16px">
    <div style="width:48px;height:48px;background:#FF0000;border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0">
      <svg viewBox="0 0 24 24" width="24" height="24" fill="white"><path d="M8 5v14l11-7z"/></svg>
    </div>
    <div style="flex:1;min-width:0">
      <div style="font-weight:600;font-size:.85rem">{title}</div>
      <div style="font-size:.75rem;color:var(--muted)">Google Ads Transparency{start_date_html}</div>
    </div>
    {"<a href=" + chr(34) + link_url + chr(34) + ' target="_blank" style="font-size:.78rem;color:var(--teal);font-weight:600;white-space:nowrap">View Ad &rarr;</a>' if link_url else ""}
  </div>"""


def _build_ad_discovery_video(company: str, report: DomainAdReport) -> str:
    """Build Ad Discovery section with MP4 downloads from Meta & iSpot,
    and embedded YouTube videos for YouTube/Google ads.
    """
    meta_count = len(report.meta_ads.ads)
    ispot_count = len(report.ispot_ads.ads)
    yt_count = len(report.youtube_ads.ads)
    total_ads = meta_count + ispot_count + yt_count

    if total_ads == 0:
        return ""

    stats_parts = []
    if meta_count:
        stats_parts.append(f"{meta_count} Meta")
    if ispot_count:
        stats_parts.append(f"{ispot_count} CTV/Linear")
    if yt_count:
        stats_parts.append(f"{yt_count} YouTube")
    stats_line = " + ".join(stats_parts) if stats_parts else f"{total_ads} total"

    sections_html = []

    # ── Meta: first ad with video_url as MP4 download ──
    meta_video = next((a for a in report.meta_ads.ads if a.video_url), None)
    if meta_video:
        sections_html.append(f"""<div>
    <div style="font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;color:var(--pink);font-weight:700;margin-bottom:10px">Meta Ad Library &middot; {meta_count} ad{"s" if meta_count != 1 else ""} found</div>
    {_build_video_card(meta_video, "Meta Ad Library")}
  </div>""")

    # ── iSpot: first ad with video_url as MP4 download ──
    ispot_video = next((a for a in report.ispot_ads.ads if a.video_url), None)
    if ispot_video:
        sections_html.append(f"""<div>
    <div style="font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;color:var(--teal);font-weight:700;margin-bottom:10px">iSpot (CTV / Linear TV) &middot; {ispot_count} ad{"s" if ispot_count != 1 else ""} found</div>
    {_build_video_card(ispot_video, "iSpot")}
  </div>""")

    # ── YouTube / Google: show first ad as MP4 if available, then embed remaining as cards ──
    yt_ads = report.youtube_ads.ads[:3]
    if yt_ads:
        yt_parts = []
        # First ad with video_url gets an MP4 player
        first_yt = yt_ads[0] if yt_ads else None
        remaining_yt = yt_ads[1:] if len(yt_ads) > 1 else []

        if first_yt and first_yt.video_url:
            yt_parts.append(_build_video_card(first_yt, "YouTube"))
            # Remaining ads as embed/link cards
            if remaining_yt:
                yt_cards = "\n    ".join(_build_youtube_embed(ad, i + 1) for i, ad in enumerate(remaining_yt))
                yt_parts.append(f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px">{yt_cards}</div>')
        else:
            # No video URL — show all as embed/link cards
            yt_cards = "\n    ".join(_build_youtube_embed(ad, i) for i, ad in enumerate(yt_ads))
            yt_parts.append(f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px">{yt_cards}</div>')

        sections_html.append(f"""<div>
    <div style="font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;color:#FF0000;font-weight:700;margin-bottom:10px">YouTube / Google Ads &middot; {yt_count} ad{"s" if yt_count != 1 else ""} found</div>
    {"".join(yt_parts)}
  </div>""")

    if not sections_html:
        return ""

    return f"""<section style="padding:48px 0">
  <div style="text-align:center;margin-bottom:32px">
    <div style="font-size:.75rem;text-transform:uppercase;letter-spacing:.12em;color:var(--teal);font-weight:700;margin-bottom:8px">Ad Discovery</div>
    <h2 style="font-size:1.8rem;margin-bottom:8px">{company}'s Current Advertising</h2>
    <p style="color:var(--muted);font-size:.9rem">We found <strong>{stats_line}</strong> active ads across platforms.</p>
  </div>
  <div style="max-width:900px;margin:0 auto;display:flex;flex-direction:column;gap:32px">
    {"".join(sections_html)}
  </div>
</section>"""


def _build_audio_demos(company: str, report: DomainAdReport) -> str:
    """Build an audio demo section with embedded HTML5 audio players for AI-generated voiceover."""
    audio_files = getattr(report, 'audio_files', None) or []
    if not audio_files:
        return ""

    # Voice styling
    voice_colors = ["#B72BB3", "#2563EB", "#0EA5E9", "#059669", "#D97706"]

    cards = []
    for i, af in enumerate(audio_files):
        voice = af.get("voice", "Voice")
        voice_short = voice.split(" - ")[0].strip() if " - " in voice else voice.split(",")[0].strip()
        voice_desc = voice.split(" - ")[1].strip() if " - " in voice else ""
        script_title = af.get("script", "Script")
        url = af.get("url", "")
        color = voice_colors[i % len(voice_colors)]
        initial = voice_short[0].upper()

        desc_html = f'<div style="font-size:.75rem;color:var(--muted);margin-top:2px">{_esc(voice_desc)}</div>' if voice_desc else ""

        cards.append(f"""<div style="background:white;border:1px solid var(--border);border-radius:14px;padding:18px;display:flex;flex-direction:column;gap:12px">
  <div style="display:flex;align-items:center;gap:12px">
    <div style="width:44px;height:44px;background:{color};border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-weight:800;font-size:1.1rem;flex-shrink:0">{initial}</div>
    <div>
      <div style="font-weight:700;font-size:.95rem">{_esc(voice_short)}</div>
      {desc_html}
    </div>
  </div>
  <div style="font-size:.78rem;color:var(--muted);text-transform:uppercase;letter-spacing:.04em">{_esc(script_title)} &middot; 30s CTV Spot</div>
  <audio controls preload="none" style="width:100%;height:40px;border-radius:8px">
    <source src="{_esc(url)}" type="audio/mpeg">
  </audio>
</div>""")

    return f"""<section style="padding:60px 0">
  <div style="text-align:center;margin-bottom:40px">
    <div style="font-size:.75rem;text-transform:uppercase;letter-spacing:.12em;color:var(--teal);font-weight:700;margin-bottom:8px">AI-Generated Voiceover</div>
    <h2 style="font-size:2rem;margin-bottom:12px">Listen to Your Ad</h2>
    <p style="color:var(--muted);max-width:600px;margin:0 auto;font-size:.95rem">
      We generated multiple professional voice options for {company}'s CTV spot.
      Select a voice that best represents your brand.
    </p>
  </div>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;max-width:1000px;margin:0 auto">
    {"".join(cards)}
  </div>
  <p style="text-align:center;font-size:.8rem;color:var(--muted);margin-top:20px">
    Powered by ElevenLabs &middot; {len(audio_files)} voice variations &middot; URLs valid for 7 days
  </p>
</section>"""


def _build_creative_showcase(report: DomainAdReport) -> str:
    """Build the Upscale Creative Showcase section — a grid of Vimeo video cards
    replicating the layout from upscale.ai/solutions#videos.

    Videos are sorted by relevance to the brand's industry/vertical.
    Shows 3 cards initially with a "View all creatives" button to expand.
    Category filter pills also expand to show all matching videos.
    """

    # ── Video catalog ──
    VIDEOS = [
        {"id": "1171126835", "brand": "Biom", "cats": ["Home", "CPG", "Subscription"]},
        {"id": "1171126946", "brand": "Book of the Month", "cats": ["Subscription"]},
        {"id": "1073355024", "h": "20adb5f2eb", "brand": "Branch", "cats": ["Home", "Furniture"]},
        {"id": "1171126818", "brand": "Canopy", "cats": ["Home", "Health", "Subscription"]},
        {"id": "1171126927", "brand": "Jones Road Beauty", "cats": ["Beauty", "Subscription"]},
        {"id": "1073355127", "brand": "Lalo", "cats": ["Home", "Baby"]},
        {"id": "1171126903", "brand": "Laundry Sauce", "cats": ["Home", "CPG", "Subscription"]},
        {"id": "1171126796", "brand": "Momofuku", "cats": ["Food", "Subscription"]},
        {"id": "1171126767", "brand": "Mood", "cats": ["Health", "Subscription"]},
        {"id": "1073354880", "h": "931ddff1fc", "brand": "Newton", "cats": ["Home", "Baby"]},
        {"id": "1171126878", "brand": "Rally", "cats": ["Fitness", "Health"]},
        {"id": "1171126858", "brand": "State Bags", "cats": ["Travel"]},
        {"id": "1171126742", "brand": "Stately Men", "cats": ["Mens Apparel"]},
    ]

    # ── Sort by relevance to the brand ──
    # Build keyword set from industry, description, and product categories
    e = report.enrichment
    relevance_keywords: set[str] = set()
    if e:
        for field in [e.industry, e.description]:
            if field:
                relevance_keywords.update(w.lower() for w in field.split() if len(w) > 2)
        if e.product_categories:
            for cat in e.product_categories:
                relevance_keywords.update(w.lower() for w in cat.split() if len(w) > 2)

    # Industry-to-showcase-cat mapping for broader matching
    INDUSTRY_MAP: dict[str, list[str]] = {
        "beauty": ["Beauty", "CPG", "Subscription"],
        "cosmetics": ["Beauty", "CPG"],
        "skincare": ["Beauty", "Health", "CPG"],
        "health": ["Health", "CPG", "Subscription"],
        "wellness": ["Health", "Fitness", "Subscription"],
        "supplement": ["Health", "CPG", "Subscription"],
        "fitness": ["Fitness", "Health"],
        "food": ["Food", "CPG", "Subscription"],
        "beverage": ["Food", "CPG"],
        "home": ["Home", "Furniture"],
        "furniture": ["Home", "Furniture"],
        "baby": ["Baby", "Home"],
        "kids": ["Baby", "Home"],
        "children": ["Baby", "Home"],
        "fashion": ["Mens Apparel", "Travel"],
        "apparel": ["Mens Apparel"],
        "clothing": ["Mens Apparel"],
        "accessories": ["Travel", "Mens Apparel"],
        "bags": ["Travel"],
        "luggage": ["Travel"],
        "subscription": ["Subscription"],
        "pet": ["CPG", "Health"],
        "sports": ["Fitness", "Health"],
    }

    # Collect matching showcase categories from the brand's keywords
    matched_cats: set[str] = set()
    for kw in relevance_keywords:
        for industry_kw, cats in INDUSTRY_MAP.items():
            if industry_kw in kw or kw in industry_kw:
                matched_cats.update(cats)

    def _relevance_score(video: dict) -> int:
        """Higher score = more relevant. Count overlapping categories."""
        return sum(1 for c in video["cats"] if c in matched_cats)

    # Sort: highest relevance first, then alphabetical by brand as tiebreaker
    VIDEOS.sort(key=lambda v: (-_relevance_score(v), v["brand"]))

    INITIAL_VISIBLE = 3

    # Collect unique categories
    all_cats = []
    seen = set()
    for v in VIDEOS:
        for c in v["cats"]:
            if c not in seen:
                all_cats.append(c)
                seen.add(c)

    # Build filter pills
    filter_pills = ['<button class="showcase-filter active" data-cat="all" onclick="filterShowcase(\'all\',this)">View all</button>']
    for cat in all_cats:
        filter_pills.append(
            f'<button class="showcase-filter" data-cat="{_esc(cat)}" onclick="filterShowcase(\'{_esc(cat)}\',this)">{_esc(cat)}</button>'
        )

    # Build video cards — first N visible, rest collapsed
    cards = []
    for i, v in enumerate(VIDEOS):
        vid = v["id"]
        h_param = f'?h={v["h"]}&amp;' if v.get("h") else "?"
        embed_url = f'https://player.vimeo.com/video/{vid}{h_param}badge=0&amp;autopause=0&amp;player_id=0&amp;app_id=58479&amp;autoplay=1'
        thumb_url = f'https://vumbnail.com/{vid}.jpg'
        brand = _esc(v["brand"])
        cat_str = ",".join(v["cats"])
        primary_cat = v["cats"][0]
        collapsed = " showcase-collapsed" if i >= INITIAL_VISIBLE else ""

        cards.append(f"""<div class="showcase-card{collapsed}" data-cats="{_esc(cat_str)}" data-embed="{embed_url}" onclick="openShowcase(this)">
  <img class="showcase-thumb" src="{thumb_url}" alt="{brand}" loading="lazy">
  <div class="showcase-overlay">
    <div class="showcase-play"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></div>
  </div>
  <div class="showcase-tag">{_esc(primary_cat)}</div>
  <div class="showcase-brand">{brand}</div>
</div>""")

    remaining = len(VIDEOS) - INITIAL_VISIBLE

    # Lightbox modal + filter + expand JS
    script = """<script>
var showcaseExpanded = false;
function openShowcase(card) {
  var modal = document.getElementById('showcase-modal');
  var inner = document.getElementById('showcase-player');
  var url = card.getAttribute('data-embed');
  inner.innerHTML = '<iframe src="' + url + '" allow="autoplay; fullscreen; picture-in-picture; clipboard-write; encrypted-media" allowfullscreen style="width:100%;height:100%;border:0"></iframe>';
  modal.classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeShowcase() {
  var modal = document.getElementById('showcase-modal');
  var inner = document.getElementById('showcase-player');
  inner.innerHTML = '';
  modal.classList.remove('open');
  document.body.style.overflow = '';
}
function expandShowcase() {
  showcaseExpanded = true;
  document.querySelectorAll('.showcase-collapsed').forEach(function(c) {
    c.classList.remove('showcase-collapsed');
  });
  var btn = document.getElementById('showcase-expand');
  if (btn) btn.style.display = 'none';
}
function filterShowcase(cat, btn) {
  // Clicking a filter always expands the grid
  if (!showcaseExpanded) expandShowcase();
  var cards = document.querySelectorAll('.showcase-card');
  cards.forEach(function(c) {
    if (cat === 'all') { c.classList.remove('hidden'); }
    else {
      var cats = c.getAttribute('data-cats').split(',');
      c.classList.toggle('hidden', cats.indexOf(cat) === -1);
    }
  });
  document.querySelectorAll('.showcase-filter').forEach(function(b) { b.classList.remove('active'); });
  btn.classList.add('active');
}
document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeShowcase(); });
</script>"""

    return f"""<section class="showcase-section">
  <div class="showcase-header">
    <div class="kicker">Creative Showcase</div>
    <h2>Upscale Creative Showcase</h2>
    <p>TV creatives developed on Upscale Studio &mdash; see what we can build for your brand.</p>
  </div>
  <div class="showcase-filters">
    {"".join(filter_pills)}
  </div>
  <div class="showcase-grid">
    {"".join(cards)}
  </div>
  <div style="text-align:center;margin-top:32px">
    <button id="showcase-expand" onclick="expandShowcase()" style="display:inline-flex;align-items:center;gap:8px;padding:12px 32px;background:var(--navy);color:white;border:none;border-radius:10px;font-size:.9rem;font-weight:600;cursor:pointer;font-family:inherit;transition:background .15s">
      View all {len(VIDEOS)} creatives
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M6 9l6 6 6-6"/></svg>
    </button>
  </div>
</section>

<div class="showcase-modal" id="showcase-modal" onclick="if(event.target===this)closeShowcase()">
  <div style="position:relative">
    <button class="showcase-modal-close" onclick="closeShowcase()">&times;</button>
    <div class="showcase-modal-inner" id="showcase-player"></div>
  </div>
</div>
{script}"""


def _build_spend_charts(company: str, budget: dict, strategy: dict) -> str:
    """Build daily (30-day) and weekly (12-week) spend charts using Chart.js."""
    import json as _json

    daily = _compute_daily_spend(budget["m1"], strategy)
    weekly = _compute_weekly_spend(budget, strategy)

    # Campaign start date
    start = _campaign_start_date()
    start_str = start.strftime("%B %d, %Y")  # e.g. "April 28, 2026"

    # Prepare chart data — use actual dates as labels
    daily_labels = _json.dumps([d["label"] for d in daily])
    daily_yt = _json.dumps([d["yt"] for d in daily])
    daily_rt = _json.dumps([d["ctv_rt"] for d in daily])
    daily_acq = _json.dumps([d["ctv_acq"] for d in daily])

    weekly_labels = _json.dumps([w["label"] for w in weekly])
    weekly_yt = _json.dumps([w["yt"] for w in weekly])
    weekly_rt = _json.dumps([w["ctv_rt"] for w in weekly])
    weekly_acq = _json.dumps([w["ctv_acq"] for w in weekly])

    total_3mo = budget["m1"] + budget["m2"] + budget["m3"]
    end_date = (start + timedelta(weeks=12)).strftime("%B %d, %Y")

    # Strategy description
    tier = strategy["tier"]
    if tier == "youtube_only":
        strategy_label = "YouTube-First"
        alloc_desc = "100% YouTube"
        channel_pills = '<span style="display:inline-block;padding:4px 12px;border-radius:6px;font-size:.78rem;font-weight:600;background:#FF0000;color:white">YouTube 100%</span>'
    elif tier == "ctv_led":
        rt_pct = round(strategy["ctv_rt_pct"] * 100)
        acq_pct = round(strategy["ctv_acq_pct"] * 100)
        yt_pct = round(strategy["yt_pct"] * 100)
        strategy_label = "CTV-Led"
        alloc_desc = f"CTV RT {rt_pct}% / CTV ACQ {acq_pct}% / YouTube {yt_pct}%"
        channel_pills = f"""<span style="display:inline-block;padding:4px 12px;border-radius:6px;font-size:.78rem;font-weight:600;background:var(--teal);color:white;margin-right:6px">CTV RT {rt_pct}%</span>
        <span style="display:inline-block;padding:4px 12px;border-radius:6px;font-size:.78rem;font-weight:600;background:var(--pink);color:white;margin-right:6px">CTV ACQ {acq_pct}%</span>
        <span style="display:inline-block;padding:4px 12px;border-radius:6px;font-size:.78rem;font-weight:600;background:#FF0000;color:white">YouTube {yt_pct}%</span>"""
    else:
        rt_pct = round(strategy["ctv_rt_pct"] * 100)
        acq_pct = round(strategy["ctv_acq_pct"] * 100)
        yt_pct = round(strategy["yt_pct"] * 100)
        strategy_label = "Full Funnel"
        alloc_desc = f"CTV RT {rt_pct}% / CTV ACQ {acq_pct}% / YouTube {yt_pct}%"
        channel_pills = f"""<span style="display:inline-block;padding:4px 12px;border-radius:6px;font-size:.78rem;font-weight:600;background:var(--teal);color:white;margin-right:6px">CTV RT {rt_pct}%</span>
        <span style="display:inline-block;padding:4px 12px;border-radius:6px;font-size:.78rem;font-weight:600;background:var(--pink);color:white;margin-right:6px">CTV ACQ {acq_pct}%</span>
        <span style="display:inline-block;padding:4px 12px;border-radius:6px;font-size:.78rem;font-weight:600;background:#FF0000;color:white">YouTube {yt_pct}%</span>"""

    # Build datasets based on tier — for YouTube-only, only show YouTube bar
    if tier == "youtube_only":
        daily_datasets = f"""[{{
            label: 'YouTube',
            data: {daily_yt},
            backgroundColor: '#FF0000',
            borderRadius: 3,
          }}]"""
        weekly_datasets = f"""[{{
            label: 'YouTube',
            data: {weekly_yt},
            backgroundColor: '#FF0000',
            borderRadius: 3,
          }}]"""
    else:
        daily_datasets = f"""[{{
            label: 'CTV Retargeting',
            data: {daily_rt},
            backgroundColor: '#0A6D86',
            borderRadius: 0,
          }},
          {{
            label: 'CTV Acquisition',
            data: {daily_acq},
            backgroundColor: '#831F80',
            borderRadius: 0,
          }},
          {{
            label: 'YouTube',
            data: {daily_yt},
            backgroundColor: '#FF0000',
            borderRadius: 3,
          }}]"""
        weekly_datasets = f"""[{{
            label: 'CTV Retargeting',
            data: {weekly_rt},
            backgroundColor: '#0A6D86',
            borderRadius: 0,
          }},
          {{
            label: 'CTV Acquisition',
            data: {weekly_acq},
            backgroundColor: '#831F80',
            borderRadius: 0,
          }},
          {{
            label: 'YouTube',
            data: {weekly_yt},
            backgroundColor: '#FF0000',
            borderRadius: 3,
          }}]"""

    return f"""<div class="section alt">
  <h2>Spend Plan for {company}</h2>
  <p class="section-sub">{strategy['description']}</p>

  <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:24px">
    <div style="flex:1;min-width:140px;padding:18px;background:white;border:1px solid var(--border);border-radius:12px;text-align:center">
      <div style="font-size:1.4rem;font-weight:800;color:var(--navy)">{start_str}</div>
      <div style="font-size:.68rem;text-transform:uppercase;color:var(--muted);letter-spacing:.05em">Campaign Start</div>
    </div>
    <div style="flex:1;min-width:120px;padding:18px;background:white;border:1px solid var(--border);border-radius:12px;text-align:center">
      <div style="font-size:1.4rem;font-weight:800;color:var(--navy)">{_fmt_money(budget['m1'])}</div>
      <div style="font-size:.68rem;text-transform:uppercase;color:var(--muted);letter-spacing:.05em">Month 1</div>
    </div>
    <div style="flex:1;min-width:120px;padding:18px;background:white;border:1px solid var(--border);border-radius:12px;text-align:center">
      <div style="font-size:1.4rem;font-weight:800;color:var(--navy)">{_fmt_money(total_3mo)}</div>
      <div style="font-size:.68rem;text-transform:uppercase;color:var(--muted);letter-spacing:.05em">3-Month Total</div>
    </div>
    <div style="flex:2;min-width:200px;padding:18px;background:white;border:1px solid var(--border);border-radius:12px">
      <div style="font-size:.68rem;text-transform:uppercase;color:var(--muted);letter-spacing:.05em;margin-bottom:8px">Channel Allocation</div>
      {channel_pills}
    </div>
  </div>

  <div class="card" style="margin-bottom:20px">
    <h3 style="font-size:1rem;margin-bottom:4px">Daily Spend — Month 1</h3>
    <p style="font-size:.78rem;color:var(--muted);margin-bottom:12px">Starting {start_str}. Ramp-up in week 1, then full daily spend through day 30.</p>
    <div style="position:relative;height:320px">
      <canvas id="dailyChart"></canvas>
    </div>
  </div>
  <div class="card">
    <h3 style="font-size:1rem;margin-bottom:4px">Weekly Spend — 12 Weeks</h3>
    <p style="font-size:.78rem;color:var(--muted);margin-bottom:12px">{start_str} &ndash; {end_date}. Budget scales: {_fmt_money(budget['m1'])} &rarr; {_fmt_money(budget['m2'])} &rarr; {_fmt_money(budget['m3'])}.</p>
    <div style="position:relative;height:320px">
      <canvas id="weeklyChart"></canvas>
    </div>
  </div>

  <script>
  (function() {{
    Chart.register(ChartDataLabels);

    function makeChartOpts(numDatasets) {{
      return {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
          legend: {{
            position: 'bottom',
            labels: {{ usePointStyle: true, pointStyle: 'rectRounded', padding: 16, font: {{ size: 11, family: 'Inter' }} }}
          }},
          tooltip: {{
            callbacks: {{
              label: function(ctx) {{ return ctx.dataset.label + ': $' + ctx.raw.toLocaleString(); }},
              footer: function(items) {{
                let sum = 0;
                items.forEach(i => sum += i.raw);
                return 'Total: $' + sum.toLocaleString();
              }}
            }}
          }},
          datalabels: {{
            display: function(ctx) {{
              return ctx.datasetIndex === numDatasets - 1;
            }},
            anchor: 'end',
            align: 'end',
            offset: 2,
            font: {{ size: 9, weight: '600', family: 'Inter' }},
            color: '#475467',
            formatter: function(value, ctx) {{
              let total = 0;
              ctx.chart.data.datasets.forEach(function(ds) {{
                total += ds.data[ctx.dataIndex] || 0;
              }});
              return total >= 1000 ? '$' + (total / 1000).toFixed(1) + 'K' : '$' + total;
            }}
          }}
        }},
        layout: {{
          padding: {{ top: 24 }}
        }},
        scales: {{
          x: {{
            stacked: true,
            grid: {{ display: false }},
            ticks: {{ font: {{ size: 9, family: 'Inter' }}, maxRotation: 0 }}
          }},
          y: {{
            stacked: true,
            grid: {{ color: '#f0f0f0' }},
            ticks: {{
              font: {{ size: 10, family: 'Inter' }},
              callback: function(v) {{ return v >= 1000 ? '$' + (v/1000) + 'K' : '$' + v; }}
            }}
          }}
        }}
      }};
    }}

    var dailyDs = {daily_datasets};
    new Chart(document.getElementById('dailyChart'), {{
      type: 'bar',
      data: {{
        labels: {daily_labels},
        datasets: dailyDs
      }},
      options: makeChartOpts(dailyDs.length)
    }});

    var weeklyDs = {weekly_datasets};
    new Chart(document.getElementById('weeklyChart'), {{
      type: 'bar',
      data: {{
        labels: {weekly_labels},
        datasets: weeklyDs
      }},
      options: makeChartOpts(weeklyDs.length)
    }});
  }})();
  </script>
</div>"""


def _build_campaign_plan(company, budget, has_shopify, has_klaviyo, strategy: dict | None = None, report: DomainAdReport | None = None) -> str:
    # Add eCommerce-specific tactics based on integrations
    m1_extras = []
    m2_extras = []
    m3_extras = []

    if has_shopify:
        m1_extras.append("Connect Shopify for real-time purchase data")
        m2_extras.append("Suppress existing purchasers to reduce waste")
        m3_extras.append("SKU-level creative for top products")
    if has_klaviyo:
        m1_extras.append("Sync Klaviyo audiences for retargeting")
        m2_extras.append("Trigger post-view email flows from TV exposure")
        m3_extras.append("Unified TV + email attribution reporting")

    # Strategy-specific tactics
    tier = strategy["tier"] if strategy else "full_funnel"
    if tier == "youtube_only":
        m1_extras.append("YouTube TrueView + Shorts campaigns")
        m2_extras.append("DemandGen for mid-funnel engagement")
        m3_extras.append("PMax for full-funnel conversion")
    elif tier == "ctv_led":
        m1_extras.append("CTV retargeting (40%) + acquisition (60%)")
        m2_extras.append("YouTube prospecting to extend reach")
    else:
        m1_extras.append("Focus on CTV retargeting to prove ROI fast")
        m2_extras.append("Scale CTV acquisition as winners emerge + YouTube unified")

    def extras_html(items):
        return "".join(f"<li>{_esc(i)}</li>" for i in items)

    # Build event calendar inline
    event_cal_html = _build_event_calendar_inline(company, report)

    return f"""<div class="section">
  <h2>3-Month Campaign Plan</h2>
  <p class="section-sub">A phased approach to prove streaming ROI for {company} and scale with confidence.</p>
  <div style="display:flex;gap:12px;margin-bottom:20px">
    <div style="flex:1;padding:14px;background:var(--teal-light);border-radius:10px;text-align:center">
      <div style="font-size:1.3rem;font-weight:800;color:var(--teal)">{_fmt_money(budget['m1'])}</div>
      <div style="font-size:.7rem;text-transform:uppercase;color:var(--teal);letter-spacing:.05em">Month 1</div>
    </div>
    <div style="flex:1;padding:14px;background:var(--pink-light);border-radius:10px;text-align:center">
      <div style="font-size:1.3rem;font-weight:800;color:var(--pink)">{_fmt_money(budget['m2'])}</div>
      <div style="font-size:.7rem;text-transform:uppercase;color:var(--pink);letter-spacing:.05em">Month 2</div>
    </div>
    <div style="flex:1;padding:14px;background:#E8F4FD;border-radius:10px;text-align:center">
      <div style="font-size:1.3rem;font-weight:800;color:var(--navy)">{_fmt_money(budget['m3'])}</div>
      <div style="font-size:.7rem;text-transform:uppercase;color:var(--navy);letter-spacing:.05em">Month 3</div>
    </div>
  </div>
  <details class="collapsible" open>
    <summary>View detailed month-by-month plan</summary>
    <div class="collapse-content">
      <div class="grid-3">
        <div class="phase-card p1">
          <div class="phase-label">Month 1 — Launch</div>
          <div class="phase-budget">{_fmt_money(budget['m1'])}</div>
          <h3>Build the Foundation</h3>
          <ul>
            <li>Retarget existing site visitors on CTV</li>
            <li>Re-engage past purchasers with video</li>
            <li>Establish baseline attribution metrics</li>
            <li>A/B test 2-3 creative concepts</li>
            <li>YouTube remarketing for cart abandoners</li>
            {extras_html(m1_extras)}
          </ul>
        </div>
        <div class="phase-card p2">
          <div class="phase-label">Month 2 — Scale</div>
          <div class="phase-budget">{_fmt_money(budget['m2'])}</div>
          <h3>Expand What Works</h3>
          <ul>
            <li>Scale winning creative from Month 1</li>
            <li>Expand to lookalike audiences</li>
            <li>Add contextual targeting by content genre</li>
            <li>Introduce YouTube prospecting campaigns</li>
            <li>Optimize toward cost-per-visit targets</li>
            {extras_html(m2_extras)}
          </ul>
        </div>
        <div class="phase-card p3">
          <div class="phase-label">Month 3 — Expand</div>
          <div class="phase-budget">{_fmt_money(budget['m3'])}</div>
          <h3>Full-Funnel Growth</h3>
          <ul>
            <li>Prospecting-heavy budget allocation</li>
            <li>ML-optimized audience expansion</li>
            <li>Incrementality test to prove lift</li>
            <li>Refresh creative with top-performing angles</li>
            <li>Review adjusted ROAS and plan Phase 2</li>
            {extras_html(m3_extras)}
          </ul>
        </div>
      </div>
    </div>
  </details>
  {event_cal_html}
</div>"""


def _build_event_calendar_inline(company: str, report: DomainAdReport | None) -> str:
    """Build an inline Event Calendar for the 3-Month Campaign Plan."""
    today = date.today()
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    next_monday = today + timedelta(days=days_until_monday)

    start_month = next_monday.month
    start_year = next_monday.year
    months_data: list[tuple[int, int, list]] = []
    for i in range(3):
        m = start_month + i
        y = start_year
        if m > 12:
            m -= 12
            y += 1
        year_events = get_events_for_year(y)
        month_events = [(ev, d) for ev, d in year_events if d.month == m]
        months_data.append((y, m, month_events))

    ECOM_CAT_COLORS = {
        "holiday": ("var(--pink)", "var(--pink-light)"),
        "sale": ("#DC2626", "#FEE2E2"),
        "seasonal": ("var(--teal)", "var(--teal-light)"),
        "cultural": ("#7C3AED", "#F3E8FF"),
    }

    month_cards = []
    for y, m, events in months_data:
        month_name = cal_mod.month_name[m]
        event_rows = []
        for ev, d in events:
            date_str = d.strftime("%b %d")
            cat = ev.category or "seasonal"
            cat_color, cat_bg = ECOM_CAT_COLORS.get(cat, ("var(--muted)", "var(--bg)"))
            badge = (
                f'<span style="font-size:.6rem;font-weight:700;text-transform:uppercase;'
                f'letter-spacing:.06em;padding:2px 6px;border-radius:4px;background:{cat_bg};'
                f'color:{cat_color}">{_esc(cat)}</span>'
            )
            event_rows.append(
                f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #f5f5f5">'
                f'<span style="font-size:.72rem;color:var(--muted);width:42px;flex-shrink:0">{date_str}</span>'
                f'<span style="font-size:.82rem;font-weight:600;color:var(--navy);flex:1">{_esc(ev.name)}</span>'
                f'{badge}'
                f'</div>'
            )
        if not event_rows:
            event_rows.append(
                '<div style="padding:6px 0;font-size:.82rem;color:var(--muted)">No major events</div>'
            )
        month_cards.append(
            f'<div class="card">'
            f'<h4 style="color:var(--navy);font-size:.95rem;margin-bottom:10px">{month_name} {y}</h4>'
            f'{"".join(event_rows)}'
            f'</div>'
        )

    return f"""<div style="margin-top:24px;padding-top:20px;border-top:1px solid var(--border)">
    <h3 style="margin-bottom:4px">Event Calendar</h3>
    <p style="font-size:.82rem;color:var(--muted);margin-bottom:12px">Key eCommerce events during your campaign window — align creative and flight increases around these dates.</p>
    <div class="grid-3">{"".join(month_cards)}</div>
  </div>"""


def _build_ctv_impact(company, report: DomainAdReport, budget, has_shopify) -> str:
    mix = report.channel_mix

    m1_impressions = int(budget["m1"] / 30 * 1000)
    m3_impressions = int((budget["m1"] + budget["m2"] + budget["m3"]) / 30 * 1000)
    reach = int(m3_impressions / 3.5)
    visits = int(m3_impressions * 0.004)

    context = ""
    if mix.has_linear:
        context = f"<p style='margin-top:16px;font-size:.9rem;color:var(--teal);font-weight:600'>&#x2713; {company} already runs linear TV — CTV extends that reach with digital-grade measurement and lower waste.</p>"
    else:
        context = f"<p style='margin-top:16px;font-size:.9rem;color:var(--pink);font-weight:600'>&#x2606; {company} has no detected TV/CTV presence — this is an untapped awareness channel with massive upside.</p>"

    shopify_note = ""
    if has_shopify:
        shopify_note = f"""<li style="padding:8px 0;color:white;font-size:.88rem">&#x1f6d2; <strong>Shopify purchase attribution</strong> — every CTV impression tied to actual revenue</li>"""

    # CTV spend by month (60% of total budget goes to CTV)
    # RT starts heavy (prove ROI), then scale into ACQ
    # Month 1: 60% RT / 40% ACQ  |  Month 2: 40% RT / 60% ACQ  |  Month 3: 25% RT / 75% ACQ
    ctv_m1 = int(budget["m1"] * 0.6)
    ctv_m2 = int(budget["m2"] * 0.6)
    ctv_m3 = int(budget["m3"] * 0.6)
    # RT / ACQ splits — shift from RT-heavy to ACQ-heavy
    ctv_m1_rt = int(ctv_m1 * 0.60); ctv_m1_acq = ctv_m1 - ctv_m1_rt
    ctv_m2_rt = int(ctv_m2 * 0.40); ctv_m2_acq = ctv_m2 - ctv_m2_rt
    ctv_m3_rt = int(ctv_m3 * 0.25); ctv_m3_acq = ctv_m3 - ctv_m3_rt
    ctv_bar_max = max(ctv_m1, ctv_m2, ctv_m3, 1)  # stacked total
    ctv_m1_imp = int(ctv_m1 / 30 * 1000)
    ctv_m2_imp = int(ctv_m2 / 30 * 1000)
    ctv_m3_imp = int(ctv_m3 / 30 * 1000)

    def _ctv_stacked(rt_val, acq_val, month_label):
        total = rt_val + acq_val
        total_pct = max(int(total / ctv_bar_max * 100), 12)
        rt_share = int(rt_val / total * 100) if total else 0
        acq_share = 100 - rt_share
        return f'''<div class="spend-bar">
        <div class="spend-bar-val">{_fmt_money(total)}</div>
        <div style="width:100%;height:{total_pct}%;display:flex;flex-direction:column;border-radius:8px;overflow:hidden;position:relative">
          <div style="flex:{acq_share};background:linear-gradient(180deg,#B72BB3 0%,var(--pink) 100%);display:flex;align-items:center;justify-content:center;font-size:.65rem;font-weight:700;color:white;min-height:18px" title="ACQ — {_fmt_money(acq_val)}">{_fmt_money(acq_val)}</div>
          <div style="flex:{rt_share};background:linear-gradient(180deg,#F9A8D4 0%,#FBCFE8 100%);display:flex;align-items:center;justify-content:center;font-size:.65rem;font-weight:700;color:#1a1a2e;min-height:18px" title="RT — {_fmt_money(rt_val)}">{_fmt_money(rt_val)}</div>
        </div>
        <div class="spend-bar-label">{month_label}</div>
      </div>'''

    return f"""<div class="section dark">
  <h2>CTV Impact for {company}</h2>
  <p class="section-sub">47% of all TV viewing is now streaming. Connected TV delivers premium, non-skippable video to your ideal customers — on the biggest screen in the house.</p>

  <div class="impact-grid" style="grid-template-columns:repeat(3,1fr)">
    <div class="impact-stat"><div class="num">{_fmt_number(m1_impressions)}</div><div class="lbl">Month 1 Impressions</div></div>
    <div class="impact-stat"><div class="num">{_fmt_number(reach)}</div><div class="lbl">Est. Unique Reach (3mo)</div></div>
    <div class="impact-stat"><div class="num">{_fmt_number(visits)}</div><div class="lbl">Est. Site Visits (3mo)</div></div>
  </div>

  <!-- 3-Month CTV Spend Chart — RT vs ACQ -->
  <div style="margin-top:32px">
    <h3 style="color:white;text-align:center;font-size:1rem;margin-bottom:4px">CTV Spend Ramp — Retargeting vs Acquisition</h3>
    <p style="text-align:center;font-size:.75rem;color:rgba(255,255,255,.5);margin-bottom:16px">Total CTV: {_fmt_money(ctv_m1 + ctv_m2 + ctv_m3)} over 3 months</p>
    <div class="spend-chart">
      {_ctv_stacked(ctv_m1_rt, ctv_m1_acq, "MONTH 1")}
      {_ctv_stacked(ctv_m2_rt, ctv_m2_acq, "MONTH 2")}
      {_ctv_stacked(ctv_m3_rt, ctv_m3_acq, "MONTH 3")}
    </div>
    <div style="display:flex;justify-content:center;gap:24px;margin-top:32px">
      <div style="display:flex;align-items:center;gap:6px"><div style="width:14px;height:14px;border-radius:3px;background:#F9A8D4"></div><span style="font-size:.72rem;color:rgba(255,255,255,.7)">Retargeting (RT)</span></div>
      <div style="display:flex;align-items:center;gap:6px"><div style="width:14px;height:14px;border-radius:3px;background:#B72BB3"></div><span style="font-size:.72rem;color:rgba(255,255,255,.7)">Acquisition (ACQ)</span></div>
    </div>
  </div>

  {context}

  <div class="grid-2" style="margin-top:24px">
    <div class="card" style="background:rgba(255,255,255,.12);border-color:rgba(255,255,255,.18);color:white">
      <h3 style="color:white">Why CTV for {company}</h3>
      <ul style="list-style:none;padding:0">
        <li style="padding:8px 0;color:white;font-size:.88rem">&#x1f4fa; <strong>47% of TV is streaming</strong> — your audience has moved</li>
        <li style="padding:8px 0;color:white;font-size:.88rem">&#x2714; Non-skippable, premium brand-safe inventory on major streamers</li>
        <li style="padding:8px 0;color:white;font-size:.88rem">&#x2714; Household-level targeting and attribution</li>
        <li style="padding:8px 0;color:white;font-size:.88rem">&#x2714; Incremental reach beyond social media audiences</li>
        {shopify_note}
      </ul>
    </div>
    <div class="card" style="background:rgba(255,255,255,.12);border-color:rgba(255,255,255,.18);color:white">
      <h3 style="color:white">Measurement That Proves It</h3>
      <ul style="list-style:none;padding:0">
        <li style="padding:8px 0;color:white;font-size:.88rem">&#x1f4ca; <strong>IP-based attribution</strong> — impression to visit to purchase</li>
        <li style="padding:8px 0;color:white;font-size:.88rem">&#x1f465; Household-level connectivity through graph relationships</li>
        <li style="padding:8px 0;color:white;font-size:.88rem">&#x1f50d; Geo-lift incrementality testing vs. holdout groups</li>
        <li style="padding:8px 0;color:white;font-size:.88rem">&#x23f0; Attribution windows: 3-day full, 4-day partial, 7-day max</li>
        <li style="padding:8px 0;color:white;font-size:.88rem">&#x1f6d2; Product/SKU-level insight where applicable</li>
        <li style="padding:8px 0;color:white;font-size:.88rem">&#x1f310; Lag-aware approach — not simplistic last-click reporting</li>
      </ul>
    </div>
  </div>
</div>"""


def _build_youtube_impact(company, report: DomainAdReport, budget) -> str:
    mix = report.channel_mix

    yt_budget_m1 = int(budget["m1"] * 0.4)
    yt_views = int(yt_budget_m1 / 0.04)
    yt_clicks = int(yt_views * 0.012)
    yt_cpc = round(yt_budget_m1 / max(yt_clicks, 1), 2)

    context = ""
    if mix.has_youtube:
        yt_count = len(report.youtube_ads.ads)
        context = f"<p style='margin-top:16px;font-size:.9rem;color:var(--teal);font-weight:600'>&#x2713; {company} already runs {yt_count} YouTube ads — Upscale adds $0-fee media buying, AI creative, and deterministic attribution to maximize your existing investment.</p>"
    else:
        context = f"<p style='margin-top:16px;font-size:.9rem;color:var(--pink);font-weight:600'>&#x2606; {company} has no detected YouTube ads — the largest growth channel in digital advertising is waiting to be activated.</p>"

    # YouTube spend by month (40% of total budget)
    # Split into RT (retargeting) and ACQ (acquisition) — 30% RT / 70% ACQ
    yt_m1 = int(budget["m1"] * 0.4)
    yt_m2 = int(budget["m2"] * 0.4)
    yt_m3 = int(budget["m3"] * 0.4)
    yt_m1_rt = int(yt_m1 * 0.3); yt_m1_acq = yt_m1 - yt_m1_rt
    yt_m2_rt = int(yt_m2 * 0.3); yt_m2_acq = yt_m2 - yt_m2_rt
    yt_m3_rt = int(yt_m3 * 0.3); yt_m3_acq = yt_m3 - yt_m3_rt
    yt_bar_max = max(yt_m1, yt_m2, yt_m3, 1)  # stacked total

    def _yt_stacked(rt_val, acq_val, month_label):
        total = rt_val + acq_val
        total_pct = max(int(total / yt_bar_max * 100), 12)
        rt_share = int(rt_val / total * 100) if total else 0
        acq_share = 100 - rt_share
        return f'''<div class="spend-bar">
        <div class="spend-bar-val">{_fmt_money(total)}</div>
        <div style="width:100%;height:{total_pct}%;display:flex;flex-direction:column;border-radius:8px;overflow:hidden;position:relative">
          <div style="flex:{acq_share};background:linear-gradient(180deg,var(--teal) 0%,#0ea5e9 100%);display:flex;align-items:center;justify-content:center;font-size:.65rem;font-weight:700;color:white;min-height:18px" title="ACQ — {_fmt_money(acq_val)}">{_fmt_money(acq_val)}</div>
          <div style="flex:{rt_share};background:linear-gradient(180deg,#6CC4D4 0%,#A8DFE8 100%);display:flex;align-items:center;justify-content:center;font-size:.65rem;font-weight:700;color:#1a1a2e;min-height:18px" title="RT — {_fmt_money(rt_val)}">{_fmt_money(rt_val)}</div>
        </div>
        <div class="spend-bar-label">{month_label}</div>
      </div>'''

    return f"""<div class="section alt">
  <h2>The YouTube Opportunity for {company}</h2>
  <p class="section-sub">YouTube is the largest, most underutilized growth channel in digital advertising. Brands are moving budget from linear TV and Meta to YouTube — but most don't have the creative, strategy, or measurement to do it well.</p>

  <div class="impact-grid">
    <div class="impact-stat"><div class="num">2.7B</div><div class="lbl">Monthly Active Users</div></div>
    <div class="impact-stat"><div class="num">#1</div><div class="lbl">Reach Among 18-49</div></div>
    <div class="impact-stat"><div class="num">70%</div><div class="lbl">CTV Watch Time Growth</div></div>
    <div class="impact-stat"><div class="num">150M+</div><div class="lbl">YouTube TV Viewers</div></div>
  </div>

  <!-- 3-Month YouTube Spend Chart — RT vs ACQ -->
  <div style="margin-top:32px">
    <h3 style="text-align:center;font-size:1rem;margin-bottom:4px">YouTube Spend Ramp — Retargeting vs Acquisition</h3>
    <p style="text-align:center;font-size:.75rem;color:var(--muted);margin-bottom:16px">Total YouTube: {_fmt_money(yt_m1 + yt_m2 + yt_m3)} over 3 months</p>
    <div class="spend-chart">
      {_yt_stacked(yt_m1_rt, yt_m1_acq, "MONTH 1")}
      {_yt_stacked(yt_m2_rt, yt_m2_acq, "MONTH 2")}
      {_yt_stacked(yt_m3_rt, yt_m3_acq, "MONTH 3")}
    </div>
    <div style="display:flex;justify-content:center;gap:24px;margin-top:32px">
      <div style="display:flex;align-items:center;gap:6px"><div style="width:14px;height:14px;border-radius:3px;background:#6CC4D4"></div><span style="font-size:.72rem;color:var(--muted)">Retargeting (RT)</span></div>
      <div style="display:flex;align-items:center;gap:6px"><div style="width:14px;height:14px;border-radius:3px;background:var(--teal)"></div><span style="font-size:.72rem;color:var(--muted)">Acquisition (ACQ)</span></div>
    </div>
  </div>

  {context}

  <!-- Full-Funnel YouTube -->
  <details class="collapsible" open style="margin-top:28px">
    <summary>Full-Funnel YouTube Coverage</summary>
    <div class="collapse-content">
    <div class="grid-4">
      <div class="card" style="border-top:4px solid var(--teal)">
        <div style="font-size:.68rem;font-weight:700;color:var(--teal);text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px">Awareness</div>
        <h3 style="font-size:.95rem">Video View Campaigns</h3>
        <ul style="list-style:none;padding:0;font-size:.8rem;color:#475467">
          <li style="padding:3px 0">Skippable in-stream + Shorts</li>
          <li style="padding:3px 0">CPVs &lt; $0.03 | CPMs &lt; $6</li>
          <li style="padding:3px 0">Podcast &amp; sports targeting</li>
        </ul>
      </div>
      <div class="card" style="border-top:4px solid var(--pink)">
        <div style="font-size:.68rem;font-weight:700;color:var(--pink);text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px">Consideration</div>
        <h3 style="font-size:.95rem">DemandGen / VAC</h3>
        <ul style="list-style:none;padding:0;font-size:.8rem;color:#475467">
          <li style="padding:3px 0">Retarget engaged viewers</li>
          <li style="padding:3px 0">Product feed integration</li>
          <li style="padding:3px 0">Companion banners + site-links</li>
        </ul>
      </div>
      <div class="card" style="border-top:4px solid var(--navy)">
        <div style="font-size:.68rem;font-weight:700;color:var(--navy);text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px">Conversion</div>
        <h3 style="font-size:.95rem">PMax + Search</h3>
        <ul style="list-style:none;padding:0;font-size:.8rem;color:#475467">
          <li style="padding:3px 0">Viewed-video remarketing</li>
          <li style="padding:3px 0">Maximize conversions bidding</li>
          <li style="padding:3px 0">Brand search capture</li>
        </ul>
      </div>
      <div class="card" style="border-top:4px solid var(--success)">
        <div style="font-size:.68rem;font-weight:700;color:var(--success);text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px">Loyalty</div>
        <h3 style="font-size:.95rem">Cross-Sell &amp; Upsell</h3>
        <ul style="list-style:none;padding:0;font-size:.8rem;color:#475467">
          <li style="padding:3px 0">Existing customer campaigns</li>
          <li style="padding:3px 0">Hero + Halo strategy</li>
          <li style="padding:3px 0">Email/SMS integration</li>
        </ul>
      </div>
    </div>
    </div>
  </details>

  <div class="grid-2" style="margin-top:20px">
    <div class="card">
      <h3>YouTube Projection for {company}</h3>
      <ul style="list-style:none;padding:0">
        <li style="padding:6px 0">&#x25b6; <strong>{_fmt_number(yt_views)}</strong> est. video views (Month 1)</li>
        <li style="padding:6px 0">&#x25b6; <strong>{_fmt_number(yt_clicks)}</strong> est. clicks at ${yt_cpc:.2f} CPC</li>
        <li style="padding:6px 0">&#x25b6; <strong>{_fmt_money(yt_budget_m1)}</strong>/mo YouTube allocation</li>
        <li style="padding:6px 0">&#x25b6; Every format: 16:9, 9:16, 6s bumper</li>
      </ul>
    </div>
    <div class="card">
      <h3>Google Deterministic Attribution</h3>
      <ul style="list-style:none;padding:0">
        <li style="padding:6px 0">&#x1f4ca; Cross-device, person-level attribution using signed-in Google users</li>
        <li style="padding:6px 0">&#x1f465; Not probabilistic. Not household. Actual people.</li>
        <li style="padding:6px 0">&#x1f50d; Geo-lift studies and holdout groups prove incremental impact</li>
        <li style="padding:6px 0">&#x1f4e1; Halo effect measurement on Search, Meta, and email</li>
      </ul>
    </div>
  </div>

  <p style="text-align:center;margin-top:20px;font-size:.82rem;color:var(--muted)">Surfaces: YouTube In-Stream &middot; Shorts &middot; YouTube TV &middot; Netflix, Prime Video, Disney+</p>
</div>"""


def _build_promo_calendar(company, report: DomainAdReport) -> str:
    # ── 3-month forward eCommerce holiday calendar ──
    today = date.today()
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    next_monday = today + timedelta(days=days_until_monday)

    # Gather 3 months of ecommerce events starting from next_monday
    start_month = next_monday.month
    start_year = next_monday.year
    months_data: list[tuple[int, int, list]] = []
    for i in range(3):
        m = start_month + i
        y = start_year
        if m > 12:
            m -= 12
            y += 1
        year_events = get_events_for_year(y)
        month_events = [(ev, d) for ev, d in year_events if d.month == m]
        months_data.append((y, m, month_events))

    # Category badge styling
    ECOM_CAT_COLORS = {
        "holiday": ("var(--pink)", "var(--pink-light)"),
        "sale": ("#DC2626", "#FEE2E2"),
        "seasonal": ("var(--teal)", "var(--teal-light)"),
        "cultural": ("#7C3AED", "#F3E8FF"),
    }

    month_cards = []
    for y, m, events in months_data:
        month_name = cal_mod.month_name[m]
        event_rows = []
        for ev, d in events:
            date_str = d.strftime("%b %d")
            cat = ev.category or "seasonal"
            cat_color, cat_bg = ECOM_CAT_COLORS.get(cat, ("var(--muted)", "var(--bg)"))
            badge = (
                f'<span style="font-size:.6rem;font-weight:700;text-transform:uppercase;'
                f'letter-spacing:.06em;padding:2px 6px;border-radius:4px;background:{cat_bg};'
                f'color:{cat_color}">{_esc(cat)}</span>'
            )
            event_rows.append(
                f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #f5f5f5">'
                f'<span style="font-size:.72rem;color:var(--muted);width:42px;flex-shrink:0">{date_str}</span>'
                f'<span style="font-size:.82rem;font-weight:600;color:var(--navy);flex:1">{_esc(ev.name)}</span>'
                f'{badge}'
                f'</div>'
            )
        if not event_rows:
            event_rows.append(
                '<div style="padding:6px 0;font-size:.82rem;color:var(--muted)">No major events this month</div>'
            )
        month_cards.append(
            f'<div class="card">'
            f'<h3 style="color:var(--navy);font-size:1rem;margin-bottom:12px">{month_name} {y}</h3>'
            f'{"".join(event_rows)}'
            f'</div>'
        )

    next_monday_str = next_monday.strftime("%B %d, %Y")
    calendar_grid = f'<div class="grid-3" style="margin-top:20px">{"".join(month_cards)}</div>'

    # ── Milled email data (conditional, collapsible) ──
    milled = report.milled_intel
    has_milled = milled and milled.found and milled.emails

    milled_section = ""
    synergy_card = ""
    bfcm_note = ""
    seasonal_summary = ""
    subtitle_extra = ""

    if has_milled:
        subtitle_extra = (
            f" We also analyzed {company}'s email marketing "
            f"({milled.emails_per_week}/wk cadence, {_fmt_number(milled.emails_last_12_months)} "
            f"emails in 12 months) to align streaming flights with your biggest promotional moments."
        )

        # Milled email month blocks
        email_months: dict[str, list] = {}
        for em in milled.emails:
            if em.date and len(em.date) >= 7:
                key = em.date[:7]
            else:
                continue
            email_months.setdefault(key, []).append(em)

        sorted_months = sorted(email_months.keys(), reverse=True)[:6]

        MILLED_CAT_COLORS = {
            "bfcm": ("var(--pink)", "var(--pink-light)"),
            "seasonal": ("var(--teal)", "var(--teal-light)"),
            "product_launch": ("#7C3AED", "#F3E8FF"),
            "sale": ("#DC2626", "#FEE2E2"),
            "newsletter": ("var(--muted)", "var(--bg)"),
        }
        MILLED_CAT_LABELS = {
            "bfcm": "BFCM",
            "seasonal": "Seasonal",
            "product_launch": "Launch",
            "sale": "Sale",
            "newsletter": "Newsletter",
        }

        month_blocks = []
        for mk in sorted_months:
            emails = email_months[mk]
            try:
                label = datetime.strptime(mk, "%Y-%m").strftime("%B %Y")
            except ValueError:
                label = mk

            rows = []
            for em in emails[:8]:
                d = em.date[5:] if em.date and len(em.date) >= 10 else em.date
                cat = em.category or "newsletter"
                cat_color, cat_bg = MILLED_CAT_COLORS.get(cat, ("var(--muted)", "var(--bg)"))
                cat_label = MILLED_CAT_LABELS.get(cat, cat)
                badge = f'<span style="font-size:.6rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;padding:2px 6px;border-radius:4px;background:{cat_bg};color:{cat_color}">{cat_label}</span>'
                rows.append(f'<div class="cal-row"><span class="cal-date">{_esc(d)}</span><span class="cal-subj">{_esc(em.subject)} {badge}</span></div>')

            overflow = ""
            if len(emails) > 8:
                overflow = f'<div class="cal-row"><span class="cal-date"></span><span class="cal-subj" style="color:var(--muted)">+ {len(emails) - 8} more</span></div>'

            month_blocks.append(f'<div class="cal-month"><h4>{label}</h4>{"".join(rows)}{overflow}</div>')

        # Seasonal analysis summary
        cats = milled.promo_categories
        if cats:
            parts = []
            if cats.get("bfcm", 0):
                parts.append(f"<strong>{cats['bfcm']}</strong> BFCM")
            if cats.get("seasonal", 0):
                parts.append(f"<strong>{cats['seasonal']}</strong> seasonal")
            if cats.get("sale", 0):
                parts.append(f"<strong>{cats['sale']}</strong> sale")
            if cats.get("product_launch", 0):
                parts.append(f"<strong>{cats['product_launch']}</strong> product launch")
            if parts:
                seasonal_summary = f'<p style="font-size:.85rem;color:#475467;margin-top:8px">We classified: {", ".join(parts)} emails in recent history.</p>'

        synergy_card = """<div class="card" style="margin-top:16px;background:var(--teal-light);border-color:var(--teal)">
    <h3 style="color:var(--teal)">&#x1f4e1; Streaming + Email Synergy</h3>
    <p>We recommend scheduling CTV and YouTube flight increases 3-5 days before your major promotional emails to prime audiences. TV exposure before the email hits increases open rates and purchase intent.</p>
  </div>"""

        if milled.has_bfcm:
            bfcm_note = f"""<div class="card" style="margin-top:16px;background:var(--pink-light);border-color:var(--pink)">
      <h3 style="color:var(--pink)">&#x1f381; BFCM Campaign Opportunity</h3>
      <p>{company} runs BFCM promotions. We recommend launching CTV flights 2 weeks before Black Friday to build awareness. TV-primed audiences convert at higher rates when they see the email or SMS drop.</p>
    </div>"""

        milled_section = f"""<details class="collapsible" style="margin-top:16px">
    <summary>View full email calendar ({_fmt_number(milled.emails_last_12_months)} emails analyzed)</summary>
    <div class="collapse-content">
      <div class="grid-2">
        <div>{"".join(month_blocks[:3])}</div>
        <div>{"".join(month_blocks[3:])}</div>
      </div>
    </div>
  </details>"""

    return f"""<div class="section alt">
  <h2>Your Promotional Calendar</h2>
  <p class="section-sub">Key eCommerce events aligned with your campaign timeline, starting {next_monday_str}.{subtitle_extra}</p>
  {calendar_grid}
  {seasonal_summary}
  {synergy_card}
  {bfcm_note}
  {milled_section}
</div>"""


def _build_competitive_landscape(company, intel: BrandIntelligence | None) -> str:
    """Build competitive landscape section showing competitor CTV/YouTube presence."""
    if not intel or not intel.competitors:
        return ""

    rows = []
    for comp in intel.competitors:
        on_ctv = comp in intel.competitors_on_ctv
        on_yt = comp in intel.competitors_on_youtube
        ctv_badge = '<span style="color:var(--success);font-weight:700">&#x2713; Active</span>' if on_ctv else '<span style="color:var(--muted)">&#x2717; Not found</span>'
        yt_badge = '<span style="color:var(--success);font-weight:700">&#x2713; Active</span>' if on_yt else '<span style="color:var(--muted)">&#x2717; Not found</span>'
        rows.append(f"""<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;padding:12px 0;border-bottom:1px solid #f0f0f0;align-items:center">
      <span style="font-weight:600;font-size:.9rem">{_esc(comp)}</span>
      <span style="font-size:.85rem">{ctv_badge}</span>
      <span style="font-size:.85rem">{yt_badge}</span>
    </div>""")

    # Build the insight message
    comp_on_ctv = len(intel.competitors_on_ctv)
    comp_on_yt = len(intel.competitors_on_youtube)
    total_comp = len(intel.competitors)

    if comp_on_ctv > 0 or comp_on_yt > 0:
        insight = f"""<div class="card" style="margin-top:20px;background:var(--pink-light);border-color:var(--pink)">
      <h3 style="color:var(--pink)">&#x26a0; Competitors Are Already There</h3>
      <p>{comp_on_ctv} of {total_comp} competitors detected on streaming TV and {comp_on_yt} on YouTube. Your competitors are capturing share of voice on the biggest screen in the house. Every day you wait, they're building frequency and brand recognition with your potential customers.</p>
    </div>"""
    else:
        insight = f"""<div class="card" style="margin-top:20px;background:var(--teal-light);border-color:var(--teal)">
      <h3 style="color:var(--teal)">&#x1f3c6; First-Mover Advantage</h3>
      <p>None of the {total_comp} competitors we checked are running streaming TV or YouTube ads. {company} has a window to own share of voice before they get there. Early movers typically see lower CPMs and stronger brand lift before the category gets crowded.</p>
    </div>"""

    return f"""<div class="section">
  <h2>Competitive Landscape</h2>
  <p class="section-sub">We checked {company}'s closest competitors for streaming TV and YouTube ad presence.</p>
  <div style="background:white;border:1px solid var(--border);border-radius:20px;padding:24px">
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;padding-bottom:8px;border-bottom:2px solid var(--navy)">
      <span style="font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)">Competitor</span>
      <span style="font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)">Streaming TV (iSpot)</span>
      <span style="font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)">YouTube Ads</span>
    </div>
    {"".join(rows)}
  </div>
  {insight}
</div>"""


def _build_proven_results(company, industry) -> str:
    cases = _match_case_studies(industry)

    cards = []
    for cs in cases:
        stats_html = "".join(
            f'<div class="case-stat"><div class="val">{_esc(val)}</div><div class="lbl">{_esc(lbl)}</div></div>'
            for val, lbl in cs["stats"]
        )
        url = cs.get("url", "")
        link_html = f'<a href="{_esc(url)}" target="_blank" style="display:inline-block;margin-top:12px;font-size:.78rem;font-weight:600;color:var(--pink);text-decoration:none">Read case study &rarr;</a>' if url else ""
        cards.append(f"""<div class="case-card">
  <div class="case-name">{_esc(cs['name'])}</div>
  <div class="case-vertical">{_esc(cs['vertical'])}</div>
  <div class="case-stats">{stats_html}</div>
  <div class="case-quote">{_esc(cs['quote'])}</div>
  {link_html}
</div>""")

    # Creative velocity proof point
    velocity_note = (
        '<p style="text-align:center;margin-top:24px;font-size:.88rem;color:var(--muted);max-width:720px;margin-left:auto;margin-right:auto">'
        '<strong style="color:var(--navy)">The pattern is unmistakable:</strong> '
        'every Upscale case study leads with creative volume — 80+ (Newton), 53 (fatty15), '
        '45 (Lalo), 30+ (Canopy), 8 (Branch). Creative velocity IS the performance lever.</p>'
    )

    return f"""<div class="section">
  <h2>Proven Results</h2>
  <p class="section-sub">Real eCommerce brands achieving measurable streaming TV performance with Upscale.</p>
  <div class="grid-3">{"".join(cards)}</div>
  {velocity_note}
</div>"""


def _build_roi_projection(
    company: str, budget: dict, monthly_rev: float | None,
    intel: BrandIntelligence | None, strategy: dict, has_shopify: bool,
    enrichment=None,
) -> str:
    """Build ROI projection waterfall: Media Spend → Impressions → Visits → Conversions → Revenue."""
    total_spend = budget["m1"] + budget["m2"] + budget["m3"]
    tier = strategy["tier"]

    # --- AOV from enrichment data or industry estimate ---
    aov = 85.0  # default DTC AOV
    if enrichment and enrichment.avg_product_price:
        try:
            aov = float(str(enrichment.avg_product_price).replace("$", "").replace(",", ""))
        except (ValueError, TypeError):
            pass

    # --- CPM / cost-per-visit / CPA assumptions by tier ---
    # CPM: $8-$15 range.  Visit: $0.75-$1.75.  CPA: 70-80% of AOV.  ROAS: 2.2x-8.5x.
    if tier == "youtube_only":
        blended_cpm = 8.50
        cost_per_visit = 0.85
        cpa_pct = 0.72   # CPA as % of AOV
        channel_note = "YouTube in-stream, Shorts, and DemandGen"
    elif tier == "ctv_led":
        blended_cpm = 12.00
        cost_per_visit = 1.25
        cpa_pct = 0.75
        channel_note = "CTV retargeting + acquisition, YouTube support"
    else:  # full_funnel
        blended_cpm = 14.50
        cost_per_visit = 1.60
        cpa_pct = 0.78
        channel_note = "CTV acquisition-led, YouTube mid-funnel, retargeting base"

    # --- Waterfall math (work backward from target CPA / cost-per-visit) ---
    impressions = int(total_spend / blended_cpm * 1000)
    visits = int(total_spend / cost_per_visit)
    cpa = round(aov * cpa_pct, 2)
    conversions = int(total_spend / cpa) if cpa > 0 else 0

    # LTV multiplier for subscription/high-repurchase
    from models.ad_models import PurchaseModel
    ltv_multiplier = 1.0
    ltv_note = ""
    if intel and intel.purchase_model == PurchaseModel.SUBSCRIPTION:
        ltv_multiplier = 3.0
        ltv_note = "3x LTV multiplier for subscription model"
    elif intel and intel.purchase_model == PurchaseModel.HIGH_REPURCHASE:
        ltv_multiplier = 2.0
        ltv_note = "2x LTV multiplier for high-repurchase model"

    incremental_revenue = int(conversions * aov * ltv_multiplier)
    roas = round(incremental_revenue / max(total_spend, 1), 2)

    # Clamp ROAS to 2.2x-8.5x range
    if roas < 2.2:
        roas = 2.2
        incremental_revenue = int(total_spend * roas)
        conversions = int(incremental_revenue / (aov * ltv_multiplier)) if aov > 0 else 0
        cpa = round(total_spend / max(conversions, 1), 2)
    elif roas > 8.5:
        roas = 8.5
        incremental_revenue = int(total_spend * roas)
        conversions = int(incremental_revenue / (aov * ltv_multiplier)) if aov > 0 else 0
        cpa = round(total_spend / max(conversions, 1), 2)

    # Recalculate cost_per_visit from actuals
    cost_per_visit = round(total_spend / max(visits, 1), 2)

    # Revenue payback
    payback_note = ""
    if monthly_rev and incremental_revenue > 0:
        payback_pct = round(incremental_revenue / (monthly_rev * 3) * 100, 1)
        payback_note = f"Projected to add ~{payback_pct}% incremental revenue over the 3-month flight."

    # LTV badge
    ltv_badge = ""
    if ltv_note:
        ltv_badge = f'<div style="margin-top:8px;padding:8px 14px;background:var(--success-light);border-radius:8px;font-size:.78rem;color:var(--success);font-weight:600">&#x1f504; {ltv_note} — true ROI is even higher when factoring repeat purchases</div>'

    # Confidence range (keep within 2.2x-8.5x bounds)
    roas_low = max(round(roas * 0.7, 1), 2.2)
    roas_high = min(round(roas * 1.4, 1), 8.5)

    return f"""<div class="section alt" id="s-roi">
  <h2>Projected ROI for {company}</h2>
  <p class="section-sub">A data-driven model based on {company}'s revenue, price point, and recommended channel mix. These are conservative estimates — actual performance optimizes upward over 90 days.</p>

  <!-- Waterfall -->
  <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:28px">
    <div style="text-align:center;padding:20px 12px;background:white;border:1px solid var(--border);border-radius:12px">
      <div style="font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-bottom:6px">Media Spend</div>
      <div style="font-size:1.6rem;font-weight:800;color:var(--navy)">{_fmt_money(total_spend)}</div>
      <div style="font-size:.72rem;color:var(--muted)">3-month flight</div>
    </div>
    <div style="text-align:center;padding:20px 12px;background:white;border:1px solid var(--border);border-radius:12px;position:relative">
      <div style="position:absolute;left:-16px;top:50%;transform:translateY(-50%);font-size:1.2rem;color:var(--muted)">&rarr;</div>
      <div style="font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-bottom:6px">Impressions</div>
      <div style="font-size:1.6rem;font-weight:800;color:var(--navy)">{_fmt_number(impressions)}</div>
      <div style="font-size:.72rem;color:var(--muted)">${blended_cpm:.0f} blended CPM</div>
    </div>
    <div style="text-align:center;padding:20px 12px;background:white;border:1px solid var(--border);border-radius:12px;position:relative">
      <div style="position:absolute;left:-16px;top:50%;transform:translateY(-50%);font-size:1.2rem;color:var(--muted)">&rarr;</div>
      <div style="font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-bottom:6px">Site Visits</div>
      <div style="font-size:1.6rem;font-weight:800;color:var(--teal)">{_fmt_number(visits)}</div>
      <div style="font-size:.72rem;color:var(--muted)">${cost_per_visit:.2f} per visit</div>
    </div>
    <div style="text-align:center;padding:20px 12px;background:white;border:1px solid var(--border);border-radius:12px;position:relative">
      <div style="position:absolute;left:-16px;top:50%;transform:translateY(-50%);font-size:1.2rem;color:var(--muted)">&rarr;</div>
      <div style="font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-bottom:6px">Conversions</div>
      <div style="font-size:1.6rem;font-weight:800;color:var(--pink)">{_fmt_number(conversions)}</div>
      <div style="font-size:.72rem;color:var(--muted)">${cpa:.0f} CPA</div>
    </div>
    <div style="text-align:center;padding:20px 12px;background:var(--success-light);border:2px solid var(--success);border-radius:12px;position:relative">
      <div style="position:absolute;left:-16px;top:50%;transform:translateY(-50%);font-size:1.2rem;color:var(--muted)">&rarr;</div>
      <div style="font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;color:var(--success);margin-bottom:6px">Est. Revenue</div>
      <div style="font-size:1.6rem;font-weight:800;color:var(--success)">{_fmt_money(incremental_revenue)}</div>
      <div style="font-size:.72rem;color:var(--success)">{roas}x projected ROAS</div>
    </div>
  </div>

  {ltv_badge}

  <!-- Key metrics + assumptions -->
  <div class="grid-2" style="margin-top:20px">
    <div class="card">
      <h3>Key Projections</h3>
      <ul style="list-style:none;padding:0">
        <li style="padding:8px 0;border-bottom:1px solid var(--border);display:flex;justify-content:space-between">
          <span style="font-size:.88rem;color:#475467">Projected ROAS Range</span>
          <strong style="color:var(--success)">{roas_low}x — {roas_high}x</strong>
        </li>
        <li style="padding:8px 0;border-bottom:1px solid var(--border);display:flex;justify-content:space-between">
          <span style="font-size:.88rem;color:#475467">Cost Per Site Visit</span>
          <strong>${cost_per_visit:.2f}</strong>
        </li>
        <li style="padding:8px 0;border-bottom:1px solid var(--border);display:flex;justify-content:space-between">
          <span style="font-size:.88rem;color:#475467">Cost Per Acquisition</span>
          <strong>${cpa:.0f}</strong>
        </li>
        <li style="padding:8px 0;border-bottom:1px solid var(--border);display:flex;justify-content:space-between">
          <span style="font-size:.88rem;color:#475467">Est. Incremental Orders</span>
          <strong>{_fmt_number(conversions)}</strong>
        </li>
        <li style="padding:8px 0;display:flex;justify-content:space-between">
          <span style="font-size:.88rem;color:#475467">AOV Used</span>
          <strong>${aov:.0f}</strong>
        </li>
      </ul>
    </div>
    <div class="card">
      <h3>Model Assumptions</h3>
      <ul style="list-style:none;padding:0;font-size:.85rem;color:#475467">
        <li style="padding:6px 0">&#x1f4ca; Channel mix: {channel_note}</li>
        <li style="padding:6px 0">&#x1f4b0; Blended CPM: ${blended_cpm:.0f} (market benchmark)</li>
        <li style="padding:6px 0">&#x1f310; Cost per visit: ${cost_per_visit:.2f} (IP-attributed + click-through)</li>
        <li style="padding:6px 0">&#x1f6d2; CPA target: {int(cpa_pct * 100)}% of AOV (conservative DTC benchmark)</li>
        <li style="padding:6px 0">&#x2197; Performance typically improves 20-40% from Month 1 to Month 3 as ML optimizes</li>
        <li style="padding:6px 0">&#x26a0; These projections exclude halo effects on branded search, Meta, and email — which typically add 15-25% incremental lift</li>
      </ul>
      {"<p style='font-size:.82rem;color:var(--success);font-weight:600;margin-top:10px'>" + payback_note + "</p>" if payback_note else ""}
    </div>
  </div>
</div>"""


def _build_audience_strategy(
    company: str, report: DomainAdReport,
    intel: BrandIntelligence | None, strategy: dict,
    has_shopify: bool, has_klaviyo: bool,
) -> str:
    """Build personalized audience targeting strategy based on brand data."""
    e = report.enrichment
    tier = strategy["tier"]

    # --- Determine audience segments based on brand data ---
    industry = (e.industry or "").lower() if e else ""
    desc = (e.description or "").lower() if e else ""

    # Contextual targeting categories based on industry
    contextual_categories = []
    if any(w in industry or w in desc for w in ["beauty", "skincare", "cosmetic"]):
        contextual_categories = ["Beauty & Personal Care", "Fashion & Style", "Health & Wellness", "Lifestyle Content"]
    elif any(w in industry or w in desc for w in ["supplement", "vitamin", "health", "wellness", "fitness"]):
        contextual_categories = ["Health & Fitness", "Nutrition & Wellness", "Sports & Outdoors", "Self-Improvement"]
    elif any(w in industry or w in desc for w in ["baby", "kids", "children", "parenting"]):
        contextual_categories = ["Parenting & Family", "Home & Living", "Health & Wellness", "Education"]
    elif any(w in industry or w in desc for w in ["pet", "dog", "cat"]):
        contextual_categories = ["Pet Care & Animals", "Home & Garden", "Outdoor & Nature", "Family Content"]
    elif any(w in industry or w in desc for w in ["food", "beverage", "snack", "drink"]):
        contextual_categories = ["Food & Cooking", "Health & Nutrition", "Lifestyle", "Entertainment"]
    elif any(w in industry or w in desc for w in ["fashion", "apparel", "clothing"]):
        contextual_categories = ["Fashion & Style", "Entertainment & Pop Culture", "Lifestyle", "Shopping"]
    elif any(w in industry or w in desc for w in ["furniture", "home", "decor"]):
        contextual_categories = ["Home & Interior Design", "Real Estate", "Lifestyle", "DIY & Renovation"]
    elif any(w in industry or w in desc for w in ["tech", "electronic", "gadget"]):
        contextual_categories = ["Technology", "Gaming", "Productivity", "Science & Innovation"]
    else:
        contextual_categories = ["Lifestyle & Entertainment", "Shopping & Retail", "News & Current Events", "Content aligned to your category"]

    # In-market audiences
    in_market = []
    if any(w in industry for w in ["beauty", "skincare"]):
        in_market = ["Beauty Products", "Skin Care", "Personal Care", "Health & Beauty Subscriptions"]
    elif any(w in industry for w in ["supplement", "vitamin", "health"]):
        in_market = ["Vitamins & Supplements", "Health Products", "Fitness Equipment", "Wellness Services"]
    elif any(w in industry for w in ["baby", "kids"]):
        in_market = ["Baby & Children's Products", "Maternity Products", "Nursery Furniture", "Kids' Clothing"]
    elif any(w in industry for w in ["food", "beverage"]):
        in_market = ["Specialty Food & Beverages", "Meal Kits", "Organic Products", "Snack Subscriptions"]
    elif any(w in industry for w in ["fashion", "apparel"]):
        in_market = ["Women's Apparel", "Men's Apparel", "Shoes & Accessories", "Luxury Goods"]
    elif any(w in industry for w in ["furniture", "home"]):
        in_market = ["Home Furnishings", "Home Decor", "Bedding & Bath", "Kitchen & Dining"]
    else:
        in_market = ["Online Shopping Enthusiasts", "DTC Brand Buyers", "Subscription Shoppers", "Premium Product Seekers"]

    # Demographics
    demo_text = "Adults 25-54, HHI $75K+"
    if e and e.avg_product_price:
        try:
            price = float(str(e.avg_product_price).replace("$", "").replace(",", ""))
            if price > 200:
                demo_text = "Adults 28-55, HHI $100K+ (premium price point)"
            elif price > 100:
                demo_text = "Adults 25-54, HHI $75K+ (mid-premium)"
            else:
                demo_text = "Adults 22-45, HHI $50K+ (accessible price point)"
        except (ValueError, TypeError):
            pass

    # Location
    geo_text = "National"
    if e and e.city and e.state:
        geo_text = f"National with DMA weighting toward {e.city}, {e.state} + top ecommerce DMAs"

    # Build 1P data card
    first_party_items = []
    if has_shopify:
        first_party_items.extend([
            "Shopify customer list &rarr; suppression + lookalike seed",
            "Purchase history &rarr; high-LTV audience modeling",
            "Cart abandoners &rarr; retargeting audience",
        ])
    if has_klaviyo:
        first_party_items.extend([
            "Klaviyo segments &rarr; email subscriber retargeting",
            "Engaged non-purchasers &rarr; mid-funnel nurture",
        ])
    if not first_party_items:
        first_party_items = [
            "Site visitors &rarr; retargeting pool (pixel-based)",
            "Converters &rarr; suppression + lookalike seed",
            "Email subscribers &rarr; CRM match for retargeting",
        ]

    first_party_html = "".join(
        f'<li style="padding:5px 0;font-size:.85rem">{item}</li>' for item in first_party_items
    )
    contextual_html = "".join(
        f'<span style="display:inline-block;padding:5px 14px;background:var(--teal-light);color:var(--teal);border-radius:6px;font-size:.8rem;font-weight:500;margin:3px 4px">{c}</span>'
        for c in contextual_categories
    )
    in_market_html = "".join(
        f'<span style="display:inline-block;padding:5px 14px;background:var(--pink-light);color:var(--pink);border-radius:6px;font-size:.8rem;font-weight:500;margin:3px 4px">{c}</span>'
        for c in in_market
    )

    # Daypart recommendation
    if tier == "youtube_only":
        daypart = "Primetime (7-11pm) + Lunchtime (11am-1pm) for peak YouTube engagement. Weekend mornings for lifestyle content."
    else:
        daypart = "CTV Primetime (7-11pm) for co-viewing on the big screen. YouTube mid-day (11am-2pm) + late evening (9pm-12am) for personal device engagement."

    return f"""<div class="section">
  <h2>Audience Strategy for {company}</h2>
  <p class="section-sub">A layered targeting approach built from {company}'s customer data, category signals, and platform intelligence — not generic demo targeting.</p>

  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:24px">
    <div style="text-align:center;padding:20px;background:var(--teal-light);border-radius:12px">
      <div style="font-size:2rem;margin-bottom:4px">&#x1f3af;</div>
      <div style="font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:var(--teal);font-weight:700">Core Demo</div>
      <div style="font-size:.92rem;font-weight:600;margin-top:4px">{demo_text}</div>
    </div>
    <div style="text-align:center;padding:20px;background:var(--pink-light);border-radius:12px">
      <div style="font-size:2rem;margin-bottom:4px">&#x1f4cd;</div>
      <div style="font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:var(--pink);font-weight:700">Geography</div>
      <div style="font-size:.92rem;font-weight:600;margin-top:4px">{geo_text}</div>
    </div>
    <div style="text-align:center;padding:20px;background:var(--success-light);border-radius:12px">
      <div style="font-size:2rem;margin-bottom:4px">&#x23f0;</div>
      <div style="font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:var(--success);font-weight:700">Dayparting</div>
      <div style="font-size:.92rem;font-weight:600;margin-top:4px">Primetime + Mid-Day</div>
    </div>
  </div>

  <div class="grid-2">
    <div class="card">
      <h3 style="display:flex;align-items:center;gap:8px"><span style="font-size:1.2rem">&#x1f512;</span> First-Party Data Activation</h3>
      <p style="font-size:.82rem;color:var(--muted);margin-bottom:10px">Your own customer data powers the most efficient targeting layers.</p>
      <ul style="list-style:none;padding:0">{first_party_html}</ul>
    </div>
    <div class="card">
      <h3 style="display:flex;align-items:center;gap:8px"><span style="font-size:1.2rem">&#x1f50d;</span> In-Market Audiences</h3>
      <p style="font-size:.82rem;color:var(--muted);margin-bottom:10px">People actively researching and buying in your category right now.</p>
      <div style="display:flex;flex-wrap:wrap;gap:2px">{in_market_html}</div>
    </div>
  </div>

  <div class="grid-2" style="margin-top:16px">
    <div class="card">
      <h3 style="display:flex;align-items:center;gap:8px"><span style="font-size:1.2rem">&#x1f4fa;</span> Contextual Targeting</h3>
      <p style="font-size:.82rem;color:var(--muted);margin-bottom:10px">Content categories where your ideal customer spends their time.</p>
      <div style="display:flex;flex-wrap:wrap;gap:2px">{contextual_html}</div>
    </div>
    <div class="card">
      <h3 style="display:flex;align-items:center;gap:8px"><span style="font-size:1.2rem">&#x23f0;</span> Daypart Strategy</h3>
      <p style="font-size:.85rem;color:#475467;line-height:1.6">{daypart}</p>
      <p style="font-size:.82rem;color:var(--muted);margin-top:10px">ML continuously optimizes daypart weights based on live conversion data — shifting spend to your brand's peak performance windows.</p>
    </div>
  </div>
</div>"""


def _build_objection_killer(company: str, report: DomainAdReport, budget: dict, strategy: dict) -> str:
    """Build myth vs. reality objection-handling section."""
    mix = report.channel_mix
    m1 = budget["m1"]
    tier = strategy["tier"]

    # Customize based on what the brand is already doing
    channel_label = "Streaming TV"
    if tier == "youtube_only":
        channel_label = "YouTube at Scale"

    # Dynamic objection content
    objections = []

    # Objection 1: Measurement — always include
    objections.append({
        "myth": "You can't measure streaming TV like Meta or Google",
        "reality": "Upscale's 4-layer attribution (IP matching, household graph, Google deterministic IDs, incrementality testing) gives you cost-per-visit, CPA, and ROAS — the same metrics you track on every other channel. 20% holdout testing proves true incrementality.",
        "icon": "&#x1f4ca;",
    })

    # Objection 2: Budget — always include
    objections.append({
        "myth": f"Our budget ({_fmt_money(m1)}/mo) is too small for TV",
        "reality": f"Streaming TV starts at $10K/month — no upfronts, no long-term commitments. {company}'s recommended {_fmt_money(m1)}/mo is well within the performance range. Scale up only when ROAS proves out.",
        "icon": "&#x1f4b0;",
    })

    # Objection 3: Creative — always include
    objections.append({
        "myth": "TV creative costs $50K+ and takes months",
        "reality": "Upscale produces TV-ready creative in 6 days at $500/spot using AI-assisted production. Your existing social video, UGC, and product content can be reformatted into CTV and YouTube creative — no new shoot required.",
        "icon": "&#x1f3ac;",
    })

    # Objection 4: Conditional based on brand situation
    if mix.has_youtube and tier != "youtube_only":
        objections.append({
            "myth": "We already do YouTube — why add CTV?",
            "reality": "CTV reaches 30-40% of audiences your YouTube ads don't — cord-cutters watching on Hulu, Peacock, and Roku. Plus, CTV exposure lifts YouTube ad performance by 18-25%. One platform manages both channels with unified measurement.",
            "icon": "&#x1f4fa;",
        })
    elif mix.has_meta and not mix.has_youtube:
        objections.append({
            "myth": "Meta already handles our video — why add streaming?",
            "reality": "Social video is 6-second, sound-off, thumb-scroll. Streaming is 15-30 seconds, full-screen, sound-on, and 95% completion rate. They reach fundamentally different audiences in fundamentally different mindsets. Together they drive 25%+ lift over social alone.",
            "icon": "&#x1f4f1;",
        })
    else:
        objections.append({
            "myth": "Our team doesn't have bandwidth for another channel",
            "reality": "Upscale handles everything — strategy, creative, media buying, optimization, and reporting. Your team approves creative briefs and reviews weekly performance reports. Total time commitment: ~1 hour per week.",
            "icon": "&#x23f0;",
        })

    rows = []
    for obj in objections:
        rows.append(f"""<div style="display:grid;grid-template-columns:1fr 1fr;gap:0;margin-bottom:16px;border-radius:12px;overflow:hidden;border:1px solid var(--border)">
      <div style="padding:20px 24px;background:#FEF3F2">
        <div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:#B42318;font-weight:700;margin-bottom:8px">{obj['icon']} The Myth</div>
        <p style="font-size:.92rem;color:#B42318;font-weight:600;line-height:1.5">"{obj['myth']}"</p>
      </div>
      <div style="padding:20px 24px;background:var(--success-light)">
        <div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:var(--success);font-weight:700;margin-bottom:8px">&#x2713; The Reality</div>
        <p style="font-size:.88rem;color:#344054;line-height:1.6">{obj['reality']}</p>
      </div>
    </div>""")

    return f"""<div class="section" id="s-myths">
  <h2>Myth vs. Reality: {channel_label}</h2>
  <p class="section-sub">The most common objections we hear from DTC brands — and the data that disproves them.</p>
  {"".join(rows)}
</div>"""


def _build_why_upscale() -> str:
    from data.competitive_intel import COMPETITIVE_MATRIX

    wins = [
        ("In-House Creative Team", "4-12 net new brand-matched ads per month — brief-based, built from your brand guide and product assets. No outsourcing, no templates, no AI slop. No other CTV platform offers this."),
        ("Creative System, Not a Bottleneck", "Always-on creative engine producing continuous performance variations. Data from every campaign feeds the next creative cycle. The flywheel gets smarter with every iteration."),
        ("Native eCommerce Integrations", "Direct Shopify + Klaviyo integration — first-party purchase data feeds targeting, attribution, and audience suppression. Built for commerce, not retrofitted."),
        ("CTV + YouTube Unified", "Streaming TV + YouTube in one platform — no separate vendor, no fragmented measurement. One system covering In-Stream, Shorts, YouTube TV, and 150+ streaming apps."),
        ("Measurement That Proves It", "IP-based attribution, incrementality testing, and SKU-level insight are native — not a third-party add-on. Lag-aware approach, not simplistic last-click."),
        ("Speed to Market", "Live in 2 weeks — not 6-7 weeks. From brief to first ad in 6 days. Repurpose your existing creative assets into TV-ready formats without a new shoot."),
    ]

    items_html = "".join(
        f"""<div class="win-item">
  <span class="win-check">&#x2713;</span>
  <div><h4>{title}</h4><p>{desc}</p></div>
</div>"""
        for title, desc in wins
    )

    # Build competitive matrix table — highlight Upscale's unique advantages
    matrix = COMPETITIVE_MATRIX
    # Only show features where Upscale has ✓ and most others don't
    highlight_features = [
        "In-house creative team",
        "4-12 net new ads/month",
        "Brand-matched (reads brand guide)",
        "eCommerce / DTC specialization",
        "YouTube in same operating model",
        "Bundled pricing (creative + media + measurement)",
    ]
    platform_order = ["Upscale", "Vibe", "MNTN", "tvScientific", "Tatari", "Universal Ads"]

    header_cells = "".join(
        f'<th style="font-size:.68rem;font-weight:700;padding:8px 6px;text-align:center;'
        f'{"background:var(--pink);color:white;border-radius:6px 6px 0 0" if p == "Upscale" else "color:var(--muted)"}'
        f'">{p}</th>'
        for p in platform_order
    )

    matrix_rows = ""
    for feat in highlight_features:
        if feat not in matrix["features"]:
            continue
        idx = matrix["features"].index(feat)
        cells = ""
        for p in platform_order:
            val = matrix["platforms"][p][idx]
            if val == "\u2713":
                style = "color:var(--success);font-weight:800" if p != "Upscale" else "color:white;font-weight:800;background:var(--pink)"
                display = "\u2713"
            elif val == "~":
                style = "color:#F59E0B;font-weight:600"
                display = "~"
            else:
                style = "color:#D0D5DD"
                display = "\u2717"
            cells += f'<td style="text-align:center;padding:8px 6px;font-size:.85rem;{style}">{display}</td>'
        matrix_rows += f'<tr><td style="font-size:.78rem;padding:8px 10px;font-weight:500;color:var(--navy);white-space:nowrap">{feat}</td>{cells}</tr>'

    matrix_html = f"""
  <div style="margin-top:36px;overflow-x:auto">
    <h3 style="color:rgba(255,255,255,.9);font-size:1rem;margin-bottom:12px;text-align:center">How Upscale Compares</h3>
    <table style="width:100%;border-collapse:collapse;background:rgba(255,255,255,.06);border-radius:12px;overflow:hidden">
      <thead><tr><th style="padding:8px 10px"></th>{header_cells}</tr></thead>
      <tbody style="color:rgba(255,255,255,.85)">{matrix_rows}</tbody>
    </table>
    <p style="text-align:center;margin-top:12px;font-size:.75rem;color:rgba(255,255,255,.5)">
      \u2713 = Yes/Strong &nbsp;&middot;&nbsp; ~ = Partial &nbsp;&middot;&nbsp; \u2717 = Not offered
    </p>
  </div>"""

    return f"""<div class="section dark">
  <h2 style="color:white">Why Upscale Wins</h2>
  <p class="section-sub">What separates Upscale from traditional CTV vendors and generic media buying platforms.</p>
  <div class="win-grid">{items_html}</div>
  {matrix_html}
</div>"""


def _build_inventory() -> str:
    partners = [
        ("Hulu", "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Hulu_Logo.svg/440px-Hulu_Logo.svg.png"),
        ("Peacock", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/NBCUniversal_Peacock_Logo.svg/440px-NBCUniversal_Peacock_Logo.svg.png"),
        ("Paramount+", "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Paramount_Plus.svg/440px-Paramount_Plus.svg.png"),
        ("Max", "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Max_logo.svg/440px-Max_logo.svg.png"),
        ("Netflix", "https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Netflix_2015_logo.svg/440px-Netflix_2015_logo.svg.png"),
        ("Discovery+", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Discovery_Plus_logo.svg/440px-Discovery_Plus_logo.svg.png"),
        ("Tubi", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Tubi_logo_%282023%29.svg/440px-Tubi_logo_%282023%29.svg.png"),
        ("Pluto TV", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/Pluto_tv_logo_2020.svg/440px-Pluto_tv_logo_2020.svg.png"),
        ("Samsung TV+", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Samsung_Logo.svg/440px-Samsung_Logo.svg.png"),
        ("LG Channels", "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/LG_logo_%282015%29.svg/440px-LG_logo_%282015%29.svg.png"),
        ("Roku", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Roku_logo.svg/440px-Roku_logo.svg.png"),
        ("Sling TV", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Sling_TV_logo.svg/440px-Sling_TV_logo.svg.png"),
        ("Fubo", "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/FuboTV_logo.svg/440px-FuboTV_logo.svg.png"),
        ("Fox Nation", "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Fox_News_Channel_logo.svg/440px-Fox_News_Channel_logo.svg.png"),
        ("YouTube", "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/YouTube_Logo_2017.svg/440px-YouTube_Logo_2017.svg.png"),
    ]
    cards = "".join(
        f'<div class="logo-pill" style="display:flex;align-items:center;justify-content:center;min-width:130px;min-height:56px;padding:10px 16px">'
        f'<img src="{url}" alt="{name}" style="max-height:32px;max-width:110px;object-fit:contain" loading="lazy">'
        f'</div>'
        for name, url in partners
    )

    return f"""<div class="section alt">
  <h2>Premium Streaming Inventory</h2>
  <p class="section-sub">Access 150+ streaming apps and channels through our programmatic partnerships — including YouTube natively.</p>
  <div class="logo-grid">{cards}</div>
</div>"""


def _build_transparency() -> str:
    return """<div class="section">
  <h2>Complete Transparency</h2>
  <p class="section-sub">No hidden margins, no surprise fees. Everything you need is bundled in one clear price.</p>
  <div class="transparency-grid">
    <div class="transparency-item" style="background:var(--success-light)">
      <div style="font-size:2.4rem;font-weight:900;color:var(--success)">&#x2713;</div>
      <h4>Bundled Pricing</h4>
      <p>In-house creative production, media buying, measurement, and attribution bundled into clear plan tiers. No vendor handoffs, no hidden margins, no surprise fees.</p>
    </div>
    <div class="transparency-item">
      <div class="icon">&#x221e;</div>
      <h4>Creative Included</h4>
      <p>4-12 net new brand-matched ads per month included. No $50K production rounds. No 6-week waits. Every format included: 16:9, 9:16, 6s bumper.</p>
    </div>
    <div class="transparency-item">
      <div class="icon">&#x2713;</div>
      <h4>Honest Measurement</h4>
      <p>MTA + incrementality testing. Full credit, partial credit, or no credit. Halo effect on Search, Meta, and email. Prove true ROI to leadership.</p>
    </div>
  </div>
</div>"""


def _build_next_steps(company, budget) -> str:
    launch = _campaign_start_date()
    launch_str = launch.strftime("%B %d, %Y")
    return f"""<div class="cta">
  <h2>Launch Date: {launch_str}</h2>
  <p>{company} can be live on streaming TV + YouTube in 2 weeks. Three simple steps.</p>
  <div class="cta-steps">
    <div class="cta-step">
      <div class="step-num">1</div>
      <div class="step-label" style="font-weight:700;margin-bottom:4px">Days 1-3</div>
      <div style="font-size:.72rem;color:rgba(255,255,255,.6)">Onboard &amp; Connect</div>
      <div style="font-size:.68rem;color:rgba(255,255,255,.45);margin-top:6px">Brand assets, data, goals. Pixel install &amp; account connect.</div>
    </div>
    <div class="cta-step">
      <div class="step-num">2</div>
      <div class="step-label" style="font-weight:700;margin-bottom:4px">Days 4-10</div>
      <div style="font-size:.72rem;color:rgba(255,255,255,.6)">Creative &amp; Strategy</div>
      <div style="font-size:.68rem;color:rgba(255,255,255,.45);margin-top:6px">AI generates creative variations. Audiences &amp; bid strategies built.</div>
    </div>
    <div class="cta-step">
      <div class="step-num">3</div>
      <div class="step-label" style="font-weight:700;margin-bottom:4px">Day 14+</div>
      <div style="font-size:.72rem;color:rgba(255,255,255,.6)">Launch &amp; Optimize</div>
      <div style="font-size:.68rem;color:rgba(255,255,255,.45);margin-top:6px">Campaigns live. Continuous testing &amp; weekly reviews.</div>
    </div>
  </div>
  <p style="margin-top:24px;font-size:.85rem;color:rgba(255,255,255,.55)">Minimum: $100/day ad spend ({_fmt_money(budget['m1'])} recommended) &middot; $0 monthly management fee &middot; Creative included</p>
</div>"""
