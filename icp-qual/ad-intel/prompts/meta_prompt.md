# Meta Ad Library Scraping Strategy

## Target URL
```
https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=US&media_type=video&search_type=keyword_unordered&q={brand_name}
```

## Navigation Flow

1. Construct URL with pre-applied filters via query parameters
2. Load page and wait for ad cards or "no results"
3. Scroll to trigger infinite-scroll loading (up to 5 scrolls)
4. Extract ad cards

## Known Selectors (obfuscated — change frequently)

- Ad cards: `[class*='_7jvw']`, `[data-testid*='ad_card']`
- Ad text: `[class*='_7jyr']`, `span[dir='auto']`
- Video element: `video source`, `video`
- No results: `[class*='noResults']`
- Archive links: `a[href*='ads/library']`

## URL Parameters

Using query parameters avoids interacting with search/filter UI:
- `active_status=active` — Only active ads
- `ad_type=all` — All ad types
- `country=US` — US region
- `media_type=video` — Video ads only
- `search_type=keyword_unordered` — Keyword search
- `q={brand_name}` — Search query

## Infinite Scroll Handling

Meta lazy-loads ads as you scroll. Strategy:
1. Scroll to bottom of page
2. Wait 1.5 seconds for content to load
3. Repeat up to 5 times
4. Check if at bottom (no new content)

## Challenges

- Class names like `_7jvw` are build-generated and change per deploy
- May require login for some features (scraper works without login)
- Captcha/login wall possible — detected and skipped

## Error Handling

- Timeout: Retry once via page reload
- Captcha/login: Return `error: "captcha_or_login_required"`
- No results: Return `found: false`
