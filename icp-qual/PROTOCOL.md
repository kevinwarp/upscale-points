# ICP Qualification Protocol

When asked to "run ICP" or "check" a domain, execute the following steps in order.

---

## Step 1: Store Leads Research

Query the Store Leads API to research the brand before anything else.

```bash
cd icp-qual/ad-intel && python3 main.py --domain {domain} --save-json
```

This calls the Store Leads API (key: `884925c7-ba5a-4a6e-46aa-ff41a884`) and returns:
- Company name, industry, description
- Estimated monthly & annual revenue
- Employee count, ecommerce platform
- Location (city, state, country)
- LinkedIn URL

Review the enrichment data to understand the brand before proceeding.

---

## Step 2: Ad Discovery Pipeline

The same command from Step 1 also runs the 3-platform ad discovery:
- **iSpot (Linear TV)** — searches ispot.tv for linear/CTV ads
- **YouTube** — searches Google Ads Transparency Center (last 30 days)
- **Meta** — searches Meta Ad Library for active video ads

Output: `output/reports/{domain}.json` with all ad URLs, counts, and channel mix.

---

## Step 3: Brand DNA Extraction

Extract the brand's visual identity, voice, colors, typography, and target audience from their website.

Using the `ads-dna` skill:
- Fetch their homepage, about page, and product page
- Extract colors, typography, voice axes (formal↔casual, bold↔subtle, etc.)
- Identify imagery style, brand values, target audience
- Output: `brand-profile.json`

---

## Step 4: Competitor Ad Intelligence

Using the `ads-competitor` skill and the ad discovery data from Step 2:
- Analyze the discovered ad URLs across Meta, YouTube, and iSpot
- Assess ad copy themes, creative strategy, messaging pillars
- Identify platform gaps (which channels they're NOT on)
- Identify messaging gaps and audience opportunities
- Estimate creative refresh velocity from ad start dates

---

## Step 5: Creative Quality Assessment

Using the `ads-creative` skill:
- Evaluate the quality and diversity of discovered ads
- Check for creative fatigue signals (ad age, volume, refresh cadence)
- Assess format diversity (video, image, carousel, UGC)
- Score creative health per platform
- Identify production priority recommendations

---

## Step 6: Platform-Specific Deep Dives

Run the relevant platform skills based on which platforms had active ads:

- **If Meta ads found** → Run `ads-meta` (46 checks: pixel/CAPI health, creative fatigue, structure, audience)
- **If YouTube ads found** → Run `ads-youtube` (video quality, hook, subtitles, format analysis)
- **If TikTok data available** → Run `ads-tiktok` (25 checks: creative, tech, bidding, structure)

Skip platforms that returned 0 ads in Step 2.

---

## Step 7: Multi-Platform Audit & Scoring

Using the `ads-audit` skill:
- Aggregate findings from Steps 4-6
- Calculate per-platform health score (0-100)
- Calculate aggregate Ads Health Score weighted by platform presence
- Generate prioritized action plan (Critical → High → Medium → Low)
- Identify Quick Wins (high-impact fixes < 15 minutes)
- Grade: A (90-100), B (75-89), C (60-74), D (40-59), F (<40)

---

## Step 8: E-Commerce Strategy Plan

Using the `ads-plan` skill with the ecommerce template:
- Platform selection recommendations based on their current mix
- Campaign architecture (prospecting, retargeting, testing tiers)
- Budget planning framework (70/20/10 allocation)
- Creative strategy and content pillars
- Implementation roadmap (4 phases over 12 weeks)

---

## Step 9: Campaign Brief Generation

Using the `ads-create` skill:
- Read `brand-profile.json` from Step 3
- Incorporate audit findings from Step 7
- Select appropriate copy framework (AIDA, PAS, BAB, etc.)
- Generate 3+ campaign concepts with distinct messaging angles
- Produce platform-specific copy deck (headlines, primary text, CTAs)
- Output: `campaign-brief.md`

---

## Step 10: Summary & Delivery

Compile all findings into a single report:

1. **Company Overview** — from Store Leads enrichment
2. **Ad Discovery Results** — channel mix table (iSpot/YouTube/Meta)
3. **Brand DNA Summary** — voice, colors, target audience
4. **Competitive Intelligence** — ad strategy analysis, platform/messaging gaps
5. **Creative Assessment** — quality scores, fatigue signals, format gaps
6. **Audit Score** — aggregate health score with grade
7. **Strategy Recommendations** — e-commerce plan highlights
8. **Campaign Concepts** — brief summaries from campaign-brief.md
9. **All Ad URLs** — full list of discovered ad links

Send to #sales via Slack with canvas attachment containing the full report.

---

## Quick Reference

| Step | Skill | What It Produces |
|------|-------|-----------------|
| 1-2 | ad-intel pipeline | Company data + ad discovery (JSON) |
| 3 | ads-dna | brand-profile.json |
| 4 | ads-competitor | Competitive intelligence report |
| 5 | ads-creative | Creative quality scores |
| 6 | ads-meta/youtube/tiktok | Platform-specific deep dives |
| 7 | ads-audit | Health score (0-100) + action plan |
| 8 | ads-plan ecommerce | E-commerce strategy roadmap |
| 9 | ads-create | campaign-brief.md with copy deck |
| 10 | — | Summary + Slack delivery |
