import asyncio
import logging
import os

import httpx

from models.ad_models import CompanyEnrichment, SocialProfile

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

            # --- Revenue (values are in cents) ---
            raw_monthly = data.get("estimated_sales")
            raw_yearly = data.get("estimated_sales_yearly")
            monthly_revenue = raw_monthly / 100 if raw_monthly else None
            annual_revenue = raw_yearly / 100 if raw_yearly else (
                monthly_revenue * 12 if monthly_revenue else None
            )

            # --- Reviews (check multiple providers) ---
            review_count = None
            review_rating = None
            review_source = None
            for src in ["okendo", "trustpilot", "yotpo", "judge_me",
                         "stamped", "loox", "reviews_io"]:
                review_data = data.get(src)
                if review_data and review_data.get("review_count"):
                    review_count = review_data["review_count"]
                    review_rating = round(review_data.get("avg_rating", 0), 1)
                    review_source = src
                    break

            # --- Social profiles & contact info ---
            social_profiles = []
            linkedin_url = None
            phone = None
            emails = []
            social_types = {"twitter", "facebook", "instagram", "pinterest",
                            "youtube", "tiktok", "snapchat"}

            for contact in data.get("contact_info", []):
                ctype = contact.get("type", "")
                if ctype in social_types:
                    social_profiles.append(SocialProfile(
                        platform=ctype,
                        url=contact.get("value"),
                        followers=contact.get("followers"),
                        posts=contact.get("posts"),
                        likes=contact.get("likes"),
                        description=contact.get("description"),
                    ))
                elif ctype == "linkedin":
                    linkedin_url = contact.get("value")
                elif ctype == "phone" and not phone:
                    phone = contact.get("value")
                elif ctype == "email":
                    email = contact.get("value")
                    if email:
                        emails.append(email)

            # --- Tech stack ---
            technologies = [
                t.get("name") for t in data.get("technologies", [])
                if t.get("name")
            ]
            technologies_full = [
                {
                    "name": t.get("name"),
                    "categories": t.get("categories", []),
                    "description": t.get("description"),
                    "installed_at": t.get("installed_at"),
                }
                for t in data.get("technologies", [])
                if t.get("name")
            ]

            # --- Features ---
            features = data.get("features", [])

            # --- Price range ---
            min_price = data.get("min_price")
            max_price = data.get("max_price")
            price_range = None
            if min_price and max_price:
                price_range = f"${min_price / 100:.0f}-${max_price / 100:.0f}"

            # --- Monthly app spend (in cents) ---
            raw_app_spend = data.get("monthly_app_spend")
            monthly_app_spend = raw_app_spend / 100 if raw_app_spend else None

            return CompanyEnrichment(
                domain=domain,
                company_name=company_name,
                website=f"https://{data.get('cluster_best_ranked', domain)}",
                industry=industry,
                description=data.get("description"),
                estimated_monthly_revenue=monthly_revenue,
                estimated_annual_revenue=annual_revenue,
                employee_count=data.get("employee_count"),
                ecommerce_platform=data.get("platform"),
                ecommerce_plan=data.get("plan"),
                platform_rank=data.get("platform_rank"),
                product_count=data.get("product_count"),
                avg_product_price=data.get("avg_price_formatted"),
                price_range=price_range,
                monthly_app_spend=monthly_app_spend,
                estimated_monthly_visits=data.get("estimated_visits"),
                estimated_monthly_pageviews=data.get("estimated_page_views"),
                review_count=review_count,
                review_rating=review_rating,
                review_source=review_source,
                logo_url=data.get("icon"),
                og_image_url=data.get("og_image"),
                social_profiles=social_profiles,
                technologies=technologies,
                technologies_full=technologies_full,
                features=features,
                phone=phone,
                emails=emails,
                country=country,
                city=city,
                state=state,
                linkedin_url=linkedin_url,
                store_created_at=data.get("created_at"),
                last_updated_at=data.get("last_updated_at"),
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"Store Leads HTTP error: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Store Leads error: {e}")
            return None
