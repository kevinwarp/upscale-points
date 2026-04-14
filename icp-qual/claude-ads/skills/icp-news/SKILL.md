---
name: icp-news
description: "Surfaces recent news about a company: funding rounds, product launches, partnerships, M&A, and press mentions. Categorized with counts. Use for timely conversation starters and understanding company momentum."
user-invokable: false
---

# Recent News

## Prerequisites

See `_lib/report-loader.md` for how to load the report JSON.

## Data Sources

| Report Field | What It Provides |
|---|---|
| `report.recent_news[]` | News items with category, headline, url, source, date |

### News Categories

- `funding` — Investment rounds, fundraising
- `product_launch` — New products, features
- `partnership` — Strategic partnerships, integrations
- `m_and_a` — Mergers, acquisitions
- `press` — Media coverage, interviews
- `other` — Uncategorized

## Process

1. **Load report** for the given domain
2. **Check** if `recent_news` exists and has items — if empty, output "No recent news found"
3. **Category summary**: count items per category, show as summary line
4. **News cards**: up to 12 items, each with category icon, headline (linked), source, date
5. **Sort** by date descending (most recent first)

## Output

```markdown
## Recent News — {company_name}

**Categories:** Funding ({n}) · Product ({n}) · Partnership ({n}) · Press ({n})

### Headlines
- **[{headline}]({url})** — {source}, {date} [{category}]
- ...
```

## Use Cases

- **Funding news** → "Congrats on the round — how are you thinking about scaling paid media?"
- **Product launch** → "Saw the new product line — have you considered CTV for the launch?"
- **Partnership** → Reference in pitch as potential co-marketing angle
