"""Technology Category Index

Maps technology names to their categories for grouping in reports.
Categories sourced from StoreLeads API technology data and BuiltWith API v22.

Used by the internal report to group technologies by category instead
of showing a flat list of pills.

Hierarchy:
  1. Static TECH_CATEGORIES mapping (highest priority, ~150 known martech tools)
  2. StoreLeads API categories (returned with enrichment data)
  3. BuiltWith subcategory → display category normalization
  4. Fallback to "Other"
"""

from data.builtwith_categories import BUILTWITH_CATEGORIES, SUBCATEGORY_LOOKUP

# Category display order and colors for the internal report
CATEGORY_COLORS: dict[str, str] = {
    "Advertising": "#EEF4FF",
    "Analytics": "#F0FDF4",
    "Attribution": "#FFF7ED",
    "CRM": "#FDF2F8",
    "Customer Data Platform": "#F5F3FF",
    "Email Marketing": "#ECFDF5",
    "SMS": "#FEF3C7",
    "Reviews": "#F0F9FF",
    "Loyalty & Rewards": "#FFF1F2",
    "Payments": "#F0FDF4",
    "Fulfillment": "#F8FAFC",
    "Customer Support": "#FEF9C3",
    "Personalization": "#EDE9FE",
    "A/B Testing": "#DBEAFE",
    "Tag Management": "#E0E7FF",
    "Consent Management": "#F1F5F9",
    "Appointment Scheduling": "#FCE7F3",
    "Social Commerce": "#CCFBF1",
    "Referral": "#FEE2E2",
    "Subscription": "#D1FAE5",
    "Search": "#FEF3C7",
    "Content Management": "#E0F2FE",
    "Chat & Messaging": "#F3E8FF",
    "eCommerce": "#FFF7ED",
    "Shipping": "#F0F9FF",
    "JavaScript": "#DBEAFE",
    "Frameworks": "#E0E7FF",
    "Video & Media": "#FCE7F3",
    "Hosting": "#F1F5F9",
    "Email Hosting": "#ECFDF5",
    "SSL & Security": "#F8FAFC",
    "Other": "#F3F4F6",
}

# ── BuiltWith category ID → display category mapping ───────────
# Maps BuiltWith top-level group IDs to our display category names.
# This normalizes the 22 BuiltWith groups into our display taxonomy.
BUILTWITH_GROUP_TO_DISPLAY: dict[str, str] = {
    "analytics": "Analytics",
    "ads": "Advertising",
    "ns": "Hosting",
    "widgets": "Other",        # Widgets is too broad; subcategories get remapped below
    "payment": "Payments",
    "hosting": "Hosting",
    "docinfo": "Other",
    "mx": "Email Hosting",
    "shop": "eCommerce",
    "mapping": "Other",
    "link": "Other",
    "cms": "Content Management",
    "Web Server": "Hosting",
    "agency": "Other",
    "javascript": "JavaScript",
    "media": "Video & Media",
    "Server": "Hosting",
    "ssl": "SSL & Security",
    "framework": "Frameworks",
    "cdns": "Hosting",
    "shipping": "Shipping",
    "robots": "Other",
}

