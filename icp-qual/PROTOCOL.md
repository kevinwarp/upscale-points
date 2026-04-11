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

Send to **#sales** (`C0A74SWFK43`) as an executive summary + threaded detail sections.

### 10a. Executive Summary (main message)

Post a single scannable message to #sales. Keep it under 2000 chars. Format:

```
{logo_url}
**{company_name}** — {industry}
{description}

Revenue: ${estimated_monthly_revenue}/mo (${estimated_annual_revenue}/yr DTC)
Traffic: {estimated_monthly_visits} visits/mo
Platform: {ecommerce_platform} ({ecommerce_plan}) | {product_count} products | Avg ${avg_product_price}
Location: {city}, {state}, {country}
Employees: {employee_count}

Ad Activity: {total_platforms} platforms | {total_ads_found} ads found
  iSpot: {count} | YouTube: {count} | Meta: {count}

Ads Health Score: {score}/100 ({grade})

Top 3 Recommendations:
1. {critical finding}
2. {high priority finding}
3. {quick win}

See thread for full analysis
```

Save the returned message timestamp as `thread_ts` for all subsequent replies.

### 10b. Threaded Detail Sections

Reply to the executive summary using `thread_ts`. Send each section as a separate threaded message in this order:

**Thread 1 — Company Profile**
Full enrichment data: revenue breakdown, tech spend ratio, price range, monthly app spend, store age, reviews ({review_count} on {review_source}, {review_rating} stars), LinkedIn URL, phone, emails. Include social profiles table (platform, URL, followers, posts, likes).

**Thread 2 — Tech Stack & Features**
Full technologies list grouped by category (tracking/attribution, marketing automation, analytics, ecommerce apps, other). Features list. Tech sophistication assessment.

**Thread 3 — Ad Discovery**
Channel mix table showing platform, ad count, and status. List every discovered ad URL grouped by platform with titles and dates.

**Thread 4 — Brand DNA**
Voice axes, color palette, typography, imagery style, target audience, brand values. From brand-profile.json (Step 3).

**Thread 5 — Competitive Intelligence**
Ad strategy analysis, messaging pillars, platform gaps, audience opportunities, creative refresh velocity. From ads-competitor (Step 4).

**Thread 6 — Creative Assessment**
Quality scores per platform, format diversity, fatigue signals, production priority recommendations. From ads-creative (Step 5).

**Thread 7 — Platform Deep Dives**
One section per active platform (Meta/YouTube/TikTok). Key check results, scores, and specific findings. From ads-meta/youtube/tiktok (Step 6).

**Thread 8 — Audit Scorecard**
Full scoring breakdown by category. Per-platform health scores. Prioritized action plan (Critical > High > Medium > Low). Quick wins list. From ads-audit (Step 7).

**Thread 9 — Strategy & Campaign Brief**
E-commerce strategy highlights: platform mix, budget framework, campaign architecture, implementation roadmap phases. Campaign concepts with messaging angles and platform-specific copy. From ads-plan + ads-create (Steps 8-9).

### Delivery Rules

- Each thread message must be under 4000 chars (Slack limit is 5000, leave buffer)
- Use plain text formatting only — no markdown tables (Slack doesn't render them)
- Use spacing and indentation for visual structure
- If a section exceeds 4000 chars, split into multiple threaded replies (e.g., "Platform Deep Dives 1/2", "2/2")
- Include URLs as plain links, not markdown links with query params (those can break)
- Do NOT create a canvas — the threaded format replaces it

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
| 10 | — | Executive summary + 9 threaded detail sections to #sales |
