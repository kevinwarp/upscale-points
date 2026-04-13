"""Wayback Machine Scraper — Promotional Activity Detection

Checks the Wayback Machine CDX API for website snapshots around key eCommerce
holidays/sales events to detect promotional activity patterns.

Uses the CDX API: https://web.archive.org/cdx/search/cdx
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import date, timedelta

import httpx

from data.ecommerce_calendar import ECOMMERCE_EVENTS, EcommerceEvent

logger = logging.getLogger(__name__)

CDX_API = "https://web.archive.org/cdx/search/cdx"
WAYBACK_SNAPSHOT = "https://web.archive.org/web/{timestamp}/{url}"


@dataclass
class WaybackSnapshot:
    """A single Wayback Machine snapshot."""

    timestamp: str  # YYYYMMDDHHmmss
    url: str
    status_code: str
    digest: str  # Content hash — different digest = page changed
    length: str

    @property
    def date(self) -> date:
        return date(int(self.timestamp[:4]), int(self.timestamp[4:6]), int(self.timestamp[6:8]))

    @property
    def archive_url(self) -> str:
        return WAYBACK_SNAPSHOT.format(timestamp=self.timestamp, url=self.url)


@dataclass
class EventActivity:
    """Detected promotional activity around a specific event."""

    event: EcommerceEvent
    event_date: date
    snapshots_in_window: int = 0
    unique_versions: int = 0  # distinct content digests = how many times page changed
    snapshots: list[WaybackSnapshot] = field(default_factory=list)
    activity_detected: bool = False
    # Comparison: snapshots in same window from non-event period
    baseline_snapshots: int = 0

    @property
    def activity_score(self) -> int:
        """0-5 score based on update frequency vs baseline."""
        if self.unique_versions == 0:
            return 0
        if self.unique_versions >= 4:
            return 5
        if self.unique_versions >= 3:
            return 4
        if self.unique_versions >= 2:
            return 3
        if self.snapshots_in_window >= 3:
            return 2
        return 1


@dataclass
class WaybackIntel:
    """Complete Wayback Machine analysis for a domain."""

    domain: str
    total_snapshots_checked: int = 0
    events_with_activity: list[EventActivity] = field(default_factory=list)
    total_events_checked: int = 0
    active_events: int = 0  # events where activity_detected = True
    promotional_intensity: str = "unknown"  # low, mid, high
    years_analyzed: list[int] = field(default_factory=list)
    found: bool = False
    error: str | None = None
    scrape_duration_seconds: float = 0.0

    @property
    def top_events(self) -> list[EventActivity]:
        """Return events sorted by activity score, descending."""
        return sorted(
            [e for e in self.events_with_activity if e.activity_detected],
            key=lambda x: x.activity_score,
            reverse=True,
        )


async def scrape_wayback(domain: str, years: list[int] | None = None) -> WaybackIntel:
    """Analyze Wayback Machine snapshots around eCommerce events.

    Args:
        domain: The domain to check (e.g. 'seed.com')
        years: Years to analyze. Defaults to current year and previous year.

    Returns:
        WaybackIntel with detected promotional patterns.
    """
    start = time.monotonic()
    intel = WaybackIntel(domain=domain)

    if years is None:
        current_year = date.today().year
        years = [current_year - 1, current_year]

    intel.years_analyzed = years

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First, get a baseline: how often is the site crawled normally?
            # Check a "quiet" 2-week period (mid-March, no major events)
            baseline_digests = set()
            for year in years:
                baseline_start = date(year, 3, 5)
                baseline_end = date(year, 3, 18)
                baseline_snaps = await _fetch_cdx(
                    client, domain, baseline_start, baseline_end
                )
                baseline_digests.update(s.digest for s in baseline_snaps)
            baseline_per_window = max(len(baseline_digests), 1)

            # Check each event across each year
            all_activities: list[EventActivity] = []

            for event in ECOMMERCE_EVENTS:
                best_activity: EventActivity | None = None

                for year in years:
                    window = event.get_window(year)
                    if not window:
                        continue

                    start_date, end_date = window
                    snapshots = await _fetch_cdx(client, domain, start_date, end_date)
                    intel.total_snapshots_checked += len(snapshots)
                    intel.total_events_checked += 1

                    # Count unique content versions (different digests = page changed)
                    digests = set(s.digest for s in snapshots)
                    unique = len(digests)

                    activity = EventActivity(
                        event=event,
                        event_date=event.resolve_date(year) or start_date,
                        snapshots_in_window=len(snapshots),
                        unique_versions=unique,
                        snapshots=snapshots[:5],  # Keep top 5 for display
                        baseline_snapshots=baseline_per_window,
                        activity_detected=unique >= 2,  # At least 2 different page versions
                    )

                    # Keep the best year for this event
                    if best_activity is None or activity.activity_score > best_activity.activity_score:
                        best_activity = activity

                if best_activity:
                    all_activities.append(best_activity)

            intel.events_with_activity = all_activities
            intel.active_events = sum(1 for a in all_activities if a.activity_detected)

            # Classify promotional intensity
            active_pct = intel.active_events / max(len(all_activities), 1)
            high_activity = sum(1 for a in all_activities if a.activity_score >= 4)

            if active_pct >= 0.6 or high_activity >= 8:
                intel.promotional_intensity = "high"
            elif active_pct >= 0.3 or high_activity >= 4:
                intel.promotional_intensity = "mid"
            else:
                intel.promotional_intensity = "low"

            intel.found = intel.total_snapshots_checked > 0

    except Exception as e:
        logger.error(f"Wayback scraper error: {e}")
        intel.error = str(e)

    intel.scrape_duration_seconds = round(time.monotonic() - start, 2)
    return intel


async def _fetch_cdx(
    client: httpx.AsyncClient,
    domain: str,
    from_date: date,
    to_date: date,
) -> list[WaybackSnapshot]:
    """Query the Wayback Machine CDX API for snapshots in a date range."""
    params = {
        "url": domain,
        "output": "json",
        "from": from_date.strftime("%Y%m%d"),
        "to": to_date.strftime("%Y%m%d"),
        "fl": "timestamp,original,statuscode,digest,length",
        "filter": "statuscode:200",
        "collapse": "digest",  # Deduplicate identical snapshots
        "limit": "20",
    }

    try:
        resp = await client.get(CDX_API, params=params)
        if resp.status_code != 200:
            logger.debug(f"CDX API returned {resp.status_code}")
            return []

        rows = resp.json()
        if not rows or len(rows) < 2:  # First row is headers
            return []

        # Skip header row
        snapshots = []
        for row in rows[1:]:
            if len(row) >= 5:
                snapshots.append(
                    WaybackSnapshot(
                        timestamp=row[0],
                        url=row[1],
                        status_code=row[2],
                        digest=row[3],
                        length=row[4],
                    )
                )
        return snapshots

    except Exception as e:
        logger.debug(f"CDX fetch error for {domain} ({from_date} to {to_date}): {e}")
        return []
