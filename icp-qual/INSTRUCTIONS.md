# How to Use the Ad Intelligence Pipeline

## First-Time Setup (5 minutes)

### 1. Install Python dependencies

```bash
cd icp-qual/ad-intel
pip install -r requirements.txt
```

### 2. Install the browser

```bash
playwright install chromium
```

### 3. Set up your API key

```bash
cp .env.example .env
```

Open `.env` and add your Store Leads API key:

```
STORELEADS_API_KEY=your-key-here
```

That's it. You're ready to run.

---

## Running a Scan

### Basic usage

```bash
cd icp-qual/ad-intel
python main.py --domain jonesroadbeauty.com --save-json
```

This will:
- Look up the company on Store Leads (revenue, headcount, industry, LinkedIn)
- Check iSpot.tv for linear TV ads
- Check Google Ads Transparency for YouTube ads (last 30 days)
- Check Meta Ad Library for Facebook/Instagram video ads (last 30 days)
- Print a summary to your terminal
- Save a full JSON report to `output/reports/jonesroadbeauty.com.json`

### What you'll see

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

Report saved to: output/reports/jonesroadbeauty.com.json
```

---

## Common Commands

### Quick check (no file saved)

```bash
python main.py --domain nike.com
```

Just prints the summary to your terminal. Good for a fast yes/no on whether someone is running ads.

### Full report with JSON output

```bash
python main.py --domain nike.com --save-json
```

Saves the complete report to `output/reports/nike.com.json` with all ad links, company data, and timing.

### Debug mode (see the browser)

```bash
python main.py --domain nike.com --no-headless --verbose
```

Opens a visible Chrome window so you can watch the scrapers work. Useful if a scraper is returning 0 results and you want to see what's happening.

### Custom output filename

```bash
python main.py --domain nike.com --save-json --output nike_march2026.json
```

---

## Reading the Output

### JSON report structure

The saved JSON file contains:

| Section | What's in it |
|---------|-------------|
| `enrichment` | Company name, revenue, headcount, industry, ecommerce platform, city/state, LinkedIn URL |
| `ispot_ads` | Linear TV ads with titles and iSpot.tv links |
| `youtube_ads` | YouTube video ads with links to Google Ads Transparency Center |
| `meta_ads` | Meta video ads with advertiser name, start date, and Ad Library links |
| `channel_mix` | Which platforms are active, total ads found |
| `running_any_ads` | `true` / `false` — are they running anything at all? |

### What to look for

**For ICP qualification:**
- `running_any_ads` — quick yes/no filter
- `channel_mix.total_platforms` — are they on 1 platform or all 3?
- `channel_mix.total_ads_found` — light spender (< 5 ads) vs. heavy (30+)

**For sales prep:**
- `enrichment.estimated_revenue` — company size
- `enrichment.ecommerce_platform` — Shopify, custom, etc.
- `meta_ads.ads[].title` — look for creator/influencer names (e.g., "Shawn Johnson East with Jones Road Beauty" means they're running branded content partnerships)
- `meta_ads.ads[].start_date` — how recently are they launching new creative?

**For outreach talking points:**
- If they're heavy on Meta but not YouTube → "We noticed you're investing heavily in Meta video ads but haven't expanded to YouTube yet..."
- If they're using influencers → reference specific creators by name
- If they have no linear TV → opportunity to discuss CTV/linear

---

## Tips

### Pipeline takes 12–20 seconds
The YouTube scraper is usually the slowest (10–12s). All three scrapers run in parallel, so total time = the slowest one.

### iSpot often returns 0 for DTC brands
Most DTC/ecommerce brands don't run linear TV ads. A 0 from iSpot is normal — it doesn't mean the scraper is broken.

### Meta results may include unrelated ads
Meta Ad Library searches by keyword, not advertiser ID. If you search "Nike," you might see ads from resellers or affiliates that mention Nike. Check the advertiser name in the results.

### YouTube titles are generic
Google Ads Transparency doesn't expose actual ad titles. You'll see "Advertisement (1 of 40)" — click the link to view the actual creative.

### If a scraper fails
One scraper failing won't crash the pipeline. You'll see an error message in the output but still get results from the other two. Common reasons:
- **Timeout** — the site was slow to load. Try again.
- **Captcha** — the site detected automation. Wait a few minutes and retry.
- **No results** — the brand genuinely isn't advertising on that platform.

### Run with `--verbose` to troubleshoot
If something looks wrong, add `--verbose` to see detailed logs of what each scraper is doing step by step.

---

## Where Reports Go

All reports save to:

```
icp-qual/ad-intel/output/reports/
```

Files are named by domain: `nike.com.json`, `jonesroadbeauty.com.json`, etc. Running the same domain again overwrites the previous report.
