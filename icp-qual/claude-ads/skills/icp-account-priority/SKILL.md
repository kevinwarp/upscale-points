---
name: icp-account-priority
description: "Calculates account priority level (High/Medium/Low) based on fit score, revenue scale, Shopify usage, CTV competitor presence, ad activity, contact availability, and CRM status. Shows priority banner with justification and signal breakdown. Use for pipeline prioritization and routing."
user-invokable: false
---

# Account Priority Signal

## Prerequisites

See `_lib/report-loader.md` for how to load the report JSON and fit score.

## Data Sources

| Report Field | What It Provides |
|---|---|
| `report.enrichment` | Revenue (annual), ecommerce platform |
| `report.brand_intel` | competitors_on_ctv |
| `report.channel_mix` | total_ads_found, has_linear |
| `report.competitor_detection` | Detected CTV competitors |
| `report.contact_intel` | Contact availability |
| `report.company_pulse` | CRM status |
| `fit.total_score` | 0-100 qualification score |
| `fit.grade` | A-F grade |

## Process

1. **Load report** and calculate fit score
2. **Evaluate positive signals** (+):
   - Revenue > $5M annual
   - Shopify platform
   - Competitor CTV activity (urgency)
   - Active ad presence (>10 ads)
   - Contacts available (>2 discovered)
   - CRM status active/engaged
3. **Evaluate risk signals** (-):
   - CTV competitor detected (displacement sale = harder)
   - Low ad activity (<5 ads)
   - No contacts found
   - CRM status cold/unresponsive
   - Low revenue scale
4. **Priority determination**:
   - **High**: fit score >= 70 AND positive signals >= 4
   - **Medium**: fit score >= 45 OR positive signals >= 3
   - **Low**: everything else
5. **Justification text**: 1-2 sentence summary of why this priority level
6. **Signal grid**: two-column positive vs risk signals

## Output

```markdown
## Account Priority — {company_name}

### Priority: {HIGH / MEDIUM / LOW}
**Fit Score:** {score}/100 ({grade})

{justification_text}

### Positive Signals
✅ {signal_1}
✅ {signal_2}
✅ {signal_3}

### Risk Signals
⚠️ {risk_1}
⚠️ {risk_2}
```

## Priority Actions

- **High Priority**: immediate outreach, personalized pitch, multi-thread buying committee
- **Medium Priority**: sequence into nurture campaign, send pitch report, follow up in 1-2 weeks
- **Low Priority**: add to long-term nurture, revisit quarterly, watch for trigger events
