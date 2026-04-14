---
name: icp-competitor-alert
description: "Detects CTV/streaming competitors already working with the brand. Builds competitive intel cards with Creative Reality Matrix comparisons, sell motions, discovery questions, landmines, objection handling, and attribution model analysis. Use when a displacement sale is detected."
user-invokable: false
---

# Competitor Alert

## Prerequisites

See `_lib/report-loader.md` for how to load the report JSON.

## Data Sources

| Report Field | What It Provides |
|---|---|
| `report.competitor_detection` | Detected CTV competitors and tags matched |
| `report.domain` | Used for case study cross-reference |

### External References

- `get_case_study_brand_intel(domain)` — checks if domain appears in competitor case studies
- `get_competitor_intel(competitor_name)` — returns sell motions, discovery questions, landmines, objections
- `CREATIVE_REALITY_MATRIX` — side-by-side competitor vs Upscale creative capability comparison

### Key Sub-fields

- `competitor_detection.found`: boolean
- `competitor_detection.competitors_detected[]`: list of competitor names
- `competitor_detection.tags_matched[]`: detection evidence

## Process

1. **Load report** for the given domain
2. **Check** `competitor_detection.found` — if false, check case study intel as fallback
3. **For each detected competitor**:
   a. Pull Creative Reality Matrix (competitor vs Upscale side-by-side)
   b. Pull sell motions and discovery questions
   c. Pull landmines ("don't say" items)
   d. Pull objection/response pairs
   e. Pull attribution model comparison
4. **Case study check**: if domain appears in competitor case studies, flag as "warm prospect"
5. **Return empty** if no competitors detected AND no case study intel

## Output

```markdown
## Competitor Alert — {company_name}

### 🔴 CTV Competitor Detected: {competitor_name}

#### Creative Reality Matrix
| Capability | {Competitor} | Upscale |
|-----------|-------------|---------|
| Creative Cost | $10K+ | $500 |
| Launch Time | 6-7 weeks | 6 days |
| Variations/Month | 2-5 | 20+ |

#### Sell Motions
- ...

#### Discovery Questions
- ...

#### ⚠️ Landmines (Don't Say)
- ...

#### Objection Handling
| Objection | Response |
|-----------|----------|

#### Attribution Comparison
| Model | {Competitor} | Upscale |
|-------|-------------|---------|
```

## Alert Levels

- **Red**: Active CTV competitor detected (displacement sale)
- **Yellow**: Brand appears in competitor case studies (warm prospect, competitor may have churned)
- **None**: No competitor signals — greenfield opportunity
