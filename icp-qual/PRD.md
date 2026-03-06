# Product Requirements Document — Ad Intelligence Pipeline

## Overview

The Ad Intelligence Pipeline is an internal tool that enables the sales team to quickly assess whether a prospect is actively running paid advertising, on which channels, at what volume, and with which creative strategies. It supports ICP qualification by revealing a company's ad footprint in under 20 seconds.

## Problem Statement

Sales reps spend significant time manually researching whether a prospect runs ads across linear TV, YouTube, and Meta. This involves visiting three separate ad transparency platforms, searching for the brand, and compiling results by hand. The process is slow, inconsistent, and doesn't scale.

## Solution

A single CLI command that accepts a domain and returns a unified ad intelligence report combining data from four sources:

1. **Store Leads** — Company enrichment (name, revenue, headcount, industry, ecommerce platform)
2. **iSpot.tv** — Linear/CTV TV ad detection
3. **Google Ads Transparency Center** — YouTube video ads (last 30 days)
4. **Meta Ad Library** — Facebook/Instagram video ads (last 30 days)

## Users

- Sales reps qualifying inbound leads
- BDRs researching outbound prospects
- Account managers preparing for renewals or upsell conversations

## Key Features

### 1. Domain-Based Lookup
- Input: any domain (e.g., `jonesroadbeauty.com`)
- The pipeline automatically resolves the brand name and searches all three ad platforms

### 2. Company Enrichment
- Revenue estimate, employee count, industry, ecommerce platform, LinkedIn URL
- Powered by Store Leads API

### 3. Multi-Platform Ad Detection
- **iSpot.tv (Linear):** Detects TV ad history with ad titles and detail links
- **YouTube (Google Ads Transparency):** Active video ads in the last 30 days with creative links
- **Meta (Ad Library):** Active video ads with advertiser names, start dates, and Library IDs

### 4. Channel Mix Summary
- Which platforms have active ads
- Total ads found across all platforms
- Boolean flag: `running_any_ads`

### 5. Structured Output
- JSON report with all data points, saved to `output/reports/{domain}.json`
- Human-readable CLI summary printed to terminal
- Markdown report with clickable links for Slack distribution

### 6. Influencer/Creator Detection (Meta)
- Meta ads that use branded content partnerships surface the creator name alongside the brand
- Enables sales reps to understand the prospect's creator strategy

## Non-Goals (v1)

- No web UI — CLI only
- No database or persistence beyond JSON files
- No automated scheduling or batch processing
- No Slack integration built into the pipeline (manual post for now)
- No ad spend estimation (only ad count and presence)

## Success Metrics

| Metric | Target |
|--------|--------|
| Pipeline completion time | < 20 seconds |
| Platform coverage | 3/3 scrapers return results for known advertisers |
| Enrichment hit rate | > 90% of domains return company data |
| Adoption | Sales team uses pipeline for > 50% of prospect research |

## Constraints

- Must run locally (no cloud infrastructure)
- Must use headless Chromium for scraping (no paid scraping APIs)
- Must respect rate limits on all platforms
- Must gracefully degrade — one scraper failure should never crash the pipeline
- Store Leads API key required for enrichment

## Future Considerations

- Batch mode: accept a CSV of domains and produce reports for all
- Slack bot integration: `/ad-intel nike.com` triggers pipeline and posts to channel
- Ad spend estimation via iSpot data
- Historical tracking: compare ad activity over time
- Additional platforms: TikTok Ad Library, LinkedIn Ads
- Web UI dashboard for non-technical users
