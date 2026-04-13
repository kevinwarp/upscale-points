"""Contact Search API Client

Discovers key contacts at a brand (CEO, CMO, Growth, Paid Media, Ecommerce,
Director, Manager, High-Intent) via Apollo + Lusha enrichment, and searches
the existing contact database for prior outreach history.

Two main functions:
    contacts = await discover_contacts("seed.com")   # 10-30s, no auth needed
    existing = await search_contacts("seed.com")      # instant, auth required

Both return structured ContactSearchResult with parsed contact records.
"""

from __future__ import annotations

import csv
import io
import logging
import os
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://contact-search-232209276549.us-central1.run.app"
DEFAULT_API_KEY = "3d0608ed1a0438c62f17421e1500e281c8ebe2e55b12a778715e342e1c3200cc"


@dataclass
class DiscoveredContact:
    """A contact found via the discover-csv endpoint."""
    first_name: str = ""
    last_name: str = ""
    title: str = ""
    email: str = ""
    company: str = ""
    domain: str = ""
    linkedin_url: str = ""
    email_sources: str = ""
    confidence_score: float = 0.0
    all_emails: str = ""


@dataclass
class ExistingContact:
    """A contact already in the database from search endpoint."""
    id: str = ""
    first_name: str = ""
    last_name: str = ""
    title: str = ""
    best_email: str = ""
    company_name: str = ""
    company_domain: str = ""
    city: str = ""
    linkedin_url: str = ""
    outreach_status: str = ""  # "recently_contacted" | "eligible_for_outreach"
    replied_at: str | None = None
    confidence_score: float = 0.0
    email_sources: list[str] = field(default_factory=list)


@dataclass
class ContactSearchResult:
    """Combined result from contact discovery and/or search."""
    domain: str = ""
    discovered: list[DiscoveredContact] = field(default_factory=list)
    existing: list[ExistingContact] = field(default_factory=list)
    total_existing: int = 0
    error: str | None = None


async def discover_contacts(
    domain: str,
    base_url: str | None = None,
) -> list[DiscoveredContact]:
    """Discover contacts for a domain via Apollo + Lusha enrichment.

    This is a PUBLIC endpoint (no auth needed). Searches 8 title buckets
    and returns enriched contacts as CSV. Takes 10-30 seconds.

    Args:
        domain: Company domain (e.g. "seed.com")
        base_url: Override base URL

    Returns:
        List of DiscoveredContact records.
    """
    base_url = base_url or os.getenv("CONTACT_SEARCH_API_URL", BASE_URL)
    url = f"{base_url.rstrip('/')}/api/contacts/discover-csv"

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(url, params={"domain": domain})
            resp.raise_for_status()

        # Parse CSV response
        contacts = []
        reader = csv.DictReader(io.StringIO(resp.text))
        for row in reader:
            score = 0.0
            try:
                score = float(row.get("confidence_score", 0))
            except (ValueError, TypeError):
                pass

            contacts.append(DiscoveredContact(
                first_name=row.get("first_name", ""),
                last_name=row.get("last_name", ""),
                title=row.get("title", ""),
                email=row.get("email", ""),
                company=row.get("company", ""),
                domain=row.get("domain", ""),
                linkedin_url=row.get("linkedin_url", ""),
                email_sources=row.get("email_sources", ""),
                confidence_score=score,
                all_emails=row.get("all_emails", ""),
            ))

        logger.info(f"Contact discovery: found {len(contacts)} contacts for {domain}")
        return contacts

    except httpx.TimeoutException:
        logger.warning(f"Contact discovery: timeout for {domain} (takes 10-30s)")
        return []
    except Exception as e:
        logger.error(f"Contact discovery: error for {domain}: {e}")
        return []


async def search_contacts(
    domain: str,
    api_key: str | None = None,
    base_url: str | None = None,
    page_size: int = 50,
) -> tuple[list[ExistingContact], int]:
    """Search the contact database for existing contacts at a domain.

    This is a PROTECTED endpoint (auth required). Returns contacts already
    in the database with outreach status and reply history.

    Args:
        domain: Company domain to filter by
        api_key: API key (falls back to CONTACT_SEARCH_API_KEY env var)
        base_url: Override base URL
        page_size: Results per page (max 50)

    Returns:
        Tuple of (list of ExistingContact, total count).
    """
    api_key = api_key or os.getenv("CONTACT_SEARCH_API_KEY", DEFAULT_API_KEY)
    base_url = base_url or os.getenv("CONTACT_SEARCH_API_URL", BASE_URL)
    url = f"{base_url.rstrip('/')}/api/search/contacts"

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
            resp = await client.get(
                url,
                params={"company": domain, "pageSize": page_size},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            # Handle session-based auth redirects (NextAuth)
            if resp.status_code in (301, 302, 307, 308):
                logger.info(f"Contact search: {domain} — search endpoint requires session auth, skipping")
                return [], 0
            resp.raise_for_status()
            data = resp.json()

        contacts = []
        for item in data.get("items", []):
            contacts.append(ExistingContact(
                id=item.get("id", ""),
                first_name=item.get("firstName", ""),
                last_name=item.get("lastName", ""),
                title=item.get("title", ""),
                best_email=item.get("bestEmail", ""),
                company_name=item.get("companyName", ""),
                company_domain=item.get("companyDomain", ""),
                city=item.get("city", ""),
                linkedin_url=item.get("linkedinUrl", ""),
                outreach_status=item.get("outreachStatus", ""),
                replied_at=item.get("repliedAt"),
                confidence_score=item.get("confidenceScore", 0.0),
                email_sources=item.get("emailSources", []),
            ))

        total = data.get("pagination", {}).get("total", len(contacts))
        logger.info(f"Contact search: {len(contacts)} existing contacts for {domain} ({total} total)")
        return contacts, total

    except Exception as e:
        logger.error(f"Contact search: error for {domain}: {e}")
        return [], 0


async def fetch_contacts_for_domain(
    domain: str,
    api_key: str | None = None,
    base_url: str | None = None,
) -> ContactSearchResult:
    """Run both contact discovery and database search in parallel.

    This is the main entry point for the ICP pipeline. It:
    1. Discovers new contacts via Apollo + Lusha (public, 10-30s)
    2. Searches existing database for prior outreach (protected, instant)

    Returns a combined ContactSearchResult.
    """
    import asyncio

    result = ContactSearchResult(domain=domain)

    discover_task = asyncio.create_task(discover_contacts(domain, base_url))
    search_task = asyncio.create_task(search_contacts(domain, api_key, base_url))

    try:
        discovered, (existing, total) = await asyncio.gather(
            discover_task, search_task
        )
        result.discovered = discovered
        result.existing = existing
        result.total_existing = total
    except Exception as e:
        logger.error(f"Contact fetch: error for {domain}: {e}")
        result.error = str(e)

    return result
