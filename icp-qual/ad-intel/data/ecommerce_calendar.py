"""eCommerce DTC Holiday & Sales Calendar

25 key promotional events that DTC brands typically run campaigns around.
Used for Wayback Machine snapshot analysis and promotional pattern detection.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import calendar


@dataclass
class EcommerceEvent:
    """A key eCommerce promotional event."""

    name: str
    category: str  # holiday, sale, seasonal, cultural
    # For fixed-date events: month and day
    month: int | None = None
    day: int | None = None
    # For floating events, a callable returns the date for a given year
    _resolver: str | None = None  # name of resolver function
    # Window around the event to check Wayback (days before/after)
    window_before: int = 5
    window_after: int = 2
    # How important for DTC brands (1-5)
    importance: int = 3
    description: str = ""

    def resolve_date(self, year: int) -> date | None:
        """Return the exact date for this event in the given year."""
        if self.month and self.day:
            try:
                return date(year, self.month, self.day)
            except ValueError:
                return None

        if self._resolver:
            resolver = _RESOLVERS.get(self._resolver)
            if resolver:
                return resolver(year)
        return None

    def get_window(self, year: int) -> tuple[date, date] | None:
        """Return (start, end) date window for Wayback snapshot checking."""
        d = self.resolve_date(year)
        if not d:
            return None
        return (d - timedelta(days=self.window_before), d + timedelta(days=self.window_after))


# ── Floating date resolvers ──


def _presidents_day(year: int) -> date:
    """Third Monday of February."""
    return _nth_weekday(year, 2, calendar.MONDAY, 3)


def _easter(year: int) -> date:
    """Computus algorithm for Easter Sunday."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    month = (h + l_ - 7 * m + 114) // 31
    day = ((h + l_ - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _mothers_day(year: int) -> date:
    """Second Sunday of May."""
    return _nth_weekday(year, 5, calendar.SUNDAY, 2)


def _memorial_day(year: int) -> date:
    """Last Monday of May."""
    return _last_weekday(year, 5, calendar.MONDAY)


def _fathers_day(year: int) -> date:
    """Third Sunday of June."""
    return _nth_weekday(year, 6, calendar.SUNDAY, 3)


def _labor_day(year: int) -> date:
    """First Monday of September."""
    return _nth_weekday(year, 9, calendar.MONDAY, 1)


def _thanksgiving(year: int) -> date:
    """Fourth Thursday of November."""
    return _nth_weekday(year, 11, calendar.THURSDAY, 4)


def _black_friday(year: int) -> date:
    return _thanksgiving(year) + timedelta(days=1)


def _small_biz_saturday(year: int) -> date:
    return _thanksgiving(year) + timedelta(days=2)


def _cyber_monday(year: int) -> date:
    return _thanksgiving(year) + timedelta(days=4)


def _green_monday(year: int) -> date:
    """Second Monday of December."""
    return _nth_weekday(year, 12, calendar.MONDAY, 2)


def _prime_day(year: int) -> date:
    """Amazon Prime Day — typically mid-July (estimate Jul 15)."""
    return date(year, 7, 15)


def _back_to_school(year: int) -> date:
    """Back-to-school season start — early August."""
    return date(year, 8, 1)


def _free_shipping_day(year: int) -> date:
    """Free Shipping Day — typically Dec 14-15."""
    return date(year, 12, 14)


# ── Helpers ──


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Return the nth occurrence of weekday in month/year."""
    first = date(year, month, 1)
    # Days until first occurrence of weekday
    days_ahead = weekday - first.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return first + timedelta(days=days_ahead + 7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> date:
    """Return the last occurrence of weekday in month/year."""
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    days_back = last_day.weekday() - weekday
    if days_back < 0:
        days_back += 7
    return last_day - timedelta(days=days_back)


_RESOLVERS: dict[str, callable] = {
    "presidents_day": _presidents_day,
    "easter": _easter,
    "mothers_day": _mothers_day,
    "memorial_day": _memorial_day,
    "fathers_day": _fathers_day,
    "labor_day": _labor_day,
    "thanksgiving": _thanksgiving,
    "black_friday": _black_friday,
    "small_biz_saturday": _small_biz_saturday,
    "cyber_monday": _cyber_monday,
    "green_monday": _green_monday,
    "prime_day": _prime_day,
    "back_to_school": _back_to_school,
    "free_shipping_day": _free_shipping_day,
}


# ── The 25 Events ──

ECOMMERCE_EVENTS: list[EcommerceEvent] = [
    # ── Q1 ──
    EcommerceEvent(
        name="New Year's Day",
        category="holiday",
        month=1, day=1,
        window_before=3, window_after=1,
        importance=3,
        description="New year sales, resolution-driven products, clearance",
    ),
    EcommerceEvent(
        name="Valentine's Day",
        category="holiday",
        month=2, day=14,
        window_before=10, window_after=1,
        importance=4,
        description="Gift-giving, couples products, self-care",
    ),
    EcommerceEvent(
        name="Presidents' Day",
        category="sale",
        _resolver="presidents_day",
        window_before=5, window_after=1,
        importance=2,
        description="Winter clearance sales, mattress/furniture big event",
    ),
    EcommerceEvent(
        name="St. Patrick's Day",
        category="cultural",
        month=3, day=17,
        window_before=5, window_after=1,
        importance=2,
        description="Themed promotions, food/beverage brands",
    ),
    EcommerceEvent(
        name="Easter",
        category="holiday",
        _resolver="easter",
        window_before=7, window_after=1,
        importance=3,
        description="Spring sales, candy, kids products, home décor",
    ),

    # ── Q2 ──
    EcommerceEvent(
        name="Earth Day",
        category="cultural",
        month=4, day=22,
        window_before=5, window_after=2,
        importance=2,
        description="Sustainability campaigns, eco-friendly product launches",
    ),
    EcommerceEvent(
        name="Mother's Day",
        category="holiday",
        _resolver="mothers_day",
        window_before=10, window_after=1,
        importance=5,
        description="Top gift-giving holiday — beauty, jewelry, home, wellness",
    ),
    EcommerceEvent(
        name="Memorial Day",
        category="sale",
        _resolver="memorial_day",
        window_before=7, window_after=2,
        importance=4,
        description="Major sale weekend, summer kickoff, outdoor/home",
    ),
    EcommerceEvent(
        name="Father's Day",
        category="holiday",
        _resolver="fathers_day",
        window_before=10, window_after=1,
        importance=4,
        description="Gift-giving — grooming, tech, outdoor, apparel",
    ),

    # ── Q3 ──
    EcommerceEvent(
        name="4th of July",
        category="holiday",
        month=7, day=4,
        window_before=7, window_after=2,
        importance=3,
        description="Summer sale, outdoor/grilling, patriotic themes",
    ),
    EcommerceEvent(
        name="Amazon Prime Day",
        category="sale",
        _resolver="prime_day",
        window_before=5, window_after=3,
        importance=4,
        description="Counter-sales across all DTC — 'anti-Prime Day' deals",
    ),
    EcommerceEvent(
        name="Back to School",
        category="seasonal",
        _resolver="back_to_school",
        window_before=14, window_after=21,
        importance=4,
        description="Extended season — kids, teens, college, school supplies",
    ),
    EcommerceEvent(
        name="Labor Day",
        category="sale",
        _resolver="labor_day",
        window_before=7, window_after=2,
        importance=4,
        description="End-of-summer clearance, fall launches, mattress sales",
    ),

    # ── Q4 ──
    EcommerceEvent(
        name="Halloween",
        category="holiday",
        month=10, day=31,
        window_before=14, window_after=1,
        importance=3,
        description="Costumes, candy, themed products, fall seasonal",
    ),
    EcommerceEvent(
        name="Singles' Day / Veterans Day (11/11)",
        category="sale",
        month=11, day=11,
        window_before=5, window_after=1,
        importance=2,
        description="Global shopping event + military discount sales",
    ),
    EcommerceEvent(
        name="Thanksgiving",
        category="holiday",
        _resolver="thanksgiving",
        window_before=7, window_after=0,
        importance=3,
        description="Pre-BFCM teaser sales, early access for VIPs",
    ),
    EcommerceEvent(
        name="Black Friday",
        category="sale",
        _resolver="black_friday",
        window_before=7, window_after=1,
        importance=5,
        description="Biggest shopping day — sitewide sales, doorbuster deals",
    ),
    EcommerceEvent(
        name="Small Business Saturday",
        category="sale",
        _resolver="small_biz_saturday",
        window_before=2, window_after=0,
        importance=2,
        description="Support local/indie brands, DTC brand storytelling",
    ),
    EcommerceEvent(
        name="Cyber Monday",
        category="sale",
        _resolver="cyber_monday",
        window_before=1, window_after=1,
        importance=5,
        description="Online-focused deals, extended BFCM, flash sales",
    ),
    EcommerceEvent(
        name="Giving Tuesday",
        category="cultural",
        month=12, day=3,
        window_before=2, window_after=1,
        importance=2,
        description="Charity tie-ins, cause marketing, 1-for-1 promos",
    ),
    EcommerceEvent(
        name="Green Monday",
        category="sale",
        _resolver="green_monday",
        window_before=3, window_after=1,
        importance=3,
        description="Second-biggest online shopping day in Dec, last-chance deals",
    ),
    EcommerceEvent(
        name="Free Shipping Day",
        category="sale",
        _resolver="free_shipping_day",
        window_before=2, window_after=1,
        importance=3,
        description="Last guaranteed delivery before Christmas",
    ),
    EcommerceEvent(
        name="Christmas",
        category="holiday",
        month=12, day=25,
        window_before=14, window_after=1,
        importance=5,
        description="Peak gifting season, holiday collections, gift guides",
    ),
    EcommerceEvent(
        name="After-Christmas / Boxing Day",
        category="sale",
        month=12, day=26,
        window_before=1, window_after=5,
        importance=3,
        description="Post-holiday clearance, gift card spending, returns season",
    ),
    EcommerceEvent(
        name="New Year's Eve",
        category="holiday",
        month=12, day=31,
        window_before=3, window_after=0,
        importance=2,
        description="Year-end clearance, resolution products pre-launch",
    ),
]


def get_events_for_year(year: int) -> list[tuple[EcommerceEvent, date]]:
    """Return all events with resolved dates for a given year, sorted chronologically."""
    results = []
    for event in ECOMMERCE_EVENTS:
        d = event.resolve_date(year)
        if d:
            results.append((event, d))
    results.sort(key=lambda x: x[1])
    return results


def get_upcoming_events(from_date: date | None = None, count: int = 5) -> list[tuple[EcommerceEvent, date]]:
    """Return the next N upcoming events from a given date."""
    if from_date is None:
        from_date = date.today()
    year_events = get_events_for_year(from_date.year) + get_events_for_year(from_date.year + 1)
    upcoming = [(ev, d) for ev, d in year_events if d >= from_date]
    return upcoming[:count]