# ── BuiltWith subcategory ID → display category overrides ──────
# For subcategories where the parent group mapping is too broad
# (especially "widgets" and "analytics" which contain everything)
BUILTWITH_SUB_TO_DISPLAY: dict[str, str] = {
    # Analytics subcategories → more specific display categories
    "a/b-testing": "A/B Testing",
    "tag-management": "Tag Management",
    "crm": "CRM",
    "customer-data-platform": "Customer Data Platform",
    "personalization": "Personalization",
    "email-marketing": "Email Marketing",
    "sms-marketing": "SMS",
    "lead-generation": "Analytics",
    "conversion-optimization": "Analytics",
    "marketing-automation": "Analytics",
    "social-commerce": "Social Commerce",
    "subscription-management": "Subscription",
    "review-management": "Reviews",
    "loyalty-management": "Loyalty & Rewards",
    "referral-marketing": "Referral",
    "privacy-compliance": "Consent Management",
    "live-chat": "Chat & Messaging",
    "on-site-search": "Search",
    # Widget subcategories → specific display categories
    "chatbot": "Chat & Messaging",
    "customer-service-platform": "Customer Support",
    "help-desk-software": "Customer Support",
    "appointment-booking": "Appointment Scheduling",
    "call-tracking": "Analytics",
    "feedback-forms-and-surveys": "Analytics",
    "payment-processing": "Payments",
    "shipping-management": "Shipping",
    "email-validation": "Email Marketing",
    "push-notifications": "Analytics",
    "social-proof": "Reviews",
    "testimonial-management": "Reviews",
    "form-builder": "Analytics",
    "seo-management": "Analytics",
    "video-engagement-platform": "Video & Media",
    "webinar-platform": "Video & Media",
    # Payment subcategories
    "checkout-buttons": "Payments",
    "payments-processor": "Payments",
    "pay-later": "Payments",
    "digital-wallets": "Payments",
    # eCommerce subcategories
    "shopify-app": "eCommerce",
    "shopify-theme": "eCommerce",
    "woocommerce-extension": "eCommerce",
    "inventory-management": "Fulfillment",
    "order-management": "Fulfillment",
    "order-management-system": "Fulfillment",
    "post-purchase-solutions": "Fulfillment",
    "returns-management": "Fulfillment",
}

