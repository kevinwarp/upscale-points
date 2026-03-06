import re
from urllib.parse import urlparse


def normalize_domain(raw: str) -> str:
    """
    Accepts various URL formats and returns a clean domain.

    'https://www.brand.com/shop' -> 'brand.com'
    'www.brand.com' -> 'brand.com'
    'brand.com' -> 'brand.com'
    """
    raw = raw.strip().lower()
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    parsed = urlparse(raw)
    hostname = parsed.hostname or raw
    if hostname.startswith("www."):
        hostname = hostname[4:]
    return hostname


def domain_to_brand_guess(domain: str) -> str:
    """
    Derive a likely brand name from a domain.

    'acme-widgets.com' -> 'Acme Widgets'
    'nike.com' -> 'Nike'
    """
    name = domain.split(".")[0]
    name = re.sub(r"[-_]", " ", name)
    return name.title()


def safe_filename(domain: str) -> str:
    """Sanitize a domain for use as a filename."""
    return re.sub(r"[^a-z0-9.-]", "_", domain.lower())
