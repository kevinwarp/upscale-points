---
name: icp-gaps-analysis
description: "Identifies qualification gaps and opportunities: missing CTV/YouTube presence, revenue scale concerns, digital maturity gaps, reputation risks, and seasonal planning blind spots. Shows opportunity cards (green) and gap cards (neutral). Use to prioritize pitch angles and identify deal risks."
user-invokable: false
---

# Gaps & Opportunities Analysis

## Prerequisites

See `_lib/report-loader.md` for how to load the report JSON and fit score.

## Data Sources

| Report Field | What It Provides |
|---|---|
| `report.channel_mix` | has_linear, has_youtube |
| `report.enrichment` | Monthly revenue, review rating, review source |
| `report.milled_intel` | Email marketing data presence |
| `fit.categories[]` | Per-category scores for threshold checks |

## Process

1. **Load report** and calculate fit score
2. **Evaluate 7 conditions** — each produces an Opportunity or Gap card:

| # | Condition | Type | Card |
|---|-----------|------|------|
| 1 | No CTV (no iSpot ads) | Opportunity | Primary CTV opportunity — greenfield market |
| 2 | No YouTube (no YT ads) | Opportunity | YouTube opportunity — untapped video channel |
| 3 | Linear TV without YouTube | Opportunity | Complement linear with streaming |
| 4 | Revenue < $500K/month | Gap | Budget constraint — may need smaller test |
| 5 | Digital Maturity score < 40 | Gap | Infrastructure gap — needs measurement setup |
| 6 | Review rating < 2.5 | Gap | Reputation risk — address before scaling |
| 7 | No Milled data | Gap | Seasonal planning blind spot — no email history |

3. **Return empty** if no gaps or opportunities detected
4. **Color-code**: Opportunities = green border, Gaps = neutral border

## Output

```markdown
## Gaps & Opportunities — {company_name}

### Opportunities
🟢 **{title}**
{description}

🟢 **{title}**
{description}

### Gaps
⚪ **{title}**
{description}

⚪ **{title}**
{description}
```

## Interpretation

- **All opportunities, no gaps** = strong ICP, pitch aggressively
- **Gaps present** = address in pitch (e.g., "We handle measurement setup" for infrastructure gap)
- **Revenue gap** = adjust budget tier downward, emphasize low-entry CTV test
- **Reputation risk** = caution — CTV amplifies brand perception, good and bad
- **No opportunities detected** = brand may already be fully covered, look for displacement angle instead
