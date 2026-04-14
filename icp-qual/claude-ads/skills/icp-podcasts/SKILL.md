---
name: icp-podcasts
description: "Lists podcast appearances by company leadership. Shows episode titles, show names, speakers, and dates. Use to understand thought leadership positioning and identify conversation hooks for outreach."
user-invokable: false
---

# Podcast Appearances

## Prerequisites

See `_lib/report-loader.md` for how to load the report JSON.

## Data Sources

| Report Field | What It Provides |
|---|---|
| `report.podcasts[]` | Podcast episodes featuring company leaders |

### Fields per Episode

- `episode_title`: episode name
- `show_name`: podcast name
- `url`: link to episode
- `person_name`: speaker from the company
- `person_title`: speaker's role
- `date`: air date

## Process

1. **Load report** for the given domain
2. **Check** if `podcasts` exists and has items — if empty, output "No podcast appearances found"
3. **Render cards**: up to 10 episodes, each with episode title, show name, speaker info, date
4. **Sort** by date descending

## Output

```markdown
## Podcast Appearances — {company_name}

- **{episode_title}** on *{show_name}*
  {person_name}, {person_title} — {date}
  [Listen]({url})
- ...
```

## Use Cases

- Reference specific episodes in outreach: "Heard {person_name} on {show_name} discussing..."
- Identify which leaders are public-facing (likely decision influencers)
- Understand brand messaging themes from episode topics
