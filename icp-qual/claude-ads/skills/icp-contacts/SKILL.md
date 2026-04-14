---
name: icp-contacts
description: "Maps discovered contacts and CRM contacts for a domain. Shows names, titles, emails, LinkedIn URLs, confidence scores, outreach status, and email engagement data from Instantly/Beehiiv. Use to identify who to reach and who's already been contacted."
user-invokable: false
---

# Contact Intelligence

## Prerequisites

See `_lib/report-loader.md` for how to load the report JSON.

## Data Sources

| Report Field | What It Provides |
|---|---|
| `report.contact_intel` | Discovered contacts with emails, titles, confidence scores, outreach status |
| `report.company_pulse` | CRM contacts with lifecycle stage and outreach history (Instantly, Beehiiv) |

### Key Sub-fields

**contact_intel:**
- `found`: boolean
- `discovered_count` / `existing_count`: counts
- `contacts[]`: first_name, last_name, title, email, linkedin_url, replied_at, email_sources, confidence_score, outreach_status

**company_pulse.contacts[]:**
- first_name, last_name, title, email, lifecycle_stage
- `outreach[]`: provider (instantly/beehiiv), sent, opened, clicked

**company_pulse.outreach_summary:**
- `instantly`: total sent/opened/clicked
- `beehiiv`: total sent/opened/clicked

## Process

1. **Load report** for the given domain
2. **Discovered contacts table**: name, title, email, LinkedIn, confidence score, sources, outreach status, reply date
3. **Cross-reference** discovered contact emails against Instantly outreach data from CRM
4. **CRM contacts table**: name, title, email, lifecycle stage, outreach provider badges
5. **Outreach summary bar**: Instantly and Beehiiv aggregate stats (sent/opened/clicked)
6. **Collapse** tables beyond 5 rows with expand toggle

## Output

```markdown
## Contact Intelligence — {company_name}

### Discovered Contacts ({count})
| Name | Title | Email | LinkedIn | Confidence | Status |
|------|-------|-------|----------|------------|--------|

### CRM Contacts ({count})
| Name | Title | Email | Stage | Outreach |
|------|-------|-------|-------|----------|

### Outreach Summary
- Instantly: {sent} sent / {opened} opened / {clicked} clicked
- Beehiiv: {sent} sent / {opened} opened / {clicked} clicked
```

## Formatting

- Confidence scores: percentage (e.g., 95%)
- Outreach status badges: "Contacted", "Replied", "New"
- Missing data: show "—"