# Known technology -> category mapping
# When a tech is looked up here first; if not found, use the StoreLeads
# category data from the API response (stored on CompanyEnrichment)
TECH_CATEGORIES: dict[str, str] = {
    # Advertising
    "Google Ads": "Advertising",
    "Meta Pixel": "Advertising",
    "Facebook Pixel": "Advertising",
    "AppLovin AXON Pixel": "Advertising",
    "TikTok Pixel": "Advertising",
    "Pinterest Tag": "Advertising",
    "Snapchat Pixel": "Advertising",
    "Twitter Pixel": "Advertising",
    "Criteo": "Advertising",
    "AdRoll": "Advertising",
    "Taboola": "Advertising",
    "Outbrain": "Advertising",
    "StackAdapt": "Advertising",
    "The Trade Desk": "Advertising",
    "Blotout": "Advertising",

    # CTV / Streaming (competitors)
    "Tatari": "Advertising",
    "Tatari Pixel": "Advertising",
    "MNTN": "Advertising",
    "MNTN Pixel": "Advertising",
    "SteelHouse": "Advertising",
    "Steelhouse": "Advertising",
    "tvScientific": "Advertising",
    "tvScientific Pixel": "Advertising",
    "Vibe": "Advertising",
    "Vibe Pixel": "Advertising",
    "Universal Ads": "Advertising",
    "Universal Ads Pixel": "Advertising",
    "FreeWheel": "Advertising",

    # Analytics
    "Google Analytics": "Analytics",
    "Google Analytics 4": "Analytics",
    "Google Tag Manager": "Tag Management",
    "Heap": "Analytics",
    "Hotjar": "Analytics",
    "Lucky Orange": "Analytics",
    "Crazy Egg": "Analytics",
    "FullStory": "Analytics",
    "Amplitude": "Analytics",
    "Mixpanel": "Analytics",
    "Segment": "Customer Data Platform",
    "mParticle": "Customer Data Platform",
    "Tealium": "Customer Data Platform",
    "Rudderstack": "Customer Data Platform",

    # Attribution
    "Elevar": "Attribution",
    "Triple Whale": "Attribution",
    "Northbeam": "Attribution",
    "Rockerbox": "Attribution",
    "Hyros": "Attribution",
    "Wicked Reports": "Attribution",
    "Attribution App": "Attribution",
    "Measured": "Attribution",

    # Email Marketing
    "Klaviyo": "Email Marketing",
    "Mailchimp": "Email Marketing",
    "Omnisend": "Email Marketing",
    "Drip": "Email Marketing",
    "Privy": "Email Marketing",
    "Retention.com": "Email Marketing",
    "Sendlane": "Email Marketing",
    "Postscript": "SMS",
    "Attentive": "SMS",
    "Recart": "SMS",
    "SMSBump": "SMS",

    # Reviews
    "Yotpo": "Reviews",
    "Okendo": "Reviews",
    "Judge.me": "Reviews",
    "Stamped": "Reviews",
    "Loox": "Reviews",
    "Reviews.io": "Reviews",
    "Trustpilot": "Reviews",
    "Bazaarvoice": "Reviews",

    # Loyalty
    "Smile.io": "Loyalty & Rewards",
    "LoyaltyLion": "Loyalty & Rewards",
    "Yotpo Loyalty": "Loyalty & Rewards",
    "Rise.ai": "Loyalty & Rewards",

    # Subscription
    "Recharge": "Subscription",
    "Bold Subscriptions": "Subscription",
    "Ordergroove": "Subscription",
    "Skio": "Subscription",
    "Loop Subscriptions": "Subscription",
    "Smartrr": "Subscription",
    "Stay AI": "Subscription",

    # Payments
    "Shopify Payments": "Payments",
    "Shop Pay": "Payments",
    "Afterpay": "Payments",
    "Klarna": "Payments",
    "Affirm": "Payments",
    "Sezzle": "Payments",
    "PayPal": "Payments",
    "Stripe": "Payments",

    # Fulfillment
    "ShipStation": "Fulfillment",
    "Arrive": "Fulfillment",
    "Narvar": "Fulfillment",
    "AfterShip": "Fulfillment",
    "Route": "Fulfillment",
    "Malomo": "Fulfillment",
    "Loop Returns": "Fulfillment",
    "Returnly": "Fulfillment",

    # Personalization
    "Nosto": "Personalization",
    "Dynamic Yield": "Personalization",
    "Rebuy": "Personalization",
    "LimeSpot": "Personalization",
    "Searchspring": "Search",
    "Algolia": "Search",
    "Klevu": "Search",

    # A/B Testing
    "Google Optimize": "A/B Testing",
    "Optimizely": "A/B Testing",
    "VWO": "A/B Testing",
    "Convert": "A/B Testing",
    "Intelligems": "A/B Testing",
    "Shoplift": "A/B Testing",

    # Social Commerce
    "Instagram Shopping": "Social Commerce",
    "TikTok Shop": "Social Commerce",
    "Gatsby": "Social Commerce",

    # Referral
    "ReferralCandy": "Referral",
    "Friendbuy": "Referral",

    # Chat & Support
    "Gorgias": "Customer Support",
    "Zendesk": "Customer Support",
    "Intercom": "Chat & Messaging",
    "Tidio": "Chat & Messaging",
    "Kustomer": "Customer Support",
    "Reamaze": "Customer Support",

    # Consent
    "OneTrust": "Consent Management",
    "Cookiebot": "Consent Management",
    "TrustArc": "Consent Management",
    "reCAPTCHA": "Consent Management",

    # CRM
    "HubSpot": "CRM",
    "Salesforce": "CRM",

    # Content
    "Contentful": "Content Management",
    "Sanity": "Content Management",

    # Scheduling
    "Acuity Scheduling": "Appointment Scheduling",
    "Calendly": "Appointment Scheduling",

    # Hosting / CDN / Infrastructure
    "Cloudflare": "Hosting",
    "Cloudflare CDN": "Hosting",
    "Fastly": "Hosting",
    "Akamai": "Hosting",
    "Amazon CloudFront": "Hosting",
    "AWS": "Hosting",
    "Google Cloud": "Hosting",
    "Vercel": "Hosting",
    "Netlify": "Hosting",
    "Heroku": "Hosting",

    # Additional Advertising Pixels
    "Google Ads Pixel": "Advertising",
    "Google Adsense": "Advertising",
    "Pinterest Pixel": "Advertising",
    "ShareASale": "Advertising",
    "Rokt": "Advertising",
    "Superfiliate": "Referral",

    # Analytics (additional)
    "Snowplow": "Analytics",
    "Heatmap": "Analytics",
    "PostPilot": "Analytics",

    # Customer Support (additional)
    "Richpanel": "Customer Support",

    # Chat & Messaging (additional)
    "Octane AI": "Chat & Messaging",
    "Wunderkind": "Email Marketing",
    "WisePops": "Analytics",

    # Video & Media
    "YouTube Player": "Video & Media",
    "Vimeo": "Video & Media",
    "Wistia": "Video & Media",
    "Brightcove": "Video & Media",

    # eCommerce tools
    "Global-e": "eCommerce",
    "Shopify": "eCommerce",
    "Shopify Plus": "eCommerce",
    "WooCommerce": "eCommerce",
    "BigCommerce": "eCommerce",
    "Magento": "eCommerce",

    # Fraud / Security
    "Kount": "SSL & Security",
    "NoFraud": "SSL & Security",
    "Signifyd": "SSL & Security",

    # Reviews (additional)
    "Junip": "Reviews",

    # Payments (additional)
    "PayPal Express Checkout": "Payments",
    "Apple Pay": "Payments",
    "Google Pay": "Payments",
    "Amazon Pay": "Payments",
}


