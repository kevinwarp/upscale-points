---
name: icp-company-profile
description: "Generates a comprehensive company profile card from enrichment data, Clay intel, and social profiles. Shows firmographics, key people, funding, tech stack, and social presence. Use for quick company overview during ICP qualification."
user-invokable: false
---

# Company Profile

## Prerequisites

See `_lib/report-loader.md` for how to load the report JSON.

## Data Sources

| Report Field | What It Provides |
|---|---|
| `report.enrichment` | Industry, HQ, employees, revenue, ecommerce platform, product catalog, reviews, technologies, social profiles, key people, funding |
| `report.clay` | Founders, revenue model, target audience, headcount growth, investors, competitors, recent news |
| `report.company_name` | Resolved company name |
| `report.domain` | Domain analyzed |

## Process

1. **Load report** for the given domain
2. **Build hero card**: company initials, name, industry, HQ (city/state/country), founded date (from `store_created_at`), employee count, ecommerce platform
3. **Key people grid**: from `enrichment.key_people`, fallback to `clay.founders` if empty
4. **Company details table** (two-column): domain, legal name, phone, email, revenue (monthly + annual), visits, pageviews, product count, avg price, price range, platform rank, reviews
5. **Fundraising block**: total funding, latest round, investors (merge enrichment + clay)
6. **Crunchbase data**: categories as pills, link to profile
7. **Social profiles grid**: Instagram, Facebook, Twitter/X, YouTube, TikTok, Pinterest, Snapchat, LinkedIn — each with follower/post/like stats where available
8. **Clay enrichment block**: revenue model, target audience, headcount growth, competitors, recent news
9. **Tech stack**: full technologies list with analytics tools highlighted

## Output

Return clean markdown with these sections:

```markdown
## Company Profile — {company_name}

### Overview
| Field | Value |
|-------|-------|
| Industry | ... |
| HQ | ... |
| Employees | ... |
| Platform | ... |
| Monthly Revenue | ... |
| Annual Revenue | ... |

### Key People
- {name} — {title}

### Fundraising
- Total Funding: ...
- Latest Round: ...
- Investors: ...

### Social Presence
| Platform | Followers | Posts |
|----------|-----------|-------|

### Tech Stack
- Analytics: ...
- eCommerce: ...
- Marketing: ...

### Clay Intel
- Revenue Model: ...
- Target Audience: ...
- Competitors: ...
```

## Formatting

- Money: `$30K`, `$1.2M`, `$125,000`
- Missing data: show "—"
- Large numbers: use K/M suffixes
