---
name: icp-case-studies
description: "Surfaces published case studies featuring the brand on ad platforms (Meta, Google, TikTok, Shopify, YouTube, Klaviyo, Triple Whale). Shows platform, title, key metrics, and summary. Use to understand proven channel performance and pitch around gaps."
user-invokable: false
---

# Published Case Studies

## Prerequisites

See `_lib/report-loader.md` for how to load the report JSON.

## Data Sources

| Report Field | What It Provides |
|---|---|
| `report.case_studies[]` | Published case studies from ad/ecommerce platforms |

### Fields per Case Study

- `platform`: Meta, Google, TikTok, Shopify, YouTube, Klaviyo, Triple Whale
- `title`: case study title
- `url`: link to full case study
- `key_metrics`: headline results (e.g., "3.5x ROAS", "40% lower CPA")
- `summary`: brief description of what was achieved

## Process

1. **Load report** for the given domain
2. **Check** if `case_studies` exists and has items — if empty, output "No published case studies found"
3. **Platform-branded cards**: up to 8 case studies, each color-coded by platform
4. **Key metrics** as highlighted badges
5. **Summary text** below metrics

### Platform Colors

| Platform | Color |
|----------|-------|
| Meta | #1877F2 |
| Google | #4285F4 |
| TikTok | #000000 |
| Shopify | #96BF48 |
| YouTube | #FF0000 |
| Klaviyo | #1A1A2E |
| Triple Whale | #0A6D86 |

## Output

```markdown
## Published Case Studies — {company_name}

### {platform}: {title}
**Key Metrics:** {metric_1} · {metric_2}
{summary}
[Read full case study]({url})
```

## Interpretation

- Brands with Meta/Google case studies are proven paid media investors → strong ICP signal
- No CTV/YouTube case studies = opportunity gap for Upscale pitch
- Key metrics indicate performance benchmarks the brand expects to hit
