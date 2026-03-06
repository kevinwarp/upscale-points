import asyncio
import logging
import os

import httpx

from models.ad_models import CompanyEnrichment

logger = logging.getLogger(__name__)

STORELEADS_BASE = "https://storeleads.app/json/api/v1/all/domain"


async def enrich_domain(domain: str) -> CompanyEnrichment | None:
    """Enrich a domain via the Store Leads API. Returns None on failure."""
    api_key = os.getenv("STORELEADS_API_KEY")
    if not api_key:
        logger.warning("STORELEADS_API_KEY not set, skipping enrichment")
        return None

    url = f"{STORELEADS_BASE}/{domain}"
    headers = {"Authorization": f"Bearer {api_key}"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url, headers=headers)

            # Handle rate limiting with single retry
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", "5"))
                logger.warning(f"Store Leads rate limited, retrying after {retry_after}s")
                await asyncio.sleep(retry_after)
                resp = await client.get(url, headers=headers)

            if resp.status_code == 404:
                logger.info(f"Store Leads: no data for {domain}")
                return CompanyEnrichment(domain=domain)

            resp.raise_for_status()
            raw = resp.json()

            # Store Leads nests domain data under a "domain" key
            data = raw.get("domain", raw)

            # Extract company name: prefer merchant_name or title over
            # the "name" field which is often just the domain
            company_name = data.get("merchant_name") or data.get("title")
            if company_name:
                # Clean up trailing taglines like "Nike. Just Do It"
                company_name = company_name.split(".")[0].strip()
                company_name = company_name.split("|")[0].strip()
                company_name = company_name.split(" - ")[0].strip()

            # Parse location field "Beaverton, OR, USA" into parts
            location = data.get("location", "")
            loc_parts = [p.strip() for p in location.split(",")] if location else []
            city = loc_parts[0] if len(loc_parts) >= 1 else None
            state = loc_parts[1] if len(loc_parts) >= 2 else None
            country = loc_parts[2] if len(loc_parts) >= 3 else data.get("country_code")

            # Extract categories as industry
            categories = data.get("categories", [])
            industry = categories[0] if categories else None

            # Find LinkedIn from contact_info array
            linkedin_url = None
            for contact in data.get("contact_info", []):
                if contact.get("type") == "linkedin":
                    linkedin_url = contact.get("value")
                    break

            return CompanyEnrichment(
                domain=domain,
                company_name=company_name,
                website=f"https://{data.get('cluster_best_ranked', domain)}",
                industry=industry,
                estimated_revenue=(
                    str(data.get("estimated_sales"))
                    if data.get("estimated_sales")
                    else None
                ),
                employee_count=data.get("employee_count"),
                ecommerce_platform=data.get("platform"),
                description=data.get("description"),
                country=country,
                city=city,
                state=state,
                linkedin_url=linkedin_url,
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"Store Leads HTTP error: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Store Leads error: {e}")
            return None
