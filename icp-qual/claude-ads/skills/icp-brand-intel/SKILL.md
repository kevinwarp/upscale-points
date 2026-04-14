---
name: icp-brand-intel
description: "Deep analysis of purchase model, analytics maturity, attribution stack, tech infrastructure, and competitive landscape with enriched competitor cards. Shows which tools the brand uses and how sophisticated their measurement is. Use for strategy and pitch personalization."
user-invokable: false
---

# Brand Intelligence

## Prerequisites

See `_lib/report-loader.md` for how to load the report JSON.

## Data Sources

| Report Field | What It Provides |
|---|---|
| `report.brand_intel` | Purchase model, analytics maturity, attribution tools, competitors, CTV/YouTube competitor presence |
| `report.enrichment` | Technologies, technologies_full, features |
| `report.enriched_competitors[]` | Competitor cards with revenue, industry, platform, CTV/YouTube badges |

### Key Sub-fields

**brand_intel:**
- `purchase_model`: subscription / one_time / high_repurchase
- `purchase_model_signals[]`: evidence for model classification
- `analytics_maturity`: basic / intermediate / advanced
- `analytics_tools[]`: GA4, Mixpanel, Amplitude, etc.
- `attribution_tools[]`: Triple Whale, Northbeam, etc.
- `maturity_notes[]`: qualitative assessment
- `competitors[]`: competitor names
- `competitors_on_ctv[]`: competitors running CTV
- `competitors_on_youtube[]`: competitors running YouTube

**enriched_competitors[]:**
- name, domain, estimated_annual_revenue, industry, ecommerce_platform, on_ctv, on_youtube, logo_url

## Process

1. **Load report** for the given domain
2. **Purchase model**: show model type with supporting signals
3. **Analytics & attribution tools**: pill grid of all tools, maturity level badge
4. **Maturity notes**: qualitative assessment bullets
5. **Competitive landscape**: enriched competitor cards with revenue, industry, CTV/YouTube badges
6. **Tech stack**: full merged technologies + features list
7. **Analytics highlight box**: separate analytics tools with maturity level badge, highlight key tools (Hotjar, Triple Whale, TikTok Pixel)
8. **CTV competitor tags**: flag competitors running CTV in the tech stack view

## Output

```markdown
## Brand Intelligence — {company_name}

### Purchase Model
**{model_type}**
Signals:
- {signal_1}
- {signal_2}

### Analytics Maturity: {level}
**Tools:** {tool_1}, {tool_2}, ...
**Attribution:** {tool_1}, {tool_2}, ...
Notes:
- {note}

### Competitive Landscape
| Competitor | Revenue | Platform | CTV | YouTube |
|-----------|---------|----------|-----|---------|

### Tech Stack
- **Analytics:** {tools}
- **eCommerce:** {tools}
- **Marketing:** {tools}
- **Other:** {tools}
```

## Key Signals for Sales

- `analytics_maturity: advanced` + attribution tools = data-driven buyer, lead with measurement pitch
- `competitors_on_ctv` not empty = urgency signal, competitors already in market
- `purchase_model: subscription` = strong LTV story for CTV
