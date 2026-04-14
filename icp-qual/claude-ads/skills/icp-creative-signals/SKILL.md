---
name: icp-creative-signals
description: "Analyzes creative format mix, average duration, messaging themes, and promotional patterns across Meta/iSpot/YouTube ads and Milled emails. Shows format distribution, theme intensity chart, and offer patterns. Use to understand creative strategy and identify gaps."
user-invokable: false
---

# Creative & Messaging Signals

## Prerequisites

See `_lib/report-loader.md` for how to load the report JSON.

## Data Sources

| Report Field | What It Provides |
|---|---|
| `report.meta_ads.ads[]` | Meta ad format, title, video_url, duration |
| `report.ispot_ads.ads[]` | iSpot ad format, title, duration |
| `report.youtube_ads.ads[]` | YouTube ad format, title, duration |
| `report.milled_intel` | Email subjects, promo categories, emails per week |
| `report.enrichment` | Supporting firmographic context |

## Process

1. **Load report** for the given domain
2. **Format analysis**: classify each ad as Video / Static Image / Carousel / Other based on format field and video_url presence
3. **Format distribution**: count and show as pills with percentages
4. **Duration stats**: average video duration across all platforms
5. **Messaging theme detection**: scan ad titles + email subjects for theme keywords
6. **Theme scoring**: rate each theme's intensity (0-100) based on keyword frequency
7. **Offer & promotion patterns**: extract from Milled promo_categories (sale, BFCM, product_launch, seasonal)

### Messaging Themes

| Theme | Keywords |
|-------|----------|
| Price | sale, discount, off, save, deal, free, BOGO |
| Quality | premium, quality, best, luxury, crafted, artisan |
| Outcomes | results, transform, before/after, proven, works |
| Trust | reviews, rated, award, certified, guarantee, warranty |
| Speed/Convenience | fast, easy, simple, delivered, instant, hassle-free |

## Output

```markdown
## Creative & Messaging Signals — {company_name}

### Format Mix
- Video: {n} ({pct}%)
- Static Image: {n} ({pct}%)
- Carousel: {n} ({pct}%)
- Other: {n} ({pct}%)

**Avg Video Duration:** {seconds}s

### Messaging Themes
| Theme | Intensity |
|-------|-----------|
| Price | ████░░░░░░ 40% |
| Quality | ██████░░░░ 60% |
| Outcomes | ████████░░ 80% |
| Trust | ███░░░░░░░ 30% |
| Speed | █████░░░░░ 50% |

### Offers & Promotions
- {category}: detected
- BFCM: {yes/no}
- Email Frequency: {per_week}/week
```

## Interpretation

- **Heavy video, no CTV** = creative assets exist, low barrier to CTV entry
- **Price-dominant messaging** = discount-driven brand, pitch ROAS/incrementality
- **Outcomes-dominant** = testimonial-ready, pitch CTV storytelling
- **High email frequency** = active promotional calendar, align CTV with promotions
