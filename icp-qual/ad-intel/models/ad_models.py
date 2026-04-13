from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Platform(str, Enum):
    ISPOT = "ispot"
    YOUTUBE = "youtube"
    META = "meta"


class Ad(BaseModel):
    title: Optional[str] = None
    video_url: Optional[str] = None
    ad_page_url: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    format: Optional[str] = None
    duration_seconds: Optional[int] = None
    thumbnail_url: Optional[str] = None


class PlatformResult(BaseModel):
    found: bool = False
    platform: Platform
    ads: list[Ad] = Field(default_factory=list)
    error: Optional[str] = None
    scrape_duration_seconds: Optional[float] = None


class SocialProfile(BaseModel):
    platform: str
    url: Optional[str] = None
    followers: Optional[int] = None
    posts: Optional[int] = None
    likes: Optional[int] = None
    description: Optional[str] = None


class CompanyEnrichment(BaseModel):
    domain: str
    company_name: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None

    # Revenue & sizing
    estimated_monthly_revenue: Optional[float] = None
    estimated_annual_revenue: Optional[float] = None
    employee_count: Optional[int] = None

    # E-commerce details
    ecommerce_platform: Optional[str] = None
    ecommerce_plan: Optional[str] = None
    platform_rank: Optional[int] = None
    product_count: Optional[int] = None
    avg_product_price: Optional[str] = None
    price_range: Optional[str] = None
    monthly_app_spend: Optional[float] = None

    # Web traffic
    estimated_monthly_visits: Optional[int] = None
    estimated_monthly_pageviews: Optional[int] = None

    # Reviews
    review_count: Optional[int] = None
    review_rating: Optional[float] = None
    review_source: Optional[str] = None

    # Branding
    logo_url: Optional[str] = None
    og_image_url: Optional[str] = None

    # Social profiles
    social_profiles: list[SocialProfile] = Field(default_factory=list)

    # Tech stack & features
    technologies: list[str] = Field(default_factory=list)
    # Full technology data with categories (from StoreLeads)
    technologies_full: list[dict] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)

    # Contact
    phone: Optional[str] = None
    emails: list[str] = Field(default_factory=list)

    # Location
    country: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    linkedin_url: Optional[str] = None

    # Dates
    store_created_at: Optional[str] = None
    last_updated_at: Optional[str] = None


class MilledEmail(BaseModel):
    date: str
    subject: str
    subheading: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None  # sale, product_launch, seasonal, bfcm, newsletter, other


class MilledIntel(BaseModel):
    milled_url: Optional[str] = None
    brand_slug: Optional[str] = None
    total_emails: int = 0
    emails_last_12_months: int = 0
    emails_per_week: float = 0.0
    emails: list[MilledEmail] = Field(default_factory=list)
    found: bool = False
    # Seasonal analysis
    has_bfcm: bool = False
    has_seasonal_sales: bool = False
    promo_categories: dict[str, int] = Field(default_factory=dict)  # category -> count
    error: Optional[str] = None


class WaybackEventHit(BaseModel):
    """A detected promotional event from Wayback Machine analysis."""
    event_name: str = ""
    event_date: str = ""
    category: str = ""  # holiday, sale, seasonal, cultural
    activity_score: int = 0  # 0-5
    unique_versions: int = 0
    snapshots_count: int = 0
    archive_url: Optional[str] = None


class WaybackIntelModel(BaseModel):
    """Wayback Machine promotional activity analysis (serializable)."""
    domain: str = ""
    total_snapshots_checked: int = 0
    total_events_checked: int = 0
    active_events: int = 0
    promotional_intensity: str = "unknown"  # low, mid, high
    years_analyzed: list[int] = Field(default_factory=list)
    events: list[WaybackEventHit] = Field(default_factory=list)
    found: bool = False
    error: Optional[str] = None
    scrape_duration_seconds: float = 0.0


class SpendEstimate(BaseModel):
    """Estimated advertising spend breakdown based on revenue."""
    estimated_monthly_ad_spend: float = 0
    ad_spend_pct_of_revenue: float = 0
    meta_spend: float = 0
    google_search_spend: float = 0
    youtube_spend: float = 0
    ctv_spend: float = 0  # current estimated CTV spend (may be 0)
    other_spend: float = 0
    recommended_ctv_test: float = 0  # recommended CTV test budget
    recommended_ctv_pct: float = 0  # as % of total ad spend


