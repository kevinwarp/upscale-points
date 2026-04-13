# ICP Qualification Protocol

When asked to "run ICP" or "check" a domain, execute ALL of the following steps in order.
Every step is MANDATORY — do not skip any step.

---

## Step 1: Pipeline + Clay Enrichment (in parallel)

Run BOTH of these simultaneously:

### 1a. Ad Intelligence Pipeline

```bash
cd icp-qual/ad-intel && python3 main.py --domain {domain} --save-json
```

This single command runs:
- **Store Leads enrichment** — company name, industry, revenue, employees, platform, tech stack
- **Company Pulse CRM lookup** — relationship health, contacts, deals, meetings, outreach history
- **Contact Search discovery** — target contacts via Apollo + Lusha (8 title buckets)
- **iSpot scraper** — linear/CTV ad detection
- **YouTube scraper** — Google Ads Transparency Center (last 30 days)
- **Meta scraper** — Meta Ad Library active video ads
- **Milled scraper** — email newsletter history
- **Google Trends** — brand search trend (rising/stable/declining)
- **Competitor landscape** — finds competitors, checks CTV + YouTube presence
- **Brand intelligence analysis** — purchase model, spend estimate, analytics maturity
- **Upscale Fit scoring** — 0-100 score across 6 weighted categories

Output: JSON report saved to `output/reports/{domain}.json`

Real-time status: `output/status/{domain}.jsonl` (JSONL events for frontend)

### 1b. Clay MCP Enrichment (start simultaneously with 1a)

Call `find-and-enrich-company` with ALL of these data points:

```
companyIdentifier: {domain}
companyDataPoints:
  - { type: "Company Competitors" }
  - { type: "Revenue Model" }
  - { type: "Investors" }
  - { type: "Latest Funding" }
  - { type: "Custom", dataPointName: "Target Audience", dataPointDescription: "Target customer demographics and audience profile" }
  - { type: "Custom", dataPointName: "Founders", dataPointDescription: "Founders and co-founders of the company" }
```

Wait for all enrichments to complete (poll with `get-task` until no enrichments show `in-progress`).

This provides:
- Company logo URL (higher quality than StoreLeads)
- Headquarters location
- Competitors (3 direct competitors)
- Revenue model (subscription, transactional, etc.)
- Target audience demographics and profile
- Founders and co-founders
- Investors (if venture-backed)
- Latest funding round details
- Headcount growth trajectory
- Recent news and trigger events

### 1c. Merge Clay Data & Generate Reports

After BOTH 1a and 1b complete, save Clay data to a JSON file and re-generate reports:

```bash
# Save Clay data to /tmp/clay_{domain}.json with this structure:
# {
#   "logo_url": "...",
#   "headquarters": "City, ST",
#   "competitors": ["A", "B", "C"],
#   "revenue_model": "DTC eCommerce",
#   "target_audience": "...",
#   "founders": ["Name"],
#   "investors": ["Firm"],
#   "latest_funding": "Series A - $10M",
#   "headcount_growth": "15%",
#   "recent_news": ["Headline 1", "Headline 2"]
# }

cd icp-qual/ad-intel && python3 main.py \
  --domain {domain} \
  --from-report output/reports/{domain}.json \
  --clay-json /tmp/clay_{domain}.json \
  --save-json \
  --publish
```

This:
1. Loads the existing pipeline JSON report
2. Merges Clay enrichment data
3. Regenerates both HTML reports (internal + pitch) WITH Clay data
4. Uploads both reports to the Reports API
5. Saves updated JSON with Clay data
6. Outputs shareable URLs for both reports

---

## Step 2: Slack Delivery to #gtm-icp-qualification

Send to **#gtm-icp-qualification** (C08U7N6KZV4) as an executive summary with report links.

### Main Message Format

Post a SHORT executive summary. Keep it scannable — details go in threads.

If competitor CTV tags were detected (Tatari, MNTN/SteelHouse, etc.), add a :rotating_light: warning line.

```
*{company_name}* | {industry} | {ecommerce_platform}
{headquarters from Clay} | {employee_count} employees | Founded by {founders}

Revenue: ${estimated_monthly_revenue}/mo (${estimated_annual_revenue}/yr)
Ad Spend: ~${estimated_monthly_ad_spend}/mo | {total_platforms} platforms | {total_ads_found} ads
CRM: {health_status} ({health_score}/100) | {crm_contact_count} contacts | {deal_count} deals

:rotating_light: COMPETITOR DETECTED: {competitor_names} — see Thread 6 for positioning
(only include this line if competitor_detection.found is True)

Upscale Fit: {score}/100 ({grade})

:page_facing_up: {internal_share_url}
:bar_chart: {pitch_share_url}
```

### Threaded Detail Sections

Reply in thread with SHORT summaries. Full details are in the internal report — reference it, don't duplicate it.

