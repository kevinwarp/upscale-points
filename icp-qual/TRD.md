# Technical Requirements Document — Ad Intelligence Pipeline

## 1. Architecture Overview

The pipeline is a local Python application that orchestrates one API call and three parallel browser scraping jobs. It uses a single Chromium process with isolated browser contexts for each scraper, connected by an async orchestrator.

```
                    ┌─────────────┐
                    │   main.py   │  CLI entrypoint
                    │  (argparse) │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ orchestrator │  Pipeline coordinator
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼────┐ ┌────▼─────┐ ┌────▼─────┐
        │  iSpot   │ │ YouTube  │ │   Meta   │    3 scrapers
        │ scraper  │ │ scraper  │ │ scraper  │    (parallel)
        └─────┬────┘ └────┬─────┘ └────┬─────┘
              │            │            │
        ┌─────▼────────────▼────────────▼─────┐
        │        BrowserAgent (Playwright)     │  Single Chromium
        │     1 browser, 3 isolated contexts   │  instance
        └─────────────────────────────────────┘
```

A separate async HTTP call to the Store Leads API runs before the browser launches.

## 2. Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.11+ |
| Browser automation | Playwright | >= 1.40.0 |
| HTTP client | httpx | >= 0.26.0 |
| Data models | Pydantic v2 | >= 2.5.0 |
| Environment | python-dotenv | >= 1.0.0 |
| HTML parsing | BeautifulSoup4 | >= 4.12.0 |
| Runtime | asyncio | stdlib |

## 3. Module Specifications

### 3.1 `main.py` — CLI Entrypoint

- Parses CLI arguments via `argparse`
- Loads `.env` via `python-dotenv`
- Configures logging (INFO default, DEBUG with `--verbose`)
- Calls `orchestrator.run_pipeline()` via `asyncio.run()`
- Prints summary and optionally saves JSON
- Exit code: `0` if any ads found, `1` if none

**CLI arguments:**
- `--domain` / `-d` (required): Domain to analyze
- `--save-json`: Save report to disk
- `--output` / `-o`: Custom output filename
- `--headless` / `--no-headless`: Browser visibility
- `--verbose` / `-v`: Debug logging

### 3.2 `orchestrator.py` — Pipeline Coordinator

**Flow:**
1. Normalize domain via `domain_utils.normalize_domain()`
2. Enrich via Store Leads API (async HTTP)
3. Resolve brand name: Store Leads `company_name` → fallback `domain_to_brand_guess()`
4. Launch single Chromium via `managed_browser()` context manager
5. Run 3 scrapers concurrently via `asyncio.gather()`
6. Each scraper wrapped in `_safe_scrape()` — catches all exceptions, returns empty `PlatformResult` on crash
7. Compute `ChannelMix` from results
8. Return `DomainAdReport`

**Key design decisions:**
- Single browser, 3 contexts: reduces resource usage while maintaining isolation
- `_safe_scrape()` wrapper: one scraper failure never crashes the pipeline
- Brand name resolution: API-derived name preferred over domain guess for search accuracy

### 3.3 `scraping/browser_agent.py` — Browser Lifecycle

**`BrowserAgent` class:**
- Manages one Chromium instance (`playwright.chromium.launch()`)
- Provides `new_context()` and `new_page()` async context managers
- Each context gets:
  - Viewport: 1280x800
  - Realistic user-agent string
  - Navigation timeout: 15s
  - Action timeout: 10s
  - Resource blocking: images, fonts, icons (`.png`, `.jpg`, `.svg`, `.woff`, `.woff2`, `.ttf`, `.ico`)

**`managed_browser()` top-level context manager:**
- Creates `BrowserAgent`, calls `start()`, yields, calls `stop()`
- Ensures browser cleanup even on pipeline crash

**Anti-detection:**
- `--disable-blink-features=AutomationControlled` flag
- Realistic Chrome user-agent
- Resource blocking reduces fingerprint surface

### 3.4 `scraping/ispot_scraper.py` — iSpot.tv (Linear TV)

**Strategy:**
1. Navigate to `https://www.ispot.tv/search/{brand_name}`
2. Wait for `a.card-container` or `.top-results` selectors (8s timeout, 1 retry)
3. If brand page link found (`a.card-container[href*='/brands/']`), navigate to it
4. Extract ads using two strategies:
   - `a.card-container` links (search results page)
   - `a[href*="/ad/"]` links (brand page — different DOM structure)