class PurchaseModel(str, Enum):
    SUBSCRIPTION = "subscription"
    SINGLE_PURCHASE = "single_purchase"
    HIGH_REPURCHASE = "high_repurchase"
    UNKNOWN = "unknown"


class BrandIntelligence(BaseModel):
    """Extended brand intelligence gathered from multiple sources."""
    # Purchase model
    purchase_model: PurchaseModel = PurchaseModel.UNKNOWN
    purchase_model_signals: list[str] = Field(default_factory=list)

    # Spend estimation
    spend_estimate: Optional[SpendEstimate] = None

    # Analytics maturity
    analytics_maturity: str = "unknown"  # basic, intermediate, advanced
    analytics_tools: list[str] = Field(default_factory=list)
    attribution_tools: list[str] = Field(default_factory=list)
    maturity_notes: list[str] = Field(default_factory=list)

    # Brand search trends
    brand_search_trend: Optional[str] = None  # rising, stable, declining
    monthly_search_volume: Optional[int] = None

    # Target audience (from Clay enrichment)
    target_audience: Optional[str] = None
    target_demographics: Optional[str] = None

    # Company info (from Clay / Crunchbase enrichment)
    logo_url: Optional[str] = None
    headquarters: Optional[str] = None
    founders: list[str] = Field(default_factory=list)
    investors: list[str] = Field(default_factory=list)
    total_funding: Optional[str] = None  # e.g. "$25M"
    recent_funding_round: Optional[str] = None  # e.g. "Series B - $15M (Jan 2025)"

    # Competitive landscape
    competitors: list[str] = Field(default_factory=list)
    competitors_on_ctv: list[str] = Field(default_factory=list)
    competitors_on_youtube: list[str] = Field(default_factory=list)

    # Creative samples
    sample_video_urls: list[str] = Field(default_factory=list)


class CrmOutreach(BaseModel):
    """Outreach activity for a contact from Company Pulse."""
    provider: Optional[str] = None  # "instantly", "beehiiv", etc.
    sent: bool = False
    opened: bool = False
    clicked: bool = False
    confidence: Optional[str] = None
    campaign_name: Optional[str] = None


class CrmContact(BaseModel):
    """Contact from Company Pulse CRM data."""
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    lifecycle_stage: Optional[str] = None
    last_conversation_date: Optional[str] = None
    outreach: list[CrmOutreach] = Field(default_factory=list)


class CrmDeal(BaseModel):
    """Deal/opportunity from Company Pulse."""
    title: Optional[str] = None
    stage: Optional[str] = None
    deal_size: Optional[float] = None
    probability: Optional[float] = None
    days_in_stage: Optional[int] = None
    close_date: Optional[str] = None
    pipeline: Optional[str] = None


class CrmMeeting(BaseModel):
    """Meeting from Company Pulse."""
    title: Optional[str] = None
    date: Optional[str] = None
    attendees: list[str] = Field(default_factory=list)
    summary: Optional[str] = None
    key_points: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)


class CompanyPulse(BaseModel):
    """Company Pulse CRM intelligence for a domain."""
    found: bool = False
    report_id: Optional[str] = None

    # Organization status
    current_status: Optional[str] = None
    status_summary: list[str] = Field(default_factory=list)
    next_steps: Optional[str] = None
    owner_email: Optional[str] = None

    # Health
    health_score: Optional[int] = None  # 0-100
    health_status: Optional[str] = None  # healthy, at_risk, critical
    health_signals: list[dict] = Field(default_factory=list)

    # Pipeline
    contacts: list[CrmContact] = Field(default_factory=list)
    opportunities: list[CrmDeal] = Field(default_factory=list)
    meetings: list[CrmMeeting] = Field(default_factory=list)

    # Outreach summary
    days_since_first_contact: Optional[int] = None
    outreach_summary: Optional[dict] = None

    # Upscale score from CRM (may differ from our computed fit score)
    crm_tier: Optional[str] = None  # A, B, C, D

    error: Optional[str] = None


