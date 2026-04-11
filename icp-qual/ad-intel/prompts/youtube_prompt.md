# Google Ads Transparency Center Scraping Strategy

## Target URL
`https://adstransparency.google.com/`

## Navigation Flow

1. Load Transparency Center homepage
2. Enter brand name in search input
3. Wait for autocomplete/search results
4. Click the best-matching advertiser result
5. Apply filters: Platform=YouTube, Timeframe=Last 30 days
6. Extract ad cards from advertiser page

## Known Selectors (may change — heavy SPA)

- Search input: `input[type='text']`, `[role='searchbox']`
- Results: `[class*='result']`, `[role='option']`
- Ad cards: `[class*='ad-card']`, `[class*='creative']`
- Filter buttons: `button[aria-haspopup]`, `[class*='chip']`

## Filter Application

The Transparency Center uses custom dropdown widgets. The filter strategy:
1. Find buttons with text containing "format", "platform", or "type"
2. Click to open dropdown
3. Select "Video" or "YouTube" option
4. Repeat for time range, selecting "Last 30 days"

## Challenges

- DOM is heavily obfuscated — selectors break frequently
- Advertiser legal names may differ from brand names
- The SPA requires `networkidle` wait strategy
- Filter controls are custom widgets, not standard selects

## Error Handling

- Timeout: Retry search with domain root instead of brand name
- No advertiser match: Return `found: false`
- Filter failure: Continue without filters, note in logs
