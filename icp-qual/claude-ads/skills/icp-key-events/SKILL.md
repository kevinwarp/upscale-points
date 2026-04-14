---
name: icp-key-events
description: "12-month forward event calendar, Wayback Machine activity history, and Milled email newsletter analysis. Shows promotional intensity, BFCM activity, seasonal patterns, and site change history. Use for campaign timing and promotional calendar alignment."
user-invokable: false
---

# Key Events & Promotional Calendar

## Prerequisites

See `_lib/report-loader.md` for how to load the report JSON.

## Data Sources

| Report Field | What It Provides |
|---|---|
| `report.wayback_intel` | Historical site changes, events, promotional intensity, snapshots |
| `report.milled_intel` | Email newsletter history, BFCM detection, promo categories, email frequency |

### Key Sub-fields

**wayback_intel:**
- `found`: boolean
- `events[]`: event_name, activity_score, category, event_date, archive_url, unique_versions, snapshots_count
- `promotional_intensity`: overall intensity rating
- `active_events` / `total_events_checked` / `total_snapshots_checked`
- `years_analyzed`: how far back data goes

**milled_intel:**
- `found`: boolean
- `emails[]`: subject, date, url
- `total_emails`: count
- `milled_url`: link to Milled profile
- `has_bfcm`: boolean — detected BFCM campaigns
- `promo_categories[]`: sale, product_launch, seasonal, bfcm
- `emails_per_week`: frequency

## Process

1. **Load report** for the given domain
2. **12-month forward calendar**: 3-column grid showing ecommerce events by month with importance stars
3. **Cross-reference** Wayback events with ecommerce calendar events
4. **Wayback activity table**: events with activity dots, version counts, snapshot links
5. **Promotional intensity badge** from Wayback data
6. **Milled email analysis**: grouped by month, promotional intensity assessment
7. **BFCM flag**: highlight if brand runs BFCM campaigns
8. **Promotional intensity scoring**: evaluates promo keywords + Wayback data + email subjects

### Calendar Source

Uses `get_events_for_year()` for standard ecommerce event calendar. Calendar starts from next month, spans 12 months forward.

## Output

```markdown
## Key Events — {company_name}

### 12-Month Calendar
| Month | Events | Importance |
|-------|--------|------------|

### Wayback Activity
| Event | Activity | Versions | Snapshots |
|-------|----------|----------|-----------|
Promotional Intensity: {rating}

### Email Newsletter Analysis
- Total Emails: {count}
- Frequency: {per_week}/week
- BFCM: {yes/no}
- Categories: {sale, product_launch, seasonal}

### Monthly Email Volume
| Month | Count | Key Subjects |
|-------|-------|-------------|
```

## Use Cases

- Align CTV campaign launches with major promotional events
- Identify brands with strong BFCM activity → Q4 budget opportunity
- Use promotional frequency to estimate creative velocity needs
