---
name: icp-report
description: "Orchestrator for ICP qualification report skills. Run all 22 sections, a group, or a single section for any domain. Loads the domain report once and delegates to individual skills. Use: /icp-report <domain>, /icp-report sales-prep <domain>, /icp-report fit-score <domain>."
user-invokable: true
---

# ICP Report Orchestrator

## Usage

```
/icp-report <domain>                    # Full report (all 22 sections)
/icp-report <group> <domain>            # Run one group
/icp-report <skill-name> <domain>       # Run one skill
```

### Examples

```
/icp-report frida.com                   # Full ICP report
/icp-report company-intel frida.com     # Group A only
/icp-report sales-prep frida.com        # Group C only
/icp-report fit-score frida.com         # Single skill
/icp-report call-talk-track frida.com   # Single skill
```

## Shared Data Loading

See `_lib/report-loader.md` for the standard report loading protocol.

All skills share the same report JSON and fit score:

```
Report: icp-qual/ad-intel/output/reports/{domain}_report.json
Fit:    from scoring.upscale_fit import calculate_upscale_fit
```

Load once, pass to each skill. Never reload per-skill.

## Skill Groups

### Group A — Company Intel

| # | Skill | Command | What It Does |
|---|-------|---------|-------------|
| 1 | icp-company-profile | `/icp-report company-profile <domain>` | Firmographics, key people, funding, tech stack, social presence |
| 2 | icp-crm-intel | `/icp-report crm-intel <domain>` | CRM health, deals, meetings, outreach signals |
| 3 | icp-contacts | `/icp-report contacts <domain>` | Discovered + CRM contacts, outreach status |
| 4 | icp-hiring | `/icp-report hiring <domain>` | Open jobs, velocity, headcount growth, marketing roles |
| 5 | icp-news | `/icp-report news <domain>` | Recent headlines by category |
| 6 | icp-podcasts | `/icp-report podcasts <domain>` | Podcast appearances by leadership |
| 7 | icp-case-studies | `/icp-report case-studies <domain>` | Published platform case studies |

**Group command:** `/icp-report company-intel <domain>`

### Group B — Competitive & Ad Analysis

| # | Skill | Command | What It Does |
|---|-------|---------|-------------|
| 8 | icp-competitor-alert | `/icp-report competitor-alert <domain>` | CTV competitor detection, objection handling |
| 9 | icp-ads-overview | `/icp-report ads-overview <domain>` | Ad discovery across iSpot/YouTube/Meta |
| 10 | icp-brand-intel | `/icp-report brand-intel <domain>` | Purchase model, analytics maturity, tech stack |
| 11 | icp-key-events | `/icp-report key-events <domain>` | Event calendar, Wayback history, email analysis |
| 12 | icp-creative-pipeline | `/icp-report creative-pipeline <domain>` | AI creative: brief, script, VO demos, images |
| 13 | icp-creative-signals | `/icp-report creative-signals <domain>` | Format mix, messaging themes, promo patterns |

**Group command:** `/icp-report competitive <domain>`

### Group C — Sales Prep

| # | Skill | Command | What It Does |
|---|-------|---------|-------------|
| 14 | icp-paid-media-maturity | `/icp-report paid-media-maturity <domain>` | Overall/CTV/YouTube maturity scoring |
| 15 | icp-buying-committee | `/icp-report buying-committee <domain>` | Role mapping + objection handling |
| 16 | icp-call-talk-track | `/icp-report call-talk-track <domain>` | Opening insights, discovery Qs, proof points |
| 17 | icp-ctv-hypotheses | `/icp-report ctv-hypotheses <domain>` | Why CTV now, products for TV, test budget |
| 18 | icp-account-priority | `/icp-report account-priority <domain>` | Priority level with signal breakdown |

**Group command:** `/icp-report sales-prep <domain>`

### Group D — Scoring & Proposal

| # | Skill | Command | What It Does |
|---|-------|---------|-------------|
| 19 | icp-kpi-cards | `/icp-report kpi-cards <domain>` | 5 headline KPI cards |
| 20 | icp-fit-score | `/icp-report fit-score <domain>` | Fit score with category breakdown |
| 21 | icp-proposal | `/icp-report proposal <domain>` | Budget proposal, channel allocation, daily/weekly spend |
| 22 | icp-gaps-analysis | `/icp-report gaps-analysis <domain>` | Qualification gaps and opportunities |

**Group command:** `/icp-report scoring <domain>`

## Full Report Order

When running all 22 sections, execute in this order:

1. **KPI Cards** (dashboard header)
2. **Fit Score** (qualification context)
3. **Account Priority** (routing decision)
4. **Company Profile** (who they are)
5. **CRM Intel** (existing relationship)
6. **Contacts** (who to reach)
7. **Competitor Alert** (displacement detection)
8. **Ads Overview** (current ad activity)
9. **Brand Intel** (purchase model + tech stack)
10. **Key Events** (calendar + promotions)
11. **Creative Pipeline** (AI creative output)
12. **Creative Signals** (format + messaging analysis)
13. **Paid Media Maturity** (sophistication level)
14. **Buying Committee** (role mapping)
15. **Call Talk Track** (call prep)
16. **CTV Hypotheses** (investment case)
17. **Proposal** (budget + strategy)
18. **Gaps Analysis** (risks + opportunities)
19. **Hiring** (growth signals)
20. **News** (conversation starters)
21. **Podcasts** (leadership visibility)
22. **Case Studies** (proven performance)

## Process

1. **Parse command**: extract domain and optional group/skill name
2. **Load report** JSON for domain (see `_lib/report-loader.md`)
3. **Calculate fit score** if any skill in the request needs it
4. **Route**:
   - Full report → run all 22 in order above
   - Group → run only that group's skills
   - Single skill → run only that skill
5. **Combine output**: concatenate all skill outputs with `---` separators
6. **Report failures**: if any skill errors, note it but continue with remaining skills

## Error Handling

If a skill fails:
- Log the skill name and error
- Continue with remaining skills
- Append failure summary at the end:
  ```
  ---
  ⚠️ {n} section(s) failed: {skill_1}, {skill_2}
  ```