class TargetContact(BaseModel):
    """A discovered or existing contact for the brand."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    confidence_score: float = 0.0
    email_sources: list[str] = Field(default_factory=list)
    outreach_status: Optional[str] = None  # "recently_contacted" | "eligible_for_outreach"
    replied_at: Optional[str] = None


class ContactIntel(BaseModel):
    """Contact search results for the brand."""
    found: bool = False
    discovered_count: int = 0
    existing_count: int = 0
    contacts: list[TargetContact] = Field(default_factory=list)
    error: Optional[str] = None


class ClayEnrichment(BaseModel):
    """Enrichment data from Clay MCP find-and-enrich-company."""
    enriched: bool = False
    logo_url: Optional[str] = None
    headquarters: Optional[str] = None
    competitors: list[str] = Field(default_factory=list)
    revenue_model: Optional[str] = None
    target_audience: Optional[str] = None
    founders: list[str] = Field(default_factory=list)
    investors: list[str] = Field(default_factory=list)
    latest_funding: Optional[str] = None
    headcount_growth: Optional[str] = None
    recent_news: list[str] = Field(default_factory=list)
    raw_data: Optional[dict] = None  # Full Clay response for debugging


class PipelineEvent(BaseModel):
    """A single pipeline status event for frontend consumption."""
    ts: str  # ISO timestamp
    event: str  # pipeline_start, step_start, step_complete, step_error, pipeline_complete
    step: Optional[str] = None
    label: str = ""
    progress: int = 0  # 0-100
    duration_ms: Optional[int] = None
    data: Optional[dict] = None
    error: Optional[str] = None


class EnrichedCompetitor(BaseModel):
    """A competitor enriched with StoreLeads data."""
    name: str = ""
    domain: str = ""
    industry: Optional[str] = None
    estimated_annual_revenue: Optional[float] = None
    ecommerce_platform: Optional[str] = None
    employee_count: Optional[int] = None
    logo_url: Optional[str] = None
    on_ctv: bool = False
    on_youtube: bool = False
    validated: bool = False


class CompetitorDetection(BaseModel):
    """Detected CTV competitor tags in a brand's tech stack."""
    found: bool = False
    competitors_detected: list[str] = Field(default_factory=list)  # e.g. ["Tatari", "MNTN"]
    tags_matched: list[str] = Field(default_factory=list)  # raw tech stack entries matched
    warning: str = ""  # e.g. "Brand is using Tatari — active CTV competitor client"


# Known CTV competitor technology tags and their mappings
CTV_COMPETITOR_TAGS: dict[str, str] = {
    "tatari": "Tatari",
    "tatari pixel": "Tatari",
    "tatari tag": "Tatari",
    "steelhouse": "MNTN",
    "mntn": "MNTN",
    "mntn pixel": "MNTN",
    "mntn performance tv": "MNTN",
    "tvscientific": "tvScientific",
    "tvscientific pixel": "tvScientific",
    "vibe": "Vibe",
    "vibe pixel": "Vibe",
    "vibe.co": "Vibe",
    "universal ads": "Universal Ads",
    "universal ads pixel": "Universal Ads",
    "freewheel": "Universal Ads",
}


class ChannelMix(BaseModel):
    has_linear: bool = False
    has_youtube: bool = False
    has_meta: bool = False
    total_platforms: int = 0
    total_ads_found: int = 0


class CreativePipelineResult(BaseModel):
    """Result from the upscale.ai Creative Pipeline (tvads-api)."""
    found: bool = False
    job_id: str = ""
    status: str = ""              # pending, processing, complete, error, timeout
    # Brand intel
    brand_name: str = ""
    brand_url: str = ""
    brand_brief: str = ""
    # Script
    script: str = ""
    # Assets
    image_urls: list[str] = Field(default_factory=list)
    video_urls: dict[str, list[str]] = Field(default_factory=dict)  # provider -> [urls]
    voiceover_url: str = ""
    # Documents
    docx_url: str = ""
    zip_url: str = ""
    # Meta
    elapsed_seconds: float = 0
    error: Optional[str] = None
    error_code: Optional[str] = None


class NewsItem(BaseModel):
    """A news article or press mention for the brand."""
    headline: str = ""
    source: Optional[str] = None
    url: Optional[str] = None
    date: Optional[str] = None
    category: str = ""  # press, product_launch, partnership, m_and_a, funding, other


class PodcastAppearance(BaseModel):
    """A podcast or thought leadership appearance by a company leader."""
    person_name: str = ""
    person_title: Optional[str] = None
    show_name: str = ""
    episode_title: str = ""
    url: Optional[str] = None
    date: Optional[str] = None