def _normalize_api_category(raw_category: str) -> str:
    """Normalize a StoreLeads/BuiltWith API category string to a display category.

    Checks subcategory overrides first, then group-level mapping, then returns as-is.
    """
    slug = raw_category.lower().replace(" ", "-")

    # Check subcategory-level overrides first (most specific)
    if slug in BUILTWITH_SUB_TO_DISPLAY:
        return BUILTWITH_SUB_TO_DISPLAY[slug]

    # Check if it's a known subcategory in the BuiltWith taxonomy
    if slug in SUBCATEGORY_LOOKUP:
        parent_id, _sub_name = SUBCATEGORY_LOOKUP[slug]
        return BUILTWITH_GROUP_TO_DISPLAY.get(parent_id, raw_category)

    # Check if the raw string matches a display category directly
    if raw_category in CATEGORY_COLORS:
        return raw_category

    # Check group-level mapping by name match
    for cat in BUILTWITH_CATEGORIES:
        if raw_category.lower() == cat["name"].lower():
            return BUILTWITH_GROUP_TO_DISPLAY.get(cat["id"], raw_category)

    return raw_category


def categorize_tech(tech_name: str, api_categories: list[str] | None = None) -> str:
    """Return the display category for a technology name.

    Priority:
      1. Static TECH_CATEGORIES mapping (~150 known martech tools)
      2. StoreLeads/BuiltWith API categories (normalized through BuiltWith taxonomy)
      3. Fallback to 'Other'
    """
    if tech_name in TECH_CATEGORIES:
        return TECH_CATEGORIES[tech_name]
    if api_categories:
        # Normalize through BuiltWith taxonomy
        return _normalize_api_category(api_categories[0])
    return "Other"


def group_technologies(
    tech_names: list[str],
    tech_with_categories: list[dict] | None = None,
) -> dict[str, list[str]]:
    """Group a list of technology names by category.

    Args:
        tech_names: List of technology name strings
        tech_with_categories: Optional list of dicts with 'name' and 'categories' keys
            (from StoreLeads API response, stored on enrichment)

    Returns:
        Dict of category -> list of tech names, sorted by CATEGORY_COLORS order
    """
    # Build lookup from API data
    api_lookup: dict[str, list[str]] = {}
    if tech_with_categories:
        for t in tech_with_categories:
            name = t.get("name", "")
            cats = t.get("categories", [])
            if name and cats:
                api_lookup[name] = cats

    groups: dict[str, list[str]] = {}
    for name in tech_names:
        cat = categorize_tech(name, api_lookup.get(name))
        groups.setdefault(cat, []).append(name)

    # Sort by CATEGORY_COLORS order
    ordered = {}
    for cat in CATEGORY_COLORS:
        if cat in groups:
            ordered[cat] = sorted(groups[cat])
    # Add any categories not in the color map
    for cat in sorted(groups):
        if cat not in ordered:
            ordered[cat] = sorted(groups[cat])

    return ordered
