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


class ChannelMix(BaseModel):
    has_linear: bool = False
    has_youtube: bool = False
    has_meta: bool = False
    total_platforms: int = 0
    total_ads_found: int = 0


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
    channel_mix: ChannelMix = Field(default_factory=ChannelMix)
    running_any_ads: bool = False
    generated_at: str = ""
    pipeline_duration_seconds: Optional[float] = None
