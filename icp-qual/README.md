# ICP Qualification — Ad Intelligence Pipeline

A local Python pipeline that accepts a domain and returns a full advertising intelligence report across linear TV, YouTube, and Meta. Built to support ICP qualification by revealing whether a prospect is actively running ads, on which platforms, at what volume, and with which creative strategies.

## What It Does

Given a domain like `jonesroadbeauty.com`, the pipeline:

1. **Enriches** the company via the Store Leads API (name, revenue, headcount, industry, ecommerce platform, LinkedIn)
2. **Scrapes iSpot.tv** for linear/CTV TV ad history
3. **Scrapes Google Ads Transparency Center** for YouTube video ads (last 30 days)
4. **Scrapes Meta Ad Library** for Facebook/Instagram video ads (last 30 days, US)
5. **Outputs** a structured JSON report + human-readable CLI summary

All three scrapers run in parallel using a single Chromium instance with isolated browser contexts. Total pipeline time is typically 12–20 seconds.

## Quick Start

```bash
cd ad-intel
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
# Add your STORELEADS_API_KEY to .env
```

### Run a scan

```bash
# Standard headless scan with JSON output
python main.py --domain nike.com --save-json

# Visible browser for debugging
python main.py --domain nike.com --no-headless --verbose

# Custom output filename
python main.py --domain nike.com --save-json --output nike_report.json
```

### CLI Flags

| Flag | Description |
|------|-------------|
| `--domain`, `-d` | Domain to analyze (required) |
| `--save-json` | Save report to `output/reports/{domain}.json` |
| `--output`, `-o` | Custom output filename |
| `--headless` | Run browser headless (default) |
| `--no-headless` | Show browser window for debugging |
| `--verbose`, `-v` | Enable debug logging |

## Example Output

```
============================================================
  Ad Intelligence Report: jonesroadbeauty.com
  Company: Jones Road Beauty
============================================================
  iSpot (Linear)      : NOT FOUND (0 ads)
  YouTube             : FOUND (4 ads)
  Meta                : FOUND (30 ads)
  Running any ads: True
  Channel mix: 2 platforms, 34 total ads
  Pipeline time: 18.3s
============================================================
```

Reports are saved as structured JSON with:
- Company enrichment data (revenue, headcount, industry, platform, LinkedIn)
- Per-platform ad results with titles, URLs, start dates
- Channel mix summary (which platforms are active)
- Pipeline timing metadata

## Project Structure

```
ad-intel/
  main.py                  # CLI entrypoint
  orchestrator.py          # Pipeline coordinator
  requirements.txt         # Python dependencies
  .env.example             # Environment template
  enrichment/
    storeleads_client.py   # Store Leads API client
  scraping/
    browser_agent.py       # Playwright browser lifecycle
    ispot_scraper.py       # iSpot.tv linear TV scraper
    youtube_transparency_scraper.py  # Google Ads Transparency scraper
    meta_ad_scraper.py     # Meta Ad Library scraper
  models/
    ad_models.py           # Pydantic data models
  utils/
    domain_utils.py        # Domain normalization
    json_formatter.py      # Report output formatting
  prompts/                 # Reference docs for scraping strategies
  output/reports/          # Generated reports (gitignored)
```

## Requirements

- Python 3.11+
- Playwright (Chromium)
- Store Leads API key ([storeleads.app](https://storeleads.app))
