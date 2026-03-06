# iSpot.tv Scraping Strategy

## Target URL
`https://www.ispot.tv/search?q={brand_name}`

## Navigation Flow

1. Load search page with brand name query
2. Check for advertiser/brand page link (`a[href*='/brand/']`)
3. If found, navigate to brand page for complete ad listing
4. Extract ad cards from the page

## Known Selectors (may change)

- Search results: `.search-result`, `.browse-card`
- No results: `.no-results`
- Ad links: `a[href*='/ad/']`
- Title: `h3`, `.title`, `.card-title`
- Duration: `.duration`

## Error Handling

- Timeout: Retry once via page reload
- Captcha: Return `error: "captcha_detected"`, skip platform
- No results: Return `found: false`

## Data Extracted

- `title` — Ad creative title
- `ad_page_url` — Link to iSpot ad detail page
- `duration_seconds` — Ad length parsed from "0:30" format