**Thread 1 — Report Status**
One-line status per section using emoji indicators. Quick scan of what the pipeline found.
```
:white_check_mark: or :x: per section:

Company Data: {found/not found}
CRM: {health status} | {contact count} contacts | {deal count} deals
Contacts: {count} discovered ({new_count} new)
iSpot (CTV): {ad count} ads found
YouTube: {ad count} ads found
Meta: {ad count} ads found
Milled (Email): {email count} emails | {emails_per_week}/wk
Google Trends: {trend direction}
Competitors: {count} validated | CTV: {ctv_count} | YT: {yt_count}
Competitor Tags: {detected/clean} {competitor names if any}
Wayback Machine: {promotional_intensity} | {active_events} events with site changes
Clay: {enriched/not run}
Tech Stack: {count} technologies
Social: {platform count} profiles
```

**Thread 2 — Contacts & CRM**
Top 3 contacts (name, title, `email`). CRM one-liner. Flag NEW contacts. "Details → report above."

**Thread 3 — Ads + Competitive**
Platform: count per channel. Spend estimate. If competitor detected: name + one sell motion. If none: "Clean prospect." "Details → report above."

### Delivery Rules

- Keep each thread under 600 chars — link to internal report for details
- Use plain text formatting only — no markdown tables
- Do NOT create a canvas
- Wrap email addresses in backticks (`email@domain.com`) to prevent Slack from auto-linking with mailto:

---

## Real-Time Status

The pipeline emits JSONL events to `output/status/{domain}.jsonl` for frontend consumption.

Each line is a JSON object:
```json
{"ts": "2026-04-11T20:04:03Z", "event": "step_complete", "domain": "example.com", "step": "storeleads", "label": "Store Leads: Example Brand", "progress": 10, "elapsed_ms": 2300, "duration_ms": 2300, "data": {"company_name": "Example Brand", "revenue": 5000000}}
```

Event types:
- `pipeline_start` — pipeline kicked off (progress: 0)
- `step_start` — a step began (includes step name + label)
- `step_complete` — a step finished (includes duration_ms + data)
- `step_error` — a step failed (includes error message)
- `pipeline_complete` — everything done (progress: 100, includes fit_score, report URLs)

Steps emitted (in order):
| Step | Progress | What It Reports |
|------|----------|----------------|
| `storeleads` | 5→10 | Company data, revenue, platform |
| `company_pulse` | 12→68 | CRM health, contacts, deals |
| `contact_search` | 14→72 | Discovered contacts count |
| `browser` | 16→18 | Browser ready |
| `scrapers` | 20→45 | Ad counts per platform |
| `analysis` | 48→50 | Channel mix, brand intel |
| `extended_scrapers` | 52→65 | Trends + competitors |
| `clay_enrichment` | 75→80 | Clay data (competitors, founders, etc.) |
| `scoring` | 75→78 | Fit score + grade |
| `reports` | 85→90 | Report URLs |

Frontend can poll the JSONL file and render a progress bar with step labels.

---

## Quick Reference

| Step | Tool | What It Produces |
|------|------|-----------------|
| 1a | `main.py --save-json` | Full pipeline: enrichment + scraping + scoring |
| 1a (auto) | Store Leads API | Company data, revenue, platform, tech stack |
| 1a (auto) | Company Pulse API | CRM health, contacts, deals, meetings, outreach |
| 1a (auto) | Contact Search API | Target contacts via Apollo + Lusha (8 title buckets) |
| 1a (auto) | Browser scrapers | iSpot + YouTube + Meta + Milled + Trends + Competitors |
| 1a (auto) | Brand intel analysis | Purchase model, spend estimate, analytics maturity |
| 1a (auto) | Upscale Fit scoring | 0-100 score, grade, recommendation |
| 1b | Clay MCP | Competitors, revenue model, audience, founders, investors, funding, news |
| 1c | `main.py --from-report --clay-json --publish` | Merge Clay + generate reports + upload |
| 1c (auto) | Internal ICP report | Full data report with Clay + CRM + contacts + proposal numbers |
| 1c (auto) | External pitch report | Personalized streaming proposal with ROI projections |
| 1c (auto) | Reports API | Both reports uploaded → shareable URLs |
| 2 | Slack MCP | Exec summary + report links + threaded details to #gtm-icp-qualification |

---

## End-to-End Checklist

When running ICP for any domain, confirm ALL of these completed:

- [ ] Pipeline ran and JSON saved to `output/reports/{domain}.json`
- [ ] Status events emitting to `output/status/{domain}.jsonl`
- [ ] Clay MCP enriched: competitors, revenue model, target audience, founders, investors, funding
- [ ] All Clay enrichments completed (no `in-progress` remaining)
- [ ] Clay data saved to file and merged into report
- [ ] Internal report generated WITH Clay data + CRM + contacts + proposal numbers
- [ ] Pitch report generated WITH Clay data
- [ ] Both reports uploaded → shareable URLs
- [ ] Slack message sent to #gtm-icp-qualification with exec summary
- [ ] Slack message includes BOTH report URLs
- [ ] Threaded replies sent: Report Status, Contacts & CRM, Ads + Competitive
