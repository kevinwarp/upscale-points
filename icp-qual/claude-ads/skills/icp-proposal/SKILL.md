---
name: icp-proposal
description: "Generates budget proposal with 3-month tiered spend (ramp/optimize/scale), channel allocation (YouTube/CTV-RT/CTV-ACQ splits), daily/weekly budget breakdowns, strategy tier recommendation, and current spend estimates. Use to build the financial case for streaming investment."
user-invokable: false
---

# Budget Proposal & Strategy

## Prerequisites

See `_lib/report-loader.md` for how to load the report JSON and fit score.

## Data Sources

| Report Field | What It Provides |
|---|---|
| `report.enrichment` | Monthly revenue (for budget tier calculation) |
| `report.brand_intel` | Purchase model, analytics maturity, brand search trend, spend estimates |

### Spend Estimate Sub-fields

From `report.brand_intel.spend_estimate`:
- `estimated_monthly_ad_spend`: total estimated ad spend
- `meta_spend`: estimated Meta spend
- `google_search_spend`: estimated Google spend
- `youtube_spend`: estimated YouTube spend
- `ctv_spend`: estimated CTV spend
- `recommended_ctv_test`: recommended CTV test budget

## Process

1. **Load report** and calculate fit score
2. **Budget tier** — calculated from `_budget_tier(monthly_rev, brand_intel)`:
   - Returns `m1`, `m2`, `m3` monthly budgets
   - Default tiers: $30K / $60K / $90K
3. **Strategy tier** — from `_spend_strategy(brand_intel, budget)`:
   - `youtube_only`: 100% YouTube, 0% CTV
   - `ctv_led`: 30% YouTube, 28% CTV-RT, 42% CTV-ACQ
   - `full_funnel`: 25% YouTube, 15% CTV-RT, 60% CTV-ACQ
4. **3 budget cards**: Month 1 (Ramp), Month 2 (Optimize), Month 3 (Scale)
5. **Allocation detail**: YT%, CTV-RT%, CTV-ACQ% with visual bar chart
6. **Campaign timing**: start date via `_campaign_start_date()`
7. **Current spend estimates**: block showing estimated monthly ad spend by channel

### Daily Spend Ramp (Month 1)

```
avg = m1_budget / 30
Week 1: avg × 0.60
Week 2: avg × 0.80
Week 3: avg × 1.00
Week 4: (m1 - spent_first_21_days) / 9
```

### Weekly Spend (12 Weeks)

```
Month 1: same ramp as daily (×7 per week)
Month 2: m2 / 4 (flat)
Month 3: m3 / 4 (flat)
```

## Output

```markdown
## Budget Proposal — {company_name}

### 3-Month Investment
| Month | Budget | Phase |
|-------|--------|-------|
| Month 1 | ${m1} | Ramp |
| Month 2 | ${m2} | Optimize |
| Month 3 | ${m3} | Scale |

### Strategy: {tier_name}
| Channel | Allocation |
|---------|-----------|
| YouTube | {yt_pct}% |
| CTV Retargeting | {ctv_rt_pct}% |
| CTV Acquisition | {ctv_acq_pct}% |

### Daily Spend — Month 1
| Week | Daily | Rationale |
|------|-------|-----------|
| Week 1 | ${w1} | Ramp (60%) |
| Week 2 | ${w2} | Ramp (80%) |
| Week 3 | ${w3} | Target (100%) |
| Week 4 | ${w4} | Remainder |

### Current Spend Estimates
- Total Monthly: ${total}
- Meta: ${meta}
- Google: ${google}
- YouTube: ${youtube}
- CTV: ${ctv}
```

## Strategy Tier Logic

- **YouTube Only**: Brand has no CTV readiness signals, start with YouTube
- **CTV-Led**: Brand has CTV signals (linear TV, competitor CTV, high revenue), lead with CTV
- **Full Funnel**: Brand is mature, has budget for full CTV+YouTube deployment
