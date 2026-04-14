# Report Loader — Shared Reference

## Loading the Report

Given a domain (e.g. `frida.com`), load the report JSON:

```
icp-qual/ad-intel/output/reports/{domain}_report.json
```

Parse it as a `DomainAdReport` model. Key top-level fields:

| Field | Type | Description |
|-------|------|-------------|
| `domain` | str | The domain analyzed |
| `company_name` | str | Resolved company name |
| `enrichment` | CompanyEnrichment | Firmographic data (revenue, employees, industry, tech stack, socials) |
| `channel_mix` | ChannelMix | Ad channel presence (meta, google, tiktok, youtube, ispot) |
| `ispot_ads` | dict | iSpot CTV/streaming ad data |
| `meta_ads` | dict | Meta ad transparency data |
| `youtube_ads` | dict | YouTube ad transparency data |
| `brand_intel` | BrandIntelligence | Purchase model, analytics maturity, competitive positioning |
| `creative_pipeline` | dict | AI-generated creative brief, script, images |
| `contact_intel` | dict | Key contacts with roles and emails |
| `company_pulse` | dict | CRM health score, status, outreach history |
| `competitor_detection` | dict | Detected competitors and overlap analysis |
| `wayback_intel` | dict | Historical web activity and key events |
| `clay` | dict | Clay enrichment (HQ, funding, founders, revenue model) |
| `audio_files` | list | AI-generated voiceover demos |

## Loading the Fit Score

If the skill needs the fit score, run:

```python
from scoring.upscale_fit import calculate_upscale_fit
fit = calculate_upscale_fit(report)
```

Key fit fields: `fit.grade` (A-F), `fit.total_score` (0-100), `fit.categories[]` (name, score, weight, notes).

## Formatting Conventions

- Money: `$30K`, `$1.2M`, `$125,000`
- Grades: A (90-100), B (75-89), C (60-74), D (40-59), F (<40)
- Grade colors: A=#027A48, B=#0A6D86, C=#B54708, D=#B42318, F=#B42318
- Missing data: Show "—" not "None" or blank
- Section output: Return clean markdown, not HTML
