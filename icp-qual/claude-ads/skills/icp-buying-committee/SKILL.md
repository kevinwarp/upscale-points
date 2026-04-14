---
name: icp-buying-committee
description: "Maps contacts to buying committee roles (Budget Owner, Technical Gatekeeper, Creative Stakeholder, Best Champion) using title-based classification. Includes role-specific objection handling with pre-written counter-arguments. Use to prepare multi-threaded outreach strategy."
user-invokable: false
---

# Buying Committee Map

## Prerequisites

See `_lib/report-loader.md` for how to load the report JSON.

## Data Sources

| Report Field | What It Provides |
|---|---|
| `report.contact_intel` | Contacts with titles, emails, LinkedIn URLs |
| `report.enrichment` | Supporting company context |
| `report.company_pulse` | CRM contacts for additional role mapping |

## Process

1. **Load report** for the given domain
2. **Role classification** by title keywords:
   - **Budget Owner**: CMO, VP Marketing, Head of Marketing, Marketing Director, CEO (small cos)
   - **Technical Gatekeeper**: Growth, Paid Media, Performance Marketing, Digital Marketing, Acquisition
   - **Creative Stakeholder**: Creative Director, Brand, Content, Design
   - **Best Champion**: Growth Manager, DTC Manager, eCommerce Manager, Marketing Manager
3. **Build role cards** (4-column grid): each role shows matched contact or "Not identified" with suggested titles
4. **Objection handling by role**: pre-written Upscale-specific rebuttals tailored to each role's concerns

### Role-Specific Objections

**Budget Owner:**
- "We don't have budget for CTV" → CTV starts at $15K/month, less than a Meta scale test
- "ROI is unproven" → Shopify-integrated attribution shows actual purchases, not estimates

**Technical Gatekeeper:**
- "How does attribution work?" → Pixel + Shopify deterministic matching, 3-day full credit window
- "We need incrementality" → Built-in holdout testing, not an add-on

**Creative Stakeholder:**
- "We don't have TV creative" → AI creative system: $500 vs $10K, 6 days vs 6 weeks
- "Quality won't match brand standards" → Full brand brief process, approval before launch

**Champion:**
- "How do I sell this internally?" → We provide pitch deck, case studies, and ROI model
- "What's the time commitment?" → Fully managed, 1 hour/week for approvals

## Output

```markdown
## Buying Committee — {company_name}

### Budget Owner
**{name}** — {title}
{email} · [LinkedIn]({url})

### Technical Gatekeeper
**{name}** — {title}
{email} · [LinkedIn]({url})

### Creative Stakeholder
**{name}** — {title}
{email} · [LinkedIn]({url})

### Best Champion
**{name}** — {title}
{email} · [LinkedIn]({url})

---

### Objection Handling by Role
#### Budget Owner Objections
| Objection | Response |
|-----------|----------|

#### Gatekeeper Objections
| Objection | Response |
|-----------|----------|

#### Creative Objections
| Objection | Response |
|-----------|----------|

#### Champion Objections
| Objection | Response |
|-----------|----------|
```

## Strategy

- **Multi-thread**: engage Champion first, then Gatekeeper, then Budget Owner
- **If no Champion identified**: suggest titles to search for in Apollo/LinkedIn
- **Creative Stakeholder**: loop in after initial interest, before creative review
