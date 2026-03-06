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


class CompanyEnrichment(BaseModel):
    domain: str
    company_name: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    estimated_revenue: Optional[str] = None
    employee_count: Optional[int] = None
    ecommerce_platform: Optional[str] = None
    description: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    linkedin_url: Optional[str] = None


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