5. Title extraction priority: HTML `title` attribute → child heading → inner text
6. Deduplication via `seen_urls` set (only added after title confirmed)
7. Skip nav links (`/ad/top-commercials`, `/ad/top-spenders`)

**Output:** Up to 30 `Ad` objects with `title` and `ad_page_url`

### 3.5 `scraping/youtube_transparency_scraper.py` — Google Ads Transparency

**Strategy:**
1. Navigate to `https://adstransparency.google.com/?region=US&domain={domain}`
2. If no domain match, fall back to text search: type brand name into `input[type='text']`, wait 1.5s, click first `material-select-item` suggestion
3. Apply platform filter: click `platform-filter` custom element → select "YouTube" from `material-select-item` options
4. Apply date filter: click `date-range-filter` → select "last 30 days"
5. Extract from `.creative-bounding-box` elements (have `href` attribute linking to ad detail)
6. Each creative has `aria-label` like "Advertisement (1 of 80)"

**Key technical details:**
- Google Ads Transparency uses custom web components (`material-select-item`, `platform-filter`, `date-range-filter`) — standard HTML selectors don't work
- Must click suggestion items, not press Enter (search doesn't submit on Enter)
- Creative boxes use `href` attribute directly, not child links

**Output:** Up to 30 `Ad` objects with `title`, `ad_page_url`, format `"video"`

### 3.6 `scraping/meta_ad_scraper.py` — Meta Ad Library

**Strategy:**
1. Navigate to pre-constructed URL with query params:
   - `active_status=active`, `country=US`, `media_type=video`
   - `search_type=keyword_unordered`, `q={brand_name}`
2. Wait for `Library ID:` text to appear in page body (12s timeout, 1 retry)
3. Scroll 3 times (1.5s pause) to trigger lazy-loading
4. Parse page text via JS `evaluate()`:
   - Split `document.body.innerText` on `"Library ID:"` delimiters
   - For each section, extract: Library ID, start date, advertiser name, ad text
   - Strip zero-width Unicode chars via `String.fromCharCode()` regex
   - Pattern: Library ID → "Started running on {date}" → "See summary/ad details" → Advertiser → "Sponsored" → Ad text

**Key technical details:**
- Text-based parsing (not DOM selectors) — Meta's DOM is highly obfuscated with randomized class names
- Zero-width character regex uses `String.fromCharCode(0x200B, 0x200C, 0x200D, 0xFEFF)` to avoid Python/JS Unicode escape conflicts
- Branded content ads surface creator names (e.g., "Emily DiDonato with Jones Road Beauty")

**Output:** Up to 30 `Ad` objects with `title` (advertiser), `ad_page_url` (Library ID link), `start_date`, format `"video"`

### 3.7 `enrichment/storeleads_client.py` — Store Leads API

**Endpoint:** `GET https://storeleads.app/json/api/v1/all/domain/{domain}`

**Response handling:**
- Response nested under `data["domain"]` key
- Company name: `merchant_name` or `title` (cleaned of taglines with `.`, `|`, ` - ` splitting)
- Location: parsed from `"Beaverton, OR, USA"` string → city/state/country
- LinkedIn: extracted from `contact_info` array (type `"linkedin"`)
- Industry: first entry in `categories` array
- Rate limiting: 429 → single retry with `Retry-After` header
- 404 → return empty `CompanyEnrichment` (domain valid but no data)

**Authentication:** Bearer token via `STORELEADS_API_KEY` env var

### 3.8 `models/ad_models.py` — Data Models

All models use Pydantic v2 `BaseModel`:

| Model | Fields |
|-------|--------|
| `Platform` | Enum: `ISPOT`, `YOUTUBE`, `META` |
| `Ad` | `title`, `video_url`, `ad_page_url`, `start_date`, `end_date`, `format`, `duration_seconds`, `thumbnail_url` |
| `PlatformResult` | `found`, `platform`, `ads[]`, `error`, `scrape_duration_seconds` |
| `CompanyEnrichment` | `domain`, `company_name`, `website`, `industry`, `estimated_revenue`, `employee_count`, `ecommerce_platform`, `description`, `country`, `city`, `state`, `linkedin_url` |
| `ChannelMix` | `has_linear`, `has_youtube`, `has_meta`, `total_platforms`, `total_ads_found` |
| `DomainAdReport` | `domain`, `company_name`, `enrichment`, `ispot_ads`, `youtube_ads`, `meta_ads`, `channel_mix`, `running_any_ads`, `generated_at`, `pipeline_duration_seconds` |

### 3.9 `utils/domain_utils.py` — Domain Utilities

- `normalize_domain(raw)`: Strips protocol, www prefix, paths → clean domain
- `domain_to_brand_guess(domain)`: `acme-widgets.com` → `Acme Widgets` (fallback when API has no name)
- `safe_filename(domain)`: Sanitizes for filesystem use

### 3.10 `utils/json_formatter.py` — Output Formatting

- `save_report(report, filename)`: Writes JSON to `output/reports/`
- `print_summary(report)`: Prints tabular CLI summary with platform status, ad counts, timing

## 4. Concurrency Model

```
asyncio event loop
  │
  ├─ await enrich_domain()                    # Sequential: API call
  │
  ├─ async with managed_browser() as agent:   # Sequential: launch browser
  │     │
  │     ├─ asyncio.gather(                    # Parallel: 3 scrapers
  │     │     _safe_scrape(scrape_ispot),
  │     │     _safe_scrape(scrape_youtube),
  │     │     _safe_scrape(scrape_meta),
  │     │   )
  │     │
  │     └─ (browser auto-closed)
  │
  └─ compute_channel_mix()                    # Sequential: aggregate
```

- Single thread, async I/O via asyncio
- Playwright runs Chromium out-of-process
- Each scraper gets its own `BrowserContext` (isolated cookies, storage, cache)
- `asyncio.gather()` runs all three concurrently — pipeline time = slowest scraper

## 5. Error Handling

| Layer | Strategy |
|-------|----------|
| Scraper crash | `_safe_scrape()` catches all exceptions, returns empty `PlatformResult` with error string |
| Page timeout | Each scraper retries once (reload page, re-wait for selector) |
| Captcha detection | Check for `[class*='captcha']` / `[id*='captcha']`, return `captcha_detected` error |
| API rate limit | 429 → single retry with `Retry-After` delay |
| API 404 | Return empty `CompanyEnrichment` (valid domain, no data) |
| Missing env var | Log warning, skip enrichment, continue with domain-guessed brand name |

## 6. Performance Characteristics

| Metric | Typical Value |
|--------|---------------|
| Total pipeline time | 12–20 seconds |
| Store Leads API | < 1 second |
| iSpot scraper | 4–6 seconds (or 17s on timeout) |
| YouTube scraper | 10–12 seconds |
| Meta scraper | 7–10 seconds |
| Browser launch | < 1 second |
| Resource blocking savings | ~40% faster page loads |

## 7. File Output

**JSON report** (`output/reports/{domain}.json`):
- Full Pydantic model serialized via `model_dump_json(indent=2)`
- All fields included (nulls preserved for completeness)

**Markdown report** (`output/reports/{domain}.md`):
- Generated manually for Slack distribution
- Includes company overview, channel mix table, all ad links, creator partnerships, key takeaways

## 8. Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `STORELEADS_API_KEY` | Yes | API key for Store Leads company enrichment |

## 9. Dependencies

```
playwright>=1.40.0        # Browser automation
beautifulsoup4>=4.12.0    # HTML parsing (reserved for future use)
httpx>=0.26.0             # Async HTTP client
pydantic>=2.5.0           # Data validation and serialization
python-dotenv>=1.0.0      # Environment variable loading
```

Additionally requires: `playwright install chromium` after pip install.

## 10. Known Limitations

1. **iSpot.tv requires brand page navigation** — search results link to brand pages which have a different DOM than the search page. If no brand page link is found, 0 ads are returned.
2. **Meta Ad Library keyword matching** — searches by keyword, not advertiser ID. Results may include ads from other advertisers that mention the brand (e.g., resellers).
3. **YouTube ad titles are generic** — Google Ads Transparency shows "Advertisement (1 of N)" rather than actual creative titles.
4. **No ad spend data** — pipeline detects presence and volume only, not spend.
5. **Headless detection** — some sites may serve different content in headless mode. Use `--no-headless` for debugging.
6. **No pagination** — each scraper captures up to 30 ads from the initial page load + scroll.
