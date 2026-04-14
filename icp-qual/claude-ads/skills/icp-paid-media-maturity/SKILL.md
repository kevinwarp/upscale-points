---
name: icp-paid-media-maturity
description: "Scores overall paid media maturity, CTV maturity, and YouTube maturity using a points-based system. Evaluates channel breadth, creative volume, analytics sophistication, attribution tools, and management model. Use to calibrate pitch sophistication and identify capability gaps."
user-invokable: false
---

# Paid Media Maturity Assessment

## Prerequisites

See `_lib/report-loader.md` for how to load the report JSON and fit score.

## Data Sources

| Report Field | What It Provides |
|---|---|
| `report.channel_mix` | has_meta, has_youtube, has_linear, total_platforms, total_ads_found |
| `report.brand_intel` | analytics_maturity, analytics_tools, attribution_tools |
| `report.enrichment` | employee_count (for management model inference) |
| `report.meta_ads` | Meta ad activity |
| `report.ispot_ads` | CTV/linear ad activity |
| `report.youtube_ads` | YouTube ad activity |
| `report.competitor_detection` | Competitor presence flag |
| `fit` | UpscaleFitResult (overall qualification context) |

## Process

1. **Load report** and calculate fit score
2. **Points-based maturity scoring**:
   - Channel breadth: 1 platform=+1, 2=+2, 3+=+3
   - Creative volume: <10 ads=+1, 10-50=+2, 50+=+3
   - Analytics maturity: basic=+1, intermediate=+2, advanced=+3
   - Attribution tools present: +2
   - Incrementality tools present: +1
3. **Overall maturity level**: >=9 points = High, >=5 = Medium, else Low
4. **CTV maturity**: None / Testing / Scaling / Active (based on ispot_ads presence and volume)
5. **YouTube maturity**: None / Testing / Scaling (based on youtube_ads presence and volume)
6. **Management model inference**: <20 employees = Agency, <100 = Hybrid, 100+ = In-House
7. **Maturity signal indicators**: colored dots for each signal
8. **Detail rows**: primary channels, management model, incrementality evidence, creative fatigue risk

## Scoring Algorithm

```
Points:
  channel_breadth    = min(total_platforms, 3)         # 1-3
  creative_volume    = 1 if <10, 2 if 10-50, 3 if >50 # 1-3
  analytics_level    = 1/2/3 for basic/intermediate/advanced
  has_attribution    = 2 if attribution_tools present
  has_incrementality = 1 if incrementality tools present

Total = sum(all)   # 0-12
Grade: High (>=9), Medium (>=5), Low (<5)
```

## Output

```markdown
## Paid Media Maturity — {company_name}

### Maturity Scores
| Dimension | Level |
|-----------|-------|
| Overall Maturity | {High/Medium/Low} |
| CTV Maturity | {None/Testing/Scaling/Active} |
| YouTube Maturity | {None/Testing/Scaling} |

### Maturity Signals
🟢 {positive_signal}
🟡 {neutral_signal}
🔴 {negative_signal}

### Details
- Primary Channels: {channels}
- Management Model: {Agency/Hybrid/In-House}
- Incrementality Evidence: {yes/no}
- Creative Fatigue Risk: {low/medium/high}
```

## Pitch Calibration

- **High maturity** → lead with incrementality, attribution depth, Shopify integration
- **Medium maturity** → lead with measurement simplicity, creative velocity
- **Low maturity** → lead with managed service, creative-included, easy onboarding
