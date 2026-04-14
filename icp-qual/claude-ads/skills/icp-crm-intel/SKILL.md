---
name: icp-crm-intel
description: "Surfaces CRM health status, deal pipeline, meeting history, and outreach signals from HubSpot/Day.ai. Shows health score, active opportunities, meeting notes, and next steps. Use to understand existing relationship before outreach."
user-invokable: false
---

# CRM Intelligence

## Prerequisites

See `_lib/report-loader.md` for how to load the report JSON.

## Data Sources

| Report Field | What It Provides |
|---|---|
| `report.company_pulse` | CRM health score, status, tier, owner, contact history, opportunities, meetings, health signals |

### Key Sub-fields

- `health_status`: "healthy" / "at_risk" / "critical"
- `health_score`: 0-100
- `current_status`: pipeline stage
- `crm_tier`: account tier
- `owner_email`: assigned rep
- `days_since_first_contact`: relationship age
- `next_steps`: recommended actions
- `status_summary`: bullet-point status notes
- `health_signals[]`: positive/negative indicators with impact values
- `opportunities[]`: title, stage, deal_size, probability, close_date
- `meetings[]`: title, date, key_points, action_items
- `contacts[]`: CRM-linked contacts

## Process

1. **Load report** for the given domain
2. **Check** `company_pulse.found` — if false, output "No CRM data available"
3. **Health badge**: render status as healthy (green), at_risk (amber), or critical (red) with score
4. **Status details**: current_status, crm_tier, owner_email, days since first contact, next steps
5. **Status summary**: bullet list from status_summary
6. **Health signals**: positive signals (+) and negative signals (-) with impact values
7. **Deal pipeline**: table of opportunities with stage, size, probability, close date
8. **Meeting history**: cards with title, date, key points, action items
9. **Contacts in CRM**: list of existing contacts with lifecycle stage

## Output

```markdown
## CRM Intelligence — {company_name}

### Health Status
**{status}** — Score: {score}/100
Owner: {owner} | Tier: {tier} | Days in CRM: {days}

### Status Summary
- ...

### Health Signals
✅ {positive_signal} (+{impact})
⚠️ {negative_signal} (-{impact})

### Active Deals
| Deal | Stage | Size | Prob | Close |
|------|-------|------|------|-------|

### Recent Meetings
**{title}** — {date}
Key Points: ...
Action Items: ...

### Next Steps
- ...
```

## Formatting

- Health colors: healthy=#027A48, at_risk=#B54708, critical=#B42318
- Deal sizes: `$30K`, `$1.2M`
- Missing data: show "—"
