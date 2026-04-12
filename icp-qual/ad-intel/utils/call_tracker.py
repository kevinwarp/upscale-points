"""External Call Tracker

Tracks all external API calls made during pipeline execution.
Each call records: service name, URL, status, duration, error (if any).
Used for Slack thread summaries and error reporting.
"""

import time
import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class CallStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass
class ExternalCall:
    """Record of a single external API call."""
    service: str
    step: str
    url: str = ""
    status: CallStatus = CallStatus.SUCCESS
    status_code: int | None = None
    duration_seconds: float = 0.0
    error: str = ""
    data_summary: str = ""

    @property
    def emoji(self) -> str:
        return {
            CallStatus.SUCCESS: "✅",
            CallStatus.ERROR: "❌",
            CallStatus.TIMEOUT: "⏰",
            CallStatus.SKIPPED: "⏭️",
        }[self.status]

    def to_slack_line(self) -> str:
        """Format as a single Slack thread line."""
        dur = f" ({self.duration_seconds:.1f}s)" if self.duration_seconds else ""
        err = f" — {self.error}" if self.error else ""
        summary = f" — {self.data_summary}" if self.data_summary else ""
        return f"{self.emoji} *{self.service}*{dur}{summary}{err}"


@dataclass
class CallTracker:
    """Collects all external API calls during a pipeline run."""
    domain: str = ""
    calls: list[ExternalCall] = field(default_factory=list)
    _start_times: dict[str, float] = field(default_factory=dict)

    def start(self, step: str):
        """Mark the start of an external call (for timing)."""
        self._start_times[step] = time.monotonic()

    def record(
        self,
        service: str,
        step: str,
        url: str = "",
        status: CallStatus = CallStatus.SUCCESS,
        status_code: int | None = None,
        error: str = "",
        data_summary: str = "",
    ):
        """Record a completed external call."""
        duration = 0.0
        if step in self._start_times:
            duration = round(time.monotonic() - self._start_times.pop(step), 2)

        call = ExternalCall(
            service=service,
            step=step,
            url=url,
            status=status,
            status_code=status_code,
            duration_seconds=duration,
            error=error,
            data_summary=data_summary,
        )
        self.calls.append(call)

        if status == CallStatus.ERROR:
            logger.error(f"[CallTracker] {service} FAILED: {error}")
        else:
            logger.debug(f"[CallTracker] {service}: {status.value} in {duration:.1f}s")

    @property
    def total_calls(self) -> int:
        return len(self.calls)

    @property
    def failed_calls(self) -> list[ExternalCall]:
        return [c for c in self.calls if c.status == CallStatus.ERROR]

    @property
    def successful_calls(self) -> list[ExternalCall]:
        return [c for c in self.calls if c.status == CallStatus.SUCCESS]

    @property
    def total_duration(self) -> float:
        return round(sum(c.duration_seconds for c in self.calls), 2)

    def summary_text(self) -> str:
        """Generate a summary string for logging."""
        ok = len(self.successful_calls)
        fail = len(self.failed_calls)
        skip = len([c for c in self.calls if c.status == CallStatus.SKIPPED])
        return f"{self.total_calls} calls ({ok} ok, {fail} failed, {skip} skipped) in {self.total_duration}s"

    def to_slack_thread(self) -> list[str]:
        """Generate Slack thread messages for all external calls.

        Returns a list of message strings. First is the summary,
        rest are individual call details grouped by status.
        """
        if not self.calls:
            return [f"📊 *Pipeline for {self.domain}* — no external calls recorded"]

        ok = len(self.successful_calls)
        fail = len(self.failed_calls)
        total = self.total_calls

        # Header
        header = f"📊 *External API Calls for {self.domain}*\n"
        header += f"Total: *{total}* calls | ✅ {ok} success | ❌ {fail} failed | ⏱️ {self.total_duration}s total\n"

        # Group by step order
        lines = [c.to_slack_line() for c in self.calls]
        header += "\n".join(lines)

        messages = [header]

        # Add error details as follow-up thread messages
        for c in self.failed_calls:
            err_msg = f"❌ *{c.service}* failed\n"
            if c.url:
                err_msg += f"URL: `{c.url}`\n"
            if c.status_code:
                err_msg += f"HTTP Status: {c.status_code}\n"
            err_msg += f"Error: {c.error}\n"
            err_msg += f"Duration: {c.duration_seconds:.1f}s"
            messages.append(err_msg)

        return messages

    # ── Known pipeline services ──
    # Reference list of all external calls in the pipeline

    PIPELINE_SERVICES = [
        {
            "service": "StoreLeads API",
            "step": "storeleads",
            "module": "enrichment/storeleads_client.py",
            "purpose": "Company enrichment (revenue, employees, tech stack, socials)",
            "url": "https://api.storeleads.app/v1/all/domain/{domain}",
        },
        {
            "service": "Company Pulse (HubSpot)",
            "step": "company_pulse",
            "module": "enrichment/company_pulse.py",
            "purpose": "CRM lookup — health score, contacts, deals",
            "url": "HubSpot CRM API via MCP",
        },
        {
            "service": "Contact Search (Apollo)",
            "step": "contact_search",
            "module": "enrichment/contact_search.py",
            "purpose": "Discover marketing contacts at target company",
            "url": "Apollo API — people search",
        },
        {
            "service": "Creative Pipeline",
            "step": "creative_pipeline",
            "module": "enrichment/creative_pipeline.py",
            "purpose": "AI-generated brand brief, scripts, scene images, videos",
            "url": "Internal creative API (Cloud Run)",
        },
        {
            "service": "Voiceover Generation",
            "step": "voiceover",
            "module": "enrichment/voiceover_gen.py",
            "purpose": "AI-generated voiceover audio (ElevenLabs via Script Automation)",
            "url": "https://script-automation-backend-*.a.run.app/generate",
        },
        {
            "service": "iSpot Scraper",
            "step": "ispot",
            "module": "scraping/ispot_scraper.py",
            "purpose": "Detect linear TV / CTV ad campaigns",
            "url": "https://www.ispot.tv (browser scrape)",
        },
        {
            "service": "YouTube Ads Transparency",
            "step": "youtube",
            "module": "scraping/youtube_transparency_scraper.py",
            "purpose": "Detect YouTube/Google video ad campaigns",
            "url": "https://adstransparency.google.com (browser scrape)",
        },
        {
            "service": "Meta Ad Library",
            "step": "meta",
            "module": "scraping/meta_ad_scraper.py",
            "purpose": "Detect Facebook/Instagram ad campaigns",
            "url": "https://www.facebook.com/ads/library (browser scrape)",
        },
        {
            "service": "Milled Email Intel",
            "step": "milled",
            "module": "scraping/milled_scraper.py",
            "purpose": "Scrape email marketing campaigns and newsletter data",
            "url": "https://milled.com/{brand} (browser scrape)",
        },
        {
            "service": "Google Trends",
            "step": "trends",
            "module": "scraping/google_trends_scraper.py",
            "purpose": "Brand search trend and volume data",
            "url": "https://trends.google.com (browser scrape)",
        },
        {
            "service": "Competitor Landscape",
            "step": "competitors",
            "module": "scraping/competitor_scraper.py",
            "purpose": "Check if competitors are running CTV/YouTube ads",
            "url": "iSpot + YouTube Ads Transparency (browser scrape)",
        },
        {
            "service": "Wayback Machine",
            "step": "wayback",
            "module": "scraping/wayback_scraper.py",
            "purpose": "Historical promotional activity from web archives",
            "url": "https://web.archive.org/cdx/search/cdx",
        },
        {
            "service": "StoreLeads (Competitor Enrichment)",
            "step": "competitor_enrichment",
            "module": "orchestrator.py",
            "purpose": "Enrich competitor companies with revenue + employee data",
            "url": "https://api.storeleads.app/v1/all/domain/{competitor}",
        },
        {
            "service": "Report Upload",
            "step": "report_upload",
            "module": "reports/publisher.py",
            "purpose": "Upload generated HTML reports to hosting platform",
            "url": "https://upscale-reports-*.a.run.app/api/upload",
        },
    ]
