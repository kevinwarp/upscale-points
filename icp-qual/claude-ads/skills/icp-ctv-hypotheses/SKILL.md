---
name: icp-ctv-hypotheses
description: "Generates CTV/YouTube investment hypotheses: why now reasons, best products for TV, creative angles, and suggested test budget range. Personalized based on industry, revenue, competitor activity, purchase model, and promotional calendar. Use to build the strategic case for streaming investment."
user-invokable: false
---

# CTV/YouTube Hypotheses

## Prerequisites

See `_lib/report-loader.md` for how to load the report JSON and fit score.

## Data Sources

| Report Field | What It Provides |
|---|---|
| `report.enrichment` | Industry, monthly revenue, avg product price, reviews, ecommerce platform |
| `report.brand_intel` | competitors_on_ctv, purchase_model, recommended CTV test spend, analytics_maturity |
| `report.channel_mix` | has_linear, has_meta |
| `report.milled_intel` | has_bfcm, promo_categories |
| `report.company_name` | Brand name |
| `fit` | UpscaleFitResult |

## Process

1. **Load report** and calculate fit score
2. **"Why CTV/YouTube Now" bullet reasons** — dynamically generated based on:
   - No CTV presence (greenfield opportunity)
   - Competitor CTV activity (competitive urgency)
   - Revenue scale >= $500K/month (budget justification)
   - Meta presence without CTV (channel diversification)
   - BFCM history (Q4 budget opportunity)
   - Analytics maturity (measurement readiness)
3. **"Best Products for TV" bullets** — driven by purchase model:
   - Subscription → hero product, subscription value prop, LTV story
   - High repurchase → best-sellers, variety packs, bundles
   - One-time → flagship product, premium positioning
4. **"Creative Angles for CTV" bullets** — based on:
   - Review rating (if high, use social proof angle)
   - Review count (if high, use testimonial angle)
   - Industry vertical (match to proven CTV creative patterns)
5. **Suggested test budget range** — derived from `brand_intel.spend_estimate.recommended_ctv_test`:
   - Low end: recommended × 0.8
   - High end: recommended × 1.5
   - Default: $15K-$50K/month if no estimate available

## Output

```markdown
## CTV/YouTube Hypotheses — {company_name}

### Why CTV/YouTube Now
- {reason_1_based_on_data}
- {reason_2_based_on_competitors}
- {reason_3_based_on_revenue_scale}
- ...

### Best Products for TV
- {product_suggestion_based_on_purchase_model}
- ...

### Creative Angles
- {angle_based_on_reviews_or_industry}
- ...

### Suggested Test Budget
**${low}K — ${high}K / month**
Based on: {rationale from spend estimate or industry benchmark}
```

## Hypothesis Framework

Each hypothesis should follow: **Signal → Opportunity → Expected Outcome**

Example: "Competitors (Casper, Purple) are running CTV → Greenfield opportunity for {brand} to capture streaming audience share → Expected 3-5x ROAS based on similar DTC brands in the {industry} vertical"
