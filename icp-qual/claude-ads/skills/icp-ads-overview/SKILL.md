---
name: icp-ads-overview
description: "Summarizes ad discovery across iSpot (CTV/linear), YouTube, and Meta. Shows channel mix, ad counts, status, and clickable ad listings per platform. Use for quick view of current advertising activity and platform presence."
user-invokable: false
---

# Ad Discovery Overview

## Prerequisites

See `_lib/report-loader.md` for how to load the report JSON.

## Data Sources

| Report Field | What It Provides |
|---|---|
| `report.ispot_ads` | iSpot CTV/linear ad data (ads, scrape duration) |
| `report.youtube_ads` | YouTube ad transparency data |
| `report.meta_ads` | Meta ad transparency data |
| `report.channel_mix` | Aggregate: total platforms, total ads, has_linear, has_youtube, has_meta |

### Per-Ad Fields

- `title`: ad creative title
- `ad_page_url`: link to ad detail page
- `start_date`: when the ad started running

## Process

1. **Load report** for the given domain
2. **Channel mix summary**: total platforms active, total ads found, linear/YouTube/Meta booleans
3. **iSpot block**: ad count, found status, scrape duration, ad listing (up to 30)
4. **YouTube block**: ad count, found status, ad listing (up to 30)
5. **Meta block**: ad count, found status, ad listing (up to 30)
6. **Collapse** each platform's ad list after 5 items

## Output

```markdown
## Ad Discovery — {company_name}

**Channel Mix:** {total_platforms} platforms · {total_ads} ads found
Linear: {yes/no} · YouTube: {yes/no} · Meta: {yes/no}

### iSpot (CTV/Linear) — {count} ads
- [{title}]({url}) — {start_date}
- ...

### YouTube — {count} ads
- [{title}]({url}) — {start_date}
- ...

### Meta — {count} ads
- [{title}]({url}) — {start_date}
- ...
```

## Interpretation

- **No iSpot ads** = no CTV presence → primary Upscale opportunity
- **Linear TV present** = existing TV budget that could shift to streaming
- **Meta-heavy / No YouTube** = opportunity to expand to video/CTV
- **High ad count** = active advertiser, likely has budget for new channels
