---
name: icp-hiring
description: "Analyzes hiring signals: open jobs count, hiring velocity, headcount growth trends, and marketing/growth role listings. Indicates company growth trajectory and potential need for marketing services. Use to gauge timing and budget signals."
user-invokable: false
---

# Hiring Signals

## Prerequisites

See `_lib/report-loader.md` for how to load the report JSON.

## Data Sources

| Report Field | What It Provides |
|---|---|
| `report.hiring_intel` | Open jobs count, hiring velocity, headcount growth (12m/24m), marketing job listings |

### Key Sub-fields

- `found`: boolean
- `open_jobs_count`: total open positions
- `hiring_velocity`: "accelerating" / "stable" / "slowing"
- `headcount_growth_12m`: percentage growth last 12 months
- `headcount_growth_24m`: percentage growth last 24 months
- `marketing_jobs[]`: title, location

## Process

1. **Load report** for the given domain
2. **Check** `hiring_intel.found` — if false, output "No hiring data available"
3. **KPI grid**: open jobs count, hiring velocity badge, 12-month growth %, 24-month growth %
4. **Marketing & growth roles**: list up to 8 marketing/growth job titles with locations
5. **Color-code velocity**: accelerating=green, stable=teal, slowing=warning
6. **Color-code growth**: >20%=green, 5-20%=teal, <5%=warning, negative=red

## Output

```markdown
## Hiring Signals — {company_name}

### KPIs
| Metric | Value |
|--------|-------|
| Open Jobs | {count} |
| Hiring Velocity | {velocity} |
| 12-Month Growth | {pct}% |
| 24-Month Growth | {pct}% |

### Marketing & Growth Roles
- {title} — {location}
- ...
```

## Interpretation

- **Accelerating** hiring + marketing roles = growing team, likely increasing ad spend
- **Slowing** hiring = potential budget constraints, adjust pitch accordingly
- **Marketing roles open** = actively building capability, strong timing signal
