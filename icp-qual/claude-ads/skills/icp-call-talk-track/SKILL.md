---
name: icp-call-talk-track
description: "Generates personalized call prep: 3 opening insights based on company data, 5 discovery questions, 3 proof points (Branch/fatty15/Newton case studies), and a recommended next-step CTA. Use before sales calls for data-driven conversation starters."
user-invokable: false
---

# Call Talk Track

## Prerequisites

See `_lib/report-loader.md` for how to load the report JSON and fit score.

## Data Sources

| Report Field | What It Provides |
|---|---|
| `report.enrichment` | Revenue (annual/monthly), ecommerce platform |
| `report.brand_intel` | competitors_on_ctv, analytics_maturity |
| `report.channel_mix` | has_meta, has_linear |
| `report.company_name` | Brand name for personalization |
| `report.domain` | Domain for reference |
| `fit` | UpscaleFitResult (overall context) |

## Process

1. **Load report** and calculate fit score
2. **Generate 3 opening insights** — personalized conversation starters based on:
   - Revenue scale (if >$1M/mo, reference "at your scale...")
   - Competitor CTV presence (if competitors running CTV, create urgency)
   - Meta activity (if heavy Meta, pitch channel diversification)
   - Shopify platform (if Shopify, reference native integration)
   - Analytics maturity (if advanced, lead with measurement depth)
3. **5 discovery questions**: standard qualification questions with context-aware framing
4. **3 proof points**: hardcoded case studies
   - Branch Furniture: $50K savings, 6.2x ROAS, 500+ purchases/month
   - fatty15: 3.65x blended ROAS, 69% first-time buyers
   - Newton Baby: 40% lower CPA
5. **Recommended CTA**: next-step suggestion on dark background, references Shopify data flow

## Output

```markdown
## Call Talk Track — {company_name}

### Opening Insights
1. {personalized_insight_based_on_revenue}
2. {personalized_insight_based_on_competitors_or_channels}
3. {personalized_insight_based_on_platform_or_maturity}

### Discovery Questions
1. How are you currently measuring the impact of upper-funnel spend?
2. What's your creative production process and cost per asset?
3. Have you tested CTV/streaming before? What were the results?
4. How does your current attribution stack handle view-through conversions?
5. What does your Q{next_quarter} media plan look like?

### Proof Points
- **Branch Furniture:** $50K savings, 6.2x ROAS, 500+ purchases/month
- **fatty15:** 3.65x blended ROAS, 69% first-time buyers
- **Newton Baby:** 40% lower CPA vs previous CTV vendor

### Recommended Next Step
{CTA referencing Shopify data flow or demo}
```

## Personalization Rules

- If `has_linear` = true: reference existing TV investment, pitch streaming as complement
- If `competitors_on_ctv` not empty: name competitors, create competitive urgency
- If `ecommerce_platform` = Shopify: lead with native integration, deterministic attribution
- If `analytics_maturity` = advanced: emphasize incrementality and holdout testing
- If `estimated_annual_revenue` > $12M: reference "at your scale" framing
