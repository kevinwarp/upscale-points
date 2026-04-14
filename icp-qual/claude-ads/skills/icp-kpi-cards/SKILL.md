---
name: icp-kpi-cards
description: "Generates 5 headline KPI cards: Fit Score (grade-colored), Monthly DTC Revenue, Monthly Visits, Ads Discovered, and Promotional Activity. Provides at-a-glance qualification metrics for any domain. Use as a dashboard header or standalone quick check."
user-invokable: false
---

# KPI Cards

## Prerequisites

See `_lib/report-loader.md` for how to load the report JSON and fit score.

## Data Sources

| Report Field | What It Provides |
|---|---|
| `report.enrichment` | Monthly/annual revenue, monthly visits |
| `report.channel_mix` | Total ads found, total platforms |
| `fit.grade` | A-F qualification grade |
| `fit.total_score` | 0-100 numeric score |

### Promotional Activity Assessment

Uses `_assess_promotional_intensity(report)` which evaluates:
- Promo keywords in Milled email subjects
- Wayback data activity scores
- BFCM detection
- Returns qualitative rating: "Heavy", "Moderate", "Light", "Unknown"

## Process

1. **Load report** and calculate fit score
2. **Card 1 — Fit Score**: grade letter (A-F) with grade color, numeric score underneath
3. **Card 2 — Monthly DTC Revenue**: formatted dollar amount, annual revenue as sub-text
4. **Card 3 — Monthly Visits**: formatted number with K/M suffix
5. **Card 4 — Ads Discovered**: total count with platform count as sub-text
6. **Card 5 — Promotional Activity**: qualitative assessment from promotional intensity scoring

## Output

```markdown
## KPI Dashboard — {company_name}

| Metric | Value | Detail |
|--------|-------|--------|
| Fit Score | {grade} | {score}/100 |
| Monthly Revenue | ${amount} | ${annual}/yr |
| Monthly Visits | {visits} | — |
| Ads Discovered | {count} | {platforms} platforms |
| Promo Activity | {Heavy/Moderate/Light} | — |
```

## Formatting

- Grade colors: A=#027A48, B=#0A6D86, C=#B54708, D=#B42318, F=#B42318
- Money: `$30K`, `$1.2M`
- Visits: `125K`, `2.3M`
- Missing data: show "—"
