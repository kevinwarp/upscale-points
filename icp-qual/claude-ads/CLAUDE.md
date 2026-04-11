# Claude Ads: ICP-Qual Edition

## Overview

Curated subset of the [claude-ads](https://github.com/AgriciDaniel/claude-ads) skill
for ICP qualification workflows. Focused on DTC e-commerce brands across Meta, YouTube,
and TikTok — the platforms scraped by the `ad-intel` pipeline.

## Included Skills

| # | Skill | Command | Purpose |
|---|-------|---------|---------|
| 1 | ads-audit | `/ads audit` | Multi-platform audit orchestrator |
| 2 | ads-meta | `/ads meta` | Meta Ads deep analysis (46 checks) |
| 3 | ads-tiktok | `/ads tiktok` | TikTok Ads deep analysis (25 checks) |
| 4 | ads-youtube | `/ads youtube` | YouTube Ads analysis |
| 5 | ads-create | `/ads create` | Campaign brief & copy generation |
| 6 | ads-creative | `/ads creative` | Creative quality assessment |
| 7 | ads-dna | `/ads dna <url>` | Brand DNA extraction |
| 8 | ads-plan | `/ads plan ecommerce` | E-commerce ad strategy |
| 9 | ads-competitor | `/ads competitor` | Competitor ad intelligence |

## Architecture

```
claude-ads/
  CLAUDE.md                       # This file
  ads/
    SKILL.md                      # Orchestrator & routing
    references/                   # Scoring, benchmarks, specs, checklists
  skills/
    ads-audit/SKILL.md
    ads-meta/SKILL.md
    ads-tiktok/SKILL.md
    ads-youtube/SKILL.md
    ads-create/SKILL.md
    ads-creative/SKILL.md
    ads-dna/SKILL.md
    ads-plan/SKILL.md + assets/ecommerce*.md
    ads-competitor/SKILL.md
  agents/
    audit-meta.md
    audit-creative.md
    audit-compliance.md
    copy-writer.md
    creative-strategist.md
    format-adapter.md
```

## ICP Qualification Protocol

See `icp-qual/PROTOCOL.md` for the full 10-step workflow that integrates the
ad-intel discovery pipeline with these analysis skills.

**When asked to "run ICP" or "check" a domain, follow the protocol:**

1. Store Leads enrichment + ad discovery pipeline
2. Brand DNA extraction (`ads-dna`)
3. Competitor ad intelligence (`ads-competitor`)
4. Creative quality assessment (`ads-creative`)
5. Platform-specific deep dives (`ads-meta`, `ads-youtube`, `ads-tiktok`)
6. Multi-platform audit & scoring (`ads-audit`)
7. E-commerce strategy plan (`ads-plan ecommerce`)
8. Campaign brief generation (`ads-create`)
9. Summary & Slack delivery

## Source

Based on [claude-ads v1.4.0](https://github.com/AgriciDaniel/claude-ads) (MIT License).
Trimmed to 9 skills relevant to DTC e-commerce ICP qualification.