class PlatformCaseStudy(BaseModel):
    """A case study from an ad/tech platform mentioning the brand."""
    platform: str = ""  # "Meta", "Google", "TikTok", "Shopify", etc.
    title: str = ""
    url: Optional[str] = None
    key_metrics: list[str] = Field(default_factory=list)  # ["2.5x ROAS", "40% lower CPA"]
    summary: Optional[str] = None


class JobPosting(BaseModel):
    """An open job posting for the brand."""
    title: str = ""
    department: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None
    is_marketing: bool = False  # flagged if title matches marketing/growth/media keywords


class HiringIntel(BaseModel):
    """Hiring and growth signals for the brand."""
    found: bool = False
    open_jobs_count: int = 0
    marketing_jobs: list[JobPosting] = Field(default_factory=list)
    all_jobs: list[JobPosting] = Field(default_factory=list)
    hiring_velocity: Optional[str] = None  # "accelerating", "stable", "slowing"
    headcount_growth_12m: Optional[float] = None  # percentage
    headcount_growth_24m: Optional[float] = None
    error: Optional[str] = None


class PitchConfig(BaseModel):
    """Overridable configuration for pitch report generation.

    Any field set to a non-None value overrides the auto-computed value.
    """
    # Budget overrides (monthly amounts)
    budget_m1: Optional[float] = None
    budget_m2: Optional[float] = None
    budget_m3: Optional[float] = None

    # Strategy override
    strategy_tier: Optional[str] = None  # "youtube_only", "ctv_led", "full_funnel"

    # ROI projection overrides
    aov: Optional[float] = None  # Average order value
    blended_cpm: Optional[float] = None
    cost_per_visit: Optional[float] = None
    cpa_pct: Optional[float] = None  # CPA as % of AOV (e.g. 0.72)
    ltv_multiplier: Optional[float] = None
    roas_floor: Optional[float] = None  # Min ROAS clamp (default 2.2)
    roas_cap: Optional[float] = None  # Max ROAS clamp (default 8.5)

    # Campaign timing
    campaign_start_date: Optional[str] = None  # ISO date string

    # Content overrides
    company_name: Optional[str] = None
    industry: Optional[str] = None
    logo_url: Optional[str] = None
    tagline: Optional[str] = None  # Custom hero subtitle

    # Section toggles (True = include, False = exclude)
    include_ctv_impact: Optional[bool] = None
    include_youtube_impact: Optional[bool] = None
    include_creative_showcase: Optional[bool] = None
    include_audio_demos: Optional[bool] = None
    include_competitive: Optional[bool] = None
    include_ad_discovery: Optional[bool] = None
    include_case_studies: Optional[bool] = None


class DomainAdReport(BaseModel):
    domain: str
    company_name: Optional[str] = None
    enrichment: Optional[CompanyEnrichment] = None
    ispot_ads: PlatformResult = Field(
        default_factory=lambda: PlatformResult(platform=Platform.ISPOT)
    )
    youtube_ads: PlatformResult = Field(
        default_factory=lambda: PlatformResult(platform=Platform.YOUTUBE)
    )
    meta_ads: PlatformResult = Field(
        default_factory=lambda: PlatformResult(platform=Platform.META)
    )
    milled_intel: MilledIntel = Field(default_factory=MilledIntel)
    channel_mix: ChannelMix = Field(default_factory=ChannelMix)
    brand_intel: BrandIntelligence = Field(default_factory=BrandIntelligence)
    company_pulse: CompanyPulse = Field(default_factory=CompanyPulse)
    contact_intel: ContactIntel = Field(default_factory=ContactIntel)
    clay: ClayEnrichment = Field(default_factory=ClayEnrichment)
    competitor_detection: CompetitorDetection = Field(default_factory=CompetitorDetection)
    enriched_competitors: list[EnrichedCompetitor] = Field(default_factory=list)
    wayback_intel: WaybackIntelModel = Field(default_factory=WaybackIntelModel)
    creative_pipeline: CreativePipelineResult = Field(default_factory=CreativePipelineResult)
    # Phase 2: New data collection fields
    hiring_intel: HiringIntel = Field(default_factory=HiringIntel)
    recent_news: list[NewsItem] = Field(default_factory=list)
    podcasts: list[PodcastAppearance] = Field(default_factory=list)
    case_studies: list[PlatformCaseStudy] = Field(default_factory=list)

    running_any_ads: bool = False
    generated_at: str = ""
    pipeline_duration_seconds: Optional[float] = None
    audio_files: list[dict] = Field(default_factory=list)
    audio_run_id: Optional[str] = None
