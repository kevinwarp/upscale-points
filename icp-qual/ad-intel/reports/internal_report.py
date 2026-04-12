"""Internal ICP Report Generator

Generates a full-data HTML report for the Upscale sales team with:
- Company enrichment, scoring, ad discovery
- Milled promotional calendar
- Upscale Fit score breakdown
- Channel gaps analysis
- Branded with Upscale.ai design system
"""

from __future__ import annotations

import calendar as cal_mod
import html as html_mod
from datetime import date, datetime

from models.ad_models import CTV_COMPETITOR_TAGS, DomainAdReport, NewsItem, PodcastAppearance, PlatformCaseStudy
from data.tech_categories import group_technologies, CATEGORY_COLORS, categorize_tech
from data.competitive_intel import (
    CREATIVE_REALITY_MATRIX,
    COMPETITIVE_MATRIX,
    get_competitor_intel,
    get_case_study_brand_intel,
    CREATIVE_VELOCITY_PROOF,
)
from data.ecommerce_calendar import get_events_for_year
from reports.pitch_report import _budget_tier, _spend_strategy, _campaign_start_date
from scoring.upscale_fit import UpscaleFitResult


def _esc(val) -> str:
    """HTML-escape a value, handle None."""
    if val is None:
        return "—"
    return html_mod.escape(str(val))


def _fmt_money(val: float | None) -> str:
    if val is None:
        return "—"
    if val >= 1_000_000:
        return f"${val / 1_000_000:.1f}M"
    if val >= 1_000:
        return f"${val / 1_000:.0f}K"
    return f"${val:,.0f}"


def _fmt_number(val: int | None) -> str:
    if val is None:
        return "—"
    return f"{val:,}"


def _grade_color(grade: str) -> str:
    return {
        "A": "#027A48",
        "B": "#0A6D86",
        "C": "#B54708",
        "D": "#B42318",
        "F": "#7A271A",
    }.get(grade, "#838383")


def _score_bar_color(score: float) -> str:
    if score >= 80:
        return "#027A48"
    if score >= 60:
        return "#0A6D86"
    if score >= 40:
        return "#B54708"
    return "#B42318"


def generate_internal_report(
    report: DomainAdReport,
    fit: UpscaleFitResult,
) -> str:
    """Generate the internal ICP HTML report."""
    e = report.enrichment
    company = _esc(report.company_name or report.domain)
    domain = _esc(report.domain)
    industry = _esc(e.industry) if e else "—"
    description = _esc(e.description) if e and e.description else ""

    # Logo
    logo_html = ""
    if e and e.logo_url:
        logo_html = f'<img src="{_esc(e.logo_url)}" alt="{company}" class="brand-logo">'

    # Competitor alert banner
    competitor_alert = _build_competitor_alert(report)

    # KPI cards
    kpi_cards = _build_kpi_cards(report, fit)

    # Fit score section
    fit_section = _build_fit_section(fit)

    # Proposal numbers
    proposal_section = _build_proposal_section(report, fit)

    # Combined company profile (replaces enrichment + social sections)
    company_profile_section = _build_company_profile_section(report)

    # CRM intelligence
    crm_section = _build_crm_section(report)

    # Key contacts
    contacts_section = _build_contacts_section(report)

    # Ad discovery section
    ads_section = _build_ads_section(report)

    # Brand intelligence
    brand_intel_section = _build_brand_intel_section(report)

    # Key Events + Calendar (combined Milled + Wayback + ecommerce calendar)
    key_events_section = _build_key_events_section(report)

    # Creative Pipeline (AI-generated brief + script + images)
    creative_pipeline_section = _build_creative_pipeline_section(report)

    # Gaps analysis
    gaps_section = _build_gaps_section(report, fit)

    # Phase 1: AI Synthesis Sections
    maturity_section = _paid_media_maturity(report, fit)
    creative_signals_section = _creative_messaging_signals(report)
    hypotheses_section = _ctv_youtube_hypotheses(report, fit)
    committee_section = _buying_committee(report)
    talk_track_section = _call_talk_track(report, fit)
    priority_section = _account_priority_signal(report, fit)

    # Phase 2: Deep Research Sections
    hiring_section = _build_hiring_section(report)
    news_section = _build_news_section(report)
    podcasts_section = _build_podcasts_section(report)
    case_studies_section = _build_case_studies_section(report)

    generated = datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ICP Report — {company}</title>
<meta name="description" content="Internal ICP qualification report for {company} ({domain})">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root {{
  --pink: #831F80;
  --pink-light: #F6EBF6;
  --navy: #021A20;
  --teal: #0A6D86;
  --white: #FFFFFF;
  --border: #D7D7D7;
  --muted: #838383;
  --bg-grey: #F6F6F6;
  --success: #027A48;
  --warning: #B54708;
  --danger: #B42318;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  color: var(--navy);
  background: var(--bg-grey);
  line-height: 1.6;
}}
.page {{ max-width: 1100px; margin: 0 auto; padding: 0 24px 60px; }}
/* ── Site-style Header ── */
.site-header {{
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--white);
  border-bottom: 1px solid var(--border);
  padding: 0 32px;
  margin: 0 -24px 32px;
}}
.site-header-inner {{
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
}}
.site-header .logo-link {{
  display: flex;
  align-items: center;
  text-decoration: none;
}}
.site-header .logo-link {{ flex-direction: column; gap: 2px; }}
.site-header .logo-link svg {{ height: 28px; width: auto; }}
.logo-tagline {{ font-size: .58rem; color: var(--muted); letter-spacing: .04em; font-weight: 500; white-space: nowrap; }}
.site-header-nav {{
  display: flex;
  gap: 28px;
  align-items: center;
}}
.site-header-nav a {{
  color: var(--navy);
  text-decoration: none;
  font-size: .85rem;
  font-weight: 500;
  transition: color .15s;
}}
.site-header-nav a:hover {{ color: var(--pink); }}
.header-actions {{
  display: flex;
  align-items: center;
  gap: 12px;
}}
.header-badge {{
  background: var(--bg-grey);
  color: var(--muted);
  font-size: .7rem;
  font-weight: 600;
  letter-spacing: .06em;
  text-transform: uppercase;
  padding: 5px 12px;
  border-radius: 999px;
  border: 1px solid var(--border);
}}
.header-cta {{
  display: inline-flex;
  align-items: center;
  padding: 8px 20px;
  background: var(--navy);
  color: var(--white);
  font-size: .82rem;
  font-weight: 600;
  border-radius: 8px;
  text-decoration: none;
  transition: background .15s;
}}
.header-cta:hover {{ background: #0a3a48; }}
.brand-header {{
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 8px;
}}
.brand-logo {{
  width: 64px;
  height: 64px;
  border-radius: 16px;
  object-fit: contain;
  background: white;
  border: 1px solid var(--border);
  padding: 4px;
}}
.brand-header h1 {{
  font-size: 2.2rem;
  letter-spacing: -0.03em;
  line-height: 1.15;
}}
.brand-header .domain {{
  color: var(--muted);
  font-size: .95rem;
  font-weight: 500;
}}
.brand-description {{
  color: #304249;
  font-size: 1rem;
  max-width: 800px;
  margin: 8px 0 24px;
}}
.kpi-grid {{
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 32px;
}}
.kpi-card {{
  background: white;
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 18px;
}}
.kpi-card .value {{
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--navy);
}}
.kpi-card .label {{
  font-size: .72rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: .06em;
  margin-top: 4px;
}}
.kpi-card .sub {{
  font-size: .8rem;
  color: var(--teal);
  font-weight: 600;
  margin-top: 6px;
}}
section {{
  background: white;
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 28px;
  margin-bottom: 20px;
}}
section h2 {{
  font-size: 1.2rem;
  color: var(--pink);
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 2px solid var(--pink-light);
}}
.two-col {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}}
.detail-row {{
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: .9rem;
}}
.detail-row .lbl {{ color: var(--muted); }}
.detail-row .val {{ font-weight: 600; text-align: right; }}

/* Fit Score */
.fit-hero {{
  display: flex;
  align-items: center;
  gap: 32px;
  margin-bottom: 20px;
}}
.fit-ring {{
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  flex-shrink: 0;
}}
.fit-ring .number {{
  font-size: 2.4rem;
  font-weight: 800;
  color: white;
  line-height: 1;
}}
.fit-ring .grade {{
  font-size: 1rem;
  font-weight: 700;
  color: rgba(255,255,255,.85);
  margin-top: 2px;
}}
.fit-rec {{
  font-size: .95rem;
  line-height: 1.6;
  color: #304249;
}}
.score-bar-row {{
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
  font-size: .85rem;
}}
.score-bar-label {{
  width: 160px;
  flex-shrink: 0;
  font-weight: 600;
}}
.score-bar-track {{
  flex: 1;
  height: 10px;
  background: #eee;
  border-radius: 5px;
  overflow: hidden;
}}
.score-bar-fill {{
  height: 100%;
  border-radius: 5px;
  transition: width .4s;
}}
.score-bar-value {{
  width: 40px;
  text-align: right;
  font-weight: 700;
}}
.score-notes {{
  margin-top: 4px;
  margin-bottom: 12px;
  padding-left: 172px;
}}
.score-notes li {{
  font-size: .78rem;
  color: var(--muted);
  list-style: disc;
  margin-bottom: 2px;
}}

/* Ad cards */
.platform-block {{ margin-bottom: 18px; }}
.platform-block h3 {{
  font-size: .95rem;
  font-weight: 700;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}}
.platform-block .count-badge {{
  background: var(--pink-light);
  color: var(--pink);
  font-size: .72rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
}}
.ad-list {{
  list-style: none;
  padding: 0;
}}
.ad-list li {{
  font-size: .82rem;
  padding: 6px 0;
  border-bottom: 1px solid #f5f5f5;
}}
.ad-list li a {{
  color: var(--teal);
  text-decoration: none;
}}
.ad-list li a:hover {{ text-decoration: underline; }}

/* Milled calendar */
.month-group {{ margin-bottom: 16px; }}
.month-group h3 {{
  font-size: .88rem;
  font-weight: 700;
  color: var(--navy);
  margin-bottom: 6px;
  padding-bottom: 4px;
  border-bottom: 1px solid #f0f0f0;
}}
.email-row {{
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 8px;
  padding: 5px 0;
  font-size: .82rem;
  border-bottom: 1px solid #fafafa;
}}
.email-date {{ color: var(--muted); font-weight: 500; }}
.email-subject a {{
  color: var(--teal);
  text-decoration: none;
}}

/* Tech pills */
.pill-grid {{
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}}
.pill {{
  background: var(--bg-grey);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 4px 10px;
  font-size: .78rem;
  font-weight: 500;
}}

/* Gaps */
.gap-card {{
  background: #FFF7ED;
  border: 1px solid #FEC84B;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 10px;
}}
.gap-card.opportunity {{
  background: #ECFDF3;
  border-color: #6CE9A6;
}}
.gap-card h4 {{
  font-size: .9rem;
  margin-bottom: 4px;
}}
.gap-card p {{
  font-size: .82rem;
  color: #475467;
}}

/* ── Site-style Footer ── */
.site-footer {{
  margin-top: 80px;
}}
.footer-cta {{
  background: var(--navy);
  border-radius: 20px;
  padding: 48px 32px;
  text-align: center;
  margin-bottom: 32px;
}}
.footer-cta h3 {{
  color: var(--white);
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 8px;
  border: none;
  padding: 0;
}}
.footer-cta p {{
  color: rgba(255,255,255,.65);
  font-size: .95rem;
  margin-bottom: 20px;
}}
.footer-cta .cta-btn {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 28px;
  background: var(--white);
  color: var(--navy);
  font-size: .9rem;
  font-weight: 600;
  border-radius: 10px;
  text-decoration: none;
  transition: transform .15s, box-shadow .15s;
}}
.footer-cta .cta-btn:hover {{ transform: translateY(-1px); box-shadow: 0 4px 16px rgba(0,0,0,.2); }}
.footer-bottom {{
  padding: 24px 0 12px;
  text-align: center;
}}
.footer-nav {{
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-bottom: 20px;
}}
.footer-nav a {{
  color: var(--navy);
  text-decoration: none;
  font-size: .82rem;
  font-weight: 500;
}}
.footer-nav a:hover {{ color: var(--pink); }}
.footer-social {{
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-bottom: 20px;
}}
.footer-social a {{
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--bg-grey);
  color: var(--navy);
  text-decoration: none;
  transition: background .15s;
}}
.footer-social a:hover {{ background: var(--pink-light); }}
.footer-social a svg {{ width: 16px; height: 16px; }}
.footer-wordmark {{
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}}
.footer-wordmark svg {{ height: 22px; width: auto; opacity: .5; }}
.footer-legal {{
  display: flex;
  justify-content: center;
  gap: 18px;
  margin-bottom: 8px;
}}
.footer-legal a {{
  color: var(--muted);
  text-decoration: none;
  font-size: .75rem;
}}
.footer-legal a:hover {{ color: var(--navy); }}
.footer-meta {{
  color: var(--muted);
  font-size: .72rem;
  margin-top: 6px;
}}

/* Budget cards */
.budget-cards {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}}
.budget-card {{
  border-radius: 16px;
  padding: 20px;
  text-align: center;
  color: white;
}}
.budget-card .month {{ font-size: .75rem; text-transform: uppercase; letter-spacing: .06em; opacity: .85; }}
.budget-card .amount {{ font-size: 1.8rem; font-weight: 800; margin: 6px 0; }}
.budget-card .note {{ font-size: .72rem; opacity: .7; }}

/* Allocation bar */
.alloc-bar {{
  display: flex;
  border-radius: 8px;
  overflow: hidden;
  height: 28px;
  margin: 12px 0;
}}
.alloc-bar div {{
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: .7rem;
  font-weight: 700;
  color: white;
}}

/* Health badge */
.health-badge {{
  display: inline-block;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: .78rem;
  font-weight: 700;
  color: white;
}}

/* Data table */
.data-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: .82rem;
  margin-top: 12px;
}}
.data-table th {{
  text-align: left;
  font-size: .72rem;
  text-transform: uppercase;
  letter-spacing: .04em;
  color: var(--muted);
  padding: 8px 10px;
  border-bottom: 2px solid var(--border);
}}
.data-table td {{
  padding: 8px 10px;
  border-bottom: 1px solid #f0f0f0;
}}
.data-table tr.replied {{ background: #ECFDF380; }}

/* Signal chips */
.signal-positive {{
  color: var(--success);
  font-size: .82rem;
  padding: 2px 0;
}}
.signal-negative {{
  color: var(--danger);
  font-size: .82rem;
  padding: 2px 0;
}}

/* Meeting card */
.meeting-card {{
  background: var(--bg-grey);
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 10px;
}}
.meeting-card h4 {{ font-size: .88rem; margin-bottom: 4px; }}
.meeting-card .meta {{ font-size: .78rem; color: var(--muted); margin-bottom: 6px; }}
.meeting-card ul {{ font-size: .8rem; padding-left: 18px; margin: 4px 0; }}

@media (max-width: 900px) {{
  .kpi-grid {{ grid-template-columns: repeat(3, 1fr); }}
  .two-col {{ grid-template-columns: 1fr; }}
}}
@media (max-width: 640px) {{
  .kpi-grid {{ grid-template-columns: 1fr 1fr; }}
  .fit-hero {{ flex-direction: column; text-align: center; }}
  .score-notes {{ padding-left: 0; }}
  .score-bar-label {{ width: 100px; }}
}}

/* Section download buttons */
.section-wrap {{
  position: relative;
}}
.section-wrap .dl-btn {{
  position: absolute;
  top: 12px;
  right: 12px;
  background: var(--navy);
  color: white;
  border: none;
  border-radius: 6px;
  padding: 5px 10px;
  font-size: .68rem;
  font-weight: 600;
  font-family: 'Inter', sans-serif;
  cursor: pointer;
  opacity: 0;
  transition: opacity .2s;
  z-index: 10;
  letter-spacing: .03em;
}}
.section-wrap:hover .dl-btn {{
  opacity: .7;
}}
.section-wrap .dl-btn:hover {{
  opacity: 1;
}}
.zip-bar {{
  margin-top: 32px;
  padding: 20px;
  background: var(--navy);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}}
.zip-bar button {{
  background: var(--pink);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 10px 24px;
  font-size: .88rem;
  font-weight: 700;
  font-family: 'Inter', sans-serif;
  cursor: pointer;
  transition: background .2s;
}}
.zip-bar button:hover {{
  background: #a02a9d;
}}
.zip-bar span {{
  color: rgba(255,255,255,.6);
  font-size: .82rem;
}}
</style>
</head>
<body>
<div class="page">
  <header class="site-header">
    <div class="site-header-inner">
      <a href="https://upscale.ai" class="logo-link" target="_blank" rel="noopener">
        <svg width="136" height="35" viewBox="0 0 136 35" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M10.7512 9.8282H14.7971V12.5491L14.2694 13.4635L12.7793 16.0451H14.7971V25.5127H10.7512V23.7557C9.76786 25.22 8.2103 25.952 6.07706 25.952C4.36255 25.952 2.94576 25.3771 1.82679 24.2264C0.707924 23.0762 0.148438 21.4869 0.148438 19.4588V9.8282H4.19487V18.9564C4.19487 20.0027 4.47724 20.8022 5.04188 21.3564C5.60652 21.9107 6.35943 22.1878 7.30032 22.1878C8.34591 22.1878 9.18251 21.8632 9.81022 21.2149C10.4371 20.5666 10.7512 19.5944 10.7512 18.2977V9.8282ZM88.2742 2.61377L84.2277 4.95011V25.5127H88.2742V2.61377ZM94.4343 19.3327C94.978 21.2986 96.4518 22.2819 98.857 22.2819C100.404 22.2819 101.576 21.7588 102.37 20.7132L105.633 22.5954C104.085 24.8331 101.805 25.952 98.7941 25.952C96.2015 25.952 94.1207 25.1674 92.5521 23.5995C90.9835 22.0308 90.1995 20.0546 90.1995 17.6709C90.1995 15.3077 90.9732 13.3366 92.5208 11.7577C94.068 10.1787 96.0548 9.3894 98.4807 9.3894C100.781 9.3894 102.678 10.1839 104.174 11.7732C105.669 13.3628 106.417 15.3286 106.417 17.6709C106.417 18.1931 106.365 18.7474 106.26 19.3327H94.4343ZM94.3713 16.1963H102.37C102.14 15.13 101.665 14.335 100.943 13.8124C100.221 13.2894 99.401 13.0277 98.4807 13.0277C97.393 13.0277 96.4942 13.3049 95.7828 13.8592C95.0723 14.4135 94.6016 15.1922 94.3713 16.1963ZM78.2562 9.8282H82.3027V25.5127H78.2562V23.6617C77.0433 25.1888 75.3388 25.952 73.1433 25.952C71.0524 25.952 69.259 25.1518 67.7638 23.552C66.2685 21.9521 65.5208 19.9916 65.5208 17.6709C65.5208 15.3492 66.2685 13.3885 67.7638 11.7887C69.259 10.1891 71.0524 9.3894 73.1433 9.3894C75.3388 9.3894 77.0433 10.1526 78.2562 11.6792V9.8282ZM70.7907 20.8548C71.6064 21.6803 72.6417 22.0937 73.8963 22.0937C75.1507 22.0937 76.1909 21.6803 77.0172 20.8548C77.8434 20.0285 78.2562 18.9675 78.2562 17.6709C78.2562 16.3739 77.8434 15.3129 77.0172 14.4868C76.1909 13.6606 75.1507 13.2478 73.8963 13.2478C72.6417 13.2478 71.6064 13.6606 70.7907 14.4868C69.9748 15.3129 69.5675 16.3739 69.5675 17.6709C69.5675 18.9675 69.9748 20.0285 70.7907 20.8548ZM57.4253 25.952C55.0622 25.952 53.0913 25.1569 51.5121 23.5674C49.9332 21.9781 49.144 20.0131 49.144 17.6709C49.144 15.3286 49.9332 13.3628 51.5121 11.7732C53.0913 10.1839 55.0622 9.3894 57.4253 9.3894C58.9518 9.3894 60.3425 9.75566 61.597 10.4869C62.8523 11.2189 63.8037 12.2022 64.4515 13.436L60.9701 15.4746C60.6561 14.8268 60.1803 14.3141 59.5422 13.9377C58.9051 13.5614 58.1885 13.3731 57.3941 13.3731C56.1811 13.3731 55.1771 13.7755 54.3828 14.5809C53.5878 15.3854 53.1906 16.4155 53.1906 17.6709C53.1906 18.9044 53.5878 19.9242 54.3828 20.7288C55.1771 21.5344 56.1811 21.9366 57.3941 21.9366C58.2092 21.9366 58.9361 21.7537 59.574 21.3874C60.2115 21.0215 60.6878 20.5147 61.0014 19.8663L64.5142 21.8735C63.8246 23.1074 62.8523 24.0959 61.597 24.8382C60.3425 25.5808 58.9518 25.952 57.4253 25.952ZM39.503 14.2831C39.503 14.7009 39.7802 15.0409 40.3344 15.3026C40.8888 15.5634 41.5629 15.7938 42.3579 15.9924C43.1524 16.1911 43.9467 16.4421 44.7418 16.7453C45.5362 17.0483 46.2104 17.5559 46.7647 18.2664C47.3189 18.9778 47.5962 19.8663 47.5962 20.9325C47.5962 22.5428 46.995 23.7823 45.7925 24.6502C44.5898 25.5178 43.0894 25.952 41.2909 25.952C38.0707 25.952 35.8753 24.7073 34.7036 22.2189L38.2175 20.2427C38.6775 21.6018 39.7017 22.2819 41.2909 22.2819C42.7345 22.2819 43.4554 21.8322 43.4554 20.9325C43.4554 20.5147 43.1783 20.1745 42.624 19.9139C42.0705 19.6522 41.3955 19.4166 40.6012 19.2077C39.8059 18.9987 39.0117 18.7371 38.2175 18.4235C37.4224 18.1095 36.748 17.6129 36.1937 16.9334C35.6395 16.2541 35.3622 15.4019 35.3622 14.377C35.3622 12.829 35.932 11.6109 37.0719 10.7224C38.2123 9.8342 39.629 9.3894 41.3229 9.3894C42.5981 9.3894 43.7584 9.67682 44.8047 10.2521C45.8503 10.827 46.6759 11.6479 47.2826 12.7145L43.8318 14.5963C43.3301 13.5301 42.4935 12.9967 41.3229 12.9967C40.7996 12.9967 40.3654 13.1114 40.0208 13.3419C39.6758 13.5717 39.503 13.8858 39.503 14.2831ZM25.8503 9.3894C27.9621 9.3894 29.7658 10.1891 31.261 11.7887C32.7564 13.3885 33.5041 15.3492 33.5041 17.6709C33.5041 19.9916 32.7564 21.9521 31.261 23.552C29.7658 25.1518 27.9621 25.952 25.8503 25.952C23.6541 25.952 21.9601 25.1888 20.7686 23.6617V31.7867H16.7222V16.0451H18.7397L17.2496 13.4635L16.7222 12.5491V9.8282H20.7686V11.6792C21.9601 10.1526 23.6541 9.3894 25.8503 9.3894ZM21.9919 20.8548C22.807 21.6803 23.8423 22.0937 25.0973 22.0937C26.3519 22.0937 27.3924 21.6803 28.2187 20.8548C29.0439 20.0285 29.4574 18.9675 29.4574 17.6709C29.4574 16.3739 29.0439 15.3129 28.2187 14.4868C27.3924 13.6606 26.3519 13.2478 25.0973 13.2478C23.8423 13.2478 22.807 13.6606 21.9919 14.4868C21.1762 15.3129 20.7686 16.3739 20.7686 17.6709C20.7686 18.9675 21.1762 20.0285 21.9919 20.8548Z" fill="#2B2731"/>
          <path d="M111.441 24.1096C110.98 24.5707 110.427 24.8014 109.781 24.8014C109.136 24.8014 108.582 24.5707 108.121 24.1096C107.66 23.6485 107.43 23.0953 107.43 22.4496C107.43 21.8039 107.66 21.2506 108.121 20.7896C108.582 20.3285 109.136 20.0978 109.781 20.0978C110.427 20.0978 110.98 20.3285 111.441 20.7896C111.903 21.2506 112.133 21.8039 112.133 22.4496C112.133 23.0953 111.903 23.6485 111.441 24.1096ZM132.624 7.42658C131.978 7.42658 131.418 7.18931 130.944 6.71519C130.47 6.24096 130.233 5.68095 130.233 5.03516C130.233 4.38947 130.47 3.82452 130.944 3.3402C131.418 2.85598 131.978 2.61377 132.624 2.61377C133.29 2.61377 133.86 2.85598 134.334 3.3402C134.809 3.82452 135.046 4.38947 135.046 5.03516C135.046 5.68095 134.809 6.24096 134.334 6.71519C133.86 7.18931 133.29 7.42658 132.624 7.42658ZM130.687 24.3775V9.24275H134.592V24.3775H130.687ZM125.294 9.24275H129.199V24.3775H125.294V22.5918C124.124 24.0648 122.479 24.8014 120.36 24.8014C118.342 24.8014 116.612 24.0296 115.169 22.4859C113.726 20.9419 113.005 19.0501 113.005 16.8101C113.005 14.5702 113.726 12.6784 115.169 11.1347C116.612 9.59072 118.342 8.81888 120.36 8.81888C122.479 8.81888 124.124 9.5555 125.294 11.0285V9.24275ZM118.09 19.8824C118.877 20.6795 119.876 21.0781 121.087 21.0781C122.297 21.0781 123.301 20.6795 124.098 19.8824C124.896 19.0855 125.294 18.0613 125.294 16.8101C125.294 15.559 124.896 14.5348 124.098 13.7379C123.301 12.9408 122.297 12.5422 121.087 12.5422C119.876 12.5422 118.877 12.9408 118.09 13.7379C117.303 14.5348 116.909 15.559 116.909 16.8101C116.909 18.0613 117.303 19.0855 118.09 19.8824Z" fill="url(#paint0_linear_header)"/>
          <defs><linearGradient id="paint0_linear_header" x1="108.121" y1="24.1096" x2="135.174" y2="2.43389" gradientUnits="userSpaceOnUse"><stop stop-color="#B72BB3"/><stop offset="1" stop-color="#60B1E3"/></linearGradient></defs>
        </svg>
        <span class="logo-tagline">AI Creative + Media + Measurement &mdash; One Platform</span>
      </a>
      <nav class="site-header-nav">
        <a href="https://upscale.ai/how-it-works" target="_blank" rel="noopener">Platform</a>
        <a href="https://upscale.ai/solutions" target="_blank" rel="noopener">Solutions</a>
        <a href="https://upscale.ai/solutions#case-studies" target="_blank" rel="noopener">Case Studies</a>
        <a href="https://upscale.ai/about" target="_blank" rel="noopener">About</a>
        <a href="https://upscale.ai/careers" target="_blank" rel="noopener">Careers</a>
      </nav>
      <div class="header-actions">
        <span class="header-badge">Internal ICP Report</span>
        <a href="https://upscale.ai/contact" class="header-cta" target="_blank" rel="noopener">Get Demo</a>
      </div>
    </div>
  </header>

  <div class="brand-header">
    {logo_html}
    <div>
      <h1>{company}</h1>
      <span class="domain">{domain} &middot; {industry}</span>
    </div>
  </div>
  {f'<p class="brand-description">{description}</p>' if description else ''}

  {competitor_alert}

  {kpi_cards}

  <div class="section-wrap" data-section="Fit Score" data-filename="fit-score">
    <button class="dl-btn" onclick="dlSection(this)">&darr; Download</button>
    {fit_section}
  </div>

  <div class="section-wrap" data-section="Proposal" data-filename="proposal">
    <button class="dl-btn" onclick="dlSection(this)">&darr; Download</button>
    {proposal_section}
  </div>

  <div class="section-wrap" data-section="CRM Intelligence" data-filename="crm-intelligence">
    <button class="dl-btn" onclick="dlSection(this)">&darr; Download</button>
    {crm_section}
  </div>

  <div class="section-wrap" data-section="Key Contacts" data-filename="contacts" data-format="csv">
    <button class="dl-btn" onclick="dlContacts(this)">&darr; CSV</button>
    {contacts_section}
  </div>

  <div class="section-wrap" data-section="Ad Discovery" data-filename="ad-discovery">
    <button class="dl-btn" onclick="dlSection(this)">&darr; Download</button>
    {ads_section}
  </div>

  <div class="section-wrap" data-section="Brand Intelligence" data-filename="brand-intelligence">
    <button class="dl-btn" onclick="dlSection(this)">&darr; Download</button>
    {brand_intel_section}
  </div>

  {creative_pipeline_section}

  <div class="section-wrap" data-section="Key Events + Calendar" data-filename="key-events-calendar">
    <button class="dl-btn" onclick="dlSection(this)">&darr; Download</button>
    {key_events_section}
  </div>

  <div class="section-wrap" data-section="Company Profile" data-filename="company-profile">
    <button class="dl-btn" onclick="dlSection(this)">&darr; Download</button>
    {company_profile_section}
  </div>

  <div class="section-wrap" data-section="Channel Gaps" data-filename="channel-gaps">
    <button class="dl-btn" onclick="dlSection(this)">&darr; Download</button>
    {gaps_section}
  </div>

  <div class="section-wrap" data-section="Account Priority" data-filename="account-priority">
    <button class="dl-btn" onclick="dlSection(this)">&darr; Download</button>
    {priority_section}
  </div>

  <div class="section-wrap" data-section="Paid Media Maturity" data-filename="paid-media-maturity">
    <button class="dl-btn" onclick="dlSection(this)">&darr; Download</button>
    {maturity_section}
  </div>

  <div class="section-wrap" data-section="Creative Signals" data-filename="creative-signals">
    <button class="dl-btn" onclick="dlSection(this)">&darr; Download</button>
    {creative_signals_section}
  </div>

  <div class="section-wrap" data-section="CTV YouTube Hypotheses" data-filename="ctv-youtube-hypotheses">
    <button class="dl-btn" onclick="dlSection(this)">&darr; Download</button>
    {hypotheses_section}
  </div>

  <div class="section-wrap" data-section="Buying Committee" data-filename="buying-committee">
    <button class="dl-btn" onclick="dlSection(this)">&darr; Download</button>
    {committee_section}
  </div>

  <div class="section-wrap" data-section="Call Talk Track" data-filename="call-talk-track">
    <button class="dl-btn" onclick="dlSection(this)">&darr; Download</button>
    {talk_track_section}
  </div>

  <div class="section-wrap" data-section="Hiring Signals" data-filename="hiring-signals">
    <button class="dl-btn" onclick="dlSection(this)">&darr; Download</button>
    {hiring_section}
  </div>

  <div class="section-wrap" data-section="News &amp; Media" data-filename="news-media">
    <button class="dl-btn" onclick="dlSection(this)">&darr; Download</button>
    {news_section}
  </div>

  <div class="section-wrap" data-section="Podcasts &amp; Thought Leadership" data-filename="podcasts-thought-leadership">
    <button class="dl-btn" onclick="dlSection(this)">&darr; Download</button>
    {podcasts_section}
  </div>

  <div class="section-wrap" data-section="Platform Case Studies" data-filename="case-studies">
    <button class="dl-btn" onclick="dlSection(this)">&darr; Download</button>
    {case_studies_section}
  </div>

  <div class="zip-bar">
    <span>Download full report as Markdown + JSON</span>
    <button onclick="dlZip()">&#x1f4e6; Download ZIP</button>
  </div>

  <footer class="site-footer">
    <div class="footer-cta">
      <h3>Ready to unlock the power of AI advertising on Streaming TV?</h3>
      <p>See how Upscale.ai drives measurable performance for eCommerce brands.</p>
      <a href="https://upscale.ai/contact" class="cta-btn" target="_blank" rel="noopener">Get Demo &rarr;</a>
    </div>
    <div class="footer-bottom">
      <nav class="footer-nav">
        <a href="https://upscale.ai/how-it-works" target="_blank" rel="noopener">Platform</a>
        <a href="https://upscale.ai/solutions" target="_blank" rel="noopener">Solutions</a>
        <a href="https://upscale.ai/about" target="_blank" rel="noopener">About</a>
        <a href="https://upscale.ai/careers" target="_blank" rel="noopener">Careers</a>
        <a href="https://upscale.ai/contact" target="_blank" rel="noopener">Get Demo</a>
      </nav>
      <div class="footer-social">
        <a href="https://www.instagram.com/upscaleaihq" target="_blank" rel="noopener" title="Instagram"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg></a>
        <a href="https://www.linkedin.com/company/upscaleaihq/" target="_blank" rel="noopener" title="LinkedIn"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg></a>
        <a href="https://x.com/upscaleaiHQ" target="_blank" rel="noopener" title="X"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg></a>
        <a href="https://www.facebook.com/upscaleaihq" target="_blank" rel="noopener" title="Facebook"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg></a>
        <a href="https://www.youtube.com/@TVAdsAI" target="_blank" rel="noopener" title="YouTube"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg></a>
        <a href="https://vimeo.com/upscaleai" target="_blank" rel="noopener" title="Vimeo"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M23.977 6.416c-.105 2.338-1.739 5.543-4.894 9.609-3.268 4.247-6.026 6.37-8.29 6.37-1.409 0-2.578-1.294-3.553-3.881L5.322 11.4C4.603 8.816 3.834 7.522 3.01 7.522c-.179 0-.806.378-1.881 1.132L0 7.197c1.185-1.044 2.351-2.084 3.501-3.128C5.08 2.701 6.266 1.984 7.055 1.91c1.867-.18 3.016 1.1 3.447 3.838.465 2.953.789 4.789.971 5.507.539 2.45 1.131 3.674 1.776 3.674.502 0 1.256-.796 2.265-2.385 1.004-1.589 1.54-2.797 1.612-3.628.144-1.371-.395-2.061-1.614-2.061-.574 0-1.167.121-1.777.391 1.186-3.868 3.434-5.757 6.762-5.637 2.473.06 3.628 1.664 3.493 4.797l-.013.01z"/></svg></a>
      </div>
      <div class="footer-wordmark">
        <svg width="136" height="35" viewBox="0 0 136 35" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M10.7512 9.8282H14.7971V12.5491L14.2694 13.4635L12.7793 16.0451H14.7971V25.5127H10.7512V23.7557C9.76786 25.22 8.2103 25.952 6.07706 25.952C4.36255 25.952 2.94576 25.3771 1.82679 24.2264C0.707924 23.0762 0.148438 21.4869 0.148438 19.4588V9.8282H4.19487V18.9564C4.19487 20.0027 4.47724 20.8022 5.04188 21.3564C5.60652 21.9107 6.35943 22.1878 7.30032 22.1878C8.34591 22.1878 9.18251 21.8632 9.81022 21.2149C10.4371 20.5666 10.7512 19.5944 10.7512 18.2977V9.8282ZM88.2742 2.61377L84.2277 4.95011V25.5127H88.2742V2.61377ZM94.4343 19.3327C94.978 21.2986 96.4518 22.2819 98.857 22.2819C100.404 22.2819 101.576 21.7588 102.37 20.7132L105.633 22.5954C104.085 24.8331 101.805 25.952 98.7941 25.952C96.2015 25.952 94.1207 25.1674 92.5521 23.5995C90.9835 22.0308 90.1995 20.0546 90.1995 17.6709C90.1995 15.3077 90.9732 13.3366 92.5208 11.7577C94.068 10.1787 96.0548 9.3894 98.4807 9.3894C100.781 9.3894 102.678 10.1839 104.174 11.7732C105.669 13.3628 106.417 15.3286 106.417 17.6709C106.417 18.1931 106.365 18.7474 106.26 19.3327H94.4343ZM94.3713 16.1963H102.37C102.14 15.13 101.665 14.335 100.943 13.8124C100.221 13.2894 99.401 13.0277 98.4807 13.0277C97.393 13.0277 96.4942 13.3049 95.7828 13.8592C95.0723 14.4135 94.6016 15.1922 94.3713 16.1963ZM78.2562 9.8282H82.3027V25.5127H78.2562V23.6617C77.0433 25.1888 75.3388 25.952 73.1433 25.952C71.0524 25.952 69.259 25.1518 67.7638 23.552C66.2685 21.9521 65.5208 19.9916 65.5208 17.6709C65.5208 15.3492 66.2685 13.3885 67.7638 11.7887C69.259 10.1891 71.0524 9.3894 73.1433 9.3894C75.3388 9.3894 77.0433 10.1526 78.2562 11.6792V9.8282ZM70.7907 20.8548C71.6064 21.6803 72.6417 22.0937 73.8963 22.0937C75.1507 22.0937 76.1909 21.6803 77.0172 20.8548C77.8434 20.0285 78.2562 18.9675 78.2562 17.6709C78.2562 16.3739 77.8434 15.3129 77.0172 14.4868C76.1909 13.6606 75.1507 13.2478 73.8963 13.2478C72.6417 13.2478 71.6064 13.6606 70.7907 14.4868C69.9748 15.3129 69.5675 16.3739 69.5675 17.6709C69.5675 18.9675 69.9748 20.0285 70.7907 20.8548ZM57.4253 25.952C55.0622 25.952 53.0913 25.1569 51.5121 23.5674C49.9332 21.9781 49.144 20.0131 49.144 17.6709C49.144 15.3286 49.9332 13.3628 51.5121 11.7732C53.0913 10.1839 55.0622 9.3894 57.4253 9.3894C58.9518 9.3894 60.3425 9.75566 61.597 10.4869C62.8523 11.2189 63.8037 12.2022 64.4515 13.436L60.9701 15.4746C60.6561 14.8268 60.1803 14.3141 59.5422 13.9377C58.9051 13.5614 58.1885 13.3731 57.3941 13.3731C56.1811 13.3731 55.1771 13.7755 54.3828 14.5809C53.5878 15.3854 53.1906 16.4155 53.1906 17.6709C53.1906 18.9044 53.5878 19.9242 54.3828 20.7288C55.1771 21.5344 56.1811 21.9366 57.3941 21.9366C58.2092 21.9366 58.9361 21.7537 59.574 21.3874C60.2115 21.0215 60.6878 20.5147 61.0014 19.8663L64.5142 21.8735C63.8246 23.1074 62.8523 24.0959 61.597 24.8382C60.3425 25.5808 58.9518 25.952 57.4253 25.952ZM39.503 14.2831C39.503 14.7009 39.7802 15.0409 40.3344 15.3026C40.8888 15.5634 41.5629 15.7938 42.3579 15.9924C43.1524 16.1911 43.9467 16.4421 44.7418 16.7453C45.5362 17.0483 46.2104 17.5559 46.7647 18.2664C47.3189 18.9778 47.5962 19.8663 47.5962 20.9325C47.5962 22.5428 46.995 23.7823 45.7925 24.6502C44.5898 25.5178 43.0894 25.952 41.2909 25.952C38.0707 25.952 35.8753 24.7073 34.7036 22.2189L38.2175 20.2427C38.6775 21.6018 39.7017 22.2819 41.2909 22.2819C42.7345 22.2819 43.4554 21.8322 43.4554 20.9325C43.4554 20.5147 43.1783 20.1745 42.624 19.9139C42.0705 19.6522 41.3955 19.4166 40.6012 19.2077C39.8059 18.9987 39.0117 18.7371 38.2175 18.4235C37.4224 18.1095 36.748 17.6129 36.1937 16.9334C35.6395 16.2541 35.3622 15.4019 35.3622 14.377C35.3622 12.829 35.932 11.6109 37.0719 10.7224C38.2123 9.8342 39.629 9.3894 41.3229 9.3894C42.5981 9.3894 43.7584 9.67682 44.8047 10.2521C45.8503 10.827 46.6759 11.6479 47.2826 12.7145L43.8318 14.5963C43.3301 13.5301 42.4935 12.9967 41.3229 12.9967C40.7996 12.9967 40.3654 13.1114 40.0208 13.3419C39.6758 13.5717 39.503 13.8858 39.503 14.2831ZM25.8503 9.3894C27.9621 9.3894 29.7658 10.1891 31.261 11.7887C32.7564 13.3885 33.5041 15.3492 33.5041 17.6709C33.5041 19.9916 32.7564 21.9521 31.261 23.552C29.7658 25.1518 27.9621 25.952 25.8503 25.952C23.6541 25.952 21.9601 25.1888 20.7686 23.6617V31.7867H16.7222V16.0451H18.7397L17.2496 13.4635L16.7222 12.5491V9.8282H20.7686V11.6792C21.9601 10.1526 23.6541 9.3894 25.8503 9.3894ZM21.9919 20.8548C22.807 21.6803 23.8423 22.0937 25.0973 22.0937C26.3519 22.0937 27.3924 21.6803 28.2187 20.8548C29.0439 20.0285 29.4574 18.9675 29.4574 17.6709C29.4574 16.3739 29.0439 15.3129 28.2187 14.4868C27.3924 13.6606 26.3519 13.2478 25.0973 13.2478C23.8423 13.2478 22.807 13.6606 21.9919 14.4868C21.1762 15.3129 20.7686 16.3739 20.7686 17.6709C20.7686 18.9675 21.1762 20.0285 21.9919 20.8548Z" fill="#2B2731"/>
          <path d="M111.441 24.1096C110.98 24.5707 110.427 24.8014 109.781 24.8014C109.136 24.8014 108.582 24.5707 108.121 24.1096C107.66 23.6485 107.43 23.0953 107.43 22.4496C107.43 21.8039 107.66 21.2506 108.121 20.7896C108.582 20.3285 109.136 20.0978 109.781 20.0978C110.427 20.0978 110.98 20.3285 111.441 20.7896C111.903 21.2506 112.133 21.8039 112.133 22.4496C112.133 23.0953 111.903 23.6485 111.441 24.1096ZM132.624 7.42658C131.978 7.42658 131.418 7.18931 130.944 6.71519C130.47 6.24096 130.233 5.68095 130.233 5.03516C130.233 4.38947 130.47 3.82452 130.944 3.3402C131.418 2.85598 131.978 2.61377 132.624 2.61377C133.29 2.61377 133.86 2.85598 134.334 3.3402C134.809 3.82452 135.046 4.38947 135.046 5.03516C135.046 5.68095 134.809 6.24096 134.334 6.71519C133.86 7.18931 133.29 7.42658 132.624 7.42658ZM130.687 24.3775V9.24275H134.592V24.3775H130.687ZM125.294 9.24275H129.199V24.3775H125.294V22.5918C124.124 24.0648 122.479 24.8014 120.36 24.8014C118.342 24.8014 116.612 24.0296 115.169 22.4859C113.726 20.9419 113.005 19.0501 113.005 16.8101C113.005 14.5702 113.726 12.6784 115.169 11.1347C116.612 9.59072 118.342 8.81888 120.36 8.81888C122.479 8.81888 124.124 9.5555 125.294 11.0285V9.24275ZM118.09 19.8824C118.877 20.6795 119.876 21.0781 121.087 21.0781C122.297 21.0781 123.301 20.6795 124.098 19.8824C124.896 19.0855 125.294 18.0613 125.294 16.8101C125.294 15.559 124.896 14.5348 124.098 13.7379C123.301 12.9408 122.297 12.5422 121.087 12.5422C119.876 12.5422 118.877 12.9408 118.09 13.7379C117.303 14.5348 116.909 15.559 116.909 16.8101C116.909 18.0613 117.303 19.0855 118.09 19.8824Z" fill="url(#paint0_linear_footer)"/>
          <defs><linearGradient id="paint0_linear_footer" x1="108.121" y1="24.1096" x2="135.174" y2="2.43389" gradientUnits="userSpaceOnUse"><stop stop-color="#B72BB3"/><stop offset="1" stop-color="#60B1E3"/></linearGradient></defs>
        </svg>
      </div>
      <div class="footer-legal">
        <a href="https://upscale.ai/privacy" target="_blank" rel="noopener">Privacy</a>
        <a href="https://upscale.ai/terms" target="_blank" rel="noopener">Terms of Use</a>
      </div>
      <p class="footer-meta">Generated {generated} &middot; Confidential — Internal Use Only</p>
    </div>
  </footer>
</div>

<script src="https://cdn.jsdelivr.net/npm/jszip@3/dist/jszip.min.js"></script>
<script>
(function() {{
  /* --- Convert HTML section to Markdown-ish plain text --- */
  function htmlToMd(el) {{
    var clone = el.cloneNode(true);
    // Remove download buttons from clone
    clone.querySelectorAll('.dl-btn').forEach(function(b) {{ b.remove(); }});

    var md = '';
    // Extract headings
    clone.querySelectorAll('h2, h3, h4').forEach(function(h) {{
      var level = parseInt(h.tagName[1]);
      var prefix = '#'.repeat(level) + ' ';
      h.textContent = '\\n' + prefix + h.textContent.trim() + '\\n';
    }});

    // Convert tables to plain text rows
    clone.querySelectorAll('table').forEach(function(table) {{
      var rows = table.querySelectorAll('tr');
      var text = '\\n';
      rows.forEach(function(row) {{
        var cells = row.querySelectorAll('th, td');
        var vals = [];
        cells.forEach(function(c) {{ vals.push(c.textContent.trim()); }});
        text += '| ' + vals.join(' | ') + ' |\\n';
      }});
      table.textContent = text;
    }});

    // Convert list items
    clone.querySelectorAll('li').forEach(function(li) {{
      li.textContent = '- ' + li.textContent.trim() + '\\n';
    }});

    // Get cleaned text
    md = clone.textContent || clone.innerText || '';
    // Clean up excessive whitespace
    md = md.replace(/\\n{{3,}}/g, '\\n\\n').trim();
    return md;
  }}

  /* --- Extract tables from a section as CSV --- */
  function tablesToCsv(el) {{
    var tables = el.querySelectorAll('table.data-table');
    if (!tables.length) return '';
    var csv = '';
    tables.forEach(function(table, idx) {{
      if (idx > 0) csv += '\\n';
      // Get heading above the table if any
      var prev = table.previousElementSibling;
      if (prev && prev.tagName && prev.tagName.match(/^H[2-4]$/)) {{
        csv += '# ' + prev.textContent.trim() + '\\n';
      }}
      var rows = table.querySelectorAll('tr');
      rows.forEach(function(row) {{
        var cells = row.querySelectorAll('th, td');
        var vals = [];
        cells.forEach(function(c) {{
          var text = c.textContent.trim().replace(/"/g, '""');
          // Wrap in quotes if contains comma or newline
          if (text.indexOf(',') !== -1 || text.indexOf('\\n') !== -1) {{
            text = '"' + text + '"';
          }}
          vals.push(text);
        }});
        csv += vals.join(',') + '\\n';
      }});
    }});
    return csv;
  }}

  /* --- Download a single section as .md --- */
  window.dlSection = function(btn) {{
    var wrap = btn.closest('.section-wrap');
    var name = wrap.getAttribute('data-section');
    var filename = wrap.getAttribute('data-filename') || 'section';
    var md = '# ' + name + '\\n\\n' + htmlToMd(wrap);

    var blob = new Blob([md], {{ type: 'text/markdown' }});
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = '{domain}_' + filename + '.md';
    a.click();
    URL.revokeObjectURL(a.href);
  }};

  /* --- Download contacts section as CSV --- */
  window.dlContacts = function(btn) {{
    var wrap = btn.closest('.section-wrap');
    var csv = tablesToCsv(wrap);
    if (!csv) {{
      csv = 'No contacts found';
    }}
    var blob = new Blob([csv], {{ type: 'text/csv' }});
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = '{domain}_contacts.csv';
    a.click();
    URL.revokeObjectURL(a.href);
  }};

  /* --- Download ZIP with full report Markdown + contacts CSV --- */
  window.dlZip = function() {{
    var zip = new JSZip();
    var fullMd = '# ICP Report — {company}\\n';
    fullMd += '**Domain:** {domain}\\n';
    fullMd += '**Generated:** {generated}\\n\\n---\\n\\n';

    // Gather all sections
    var sections = document.querySelectorAll('.section-wrap');
    sections.forEach(function(wrap) {{
      var name = wrap.getAttribute('data-section');
      var filename = wrap.getAttribute('data-filename') || 'section';
      var fmt = wrap.getAttribute('data-format');

      if (fmt === 'csv') {{
        // Contacts → CSV
        var csv = tablesToCsv(wrap);
        zip.file(filename + '.csv', csv || 'No contacts found');
        fullMd += '## ' + name + '\\n\\nSee ' + filename + '.csv\\n\\n---\\n\\n';
      }} else {{
        var sectionMd = htmlToMd(wrap);
        fullMd += '## ' + name + '\\n\\n' + sectionMd + '\\n\\n---\\n\\n';
        zip.file(filename + '.md', '# ' + name + '\\n\\n' + sectionMd);
      }}
    }});

    // Add full report markdown
    zip.file('full-report.md', fullMd);

    // Generate and download
    zip.generateAsync({{ type: 'blob' }}).then(function(blob) {{
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = '{domain}_icp-report.zip';
      a.click();
      URL.revokeObjectURL(a.href);
    }});
  }};
}})();
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------


def _build_competitor_alert(report: DomainAdReport) -> str:
    """Return a prominent alert banner with Creative Reality Matrix if CTV competitors detected."""
    cd = report.competitor_detection
    # Also check if domain is in competitor case studies
    case_study_intel = get_case_study_brand_intel(report.domain)

    if not cd.found and not case_study_intel:
        return ""

    parts = []

    # --- Competitor tech detection banner ---
    if cd.found:
        competitors = ", ".join(_esc(c) for c in cd.competitors_detected) or "Unknown"
        tags = ", ".join(_esc(t) for t in cd.tags_matched) or "—"
        parts.append(f"""<div style="background:#FEF3F2;border:2px solid #FDA29B;border-radius:12px;padding:20px 24px;margin-bottom:16px">
  <div style="color:#B42318;font-weight:700;font-size:1.05rem;margin-bottom:6px">
    \u26a0 CTV COMPETITOR DETECTED: {competitors}
  </div>
  <div style="color:#B42318;font-size:.9rem;margin-bottom:16px">
    Tags found: <strong>{tags}</strong>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">""")

        # Creative Reality Matrix comparison for each detected competitor
        for comp_name in cd.competitors_detected:
            cr = CREATIVE_REALITY_MATRIX.get(comp_name)
            intel = get_competitor_intel(comp_name)
            if cr:
                parts.append(f"""    <div style="background:white;border:1px solid #FDA29B;border-radius:8px;padding:14px">
      <div style="font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#B42318;margin-bottom:6px">{_esc(comp_name)}</div>
      <div style="font-size:.82rem;font-weight:600;margin-bottom:4px">{_esc(cr['tool'])}</div>
      <div style="font-size:.78rem;color:#B42318;font-weight:600;margin-bottom:6px">{_esc(cr['verdict'])}</div>
      <div style="font-size:.78rem;color:#475467">{_esc(cr['response'])}</div>
    </div>""")

        # Always show Upscale's side
        upscale_cr = CREATIVE_REALITY_MATRIX["Upscale"]
        parts.append(f"""    <div style="background:#F6EBF6;border:1px solid #831F80;border-radius:8px;padding:14px">
      <div style="font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#831F80;margin-bottom:6px">Upscale</div>
      <div style="font-size:.82rem;font-weight:600;margin-bottom:4px">{_esc(upscale_cr['tool'])}</div>
      <div style="font-size:.78rem;color:#831F80;font-weight:600;margin-bottom:6px">{_esc(upscale_cr['verdict'])}</div>
      <div style="font-size:.78rem;color:#475467">{_esc(upscale_cr['response'])}</div>
    </div>""")

        parts.append("  </div>")

        # Sell motions + discovery questions for each competitor
        for comp_name in cd.competitors_detected:
            intel = get_competitor_intel(comp_name)
            if intel:
                motions = "".join(f'<li style="padding:3px 0;font-size:.82rem">{_esc(m)}</li>' for m in intel.get("sell_motions", []))
                questions = "".join(f'<li style="padding:3px 0;font-size:.82rem">{_esc(q)}</li>' for q in intel.get("discovery_questions", []))
                landmines = "".join(f'<li style="padding:3px 0;font-size:.82rem;color:#B42318">{_esc(l)}</li>' for l in intel.get("landmines", []))
                press = _esc(intel.get("where_upscale_presses", ""))

                # Objection/response pairs
                objections_html = ""
                for obj in intel.get("objections", []):
                    objections_html += f"""<div style="background:white;border-radius:8px;padding:12px;border:1px solid #e0e0e0;margin-bottom:8px">
        <div style="font-size:.78rem;font-weight:700;color:#B42318;margin-bottom:4px">&ldquo;{_esc(obj['objection'])}&rdquo;</div>
        <div style="font-size:.78rem;color:#475467">{_esc(obj['response'])}</div>
      </div>"""

                # Attribution comparison
                attr = intel.get("attribution", {})
                attr_html = ""
                if attr:
                    attr_html = f"""<div style="background:white;border-radius:8px;padding:14px;border:1px solid #e0e0e0">
      <div style="font-size:.72rem;font-weight:700;text-transform:uppercase;color:var(--navy);margin-bottom:10px">{_esc(comp_name)} Attribution Model</div>
      <div style="font-size:.78rem;margin-bottom:6px"><strong>Tracking:</strong> {_esc(attr.get('native_tracking', ''))}</div>
      <div style="font-size:.78rem;margin-bottom:6px"><strong>Logic:</strong> {_esc(attr.get('core_logic', ''))}</div>
      <div style="font-size:.78rem;margin-bottom:6px"><strong>Windows:</strong> {_esc(attr.get('windows', ''))}</div>
      <div style="font-size:.78rem;margin-bottom:6px"><strong>Extensions:</strong> {_esc(attr.get('extensions', ''))}</div>
      <div style="font-size:.78rem;font-style:italic;color:var(--teal);font-weight:600">{_esc(attr.get('bottom_line', ''))}</div>
    </div>"""

                parts.append(f"""
  <div style="margin-top:16px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px">
    <div style="background:white;border-radius:8px;padding:14px;border:1px solid #e0e0e0">
      <div style="font-size:.72rem;font-weight:700;text-transform:uppercase;color:var(--teal);margin-bottom:8px">Sell Motions vs {_esc(comp_name)}</div>
      <ul style="list-style:none;padding:0;margin:0">{motions}</ul>
    </div>
    <div style="background:white;border-radius:8px;padding:14px;border:1px solid #e0e0e0">
      <div style="font-size:.72rem;font-weight:700;text-transform:uppercase;color:var(--pink);margin-bottom:8px">Discovery Questions</div>
      <ul style="list-style:none;padding:0;margin:0">{questions}</ul>
    </div>
    <div style="background:white;border-radius:8px;padding:14px;border:1px solid #e0e0e0">
      <div style="font-size:.72rem;font-weight:700;text-transform:uppercase;color:#B42318;margin-bottom:8px">Landmines (Don't Say)</div>
      <ul style="list-style:none;padding:0;margin:0">{landmines}</ul>
    </div>
  </div>
  <div style="margin-top:12px;padding:12px 16px;background:#F6EBF6;border-radius:8px;font-size:.82rem">
    <strong style="color:#831F80">Where Upscale Presses:</strong> {press}
  </div>

  <div style="margin-top:16px;display:grid;grid-template-columns:1fr 1fr;gap:12px">
    <div>
      <div style="font-size:.72rem;font-weight:700;text-transform:uppercase;color:var(--navy);margin-bottom:8px;letter-spacing:.05em">Objection Handling vs {_esc(comp_name)}</div>
      {objections_html}
    </div>
    {attr_html}
  </div>""")

        parts.append("</div>")

    # --- Case study brand intelligence ---
    if case_study_intel:
        comp_names = ", ".join(_esc(c) for c in case_study_intel["competitors"])
        parts.append(f"""<div style="background:#FFFBEB;border:2px solid #F59E0B;border-radius:12px;padding:20px 24px;margin-bottom:16px">
  <div style="color:#92400E;font-weight:700;font-size:1.05rem;margin-bottom:6px">
    \U0001f4a1 WARM PROSPECT — Appears in {comp_names} Case Studies
  </div>
  <div style="font-size:.88rem;color:#92400E;margin-bottom:8px">
    <strong>Vertical:</strong> {_esc(case_study_intel['vertical'])}
  </div>
  <div style="font-size:.88rem;color:#78350F">
    <strong>Why they're a prospect:</strong> {_esc(case_study_intel['why_prospect'])}
  </div>
  <div style="font-size:.82rem;color:#92400E;margin-top:10px;font-style:italic">
    This brand has proven CTV budget, willingness to switch platforms, and engagement with performance marketing.
  </div>
</div>""")

    return "\n".join(parts)


def _build_kpi_cards(report: DomainAdReport, fit: UpscaleFitResult) -> str:
    e = report.enrichment
    mix = report.channel_mix

    cards = []

    # Fit score
    gc = _grade_color(fit.grade)
    cards.append(f"""<div class="kpi-card">
  <div class="value" style="color:{gc}">{fit.total_score}</div>
  <div class="label">Upscale Fit Score</div>
  <div class="sub" style="color:{gc}">Grade: {fit.grade}</div>
</div>""")

    # Revenue
    monthly = _fmt_money(e.estimated_monthly_revenue) if e else "—"
    annual = _fmt_money(e.estimated_annual_revenue) if e else ""
    cards.append(f"""<div class="kpi-card">
  <div class="value">{monthly}</div>
  <div class="label">Monthly DTC Revenue</div>
  <div class="sub">{annual}/yr</div>
</div>""")

    # Traffic
    visits = _fmt_number(e.estimated_monthly_visits) if e else "—"
    cards.append(f"""<div class="kpi-card">
  <div class="value">{visits}</div>
  <div class="label">Monthly Visits</div>
</div>""")

    # Ads
    cards.append(f"""<div class="kpi-card">
  <div class="value">{mix.total_ads_found if mix else 0}</div>
  <div class="label">Ads Discovered</div>
  <div class="sub">{mix.total_platforms if mix else 0} platforms</div>
</div>""")

    # Promotional Activity (qualitative assessment replacing raw email cadence)
    promo_label, promo_color, _promo_reasons = _assess_promotional_intensity(report)
    cards.append(f"""<div class="kpi-card">
  <div class="value" style="font-size:1rem;color:{promo_color};">{promo_label}</div>
  <div class="label">Promotional Activity</div>
  <div class="sub">{len(_promo_reasons)} signals detected</div>
</div>""")

    return f'<div class="kpi-grid">{"".join(cards)}</div>'


def _build_fit_section(fit: UpscaleFitResult) -> str:
    gc = _grade_color(fit.grade)

    bars = []
    for cat in fit.categories:
        bc = _score_bar_color(cat.score)
        notes_html = ""
        if cat.notes:
            items = "".join(f"<li>{_esc(n)}</li>" for n in cat.notes)
            notes_html = f'<ul class="score-notes">{items}</ul>'

        bars.append(f"""<div class="score-bar-row">
  <span class="score-bar-label">{_esc(cat.name)} ({int(cat.weight * 100)}%)</span>
  <div class="score-bar-track"><div class="score-bar-fill" style="width:{cat.score}%;background:{bc}"></div></div>
  <span class="score-bar-value">{cat.score:.0f}</span>
</div>
{notes_html}""")

    return f"""<section>
  <h2>Upscale Fit Score</h2>
  <div class="fit-hero">
    <div class="fit-ring" style="background:{gc}">
      <span class="number">{fit.total_score}</span>
      <span class="grade">{fit.grade}</span>
    </div>
    <p class="fit-rec">{_esc(fit.recommendation)}</p>
  </div>
  {"".join(bars)}
</section>"""


def _build_company_profile_section(report: DomainAdReport) -> str:
    """Combined Company Profile section — replaces enrichment + social sections."""
    e = report.enrichment
    clay = report.clay

    if not e:
        return '<section><h2>Company Profile</h2><p>No enrichment data available.</p></section>'

    # ── Hero Card ──
    company_name = _esc(e.company_name or report.company_name or report.domain)
    initial = (e.company_name or report.company_name or report.domain or "?")[0].upper()
    industry = _esc(e.industry) if e.industry else ""
    hq = _esc(", ".join(filter(None, [
        getattr(e, 'city', None),
        getattr(e, 'state', None),
        getattr(e, 'country', None),
    ])) or "—")
    year_founded = _esc(getattr(e, 'store_created_at', None) or "—")
    if year_founded and len(year_founded) >= 4:
        year_founded = year_founded[:4]
    employees = _fmt_number(e.employee_count) if e.employee_count else "—"
    platform = _esc(e.ecommerce_platform or "—")

    hero_card = f"""<div style="display:flex;gap:24px;align-items:center;padding:20px;background:var(--bg-grey);border-radius:16px;margin-bottom:24px">
  <div style="width:80px;height:80px;background:var(--navy);border-radius:16px;display:flex;align-items:center;justify-content:center;color:white;font-size:2rem;font-weight:800;flex-shrink:0">{initial}</div>
  <div>
    <h3 style="font-size:1.2rem;margin-bottom:4px">{company_name}</h3>
    <div style="font-size:.85rem;color:var(--muted)">{industry}</div>
    <div style="display:flex;gap:16px;margin-top:8px;font-size:.82rem;flex-wrap:wrap">
      <span>&#x1f4cd; {hq}</span>
      <span>&#x1f4c5; Founded {year_founded}</span>
      <span>&#x1f465; {employees} employees</span>
      <span>&#x1f6cd;&#xfe0f; {platform}</span>
    </div>
  </div>
</div>"""

    # ── Key People ──
    key_people_html = ""
    people_list = getattr(e, 'key_people', None) or []
    # Supplement with Clay founders if no key_people
    clay_founders_shown = False
    if not people_list and clay and clay.founders:
        people_list = [{"name": f, "title": "Founder"} for f in clay.founders]
        clay_founders_shown = True

    if people_list:
        people_cards = []
        for person in people_list:
            if isinstance(person, dict):
                name = person.get("name", "")
                title = person.get("title", "")
            else:
                name = getattr(person, 'name', str(person))
                title = getattr(person, 'title', '')
            if not name:
                continue
            parts = name.split()
            initials = (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else name[0].upper()
            people_cards.append(f"""<div style="display:flex;align-items:center;gap:10px;padding:10px;background:white;border:1px solid var(--border);border-radius:10px">
      <div style="width:36px;height:36px;background:var(--teal);border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:.8rem">{_esc(initials)}</div>
      <div>
        <div style="font-weight:600;font-size:.85rem">{_esc(name)}</div>
        <div style="font-size:.75rem;color:var(--muted)">{_esc(title)}</div>
      </div>
    </div>""")

        if people_cards:
            key_people_html = f"""<div style="margin-bottom:24px">
  <h3>Key People</h3>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px">
    {"".join(people_cards)}
  </div>
</div>"""

    # ── Company Details Table (from enrichment) ──
    def row(label, val):
        return f'<div class="detail-row"><span class="lbl">{label}</span><span class="val">{_esc(val)}</span></div>'

    left_rows = [
        row("Domain", e.domain),
        row("Industry", e.industry),
        row("E-Commerce Platform", f"{e.ecommerce_platform or '—'}{(' (' + e.ecommerce_plan + ')') if e.ecommerce_plan else ''}"),
        row("Monthly Revenue", _fmt_money(e.estimated_monthly_revenue)),
        row("Annual Revenue", _fmt_money(e.estimated_annual_revenue)),
        row("Employees", _fmt_number(e.employee_count)),
        row("Monthly Visits", _fmt_number(e.estimated_monthly_visits)),
        row("Monthly Pageviews", _fmt_number(e.estimated_monthly_pageviews)),
    ]

    right_rows = [
        row("Product Count", _fmt_number(e.product_count)),
        row("Avg Product Price", e.avg_product_price or "—"),
        row("Price Range", e.price_range or "—"),
        row("Platform Rank", _fmt_number(e.platform_rank)),
        row("Location", ", ".join(filter(None, [e.city, e.state, e.country])) or "—"),
        row("Store Created", (e.store_created_at or "—")[:10]),
    ]

    if e.review_count:
        right_rows.append(
            row("Reviews", f"{e.review_rating} stars / {_fmt_number(e.review_count)} on {e.review_source or 'unknown'}")
        )

    details_html = f"""<div style="margin-bottom:24px">
  <h3>Company Details</h3>
  <div class="two-col">
    <div>{"".join(left_rows)}</div>
    <div>{"".join(right_rows)}</div>
  </div>
</div>"""

    # ── Fundraising ──
    fundraising_html = ""
    fund_rows = []
    if clay and clay.enriched:
        if clay.latest_funding:
            fund_rows.append(row("Latest Funding", clay.latest_funding))
        if clay.investors:
            fund_rows.append(row("Investors", ", ".join(clay.investors)))
    # Also check enrichment for total_funding
    total_funding = getattr(e, 'total_funding', None)
    if total_funding:
        fund_rows.insert(0, row("Total Funding", total_funding))
    latest_round = getattr(e, 'latest_round', None)
    if latest_round and not (clay and clay.latest_funding):
        fund_rows.insert(0 if not total_funding else 1, row("Latest Round", latest_round))

    if fund_rows:
        fundraising_html = f"""<div style="margin-bottom:24px">
  <h3>Fundraising</h3>
  {"".join(fund_rows)}
</div>"""

    # ── Crunchbase Data ──
    cb_rows = []
    legal_name = getattr(e, 'legal_name', None)
    if legal_name:
        cb_rows.append(row("Legal Name", legal_name))
    phone = getattr(e, 'phone', None)
    if phone:
        cb_rows.append(row("Phone", phone))
    contact_email = getattr(e, 'contact_email', None)
    if contact_email:
        cb_rows.append(row("Contact Email", contact_email))
    if e.emails:
        cb_rows.append(row("Emails", ", ".join(e.emails)))
    if e.linkedin_url:
        cb_rows.append(
            f'<div class="detail-row"><span class="lbl">LinkedIn</span><span class="val"><a href="{_esc(e.linkedin_url)}" style="color:var(--teal)" target="_blank">Profile</a></span></div>'
        )
    diversity = getattr(e, 'diversity', None)
    if diversity:
        cb_rows.append(row("Diversity", diversity))
    it_spend = getattr(e, 'it_spend', None)
    if it_spend:
        cb_rows.append(row("IT Spend", it_spend))
    total_ip = getattr(e, 'total_ip', None)
    if total_ip:
        cb_rows.append(row("Trademarks / IP", total_ip))

    # Crunchbase categories as pills
    cb_categories = getattr(e, 'crunchbase_categories', None) or []
    categories_html = ""
    if cb_categories:
        pills = "".join(f'<span class="pill">{_esc(c)}</span>' for c in cb_categories)
        categories_html = f"""<div style="margin-top:12px">
  <div style="font-size:.78rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin-bottom:6px">Categories</div>
  <div class="pill-grid">{pills}</div>
</div>"""

    cb_url = getattr(e, 'crunchbase_url', None)
    cb_link_html = ""
    if cb_url:
        cb_link_html = f'<div style="margin-top:8px"><a href="{_esc(cb_url)}" target="_blank" style="color:var(--teal);font-size:.85rem;font-weight:600">View on Crunchbase &rarr;</a></div>'

    crunchbase_html = ""
    if cb_rows or categories_html or cb_link_html:
        crunchbase_html = f"""<div style="margin-bottom:24px">
  <h3>Crunchbase Data</h3>
  {"".join(cb_rows)}
  {categories_html}
  {cb_link_html}
</div>"""

    # ── Social Profiles ──
    social_html = ""
    if e.social_profiles:
        platform_styles = {
            "instagram": ("&#x1f4f7;", "#E4405F"),
            "facebook": ("&#x1f4d8;", "#1877F2"),
            "twitter": ("&#x1d54f;", "#1DA1F2"),
            "youtube": ("&#x25b6;&#xfe0f;", "#FF0000"),
            "tiktok": ("&#x266b;", "#000000"),
            "pinterest": ("&#x1f4cc;", "#E60023"),
            "snapchat": ("&#x1f47b;", "#FFFC00"),
            "linkedin": ("&#x1f4bc;", "#0A66C2"),
        }

        cards = []
        for sp in e.social_profiles:
            icon, color = platform_styles.get(sp.platform.lower(), ("&#x1f310;", "#6B7280"))
            followers = _fmt_number(sp.followers) if sp.followers else "—"
            posts = _fmt_number(sp.posts) if sp.posts else "—"
            likes = _fmt_number(sp.likes) if sp.likes else None
            desc = _esc(sp.description[:100]) + "..." if sp.description and len(sp.description) > 100 else _esc(sp.description or "")

            stats_parts = [f"<strong>{followers}</strong> followers"]
            if sp.posts:
                stats_parts.append(f"<strong>{posts}</strong> posts")
            if likes:
                stats_parts.append(f"<strong>{likes}</strong> likes")
            stats = " &middot; ".join(stats_parts)

            link_html = f'<a href="{_esc(sp.url)}" target="_blank" style="color:{color};text-decoration:none;font-weight:600">{_esc(sp.platform.title())}</a>' if sp.url else f'<span style="font-weight:600">{_esc(sp.platform.title())}</span>'
            desc_html = f'<div style="font-size:.78rem;color:var(--muted);margin-top:4px;line-height:1.4">{desc}</div>' if desc else ""

            cards.append(f"""<div style="padding:14px;background:white;border:1px solid var(--border);border-radius:10px;display:flex;gap:12px;align-items:flex-start">
  <span style="font-size:1.4rem;flex-shrink:0">{icon}</span>
  <div style="flex:1;min-width:0">
    <div style="display:flex;justify-content:space-between;align-items:center">
      <div>{link_html}</div>
    </div>
    <div style="font-size:.82rem;color:#475467;margin-top:4px">{stats}</div>
    {desc_html}
  </div>
</div>""")

        social_html = f"""<div style="margin-bottom:24px">
  <h3>Social Profiles</h3>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px">
    {"".join(cards)}
  </div>
</div>"""

    # ── Clay Enrichment ──
    clay_html = ""
    if clay and clay.enriched:
        clay_rows = []
        if clay.target_audience:
            clay_rows.append(row("Target Audience", clay.target_audience))
        if clay.revenue_model:
            clay_rows.append(row("Revenue Model", clay.revenue_model))
        if clay.headquarters:
            clay_rows.append(row("Headquarters", clay.headquarters))
        if clay.headcount_growth:
            clay_rows.append(row("Headcount Growth", clay.headcount_growth))

        # Founders (only if not already shown in Key People)
        if clay.founders and not clay_founders_shown:
            clay_rows.append(row("Founders", ", ".join(clay.founders)))

        # Competitors
        competitor_pills = ""
        if clay.competitors:
            pills = "".join(f'<span class="pill">{_esc(c)}</span>' for c in clay.competitors)
            competitor_pills = f"""<div style="margin-top:12px">
  <div style="font-size:.78rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin-bottom:6px">Competitors ({len(clay.competitors)})</div>
  <div class="pill-grid">{pills}</div>
</div>"""

        # Recent News
        news_html = ""
        if clay.recent_news:
            items = "".join(f"<li>{_esc(n)}</li>" for n in clay.recent_news[:5])
            news_html = f"""<div style="margin-top:12px">
  <div style="font-size:.78rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin-bottom:6px">Recent News</div>
  <ul style="font-size:.85rem;padding-left:18px;color:#304249">{items}</ul>
</div>"""

        if clay_rows or competitor_pills or news_html:
            clay_html = f"""<div style="margin-bottom:24px">
  <h3>Clay Enrichment</h3>
  {"".join(clay_rows)}
  {competitor_pills}
  {news_html}
</div>"""

    return f"""<section>
  <h2>Company Profile</h2>
  {hero_card}
  {key_people_html}
  {details_html}
  {fundraising_html}
  {crunchbase_html}
  {social_html}
  {clay_html}
</section>"""


def _build_enrichment_section(report: DomainAdReport) -> str:
    e = report.enrichment
    if not e:
        return '<section><h2>Company Details</h2><p>No enrichment data available.</p></section>'

    def row(label, val):
        return f'<div class="detail-row"><span class="lbl">{label}</span><span class="val">{_esc(val)}</span></div>'

    left_rows = [
        row("Industry", e.industry),
        row("E-Commerce Platform", f"{e.ecommerce_platform or '—'}{(' (' + e.ecommerce_plan + ')') if e.ecommerce_plan else ''}"),
        row("Monthly Revenue", _fmt_money(e.estimated_monthly_revenue)),
        row("Annual Revenue", _fmt_money(e.estimated_annual_revenue)),
        row("Employees", _fmt_number(e.employee_count)),
        row("Monthly Visits", _fmt_number(e.estimated_monthly_visits)),
        row("Monthly Pageviews", _fmt_number(e.estimated_monthly_pageviews)),
    ]

    right_rows = [
        row("Product Count", _fmt_number(e.product_count)),
        row("Avg Product Price", e.avg_product_price or "—"),
        row("Price Range", e.price_range or "—"),
        row("Platform Rank", _fmt_number(e.platform_rank)),
        row("Location", ", ".join(filter(None, [e.city, e.state, e.country])) or "—"),
        row("Store Created", (e.store_created_at or "—")[:10]),
    ]

    # Reviews
    if e.review_count:
        right_rows.append(
            row("Reviews", f"{e.review_rating} stars / {_fmt_number(e.review_count)} on {e.review_source or 'unknown'}")
        )

    # Contact
    contact_parts = []
    if e.phone:
        contact_parts.append(row("Phone", e.phone))
    if e.emails:
        contact_parts.append(row("Email", ", ".join(e.emails)))
    if e.linkedin_url:
        contact_parts.append(
            f'<div class="detail-row"><span class="lbl">LinkedIn</span><span class="val"><a href="{_esc(e.linkedin_url)}" style="color:var(--teal)" target="_blank">Profile</a></span></div>'
        )

    return f"""<section>
  <h2>Company Details</h2>
  <div class="two-col">
    <div>{"".join(left_rows)}</div>
    <div>{"".join(right_rows)}</div>
  </div>
  {"".join(contact_parts)}
</section>"""


def _md_inline(text: str) -> str:
    """Convert inline markdown **bold** and *italic* to HTML, with HTML escaping."""
    import re
    text = html_mod.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    return text


def _build_creative_pipeline_section(report: DomainAdReport) -> str:
    """Build full Creative Pipeline output section for internal report."""
    cp = report.creative_pipeline
    if not cp or not cp.found:
        return ""

    company = _esc(report.company_name or report.domain)

    # Status badge
    status_color = {"complete": "#027A48", "error": "#B42318", "timeout": "#B54708"}.get(cp.status, "#838383")
    status_label = cp.status.upper()

    # Brand brief — with markdown rendering
    brief_html = ""
    if cp.brand_brief:
        brief_lines = cp.brand_brief.replace("\r", "").split("\n")
        brief_content = ""
        for line in brief_lines:
            line = line.strip()
            if not line or line == "---" or line == "***":
                continue
            if line.startswith("#"):
                heading = _md_inline(line.lstrip("#").strip())
                brief_content += f'<h4 style="color:var(--teal);margin:14px 0 4px;font-size:.85rem">{heading}</h4>'
            elif line.startswith("- ") or line.startswith("* "):
                brief_content += f'<li style="font-size:.82rem;color:#444;margin-bottom:2px">{_md_inline(line[2:])}</li>'
            else:
                brief_content += f'<p style="font-size:.82rem;color:#444;margin-bottom:4px">{_md_inline(line)}</p>'
        brief_html = f"""<div style="background:white;border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:16px">
      <h3 style="margin-bottom:10px;font-size:.95rem">Brand Intelligence Brief</h3>
      <div style="max-height:400px;overflow-y:auto">{brief_content}</div>
    </div>"""

    # ── Script — parse into scenes and extract VO separately ──
    import re as _re
    script_html = ""
    vo_html = ""
    if cp.script:
        script_lines = cp.script.replace("\r", "").split("\n")

        # Parse into structured scenes
        scenes = []
        current_scene = None
        current_section = ""
        current_data = {"title": "", "duration": "", "visual": [], "vo": [], "copy": [], "notes": [], "other": []}

        for raw_line in script_lines:
            line = raw_line.strip()
            if not line or line == "---" or line == "***":
                continue

            # Detect scene headings
            is_scene = bool(
                _re.match(r'^(\*\*)?SCENE\s+\d', line, _re.IGNORECASE)
                or _re.match(r'^#{1,3}\s+.*scene', line, _re.IGNORECASE)
                or _re.match(r'^(\*\*)?Scene\s+\d', line)
            )

            if is_scene:
                if current_data["title"]:
                    scenes.append(dict(current_data))
                current_data = {"title": "", "duration": "", "visual": [], "vo": [], "copy": [], "notes": [], "other": []}
                current_data["title"] = line.lstrip("#* ").strip().rstrip("*")
                current_section = "other"
                continue

            upper = line.upper().replace("**", "")
            if upper.startswith("DURATION:") or upper.startswith("**DURATION:"):
                current_data["duration"] = line.split(":", 1)[1].strip().rstrip("*")
                continue
            elif upper.startswith("MEDIA/VISUAL") or upper.startswith("VISUAL"):
                current_section = "visual"; continue
            elif upper.startswith("VOICEOVER") or upper.startswith("VO:"):
                current_section = "vo"
                if ":" in line:
                    vo_text = line.split(":", 1)[1].strip().strip("*\"")
                    if vo_text:
                        current_data["vo"].append(vo_text)
                continue
            elif upper.startswith("ON-SCREEN COPY") or upper.startswith("COPY:"):
                current_section = "copy"; continue
            elif upper.startswith("DIRECTOR NOTES") or upper.startswith("NOTES:"):
                current_section = "notes"; continue

            if not current_data["title"]:
                continue

            clean = line.lstrip("*- ").strip().rstrip("*")
            if clean and not clean.startswith("(None"):
                if current_section == "visual":
                    current_data["visual"].append(clean)
                elif current_section == "vo":
                    current_data["vo"].append(clean.strip('"'))
                elif current_section == "copy":
                    current_data["copy"].append(clean)
                elif current_section == "notes":
                    current_data["notes"].append(clean)
                else:
                    current_data["other"].append(clean)

        if current_data["title"]:
            scenes.append(dict(current_data))

        # Build full script section — white text on dark background
        scene_cards = ""
        for i, scene in enumerate(scenes):
            title = _md_inline(scene["title"])
            dur = scene["duration"]
            dur_badge = f'<span style="background:var(--teal);color:white;padding:2px 8px;border-radius:999px;font-size:.65rem;font-weight:600;margin-left:8px">{_md_inline(dur)}</span>' if dur else ""

            parts = ""
            if scene["visual"]:
                parts += '<div style="margin-bottom:8px"><div style="font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--teal);margin-bottom:3px">Visual</div>'
                for v in scene["visual"]:
                    parts += f'<div style="font-size:.8rem;color:rgba(255,255,255,.9);margin-bottom:2px;line-height:1.5">{_md_inline(v)}</div>'
                parts += '</div>'
            if scene["vo"]:
                vo = " ".join(scene["vo"])
                parts += f'<div style="margin-bottom:8px;background:rgba(255,255,255,.08);border-left:3px solid var(--teal);padding:8px 12px;border-radius:0 6px 6px 0"><div style="font-size:.65rem;font-weight:700;color:var(--teal);margin-bottom:2px">VO</div><div style="font-size:.82rem;color:white;font-style:italic">"{_md_inline(vo)}"</div></div>'
            if scene["copy"]:
                parts += '<div style="margin-bottom:8px"><div style="font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--pink);margin-bottom:3px">On-Screen</div>'
                for c in scene["copy"]:
                    parts += f'<div style="font-size:.8rem;color:rgba(255,255,255,.85);margin-bottom:2px">{_md_inline(c)}</div>'
                parts += '</div>'

            scene_cards += f'<div style="background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:10px;padding:14px;margin-bottom:10px"><div style="font-weight:700;color:var(--pink);font-size:.88rem;margin-bottom:8px">{title}{dur_badge}</div>{parts}</div>'

        script_html = f"""<div style="background:var(--navy);border-radius:12px;padding:20px;margin-bottom:16px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
        <span style="font-size:1rem;color:white">&#x1f3ac;</span>
        <h3 style="margin:0;color:white;font-size:.95rem">Production Script (30s CTV)</h3>
      </div>
      <div style="max-height:600px;overflow-y:auto">
        {scene_cards}
      </div>
    </div>"""

        # Build separate VO script section
        vo_lines = []
        for i, scene in enumerate(scenes):
            if scene["vo"]:
                vo_text = " ".join(scene["vo"])
                vo_lines.append(f'<div style="display:flex;gap:12px;padding:12px 0;border-bottom:1px solid var(--border)"><div style="flex-shrink:0;width:28px;height:28px;border-radius:50%;background:var(--teal);color:white;display:flex;align-items:center;justify-content:center;font-size:.72rem;font-weight:700">{i+1}</div><div><div style="font-size:.72rem;font-weight:600;color:var(--teal);margin-bottom:2px">{_md_inline(scene["title"])}</div><div style="font-size:.88rem;color:var(--navy);font-style:italic;line-height:1.6">"{_md_inline(vo_text)}"</div></div></div>')
        if vo_lines:
            vo_html = f"""<div style="background:white;border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:16px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
        <span style="font-size:1rem">&#x1f399;</span>
        <h3 style="margin:0;font-size:.95rem">Voiceover Script</h3>
        <span style="margin-left:auto;font-size:.72rem;background:var(--teal-light);color:var(--teal);padding:3px 10px;border-radius:999px;font-weight:600">Read-through</span>
      </div>
      {"".join(vo_lines)}
    </div>"""

    # Images grid
    images_html = ""
    if cp.image_urls:
        img_cards = ""
        for i, url in enumerate(cp.image_urls):
            img_cards += f'<div style="border-radius:8px;overflow:hidden;border:1px solid var(--border)"><img src="{_esc(url)}" alt="Scene {i+1}" style="width:100%;aspect-ratio:16/9;object-fit:cover;display:block"><div style="padding:6px 8px;font-size:.72rem;color:var(--muted);background:white">Scene {i+1}</div></div>'
        cols = min(len(cp.image_urls), 3)
        images_html = f"""<div style="margin-bottom:16px">
      <h3 style="margin-bottom:10px;font-size:.95rem">AI-Generated Scene Stills ({len(cp.image_urls)} images)</h3>
      <div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:10px">{img_cards}</div>
    </div>"""

    # Videos
    videos_html = ""
    if cp.video_urls:
        video_cards = ""
        for provider, urls in cp.video_urls.items():
            provider_label = _esc(provider.replace("_", " ").title())
            for j, url in enumerate(urls):
                video_cards += f"""<div style="background:white;border:1px solid var(--border);border-radius:8px;padding:12px">
          <div style="font-size:.78rem;font-weight:600;color:var(--navy);margin-bottom:6px">{provider_label} — Clip {j+1}</div>
          <video controls style="width:100%;border-radius:6px;aspect-ratio:16/9;background:#000">
            <source src="{_esc(url)}" type="video/mp4">
          </video>
        </div>"""
        videos_html = f"""<div style="margin-bottom:16px">
      <h3 style="margin-bottom:10px;font-size:.95rem">AI-Generated Video Clips</h3>
      <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px">{video_cards}</div>
    </div>"""

    # Documents
    docs_html = ""
    doc_links = []
    if cp.docx_url:
        doc_links.append(f'<a href="{_esc(cp.docx_url)}" target="_blank" style="color:var(--teal);text-decoration:none;font-size:.82rem">&#x1f4c4; Creative Prompts (DOCX)</a>')
    if cp.zip_url:
        doc_links.append(f'<a href="{_esc(cp.zip_url)}" target="_blank" style="color:var(--teal);text-decoration:none;font-size:.82rem">&#x1f4e6; Full Creative Package (ZIP)</a>')
    if doc_links:
        docs_html = f'<div style="display:flex;gap:20px;margin-top:12px">{"".join(doc_links)}</div>'

    # ── Audio Demos ──
    audio_html = ""
    audio_files = getattr(report, 'audio_files', None) or []
    if audio_files:
        voice_colors = ["#B72BB3", "#2563EB", "#0EA5E9", "#059669", "#D97706"]
        audio_cards = []
        for i, af in enumerate(audio_files):
            voice = af.get("voice", "Voice")
            voice_short = voice.split(" - ")[0].strip() if " - " in voice else voice.split(",")[0].strip()
            voice_desc = voice.split(" - ")[1].strip() if " - " in voice else ""
            script_title = af.get("script", "Script")
            url = af.get("url", "")
            voice_id = af.get("voice_id", "")
            color = voice_colors[i % len(voice_colors)]

            desc_html = f'<div style="font-size:.72rem;color:var(--muted)">{_esc(voice_desc)}</div>' if voice_desc else ""

            audio_cards.append(f"""<div style="background:white;border:1px solid var(--border);border-radius:10px;padding:14px">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
    <div style="width:32px;height:32px;background:{color};border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:.85rem">{voice_short[0]}</div>
    <div>
      <div style="font-weight:600;font-size:.85rem">{_esc(voice_short)}</div>
      {desc_html}
    </div>
  </div>
  <div style="font-size:.72rem;color:var(--muted);margin-bottom:6px">{_esc(script_title)} &middot; Voice ID: <code style="font-size:.7rem">{_esc(voice_id)}</code></div>
  <audio controls preload="none" style="width:100%;height:36px"><source src="{_esc(url)}" type="audio/mpeg"></audio>
</div>""")

        audio_html = f"""<div style="margin-bottom:16px">
  <h3 style="font-size:.95rem;margin-bottom:10px">&#x1f3a7; AI-Generated Voiceover ({len(audio_files)} voices)</h3>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px">
    {"".join(audio_cards)}
  </div>
  <p style="font-size:.72rem;color:var(--muted);margin-top:8px">Powered by ElevenLabs &middot; URLs valid for 7 days</p>
</div>"""

    # Meta bar
    meta_parts = [f'Job: <code>{_esc(cp.job_id)}</code>']
    if cp.elapsed_seconds:
        meta_parts.append(f'Generated in {cp.elapsed_seconds:.0f}s')
    meta_html = " | ".join(meta_parts)

    return f"""<div class="section-wrap" data-section="Creative Pipeline" data-filename="creative-pipeline">
    <button class="dl-btn" onclick="dlSection(this)">&darr; Download</button>
    <section>
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
        <h2 style="margin:0">&#x2728; Creative Pipeline — {company}</h2>
        <span style="background:{status_color};color:white;padding:2px 10px;border-radius:999px;font-size:.72rem;font-weight:600">{status_label}</span>
      </div>
      <p style="font-size:.85rem;color:var(--muted);margin-bottom:20px">AI-generated brand brief, production script, and scene stills from the Upscale Creative Pipeline. {meta_html}</p>
      {brief_html}
      {vo_html}
      {script_html}
      {audio_html}
      {images_html}
      {videos_html}
      {docs_html}
    </section>
  </div>"""


def _build_ads_section(report: DomainAdReport) -> str:
    platforms = [
        ("iSpot (Linear TV / CTV)", report.ispot_ads),
        ("YouTube (Google Ads Transparency)", report.youtube_ads),
        ("Meta (Facebook / Instagram)", report.meta_ads),
    ]

    _COLLAPSE_ADS = 5
    blocks = []
    for name, pr in platforms:
        count = len(pr.ads)
        status = "Found" if pr.found else "Not Found"
        duration = f" &middot; {pr.scrape_duration_seconds}s" if pr.scrape_duration_seconds else ""

        ad_items = []
        for ad in pr.ads[:30]:
            title = _esc(ad.title or "Untitled")
            url = _esc(ad.ad_page_url or "#")
            date_info = f" &middot; {_esc(ad.start_date)}" if ad.start_date else ""
            ad_items.append(f'<li><a href="{url}" target="_blank">{title}</a>{date_info}</li>')

        overflow = ""
        if count > 30:
            overflow = f'<li style="color:var(--muted)">... and {count - 30} more</li>'

        # Collapse after 5
        if len(ad_items) > _COLLAPSE_ADS:
            visible = "".join(ad_items[:_COLLAPSE_ADS])
            hidden = "".join(ad_items[_COLLAPSE_ADS:]) + overflow
            ad_list_html = f"""<ul class="ad-list">{visible}</ul>
  <details style="margin-top:4px"><summary style="cursor:pointer;font-size:.82rem;color:var(--teal)">View all {count} ads</summary>
  <ul class="ad-list" style="margin-top:4px">{hidden}</ul></details>"""
        else:
            ad_list_html = f'<ul class="ad-list">{"".join(ad_items)}{overflow}</ul>'

        blocks.append(f"""<div class="platform-block">
  <h3>{name} <span class="count-badge">{count} ads &middot; {status}{duration}</span></h3>
  {ad_list_html}
</div>""")

    mix = report.channel_mix
    summary = f"""<p style="font-size:.88rem;color:var(--muted);margin-bottom:16px">
  Channel Mix: {mix.total_platforms} platform(s) &middot; {mix.total_ads_found} total ads &middot;
  Linear: {"Yes" if mix.has_linear else "No"} &middot;
  YouTube: {"Yes" if mix.has_youtube else "No"} &middot;
  Meta: {"Yes" if mix.has_meta else "No"}
</p>"""

    return f"""<section>
  <h2>Ad Discovery</h2>
  {summary}
  {"".join(blocks)}
</section>"""


def _assess_promotional_intensity(report: DomainAdReport) -> tuple[str, str, list[str]]:
    """Assess how promotional a brand is based on email subjects and wayback data."""
    score = 0
    reasons: list[str] = []

    # Check email subjects for promotional keywords
    promo_keywords = {'sale', 'off', 'free', 'limited', 'bogo', 'clearance',
                      'flash', 'exclusive', 'save', 'deal', 'discount', 'promo',
                      'hurry', 'last chance', 'ends soon', 'today only', 'code',
                      'coupon', 'gift with purchase', 'buy one', 'reward'}

    milled = report.milled_intel
    if milled and milled.emails:
        promo_count = 0
        for em in milled.emails:
            subj_lower = (em.subject or '').lower()
            if any(kw in subj_lower for kw in promo_keywords):
                promo_count += 1

        if len(milled.emails) > 0:
            promo_ratio = promo_count / len(milled.emails)
            if promo_ratio > 0.6:
                score += 3
                reasons.append(f"{promo_count}/{len(milled.emails)} emails contain promotional language")
            elif promo_ratio > 0.3:
                score += 2
                reasons.append(f"{promo_count}/{len(milled.emails)} emails contain promotional language")
            elif promo_count > 0:
                score += 1
                reasons.append(f"{promo_count} promotional emails detected")

    # Check Wayback data
    wb = report.wayback_intel
    if wb and wb.found:
        intensity = wb.promotional_intensity
        if intensity == 'high':
            score += 3
            reasons.append(f"High site changes around {wb.active_events} events")
        elif intensity == 'mid':
            score += 2
            reasons.append(f"Mid site changes around {wb.active_events} events")

    if milled and milled.has_bfcm:
        score += 1
        reasons.append("BFCM promotional activity confirmed")

    if score >= 5:
        return "Highly Promotional", "var(--danger)", reasons
    elif score >= 3:
        return "Moderately Promotional", "var(--warning)", reasons
    elif score >= 1:
        return "Light Promotional", "var(--teal)", reasons
    else:
        return "Minimal Promotional Activity", "var(--muted)", reasons


def _build_key_events_section(report: DomainAdReport) -> str:
    """Combined Key Events + Calendar section merging ecommerce calendar, Wayback, and Milled data."""
    # ── 12-month calendar grid starting from next month ──
    today = date.today()
    if today.month == 12:
        start_year, start_month = today.year + 1, 1
    else:
        start_year, start_month = today.year, today.month + 1

    # Build a lookup of Wayback active event names for overlay indicators
    wb = report.wayback_intel
    wb_event_names: dict[str, object] = {}
    if wb and wb.found:
        for ev in wb.events:
            if ev.activity_score > 0:
                wb_event_names[ev.event_name.lower().strip()] = ev

    # Collect 12 months of events
    category_colors = {
        "holiday": "var(--pink)",
        "sale": "#DC2626",
        "seasonal": "var(--teal)",
        "cultural": "#7C3AED",
    }

    months_data = []
    for i in range(12):
        m = start_month + i
        y = start_year
        if m > 12:
            m -= 12
            y += 1
        year_events = get_events_for_year(y)
        month_events = [(ev, d) for ev, d in year_events if d.month == m]
        months_data.append((y, m, month_events))

    # Build month cards
    month_cards = []
    for y, m, events in months_data:
        month_name = cal_mod.month_name[m]
        events_html = ""
        if not events:
            events_html = '<p style="color:var(--muted);font-size:.8rem;font-style:italic;margin:4px 0;">No key events</p>'
        else:
            for ev, d in events:
                badge_color = category_colors.get(ev.category, "var(--muted)")
                stars = '<span style="color:#F59E0B;">' + "&#9733;" * ev.importance + "&#9734;" * (5 - ev.importance) + "</span>"
                # Check Wayback overlay
                wb_indicator = ""
                wb_match = wb_event_names.get(ev.name.lower().strip())
                if wb_match:
                    wb_indicator = ' <span title="Site changed around this event" style="font-size:.75rem;">&#x1F504; Site changed</span>'
                events_html += f"""<div style="display:flex;align-items:center;gap:6px;padding:4px 0;border-bottom:1px solid var(--bg-grey);flex-wrap:wrap;">
  <span style="background:{badge_color};color:white;padding:1px 6px;border-radius:4px;font-size:.65rem;text-transform:uppercase;letter-spacing:.03em;white-space:nowrap;">{_esc(ev.category)}</span>
  <span style="font-size:.82rem;font-weight:600;">{_esc(ev.name)}</span>
  <span style="font-size:.75rem;color:var(--muted);white-space:nowrap;">{d.strftime('%b %d')}</span>
  <span style="font-size:.7rem;">{stars}</span>{wb_indicator}
</div>"""

        month_cards.append(f"""<div style="border:1px solid var(--border);border-radius:8px;padding:12px;background:var(--white);min-width:0;">
  <div style="font-weight:700;font-size:.9rem;margin-bottom:8px;color:var(--navy);border-bottom:2px solid var(--pink);padding-bottom:4px;">{month_name} {y}</div>
  {events_html}
</div>""")

    calendar_grid = f"""<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:24px;">
  {"".join(month_cards)}
</div>"""

    # ── Wayback Activity Table ──
    wayback_html = ""
    if wb and wb.found:
        intensity_colors = {
            "high": "var(--danger)",
            "mid": "var(--warning)",
            "low": "var(--muted)",
        }
        badge_color = intensity_colors.get(wb.promotional_intensity, "var(--muted)")

        active_events = [e for e in wb.events if e.activity_score > 0]
        active_events.sort(key=lambda x: x.activity_score, reverse=True)

        rows = ""
        for ev in active_events:
            dots = "&#9679;" * ev.activity_score + "&#9675;" * (5 - ev.activity_score)
            score_color = (
                "var(--danger)" if ev.activity_score >= 4
                else "var(--warning)" if ev.activity_score >= 3
                else "var(--teal)" if ev.activity_score >= 2
                else "var(--muted)"
            )
            cat_badge = _esc(ev.category)
            archive_link = ""
            if ev.archive_url:
                archive_link = f' <a href="{_esc(ev.archive_url)}" target="_blank" style="color:var(--teal);font-size:.75rem;">view snapshot &rarr;</a>'

            rows += f"""<tr>
  <td style="font-weight:600;">{_esc(ev.event_name)}</td>
  <td><span style="background:var(--bg-grey);padding:2px 8px;border-radius:4px;font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;">{cat_badge}</span></td>
  <td>{_esc(ev.event_date)}</td>
  <td style="color:{score_color};letter-spacing:2px;font-size:.9rem;">{dots}</td>
  <td>{ev.unique_versions} versions</td>
  <td>{ev.snapshots_count} snaps{archive_link}</td>
</tr>"""

        years_str = ", ".join(str(y) for y in wb.years_analyzed)

        wayback_html = f"""<div style="margin-top:24px;">
  <h3 style="font-size:1rem;margin-bottom:12px;">Wayback Machine Site Activity</h3>
  <div style="display:flex;gap:16px;align-items:center;margin-bottom:12px;">
    <div style="background:{badge_color};color:white;padding:4px 14px;border-radius:8px;font-size:.8rem;font-weight:700;text-transform:uppercase;">{_esc(wb.promotional_intensity)} Intensity</div>
    <span style="font-size:.85rem;color:var(--muted);">{wb.active_events}/{wb.total_events_checked} events with site changes &middot; {wb.total_snapshots_checked} snapshots analyzed &middot; Years: {years_str}</span>
  </div>
  <p style="font-size:.85rem;color:#475467;margin-bottom:12px;">Homepage changes around key eCommerce events indicate promotional activity (banners, sales messaging, seasonal creative).</p>
  <table style="width:100%;border-collapse:collapse;">
    <thead>
      <tr style="border-bottom:2px solid var(--border);text-align:left;">
        <th style="padding:8px 8px 8px 0;font-size:.75rem;color:var(--muted);text-transform:uppercase;">Event</th>
        <th style="padding:8px;font-size:.75rem;color:var(--muted);text-transform:uppercase;">Type</th>
        <th style="padding:8px;font-size:.75rem;color:var(--muted);text-transform:uppercase;">Date</th>
        <th style="padding:8px;font-size:.75rem;color:var(--muted);text-transform:uppercase;">Activity</th>
        <th style="padding:8px;font-size:.75rem;color:var(--muted);text-transform:uppercase;">Changes</th>
        <th style="padding:8px;font-size:.75rem;color:var(--muted);text-transform:uppercase;">Snapshots</th>
      </tr>
    </thead>
    <tbody>
      {rows if rows else '<tr><td colspan="6" style="padding:12px;color:var(--muted);font-style:italic;">No promotional activity detected in checked periods.</td></tr>'}
    </tbody>
  </table>
</div>"""

    # ── Milled Email History ──
    milled_html = ""
    milled = report.milled_intel
    if milled and milled.found:
        # Group emails by month
        months: dict[str, list] = {}
        for em in milled.emails:
            if em.date and len(em.date) >= 7:
                month_key = em.date[:7]
            else:
                month_key = "Unknown"
            months.setdefault(month_key, []).append(em)

        month_blocks = []
        for month_key in sorted(months.keys(), reverse=True):
            emails = months[month_key]
            try:
                label = datetime.strptime(month_key, "%Y-%m").strftime("%B %Y")
            except ValueError:
                label = month_key

            email_rows = []
            for em in emails:
                date_display = em.date[5:] if em.date and len(em.date) >= 10 else em.date
                url_html = f'<a href="{_esc(em.url)}" target="_blank">{_esc(em.subject)}</a>' if em.url else _esc(em.subject)
                email_rows.append(f"""<div class="email-row">
  <span class="email-date">{_esc(date_display)}</span>
  <span class="email-subject">{url_html}</span>
</div>""")

            month_blocks.append(f"""<div class="month-group">
  <h4>{label} ({len(emails)} emails)</h4>
  {"".join(email_rows)}
</div>""")

        promo_label, promo_color, promo_reasons = _assess_promotional_intensity(report)
        promo_badge = f"""<div style="display:flex;gap:16px;align-items:center;margin-bottom:16px;">
    <div style="background:{promo_color};color:white;padding:4px 14px;border-radius:8px;font-size:.8rem;font-weight:700;text-transform:uppercase;">{promo_label}</div>
    <span style="font-size:.85rem;color:var(--muted);">{' &middot; '.join(promo_reasons) if promo_reasons else 'No promotional signals detected'}</span>
</div>"""
        milled_link = f"""<p style="font-size:.85rem;color:var(--muted);margin-bottom:8px;">
  {_fmt_number(milled.total_emails)} total emails archived &middot;
  <a href="{_esc(milled.milled_url or '#')}" target="_blank" style="color:var(--teal)">View on Milled</a>
</p>"""

        milled_html = f"""<div style="margin-top:24px;">
  <h3 style="font-size:1rem;margin-bottom:12px;">Email Newsletter History (Milled)</h3>
  {promo_badge}
  {milled_link}
  <details style="margin-top:8px;">
    <summary style="cursor:pointer;font-size:.85rem;font-weight:600;color:var(--teal);">Show monthly email listing</summary>
    <div style="margin-top:8px;">
      {"".join(month_blocks)}
    </div>
  </details>
</div>"""

    return f"""<section>
  <h2>Key Events + Calendar</h2>
  <p style="font-size:.85rem;color:#475467;margin-bottom:16px;">12-month forward calendar of key eCommerce events starting {cal_mod.month_name[start_month]} {start_year}, with historical site-change and email activity overlaid.</p>
  {calendar_grid}
  {wayback_html}
  {milled_html}
</section>"""


def _build_tech_section(report: DomainAdReport) -> str:
    e = report.enrichment
    if not e:
        return ""

    competitor_keys = {k.lower() for k in CTV_COMPETITOR_TAGS}

    # Group technologies by category
    tech_full = e.technologies_full if hasattr(e, "technologies_full") else None
    grouped = group_technologies(e.technologies or [], tech_full)

    category_blocks = []
    for cat, techs in grouped.items():
        bg = CATEGORY_COLORS.get(cat, "#F3F4F6")
        pills = []
        for t in techs:
            if t.lower() in competitor_keys:
                pills.append(
                    f'<span class="pill" style="background:#FEF3F2;border:2px solid #FDA29B;'
                    f'color:#B42318;font-weight:700">\u26a0 COMPETITOR &mdash; {_esc(t)}</span>'
                )
            else:
                pills.append(f'<span class="pill" style="background:{bg}">{_esc(t)}</span>')
        category_blocks.append(f"""<div style="margin-bottom:12px">
  <h4 style="font-size:.78rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin-bottom:6px">{_esc(cat)} ({len(techs)})</h4>
  <div class="pill-grid">{"".join(pills)}</div>
</div>""")

    feature_pills = "".join(f'<span class="pill">{_esc(f)}</span>' for f in (e.features or []))

    return f"""<section>
  <h2>Tech Stack & Features</h2>
  <p style="font-size:.85rem;color:var(--muted);margin-bottom:16px">{len(e.technologies or [])} technologies detected, grouped by category</p>
  {"".join(category_blocks) or '<p style="color:var(--muted)">None detected</p>'}
  <h3 style="font-size:.88rem;color:var(--muted);margin:16px 0 8px">Features ({len(e.features or [])})</h3>
  <div class="pill-grid">{feature_pills or '<span style="color:var(--muted)">None detected</span>'}</div>
</section>"""


def _build_social_section(report: DomainAdReport) -> str:
    e = report.enrichment
    if not e or not e.social_profiles:
        return ""

    # Platform icons (emoji + color)
    platform_styles = {
        "instagram": ("&#x1f4f7;", "#E4405F"),
        "facebook": ("&#x1f4d8;", "#1877F2"),
        "twitter": ("&#x1d54f;", "#1DA1F2"),
        "youtube": ("&#x25b6;&#xfe0f;", "#FF0000"),
        "tiktok": ("&#x266b;", "#000000"),
        "pinterest": ("&#x1f4cc;", "#E60023"),
        "snapchat": ("&#x1f47b;", "#FFFC00"),
        "linkedin": ("&#x1f4bc;", "#0A66C2"),
    }

    cards = []
    for sp in e.social_profiles:
        icon, color = platform_styles.get(sp.platform.lower(), ("&#x1f310;", "#6B7280"))
        followers = _fmt_number(sp.followers) if sp.followers else "—"
        posts = _fmt_number(sp.posts) if sp.posts else "—"
        likes = _fmt_number(sp.likes) if sp.likes else None
        desc = _esc(sp.description[:100]) + "..." if sp.description and len(sp.description) > 100 else _esc(sp.description or "")

        stats_parts = [f"<strong>{followers}</strong> followers"]
        if sp.posts:
            stats_parts.append(f"<strong>{posts}</strong> posts")
        if likes:
            stats_parts.append(f"<strong>{likes}</strong> likes")
        stats = " &middot; ".join(stats_parts)

        link_html = f'<a href="{_esc(sp.url)}" target="_blank" style="color:{color};text-decoration:none;font-weight:600">{_esc(sp.platform.title())}</a>' if sp.url else f'<span style="font-weight:600">{_esc(sp.platform.title())}</span>'
        desc_html = f'<div style="font-size:.78rem;color:var(--muted);margin-top:4px;line-height:1.4">{desc}</div>' if desc else ""

        cards.append(f"""<div style="padding:14px;background:white;border:1px solid var(--border);border-radius:10px;display:flex;gap:12px;align-items:flex-start">
  <span style="font-size:1.4rem;flex-shrink:0">{icon}</span>
  <div style="flex:1;min-width:0">
    <div style="display:flex;justify-content:space-between;align-items:center">
      <div>{link_html}</div>
    </div>
    <div style="font-size:.82rem;color:#475467;margin-top:4px">{stats}</div>
    {desc_html}
  </div>
</div>""")

    return f"""<section>
  <h2>Social Profiles</h2>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px">
    {"".join(cards)}
  </div>
</section>"""


def _build_gaps_section(report: DomainAdReport, fit: UpscaleFitResult) -> str:
    mix = report.channel_mix
    e = report.enrichment
    gaps = []

    # Channel gaps
    if not mix.has_linear:
        gaps.append(('opportunity', 'No CTV / Linear TV Presence',
                      'Brand has no detected linear TV or CTV ads. This is the primary Upscale opportunity — pitch connected TV as a measurable awareness channel with attribution.'))
    if not mix.has_youtube:
        gaps.append(('opportunity', 'No YouTube Advertising',
                      'No YouTube ads detected. Position YouTube as a mid-funnel video channel to drive consideration and complement CTV awareness.'))
    if mix.has_linear and not mix.has_youtube:
        gaps.append(('opportunity', 'Linear TV Without YouTube',
                      'Brand invests in TV but not YouTube. Pitch YouTube as the performance complement — retarget TV-exposed audiences with measurable video ads.'))

    # Revenue gap
    if e and e.estimated_monthly_revenue and e.estimated_monthly_revenue < 500_000:
        gaps.append(('gap', 'Revenue Below $500K/mo',
                      'Current DTC revenue may limit streaming ad budget. Recommend YouTube-only pilot at lower spend before full CTV deployment.'))

    # Tech maturity gap
    for cat in fit.categories:
        if cat.name == "Digital Maturity" and cat.score < 40:
            gaps.append(('gap', 'Low Digital Maturity',
                          'Limited analytics/attribution stack detected. CTV measurement requires proper tracking infrastructure. Recommend setting up pixel + attribution before campaign launch.'))

    # Review risk
    if e and e.review_rating and e.review_rating < 2.5:
        gaps.append(('gap', 'Poor Review Rating',
                      f'{e.review_rating} stars on {e.review_source}. Negative brand sentiment may reduce CTV ad effectiveness. Consider reputation management before scaling awareness.'))

    # Milled gap
    milled = report.milled_intel
    if not milled or not milled.found:
        gaps.append(('gap', 'No Email Newsletter History',
                      'Brand not found on Milled.com. No promotional calendar data available for seasonal flight planning.'))

    if not gaps:
        return ""

    cards = []
    for gtype, title, desc in gaps:
        cls = "opportunity" if gtype == "opportunity" else ""
        cards.append(f"""<div class="gap-card {cls}">
  <h4>{"Opportunity" if gtype == "opportunity" else "Gap"}: {_esc(title)}</h4>
  <p>{_esc(desc)}</p>
</div>""")

    return f"""<section>
  <h2>Gaps & Opportunities Analysis</h2>
  {"".join(cards)}
</section>"""


# ---------------------------------------------------------------------------
# New section builders
# ---------------------------------------------------------------------------


def _build_clay_section(report: DomainAdReport) -> str:
    """Clay MCP Enrichment section."""
    clay = report.clay
    if not clay.enriched:
        return """<section>
  <h2>Clay MCP Enrichment</h2>
  <p style="color:var(--muted)">Clay enrichment not run — no additional company data available.</p>
</section>"""

    def row(label, val):
        return f'<div class="detail-row"><span class="lbl">{label}</span><span class="val">{_esc(val)}</span></div>'

    left_rows = [
        row("Headquarters", clay.headquarters),
        row("Revenue Model", clay.revenue_model),
        row("Target Audience", clay.target_audience),
        row("Headcount Growth", clay.headcount_growth),
        row("Latest Funding", clay.latest_funding),
    ]

    founders_val = ", ".join(clay.founders) if clay.founders else "—"
    investors_val = ", ".join(clay.investors) if clay.investors else "—"
    right_rows = [
        row("Founders", founders_val),
        row("Investors", investors_val),
    ]

    competitor_pills = ""
    if clay.competitors:
        pills = "".join(f'<span class="pill">{_esc(c)}</span>' for c in clay.competitors)
        competitor_pills = f"""<div style="margin-top:16px">
  <h3 style="font-size:.88rem;color:var(--muted);margin-bottom:8px">Competitors ({len(clay.competitors)})</h3>
  <div class="pill-grid">{pills}</div>
</div>"""

    news_html = ""
    if clay.recent_news:
        items = "".join(f"<li>{_esc(n)}</li>" for n in clay.recent_news[:5])
        news_html = f"""<div style="margin-top:16px">
  <h3 style="font-size:.88rem;color:var(--muted);margin-bottom:8px">Recent News</h3>
  <ul style="font-size:.85rem;padding-left:18px;color:#304249">{items}</ul>
</div>"""

    return f"""<section>
  <h2>Clay MCP Enrichment</h2>
  <div class="two-col">
    <div>{"".join(left_rows)}</div>
    <div>{"".join(right_rows)}</div>
  </div>
  {competitor_pills}
  {news_html}
</section>"""


def _build_crm_section(report: DomainAdReport) -> str:
    """CRM Intelligence (Company Pulse) section."""
    pulse = report.company_pulse
    if not pulse.found:
        return """<section>
  <h2>CRM Intelligence</h2>
  <p style="color:var(--muted)">No Company Pulse data available for this domain.</p>
</section>"""

    # Health badge
    health_colors = {
        "healthy": "var(--success)",
        "at_risk": "var(--warning)",
        "critical": "var(--danger)",
    }
    hc = health_colors.get(pulse.health_status, "var(--muted)")
    health_badge = f'<span class="health-badge" style="background:{hc}">{pulse.health_score or "—"} &middot; {_esc(pulse.health_status or "Unknown")}</span>'

    # Status & details
    def row(label, val):
        return f'<div class="detail-row"><span class="lbl">{label}</span><span class="val">{_esc(val)}</span></div>'

    detail_rows = [
        row("Current Status", pulse.current_status),
        row("CRM Tier", pulse.crm_tier),
        row("Owner", pulse.owner_email),
        row("Days Since First Contact", pulse.days_since_first_contact),
        row("Next Steps", pulse.next_steps),
    ]

    # Status summary bullets
    status_html = ""
    if pulse.status_summary:
        items = "".join(f"<li>{_esc(s)}</li>" for s in pulse.status_summary)
        status_html = f"""<div style="margin-top:12px">
  <h3 style="font-size:.88rem;color:var(--muted);margin-bottom:8px">Status Summary</h3>
  <ul style="font-size:.85rem">{items}</ul>
</div>"""

    # Outreach summary (rendered as styled bar in CRM contacts section below)
    outreach_html = ""

    # Health signals
    signals_html = ""
    if pulse.health_signals:
        items = []
        for sig in pulse.health_signals:
            sig_type = sig.get("type", "")
            sig_label = sig.get("label", sig.get("text", sig.get("signal", str(sig))))
            sig_impact = sig.get("impact", "")
            impact_str = f" ({sig_impact:+d})" if isinstance(sig_impact, (int, float)) else ""
            cls = "signal-positive" if sig_type == "positive" else "signal-negative"
            icon = "+" if sig_type == "positive" else "-"
            items.append(f'<div class="{cls}">{icon} {_esc(sig_label)}{impact_str}</div>')
        signals_html = f"""<div style="margin-top:12px">
  <h3 style="font-size:.88rem;color:var(--muted);margin-bottom:8px">Health Signals</h3>
  {"".join(items)}
</div>"""

    # Deals table
    deals_html = ""
    if pulse.opportunities:
        deal_rows = []
        for d in pulse.opportunities:
            links = []
            links.append('<a href="https://app.hubspot.com" target="_blank" title="HubSpot" style="color:#FF7A59;text-decoration:none;font-size:.78rem;font-weight:600">HS</a>')
            links.append('<a href="https://app.day.ai" target="_blank" title="Day.ai" style="color:#4F46E5;text-decoration:none;font-size:.78rem;font-weight:600">Day</a>')
            links_cell = " &middot; ".join(links)
            deal_rows.append(f"""<tr>
  <td>{_esc(d.title)}</td>
  <td>{_esc(d.stage)}</td>
  <td>{_fmt_money(d.deal_size)}</td>
  <td>{f"{d.probability:.0%}" if d.probability is not None else "—"}</td>
  <td>{_esc(d.close_date)}</td>
  <td>{links_cell}</td>
</tr>""")
        deals_html = f"""<div style="margin-top:16px">
  <h3 style="font-size:.88rem;color:var(--muted);margin-bottom:4px">Deals ({len(pulse.opportunities)})</h3>
  <table class="data-table">
    <thead><tr><th>Title</th><th>Stage</th><th>Size</th><th>Prob</th><th>Close Date</th><th>Links</th></tr></thead>
    <tbody>{"".join(deal_rows)}</tbody>
  </table>
</div>"""

    # Meetings
    meetings_html = ""
    if pulse.meetings:
        mcards = []
        for m in pulse.meetings:
            kp = "".join(f"<li>{_esc(p)}</li>" for p in (m.key_points or [])[:2])
            ai = "".join(f"<li>{_esc(a)}</li>" for a in (m.action_items or []))
            kp_html = f"<ul>{kp}</ul>" if kp else ""
            ai_html = f'<p style="font-size:.75rem;color:var(--muted);margin-top:4px">Action items:</p><ul>{ai}</ul>' if ai else ""
            mcards.append(f"""<div class="meeting-card">
  <h4>{_esc(m.title)}</h4>
  <div class="meta">{_esc(m.date)}</div>
  {kp_html}
  {ai_html}
</div>""")
        meetings_html = f"""<div style="margin-top:16px">
  <h3 style="font-size:.88rem;color:var(--muted);margin-bottom:8px">Meetings ({len(pulse.meetings)})</h3>
  {"".join(mcards)}
</div>"""

    return f"""<section>
  <h2>CRM Intelligence</h2>
  <div style="margin-bottom:16px">{health_badge}</div>
  <div class="two-col">
    <div>{"".join(detail_rows)}</div>
    <div>{outreach_html}</div>
  </div>
  {status_html}
  {signals_html}
  {deals_html}
  {meetings_html}
</section>"""


def _build_contacts_section(report: DomainAdReport) -> str:
    """Key Contacts section — discovered + CRM contacts."""
    ci = report.contact_intel
    pulse = report.company_pulse

    has_discovered = ci.found and ci.contacts
    has_crm = pulse.found and pulse.contacts

    if not has_discovered and not has_crm:
        return """<section>
  <h2>Key Contacts</h2>
  <p style="color:var(--muted)">No contacts discovered for this brand.</p>
</section>"""

    # Build set of emails that are in Instantly outreach (from CRM contacts)
    instantly_emails: set[str] = set()
    if has_crm:
        for c in pulse.contacts:
            for o in (c.outreach or []):
                if o.provider and o.provider.lower() == "instantly" and c.email:
                    instantly_emails.add(c.email.lower())

    # Discovered contacts table
    discovered_html = ""
    if has_discovered:
        _COLLAPSE_LIMIT = 5
        rows = []
        for c in ci.contacts:
            name = f"{c.first_name or ''} {c.last_name or ''}".strip() or "—"
            # Add Instantly badge if this contact's email is in Instantly outreach
            instantly_badge = ""
            if c.email and c.email.lower() in instantly_emails:
                instantly_badge = '<span style="background:#EEF2FF;color:#4F46E5;padding:1px 6px;border-radius:4px;font-size:.68rem;font-weight:600;margin-left:4px">Instantly</span>'
            li_link = f'<a href="{_esc(c.linkedin_url)}" target="_blank" style="color:var(--teal)">Profile</a>' if c.linkedin_url else "—"
            replied = "Yes" if c.replied_at else "—"
            sources = ", ".join(c.email_sources) if c.email_sources else "—"
            tr_cls = ' class="replied"' if c.replied_at else ""
            rows.append(f"""<tr{tr_cls}>
  <td>{_esc(name)}{instantly_badge}</td>
  <td>{_esc(c.title)}</td>
  <td>{_esc(c.email)}</td>
  <td>{li_link}</td>
  <td>{c.confidence_score:.0%}</td>
  <td>{_esc(sources)}</td>
  <td>{_esc(c.outreach_status)}</td>
  <td>{replied}</td>
</tr>""")
        total = len(rows)
        visible_rows = "".join(rows[:_COLLAPSE_LIMIT])
        extra_rows = "".join(rows[_COLLAPSE_LIMIT:])
        if total > _COLLAPSE_LIMIT:
            table_body = f"""{visible_rows}
</tbody></table>
<details style="margin-top:4px"><summary style="cursor:pointer;font-size:.82rem;color:var(--teal)">View all {total} contacts</summary>
<table class="data-table" style="margin-top:4px">
  <tbody>{extra_rows}</tbody>
</table></details>"""
        else:
            table_body = f"{visible_rows}</tbody></table>"
        discovered_html = f"""<h3 style="font-size:.88rem;color:var(--muted);margin-bottom:4px">Discovered Contacts ({ci.discovered_count} new, {ci.existing_count} existing)</h3>
<table class="data-table">
  <thead><tr><th>Name</th><th>Title</th><th>Email</th><th>LinkedIn</th><th>Confidence</th><th>Sources</th><th>Status</th><th>Replied</th></tr></thead>
  <tbody>{table_body}"""

    # Outreach summary bar (above CRM contacts)
    outreach_bar_html = ""
    if pulse.outreach_summary:
        os_data = pulse.outreach_summary
        instantly_data = os_data.get("instantly", {})
        beehiiv_data = os_data.get("beehiiv", {})
        bar_parts = []
        if instantly_data:
            i_found = instantly_data.get("found", 0)
            i_sent = instantly_data.get("sent", 0)
            i_opened = instantly_data.get("opened", 0)
            bar_parts.append(
                f'<div style="background:#EEF2FF;border:1px solid #C7D2FE;border-radius:8px;padding:8px 14px;font-size:.82rem">'
                f'<strong style="color:#4F46E5">Instantly</strong>: {i_found} found &middot; {i_sent} sent &middot; {i_opened} opened</div>'
            )
        if beehiiv_data:
            b_found = beehiiv_data.get("found", 0)
            b_sent = beehiiv_data.get("sent", 0)
            b_opened = beehiiv_data.get("opened", 0)
            bar_parts.append(
                f'<div style="background:#FEF3C7;border:1px solid #FDE68A;border-radius:8px;padding:8px 14px;font-size:.82rem">'
                f'<strong style="color:#B45309">Beehiiv</strong>: {b_found} found &middot; {b_sent} sent &middot; {b_opened} opened</div>'
            )
        if bar_parts:
            outreach_bar_html = f'<div style="display:flex;gap:16px;margin-bottom:12px">{"".join(bar_parts)}</div>'

    # CRM contacts
    crm_html = ""
    if has_crm:
        _COLLAPSE_LIMIT = 5
        rows = []
        for c in pulse.contacts:
            name = f"{c.first_name or ''} {c.last_name or ''}".strip() or "—"
            outreach_info = ""
            if c.outreach:
                o = c.outreach[0]
                parts = []
                if o.sent:
                    parts.append("Sent")
                if o.opened:
                    parts.append("Opened")
                if o.clicked:
                    parts.append("Clicked")
                outreach_info = ", ".join(parts) if parts else "—"
            rows.append(f"""<tr>
  <td>{_esc(name)}</td>
  <td>{_esc(c.title)}</td>
  <td>{_esc(c.email)}</td>
  <td>{_esc(c.lifecycle_stage)}</td>
  <td>{outreach_info or "—"}</td>
</tr>""")
        total = len(rows)
        visible_rows = "".join(rows[:_COLLAPSE_LIMIT])
        extra_rows = "".join(rows[_COLLAPSE_LIMIT:])
        if total > _COLLAPSE_LIMIT:
            table_body = f"""{visible_rows}
</tbody></table>
<details style="margin-top:4px"><summary style="cursor:pointer;font-size:.82rem;color:var(--teal)">View all {total} contacts</summary>
<table class="data-table" style="margin-top:4px">
  <tbody>{extra_rows}</tbody>
</table></details>"""
        else:
            table_body = f"{visible_rows}</tbody></table>"
        crm_html = f"""<div style="margin-top:20px">
  {outreach_bar_html}
  <h3 style="font-size:.88rem;color:var(--muted);margin-bottom:4px">CRM Contacts ({len(pulse.contacts)})</h3>
  <table class="data-table">
    <thead><tr><th>Name</th><th>Title</th><th>Email</th><th>Stage</th><th>Outreach</th></tr></thead>
    <tbody>{table_body}
</div>"""

    return f"""<section>
  <h2>Key Contacts</h2>
  {discovered_html}
  {crm_html}
</section>"""


def _build_proposal_section(report: DomainAdReport, fit: UpscaleFitResult) -> str:
    """Proposal Numbers section — budget tiers, strategy, spend estimates."""
    e = report.enrichment
    monthly_rev = e.estimated_monthly_revenue if e else None
    budget = _budget_tier(monthly_rev, report.brand_intel)
    strategy = _spend_strategy(report.brand_intel, budget)
    start_date = _campaign_start_date()

    # Budget cards
    budget_cards = f"""<div class="budget-cards">
  <div class="budget-card" style="background:var(--teal)">
    <div class="month">Month 1</div>
    <div class="amount">{_fmt_money(budget["m1"])}</div>
    <div class="note">Ramp-up</div>
  </div>
  <div class="budget-card" style="background:var(--pink)">
    <div class="month">Month 2</div>
    <div class="amount">{_fmt_money(budget["m2"])}</div>
    <div class="note">Optimize</div>
  </div>
  <div class="budget-card" style="background:var(--navy)">
    <div class="month">Month 3</div>
    <div class="amount">{_fmt_money(budget["m3"])}</div>
    <div class="note">Scale</div>
  </div>
</div>"""

    def row(label, val):
        return f'<div class="detail-row"><span class="lbl">{label}</span><span class="val">{_esc(val)}</span></div>'

    meta_rows = [
        row("Budget Tier", budget["label"]),
        row("Daily Budget", _fmt_money(budget["daily"])),
        row("Campaign Start", start_date.strftime("%B %d, %Y (Monday)")),
    ]

    # Strategy details
    yt_pct = strategy["yt_pct"]
    ctv_rt_pct = strategy["ctv_rt_pct"]
    ctv_acq_pct = strategy["ctv_acq_pct"]

    strategy_rows = [
        row("Strategy Tier", strategy["tier"].replace("_", " ").title()),
        row("Lead Channel", strategy["lead_channel"]),
        row("YouTube Allocation", f"{yt_pct:.0%}"),
        row("CTV Retargeting", f"{ctv_rt_pct:.0%}"),
        row("CTV Acquisition", f"{ctv_acq_pct:.0%}"),
        row("Est. Annual Ad Spend", _fmt_money(strategy["annual_ad_spend"])),
    ]

    # Allocation bar (only show segments > 0)
    bar_segments = []
    if yt_pct > 0:
        bar_segments.append(f'<div style="flex:{yt_pct};background:#FF0000">YT {yt_pct:.0%}</div>')
    if ctv_rt_pct > 0:
        bar_segments.append(f'<div style="flex:{ctv_rt_pct};background:var(--teal)">CTV-RT {ctv_rt_pct:.0%}</div>')
    if ctv_acq_pct > 0:
        bar_segments.append(f'<div style="flex:{ctv_acq_pct};background:var(--navy)">CTV-ACQ {ctv_acq_pct:.0%}</div>')
    alloc_bar = f'<div class="alloc-bar">{"".join(bar_segments)}</div>' if bar_segments else ""

    strategy_desc = f'<p style="font-size:.88rem;color:#304249;margin-top:8px">{_esc(strategy["description"])}</p>'

    # Spend estimates
    spend_html = ""
    se = report.brand_intel.spend_estimate
    if se:
        spend_rows = [
            row("Est. Monthly Ad Spend", _fmt_money(se.estimated_monthly_ad_spend)),
            row("Meta Spend", _fmt_money(se.meta_spend)),
            row("Google Search Spend", _fmt_money(se.google_search_spend)),
            row("YouTube Spend", _fmt_money(se.youtube_spend)),
            row("CTV Spend", _fmt_money(se.ctv_spend)),
            row("Recommended CTV Test", _fmt_money(se.recommended_ctv_test)),
        ]
        spend_html = f"""<div style="margin-top:16px">
  <h3 style="font-size:.88rem;color:var(--muted);margin-bottom:8px">Current Spend Estimates</h3>
  {"".join(spend_rows)}
</div>"""

    # Brand intel extras
    bi = report.brand_intel
    extras = []
    if bi.purchase_model and bi.purchase_model.value != "unknown":
        extras.append(row("Purchase Model", bi.purchase_model.value.replace("_", " ").title()))
    if bi.analytics_maturity and bi.analytics_maturity != "unknown":
        extras.append(row("Analytics Maturity", bi.analytics_maturity.title()))
    if bi.brand_search_trend:
        extras.append(row("Brand Search Trend", bi.brand_search_trend.title()))
    extras_html = "".join(extras)

    return f"""<section>
  <h2>Proposal Numbers</h2>
  {budget_cards}
  <div class="two-col">
    <div>{"".join(meta_rows)}{extras_html}</div>
    <div>{"".join(strategy_rows)}</div>
  </div>
  {alloc_bar}
  {strategy_desc}
  {spend_html}
</section>"""


def _build_brand_intel_section(report: DomainAdReport) -> str:
    """Brand Intelligence Summary section (includes tech stack)."""
    bi = report.brand_intel
    e = report.enrichment

    def row(label, val):
        return f'<div class="detail-row"><span class="lbl">{label}</span><span class="val">{_esc(val)}</span></div>'

    # Purchase model
    pm_val = bi.purchase_model.value.replace("_", " ").title() if bi.purchase_model else "Unknown"
    left_rows = [
        row("Purchase Model", pm_val),
        row("Analytics Maturity", (bi.analytics_maturity or "unknown").title()),
    ]

    # Purchase model signals
    signals_html = ""
    if bi.purchase_model_signals:
        items = "".join(f"<li>{_esc(s)}</li>" for s in bi.purchase_model_signals)
        signals_html = f"""<div style="margin-top:12px">
  <h3 style="font-size:.88rem;color:var(--muted);margin-bottom:8px">Purchase Model Signals</h3>
  <ul style="font-size:.82rem;padding-left:18px;color:#304249">{items}</ul>
</div>"""

    # Analytics tools
    analytics_pills = ""
    if bi.analytics_tools:
        pills = "".join(f'<span class="pill">{_esc(t)}</span>' for t in bi.analytics_tools)
        analytics_pills = f"""<div style="margin-top:12px">
  <h3 style="font-size:.88rem;color:var(--muted);margin-bottom:8px">Analytics Tools</h3>
  <div class="pill-grid">{pills}</div>
</div>"""

    # Attribution tools
    attr_pills = ""
    if bi.attribution_tools:
        pills = "".join(f'<span class="pill">{_esc(t)}</span>' for t in bi.attribution_tools)
        attr_pills = f"""<div style="margin-top:12px">
  <h3 style="font-size:.88rem;color:var(--muted);margin-bottom:8px">Attribution Tools</h3>
  <div class="pill-grid">{pills}</div>
</div>"""

    # Maturity notes
    maturity_html = ""
    if bi.maturity_notes:
        items = "".join(f"<li>{_esc(n)}</li>" for n in bi.maturity_notes)
        maturity_html = f"""<div style="margin-top:12px">
  <h3 style="font-size:.88rem;color:var(--muted);margin-bottom:8px">Maturity Notes</h3>
  <ul style="font-size:.82rem;padding-left:18px;color:#304249">{items}</ul>
</div>"""

    # ── Competitive Landscape (cards instead of pills) ──
    comp_html = ""
    # Build enriched competitor lookup
    enriched_map: dict[str, object] = {}
    if hasattr(report, 'enriched_competitors') and report.enriched_competitors:
        for ec in report.enriched_competitors:
            enriched_map[ec.name.lower()] = ec

    if bi.competitors or bi.competitors_on_ctv or bi.competitors_on_youtube or enriched_map:
        comp_parts = []

        # Build competitor cards — use enriched data when available
        all_comp_names = list(dict.fromkeys(
            bi.competitors
            + bi.competitors_on_ctv
            + bi.competitors_on_youtube
        ))
        if all_comp_names:
            cards = []
            for c in all_comp_names:
                ec = enriched_map.get(c.lower())
                domain = ec.domain if ec and ec.domain else c.lower().replace(" ", "") + ".com"
                initial = _esc(c[0].upper()) if c else "?"

                # Revenue display
                if ec and ec.estimated_annual_revenue:
                    rev = ec.estimated_annual_revenue
                    rev_str = f"${rev / 1_000_000:.0f}M/yr" if rev >= 1_000_000 else f"${rev / 1_000:.0f}K/yr"
                else:
                    rev_str = "—"

                # Category
                cat_str = _esc(ec.industry.split("/")[-1].strip()) if ec and ec.industry else "Industry competitor"

                # Platform badge
                platform_str = _esc(ec.ecommerce_platform) if ec and ec.ecommerce_platform else ""
                platform_badge = f'<span style="background:#EEF2FF;color:#4F46E5;padding:1px 6px;border-radius:4px;font-size:.65rem;font-weight:600;margin-left:4px">{platform_str}</span>' if platform_str else ""

                # CTV / YouTube badges
                badges = ""
                on_ctv = (ec.on_ctv if ec else False) or c in bi.competitors_on_ctv
                on_yt = (ec.on_youtube if ec else False) or c in bi.competitors_on_youtube
                if on_ctv:
                    badges += '<span style="background:#CCFBF1;color:var(--teal);padding:1px 6px;border-radius:4px;font-size:.65rem;font-weight:600;margin-right:4px">CTV</span>'
                if on_yt:
                    badges += '<span style="background:#FEE2E2;color:#DC2626;padding:1px 6px;border-radius:4px;font-size:.65rem;font-weight:600">YouTube</span>'

                # Logo or initial
                if ec and ec.logo_url:
                    avatar = f'<img src="{_esc(ec.logo_url)}" alt="{_esc(c)}" style="width:36px;height:36px;border-radius:8px;object-fit:contain;flex-shrink:0">'
                else:
                    avatar = (
                        f'<div style="width:36px;height:36px;border-radius:8px;background:var(--pink-light);'
                        f'display:flex;align-items:center;justify-content:center;flex-shrink:0;font-weight:700;'
                        f'color:var(--pink);font-size:.9rem">{initial}</div>'
                    )

                link_html = (
                    f'<a href="https://{_esc(domain)}" target="_blank" '
                    f'style="color:var(--navy);text-decoration:none;font-weight:600">{_esc(c)}</a>'
                )

                cards.append(
                    f'<div style="padding:14px;background:var(--bg-grey);border:1px solid var(--border);'
                    f'border-radius:10px;display:flex;gap:12px;align-items:flex-start">'
                    f'{avatar}'
                    f'<div style="flex:1;min-width:0">'
                    f'<div>{link_html}{platform_badge}</div>'
                    f'<div style="font-size:.78rem;color:var(--muted);margin-top:2px">Annual Sales: {rev_str} &middot; {cat_str}</div>'
                    f'<div style="margin-top:4px">{badges}</div>'
                    f'</div></div>'
                )
            comp_parts.append(
                f'<h3 style="font-size:.88rem;color:var(--muted);margin-bottom:8px">Competitors ({len(all_comp_names)})</h3>'
                f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px">'
                f'{"".join(cards)}</div>'
            )
        comp_html = f"""<div style="margin-top:16px">
  {"".join(comp_parts)}
</div>"""

    # ── Tech Stack & Features (merged in from former separate section) ──
    tech_html = ""
    if e:
        competitor_keys = {k.lower() for k in CTV_COMPETITOR_TAGS}

        # Group technologies by category
        tech_full = e.technologies_full if hasattr(e, "technologies_full") else None
        grouped = group_technologies(e.technologies or [], tech_full)

        # Identify analytics/attribution tools for special highlighting
        _ANALYTICS_KEYWORDS = {
            "hotjar", "triple whale", "triplewhale", "tiktok pixel",
            "google analytics", "ga4", "google tag manager", "gtm",
            "facebook pixel", "meta pixel", "segment", "mixpanel",
            "amplitude", "heap", "fullstory", "clarity", "microsoft clarity",
            "pinterest tag", "snapchat pixel", "twitter pixel",
            "northbeam", "rockerbox", "measured", "appsflyer",
            "branch", "kochava", "adjust", "singular",
            "posthog", "plausible", "fathom", "matomo",
            "lucky orange", "crazy egg", "mouseflow",
        }
        _ANALYTICS_CATEGORIES = {"analytics", "analytics & tracking", "attribution", "tag management"}

        # Separate analytics tools from regular tech for special treatment
        highlight_tools: list[tuple[str, str]] = []
        regular_grouped: dict[str, list[str]] = {}

        for cat, techs in grouped.items():
            regular_techs = []
            for t in techs:
                t_lower = t.lower()
                is_analytics = (
                    t_lower in _ANALYTICS_KEYWORDS
                    or cat.lower() in _ANALYTICS_CATEGORIES
                )
                if is_analytics:
                    highlight_tools.append((t, cat))
                else:
                    regular_techs.append(t)
            if regular_techs:
                regular_grouped[cat] = regular_techs

        # Analytics & Attribution highlight box
        analytics_highlight = ""
        if highlight_tools:
            _KEY_TOOLS = {"hotjar", "triple whale", "triplewhale", "tiktok pixel"}
            key_items = []
            other_items = []
            for t, cat in highlight_tools:
                if t.lower() in _KEY_TOOLS or t.lower().replace(" ", "") in _KEY_TOOLS:
                    key_items.append((t, cat))
                else:
                    other_items.append((t, cat))

            key_cards = ""
            if key_items:
                kc = []
                for t, cat in key_items:
                    kc.append(
                        f'<div style="display:inline-flex;align-items:center;gap:8px;padding:10px 16px;'
                        f'background:white;border:2px solid var(--teal);border-radius:10px;font-weight:600;'
                        f'color:var(--teal);font-size:.88rem">'
                        f'<span style="font-size:1.1rem">&#x2713;</span> {_esc(t)}'
                        f'<span style="font-size:.7rem;color:var(--muted);font-weight:400">({_esc(cat)})</span>'
                        f'</div>'
                    )
                key_cards = f'<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px">{"".join(kc)}</div>'

            other_pills = ""
            if other_items:
                op = "".join(
                    f'<span class="pill" style="background:#ECFDF5;border:1px solid #A7F3D0;color:#065F46">'
                    f'{_esc(t)}</span>'
                    for t, _ in other_items
                )
                other_pills = f'<div class="pill-grid" style="margin-top:6px">{op}</div>'

            maturity_label = (bi.analytics_maturity or "unknown").title()
            _maturity_colors = {"basic": "#B54708", "intermediate": "#0A6D86", "advanced": "#027A48"}
            maturity_color = _maturity_colors.get((bi.analytics_maturity or "").lower(), "var(--muted)")

            strength = "strong" if len(highlight_tools) >= 4 else "moderate" if len(highlight_tools) >= 2 else "basic"
            tool_count = len(highlight_tools)
            plural = "s" if tool_count != 1 else ""

            analytics_highlight = (
                f'<div style="margin-top:20px;padding:18px;background:#F0FDFA;border:1px solid #99F6E4;'
                f'border-radius:14px">'
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">'
                f'<h3 style="font-size:.95rem;color:var(--navy);margin:0">Analytics &amp; Attribution</h3>'
                f'<span style="font-size:.72rem;font-weight:600;padding:3px 10px;border-radius:999px;'
                f'background:white;color:{maturity_color};border:1px solid {maturity_color}">'
                f'{maturity_label} maturity</span>'
                f'</div>'
                f'<p style="font-size:.82rem;color:#304249;margin-bottom:12px">'
                f'{tool_count} analytics/attribution tool{plural} detected &mdash; '
                f'indicates {strength} measurement infrastructure.</p>'
                f'{key_cards}{other_pills}</div>'
            )

        # Regular tech stack categories (excluding analytics tools already shown)
        category_blocks = []
        for cat, techs in regular_grouped.items():
            bg = CATEGORY_COLORS.get(cat, "#F3F4F6")
            pills = []
            for t in techs:
                if t.lower() in competitor_keys:
                    pills.append(
                        f'<span class="pill" style="background:#FEF3F2;border:2px solid #FDA29B;'
                        f'color:#B42318;font-weight:700">\u26a0 COMPETITOR &mdash; {_esc(t)}</span>'
                    )
                else:
                    pills.append(f'<span class="pill" style="background:{bg}">{_esc(t)}</span>')
            category_blocks.append(
                f'<div style="margin-bottom:12px">'
                f'<h4 style="font-size:.78rem;text-transform:uppercase;letter-spacing:.05em;'
                f'color:var(--muted);margin-bottom:6px">{_esc(cat)} ({len(techs)})</h4>'
                f'<div class="pill-grid">{"".join(pills)}</div></div>'
            )

        feature_pills = "".join(f'<span class="pill">{_esc(f)}</span>' for f in (e.features or []))
        tech_count = len(e.technologies or [])
        feature_count = len(e.features or [])

        _none_detected = '<p style="color:var(--muted)">None detected</p>'
        _none_feat = '<span style="color:var(--muted)">None detected</span>'
        cat_content = "".join(category_blocks) or _none_detected
        feat_content = feature_pills or _none_feat

        tech_html = (
            f'<div style="margin-top:24px;padding-top:20px;border-top:1px solid var(--border)">'
            f'<h3 style="font-size:1.1rem;font-weight:700;margin-bottom:4px">Tech Stack &amp; Features</h3>'
            f'<p style="font-size:.85rem;color:var(--muted);margin-bottom:16px">'
            f'{tech_count} technologies detected, grouped by category</p>'
            f'{analytics_highlight}'
            f'<div style="margin-top:16px">{cat_content}</div>'
            f'<h4 style="font-size:.88rem;color:var(--muted);margin:16px 0 8px">Features ({feature_count})</h4>'
            f'<div class="pill-grid">{feat_content}</div></div>'
        )

    return f"""<section>
  <h2>Brand Intelligence</h2>
  {"".join(left_rows)}
  {signals_html}
  {analytics_pills}
  {attr_pills}
  {maturity_html}
  {comp_html}
  {tech_html}
</section>"""


# ---------------------------------------------------------------------------
# Phase 1: AI Synthesis Sections
# ---------------------------------------------------------------------------

def _paid_media_maturity(report: DomainAdReport, fit: UpscaleFitResult) -> str:
    """Section 1: Paid Media Maturity Assessment — Low/Medium/High rating."""
    mix = report.channel_mix
    bi = report.brand_intel
    e = report.enrichment

    # Determine primary channels
    channels_active: list[str] = []
    if mix.has_meta:
        channels_active.append("Meta")
    if mix.has_youtube:
        channels_active.append("YouTube")
    if mix.has_linear:
        channels_active.append("CTV / Linear TV")
    if report.meta_ads.found and report.meta_ads.ads:
        if "Meta" not in channels_active:
            channels_active.append("Meta")
    if report.ispot_ads.found and report.ispot_ads.ads:
        if "CTV / Linear TV" not in channels_active:
            channels_active.append("CTV / Linear TV")

    # Overall maturity score
    maturity_points = 0
    maturity_signals: list[tuple[str, str]] = []  # (signal, color)

    # Channel breadth
    if mix.total_platforms >= 3:
        maturity_points += 3
        maturity_signals.append(("Multi-channel presence (3+ platforms)", "var(--success)"))
    elif mix.total_platforms == 2:
        maturity_points += 2
        maturity_signals.append(("Dual-channel presence", "var(--teal)"))
    elif mix.total_platforms == 1:
        maturity_points += 1
        maturity_signals.append(("Single-channel only", "var(--warning)"))
    else:
        maturity_signals.append(("No ad platforms detected", "var(--danger)"))

    # Creative volume
    total_ads = mix.total_ads_found
    if total_ads >= 20:
        maturity_points += 3
        maturity_signals.append((f"{total_ads} ads found — high creative velocity", "var(--success)"))
    elif total_ads >= 5:
        maturity_points += 2
        maturity_signals.append((f"{total_ads} ads found — moderate creative testing", "var(--teal)"))
    elif total_ads >= 1:
        maturity_points += 1
        maturity_signals.append((f"{total_ads} ad(s) found — minimal creative testing", "var(--warning)"))
    else:
        maturity_signals.append(("No ads discovered", "var(--danger)"))

    # Analytics maturity
    maturity_level = (bi.analytics_maturity or "unknown").lower()
    if maturity_level == "advanced":
        maturity_points += 3
        maturity_signals.append(("Advanced analytics/attribution stack", "var(--success)"))
    elif maturity_level == "intermediate":
        maturity_points += 2
        maturity_signals.append(("Intermediate analytics stack", "var(--teal)"))
    elif maturity_level == "basic":
        maturity_points += 1
        maturity_signals.append(("Basic analytics only", "var(--warning)"))
    else:
        maturity_signals.append(("Analytics maturity unknown", "var(--muted)"))

    # Attribution tools
    if bi.attribution_tools:
        maturity_points += 2
        maturity_signals.append((f"Attribution tools: {', '.join(bi.attribution_tools[:3])}", "var(--success)"))

    # Incrementality evidence (MMM, lift tests)
    incrementality = "None detected"
    _incr_keywords = {"northbeam", "measured", "rockerbox", "triple whale", "triplewhale", "tatari"}
    incr_tools = [t for t in (bi.analytics_tools + bi.attribution_tools) if t.lower() in _incr_keywords]
    if incr_tools:
        maturity_points += 1
        incrementality = f"Possible — uses {', '.join(incr_tools)}"
        maturity_signals.append((f"Incrementality measurement likely ({', '.join(incr_tools)})", "var(--success)"))

    # Overall rating
    if maturity_points >= 9:
        rating, rating_color = "High", "var(--success)"
    elif maturity_points >= 5:
        rating, rating_color = "Medium", "var(--teal)"
    else:
        rating, rating_color = "Low", "var(--warning)"

    # CTV maturity
    ctv_maturity = "None"
    ctv_color = "var(--muted)"
    if report.competitor_detection.found:
        ctv_maturity = "Active (competitor detected)"
        ctv_color = "var(--danger)"
    elif mix.has_linear:
        if total_ads >= 5:
            ctv_maturity = "Scaling"
            ctv_color = "var(--success)"
        else:
            ctv_maturity = "Testing"
            ctv_color = "var(--teal)"

    # YouTube maturity
    yt_maturity = "None"
    yt_color = "var(--muted)"
    if mix.has_youtube:
        yt_ads = len(report.youtube_ads.ads) if report.youtube_ads.found else 0
        if yt_ads >= 5:
            yt_maturity = "Scaling"
            yt_color = "var(--success)"
        else:
            yt_maturity = "Testing"
            yt_color = "var(--teal)"

    # In-house vs agency
    agency_signal = "Unknown"
    if e and e.employee_count:
        if e.employee_count < 20:
            agency_signal = "Likely agency-managed (small team)"
        elif e.employee_count < 100:
            agency_signal = "Likely hybrid (in-house + agency)"
        else:
            agency_signal = "Likely in-house team"

    # Build signal rows
    signal_html = "".join(
        f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;'
        f'border-bottom:1px solid var(--border)">'
        f'<span style="width:8px;height:8px;border-radius:50%;background:{color};flex-shrink:0"></span>'
        f'<span style="font-size:.84rem;color:var(--navy)">{_esc(sig)}</span></div>'
        for sig, color in maturity_signals
    )

    channels_str = ", ".join(channels_active) if channels_active else "None detected"

    return f"""<section>
  <h2>Paid Media Maturity Assessment</h2>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:20px">
    <div style="padding:20px;background:var(--bg-grey);border-radius:12px;text-align:center">
      <div style="font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px">Overall Maturity</div>
      <div style="font-size:1.6rem;font-weight:800;color:{rating_color}">{rating}</div>
    </div>
    <div style="padding:20px;background:var(--bg-grey);border-radius:12px;text-align:center">
      <div style="font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px">CTV Maturity</div>
      <div style="font-size:1.1rem;font-weight:700;color:{ctv_color}">{ctv_maturity}</div>
    </div>
    <div style="padding:20px;background:var(--bg-grey);border-radius:12px;text-align:center">
      <div style="font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px">YouTube Maturity</div>
      <div style="font-size:1.1rem;font-weight:700;color:{yt_color}">{yt_maturity}</div>
    </div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
    <div>
      <h3 style="font-size:.9rem;color:var(--muted);margin-bottom:10px">Maturity Signals</h3>
      {signal_html}
    </div>
    <div>
      <div class="detail-row"><span class="lbl">Primary Channels</span><span class="val">{_esc(channels_str)}</span></div>
      <div class="detail-row"><span class="lbl">Management Model</span><span class="val">{_esc(agency_signal)}</span></div>
      <div class="detail-row"><span class="lbl">Incrementality Evidence</span><span class="val">{_esc(incrementality)}</span></div>
      <div class="detail-row"><span class="lbl">Creative Fatigue Risk</span><span class="val">{"Low" if total_ads >= 10 else "High — limited creative rotation" if total_ads <= 2 else "Medium"}</span></div>
    </div>
  </div>
</section>"""


def _creative_messaging_signals(report: DomainAdReport) -> str:
    """Section 2: Creative & Messaging Signals — ad format analysis."""
    meta_ads = report.meta_ads.ads if report.meta_ads.found else []
    ispot_ads = report.ispot_ads.ads if report.ispot_ads.found else []
    yt_ads = report.youtube_ads.ads if report.youtube_ads.found else []
    all_ads = meta_ads + ispot_ads + yt_ads
    milled = report.milled_intel
    e = report.enrichment

    if not all_ads and not (milled and milled.found):
        return """<section>
  <h2>Creative &amp; Messaging Signals</h2>
  <p style="color:var(--muted);padding:20px 0">No ads or promotional emails discovered — insufficient data for creative analysis.</p>
</section>"""

    # Format detection
    formats_detected: dict[str, int] = {}
    for ad in all_ads:
        fmt = (ad.format or "unknown").lower()
        if "video" in fmt or ad.video_url:
            formats_detected["Video"] = formats_detected.get("Video", 0) + 1
        elif "image" in fmt or "static" in fmt:
            formats_detected["Static Image"] = formats_detected.get("Static Image", 0) + 1
        elif "carousel" in fmt:
            formats_detected["Carousel"] = formats_detected.get("Carousel", 0) + 1
        else:
            formats_detected["Other"] = formats_detected.get("Other", 0) + 1

    # Duration analysis
    durations = [a.duration_seconds for a in all_ads if a.duration_seconds]
    duration_html = ""
    if durations:
        avg_dur = sum(durations) / len(durations)
        min_dur = min(durations)
        max_dur = max(durations)
        duration_html = (
            f'<div class="detail-row"><span class="lbl">Avg Duration</span>'
            f'<span class="val">{avg_dur:.0f}s (range: {min_dur}–{max_dur}s)</span></div>'
        )

    # Messaging theme detection from ad titles and milled subjects
    _theme_keywords = {
        "Price": ["discount", "off", "sale", "save", "%", "deal", "price", "free shipping", "bogo", "clearance"],
        "Quality": ["premium", "quality", "handmade", "artisan", "crafted", "luxury", "organic", "natural"],
        "Outcomes": ["results", "transform", "before", "after", "proven", "clinically", "works", "effective"],
        "Trust": ["review", "rated", "trusted", "award", "certified", "guarantee", "money back"],
        "Speed / Convenience": ["fast", "easy", "simple", "delivered", "doorstep", "minutes", "instant", "quick"],
    }

    text_corpus = " ".join([
        (a.title or "") for a in all_ads
    ] + [
        (e.subject or "") for e in (milled.emails if milled and milled.found else [])
    ]).lower()

    themes_found: list[tuple[str, int]] = []
    for theme, keywords in _theme_keywords.items():
        hits = sum(1 for k in keywords if k in text_corpus)
        if hits > 0:
            themes_found.append((theme, hits))
    themes_found.sort(key=lambda x: x[1], reverse=True)

    # Offer detection from Milled
    offers: list[str] = []
    if milled and milled.found:
        cats = milled.promo_categories
        if cats.get("sale", 0) > 0:
            offers.append(f"Sales/Discounts ({cats['sale']} emails)")
        if cats.get("bfcm", 0) > 0:
            offers.append(f"BFCM campaigns ({cats['bfcm']} emails)")
        if cats.get("product_launch", 0) > 0:
            offers.append(f"Product Launches ({cats['product_launch']} emails)")
        if cats.get("seasonal", 0) > 0:
            offers.append(f"Seasonal promos ({cats['seasonal']} emails)")
        if milled.emails_per_week > 3:
            offers.append(f"High email cadence ({milled.emails_per_week:.1f}/week)")

    # Build format pills
    format_pills = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:6px;padding:6px 14px;'
        f'background:var(--bg-grey);border:1px solid var(--border);border-radius:8px;'
        f'font-size:.84rem;font-weight:600">{_esc(fmt)} '
        f'<span style="color:var(--muted);font-weight:400">({count})</span></span>'
        for fmt, count in sorted(formats_detected.items(), key=lambda x: x[1], reverse=True)
    )

    # Build theme bars
    max_hits = themes_found[0][1] if themes_found else 1
    theme_bars = "".join(
        f'<div style="margin-bottom:8px">'
        f'<div style="display:flex;justify-content:space-between;font-size:.82rem;margin-bottom:2px">'
        f'<span style="font-weight:600">{_esc(theme)}</span>'
        f'<span style="color:var(--muted)">{hits} signal{"s" if hits != 1 else ""}</span></div>'
        f'<div style="height:6px;background:var(--border);border-radius:3px">'
        f'<div style="height:6px;background:var(--teal);border-radius:3px;width:{min(hits / max_hits * 100, 100):.0f}%"></div>'
        f'</div></div>'
        for theme, hits in themes_found
    ) if themes_found else '<p style="color:var(--muted);font-size:.84rem">No messaging themes detected</p>'

    offers_html = "".join(
        f'<div style="padding:6px 0;border-bottom:1px solid var(--border);font-size:.84rem">{_esc(o)}</div>'
        for o in offers
    ) if offers else '<p style="color:var(--muted);font-size:.84rem">No promotional offers detected</p>'

    return f"""<section>
  <h2>Creative &amp; Messaging Signals</h2>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px">
    <div>
      <h3 style="font-size:.9rem;color:var(--muted);margin-bottom:10px">Creative Formats Used</h3>
      <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px">{format_pills}</div>
      {duration_html}
      <h3 style="font-size:.9rem;color:var(--muted);margin:16px 0 10px">Offers &amp; Promotions</h3>
      {offers_html}
    </div>
    <div>
      <h3 style="font-size:.9rem;color:var(--muted);margin-bottom:10px">Messaging Themes</h3>
      {theme_bars}
    </div>
  </div>
</section>"""


def _ctv_youtube_hypotheses(report: DomainAdReport, fit: UpscaleFitResult) -> str:
    """Section 3: CTV & YouTube Hypotheses — why now, best products, creative angles, test budget."""
    e = report.enrichment
    bi = report.brand_intel
    mix = report.channel_mix
    milled = report.milled_intel

    company = _esc(report.company_name or report.domain)
    industry = _esc(e.industry) if e and e.industry else "their category"

    # Why CTV now
    why_now: list[str] = []
    if not mix.has_linear:
        why_now.append("No CTV presence detected — greenfield opportunity to own the streaming channel before competitors move in.")
    if bi.competitors_on_ctv:
        comps = ", ".join(bi.competitors_on_ctv[:3])
        why_now.append(f"Competitors already on CTV ({comps}) — risk of falling behind in share of voice.")
    if e and e.estimated_monthly_revenue and e.estimated_monthly_revenue >= 500_000:
        why_now.append("Revenue scale supports meaningful CTV test budget without over-indexing on a single channel.")
    if mix.has_meta and not mix.has_linear:
        why_now.append("Strong Meta foundation means retargeting audiences are already built — CTV adds top-of-funnel awareness that Meta can convert.")
    if milled and milled.has_bfcm:
        why_now.append("BFCM promotional history shows seasonal scaling capability — CTV can amplify peak season reach.")
    if bi.analytics_maturity in ("intermediate", "advanced"):
        why_now.append("Mature analytics stack can measure CTV impact through attribution and incrementality.")
    if not why_now:
        why_now.append(f"CTV represents an untapped awareness channel for {company} to reach cord-cutting consumers in {industry}.")

    # Best products/offers for TV
    products: list[str] = []
    if e and e.avg_product_price:
        products.append(f"Hero products at {_esc(e.avg_product_price)} price point — strong for TV impulse consideration.")
    pm = bi.purchase_model
    if pm and pm.value == "subscription":
        products.append("Subscription offer — TV drives trial subscriptions with strong LTV payback.")
    elif pm and pm.value == "high_repurchase":
        products.append("Replenishable products — CTV awareness drives first purchase, natural repurchase follows.")
    if milled and milled.promo_categories.get("product_launch", 0) > 0:
        products.append("New product launches — TV is the fastest way to build awareness for a new SKU at scale.")
    if not products:
        products.append("Lead with bestsellers or hero SKU — highest conversion probability from new TV-driven traffic.")

    # Creative angles
    angles: list[str] = []
    if e and e.review_rating and e.review_rating >= 4.0:
        angles.append(f"Social proof: {e.review_rating}★ rating across {_fmt_number(e.review_count)} reviews — trust-building TV creative.")
    angles.append("Product demo / unboxing — show the product in use within the first 3 seconds to hook viewers.")
    if pm and pm.value == "subscription":
        angles.append("Subscription value prop — \"Delivered to your door\" messaging with clear savings.")
    angles.append("Founder story / brand origin — builds emotional connection on a medium that rewards storytelling.")
    if bi.competitors_on_ctv:
        angles.append("Competitive differentiation — position against alternatives already advertising on TV.")

    # Test budget
    budget_low = 15_000
    budget_high = 50_000
    if bi.spend_estimate and bi.spend_estimate.recommended_ctv_test:
        budget_low = int(bi.spend_estimate.recommended_ctv_test * 0.8)
        budget_high = int(bi.spend_estimate.recommended_ctv_test * 1.5)

    why_items = "".join(f'<li style="margin-bottom:8px">{_esc(w)}</li>' for w in why_now)
    product_items = "".join(f'<li style="margin-bottom:8px">{_esc(p)}</li>' for p in products)
    angle_items = "".join(f'<li style="margin-bottom:8px">{_esc(a)}</li>' for a in angles)

    return f"""<section>
  <h2>CTV &amp; YouTube Hypotheses</h2>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px">
    <div>
      <h3 style="font-size:.9rem;color:var(--pink);margin-bottom:10px">Why CTV / YouTube Now</h3>
      <ul style="font-size:.84rem;padding-left:18px;color:var(--navy);line-height:1.7">{why_items}</ul>
      <h3 style="font-size:.9rem;color:var(--pink);margin:20px 0 10px">Best Products for TV</h3>
      <ul style="font-size:.84rem;padding-left:18px;color:var(--navy);line-height:1.7">{product_items}</ul>
    </div>
    <div>
      <h3 style="font-size:.9rem;color:var(--pink);margin-bottom:10px">Creative Angles for CTV</h3>
      <ul style="font-size:.84rem;padding-left:18px;color:var(--navy);line-height:1.7">{angle_items}</ul>
      <div style="margin-top:20px;padding:18px;background:var(--pink-light);border-radius:12px">
        <h3 style="font-size:.9rem;margin-bottom:8px">Suggested Test Budget</h3>
        <div style="font-size:1.4rem;font-weight:800;color:var(--pink)">{_fmt_money(budget_low)} – {_fmt_money(budget_high)}<span style="font-size:.8rem;font-weight:500;color:var(--muted)"> /month</span></div>
        <p style="font-size:.78rem;color:var(--muted);margin-top:6px">Recommended 3-month pilot across CTV + YouTube to build statistical significance.</p>
      </div>
    </div>
  </div>
</section>"""


def _buying_committee(report: DomainAdReport) -> str:
    """Section 4: Buying Committee & Champion Mapping."""
    contacts = report.contact_intel.contacts if report.contact_intel.found else []
    e = report.enrichment
    pulse = report.company_pulse

    # Role classification
    _BUDGET_TITLES = ["cmo", "vp marketing", "head of marketing", "director of marketing", "chief marketing", "svp marketing"]
    _GATE_TITLES = ["head of growth", "director of growth", "vp growth", "performance", "paid media", "acquisition", "demand gen"]
    _CREATIVE_TITLES = ["creative director", "head of creative", "brand director", "content", "design"]
    _CHAMPION_TITLES = ["growth", "paid", "media", "performance", "digital marketing", "acquisition"]

    budget_owner = None
    gatekeeper = None
    creative_stake = None
    champion = None

    for c in contacts:
        title_lower = (c.title or "").lower()
        name = f"{c.first_name or ''} {c.last_name or ''}".strip() or c.email or "Unknown"

        if not budget_owner and any(t in title_lower for t in _BUDGET_TITLES):
            budget_owner = (name, c.title, c.linkedin_url)
        if not gatekeeper and any(t in title_lower for t in _GATE_TITLES):
            gatekeeper = (name, c.title, c.linkedin_url)
        if not creative_stake and any(t in title_lower for t in _CREATIVE_TITLES):
            creative_stake = (name, c.title, c.linkedin_url)
        if not champion and any(t in title_lower for t in _CHAMPION_TITLES):
            champion = (name, c.title, c.linkedin_url)

    def _contact_card(label: str, person: tuple | None, fallback_title: str, icon: str) -> str:
        if person:
            name, title, linkedin = person
            link = f' <a href="{_esc(linkedin)}" target="_blank" style="color:var(--teal);font-size:.75rem">LinkedIn →</a>' if linkedin else ""
            return (
                f'<div style="padding:16px;background:var(--bg-grey);border-radius:10px">'
                f'<div style="font-size:1.1rem;margin-bottom:6px">{icon}</div>'
                f'<div style="font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em">{label}</div>'
                f'<div style="font-size:.92rem;font-weight:700;margin-top:4px">{_esc(name)}</div>'
                f'<div style="font-size:.82rem;color:var(--muted)">{_esc(title)}{link}</div></div>'
            )
        return (
            f'<div style="padding:16px;background:var(--bg-grey);border-radius:10px;opacity:.6">'
            f'<div style="font-size:1.1rem;margin-bottom:6px">{icon}</div>'
            f'<div style="font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em">{label}</div>'
            f'<div style="font-size:.88rem;font-weight:600;color:var(--muted);margin-top:4px">Not identified</div>'
            f'<div style="font-size:.78rem;color:var(--muted)">Look for: {fallback_title}</div></div>'
        )

    cards = (
        _contact_card("Budget Owner", budget_owner, "CMO / VP Marketing", "&#x1f4b0;")
        + _contact_card("Technical Gatekeeper", gatekeeper, "Head of Growth / Paid Media", "&#x1f6e1;")
        + _contact_card("Creative Stakeholder", creative_stake, "Creative Director / Brand Lead", "&#x1f3a8;")
        + _contact_card("Best Champion", champion, "Growth / Performance Marketing Manager", "&#x1f31f;")
    )

    # Potential objections by role
    objections = [
        ("CMO / Budget Owner", "\"We're not ready to test a new channel\" — Counter: Upscale's $500 creative cost and 6-day launch means minimal commitment."),
        ("Growth / Paid Lead", "\"How do we measure CTV?\" — Counter: Native Shopify attribution with 3-day view-through window, plus built-in incrementality."),
        ("Creative Team", "\"We don't have TV-ready creative\" — Counter: Upscale produces 2-20+ CTV variations/month from existing brand assets."),
        ("Finance / CEO", "\"CTV is too expensive\" — Counter: Bundled pricing (creative + media + measurement), no hidden margins, YouTube included."),
    ]

    obj_html = "".join(
        f'<div style="padding:10px 0;border-bottom:1px solid var(--border)">'
        f'<div style="font-size:.82rem;font-weight:700;color:var(--navy)">{_esc(role)}</div>'
        f'<div style="font-size:.82rem;color:#304249;margin-top:2px">{_esc(obj)}</div></div>'
        for role, obj in objections
    )

    return f"""<section>
  <h2>Buying Committee &amp; Champion Mapping</h2>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px">
    {cards}
  </div>
  <h3 style="font-size:.9rem;color:var(--muted);margin-bottom:10px">Potential Objections by Role</h3>
  {obj_html}
</section>"""


def _call_talk_track(report: DomainAdReport, fit: UpscaleFitResult) -> str:
    """Section 5: Call Talk Track — opening insights, discovery questions, proof points, CTA."""
    e = report.enrichment
    bi = report.brand_intel
    mix = report.channel_mix
    company = _esc(report.company_name or report.domain)

    # 3 Opening insights
    insights: list[str] = []

    # Insight 1: Revenue/scale
    if e and e.estimated_annual_revenue:
        rev = _fmt_money(e.estimated_annual_revenue)
        insights.append(f"\"I see {company} is doing roughly {rev}/year — brands at your scale typically see 3-6x ROAS on CTV within the first 90 days.\"")
    elif e and e.estimated_monthly_revenue:
        rev = _fmt_money(e.estimated_monthly_revenue)
        insights.append(f"\"At ~{rev}/month in revenue, {company} is at the sweet spot where CTV starts paying for itself through incremental new customer acquisition.\"")
    else:
        insights.append(f"\"From what I can see, {company} has strong brand presence — brands like yours are the ones who benefit most from CTV's ability to reach new audiences at scale.\"")

    # Insight 2: Competitive/channel
    if bi.competitors_on_ctv:
        comps = " and ".join(bi.competitors_on_ctv[:2])
        insights.append(f"\"I noticed {comps} {'are' if len(bi.competitors_on_ctv) > 1 else 'is'} already running CTV campaigns — there's a window to match their reach before they build too much share of voice.\"")
    elif mix.has_meta and not mix.has_linear:
        insights.append(f"\"You're clearly investing in Meta — CTV is the natural next step to drive top-of-funnel awareness that feeds your Meta retargeting.\"")
    else:
        insights.append(f"\"47% of all TV viewing is now streaming — that's where {company}'s next customers are watching.\"")

    # Insight 3: Tech/creative
    if e and e.ecommerce_platform and "shopify" in (e.ecommerce_platform or "").lower():
        insights.append(f"\"Since you're on Shopify, our native integration means we can track purchases directly — no separate attribution platform needed.\"")
    elif bi.analytics_maturity == "advanced":
        insights.append(f"\"Your analytics stack is sophisticated — you'll appreciate that Upscale provides deterministic purchase attribution, not just modeled estimates.\"")
    else:
        insights.append(f"\"One thing brands love about Upscale is we handle creative production at 95% lower cost than traditional TV — $500 vs the typical $10K+ per spot.\"")

    # 5 Discovery questions
    questions = [
        f"What channels are driving the most efficient new customer acquisition for {company} today?",
        "Have you tested any upper-funnel channels (TV, CTV, YouTube) before? What was the experience?",
        "How are you currently thinking about measurement and attribution across channels?",
        "What does your creative production process look like — in-house, agency, or a mix?",
        "What's the biggest growth challenge you're trying to solve this quarter?",
    ]

    # 3 Proof points
    proof_points = [
        "Branch Furniture: $50K savings vs previous provider, 6.2x ROAS, 500+ monthly purchases from CTV.",
        "fatty15: 3.65x blended ROAS, 69% first-time buyers, proving CTV drives new customer acquisition.",
        "Newton Baby: 40% lower CPA than previous CTV provider with 80+ creative variations tested.",
    ]

    # Next step CTA
    cta = f"\"Let's set up a 30-minute deep dive where I can show you exactly how {company}'s Shopify data would flow through our platform and model out a 90-day pilot. I'll bring mock creative based on your brand assets.\""

    insight_items = "".join(
        f'<div style="padding:12px 16px;background:var(--bg-grey);border-radius:10px;margin-bottom:8px;'
        f'font-size:.84rem;line-height:1.6;border-left:3px solid var(--pink)">{i}</div>'
        for i in insights
    )

    question_items = "".join(
        f'<div style="padding:8px 0;border-bottom:1px solid var(--border);font-size:.84rem;display:flex;gap:8px">'
        f'<span style="color:var(--teal);font-weight:700;flex-shrink:0">{idx}.</span>'
        f'<span>{_esc(q)}</span></div>'
        for idx, q in enumerate(questions, 1)
    )

    proof_items = "".join(
        f'<div style="padding:10px 14px;background:#F0FDFA;border:1px solid #99F6E4;border-radius:10px;'
        f'margin-bottom:8px;font-size:.84rem;line-height:1.5">{_esc(p)}</div>'
        for p in proof_points
    )

    return f"""<section>
  <h2>Call Talk Track</h2>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px">
    <div>
      <h3 style="font-size:.9rem;color:var(--pink);margin-bottom:10px">3 Opening Insights</h3>
      {insight_items}
      <h3 style="font-size:.9rem;color:var(--pink);margin:20px 0 10px">5 Discovery Questions</h3>
      {question_items}
    </div>
    <div>
      <h3 style="font-size:.9rem;color:var(--teal);margin-bottom:10px">Upscale Proof Points</h3>
      {proof_items}
      <div style="margin-top:20px;padding:18px;background:var(--navy);border-radius:12px;color:white">
        <h3 style="font-size:.85rem;color:rgba(255,255,255,.7);margin-bottom:8px">Recommended Next Step</h3>
        <p style="font-size:.88rem;line-height:1.6">{cta}</p>
      </div>
    </div>
  </div>
</section>"""


def _account_priority_signal(report: DomainAdReport, fit: UpscaleFitResult) -> str:
    """Section 6: Account Priority Signal — High/Medium/Low with justification."""
    e = report.enrichment
    bi = report.brand_intel
    mix = report.channel_mix

    score = fit.total_score
    signals_pro: list[str] = []
    signals_con: list[str] = []

    # Revenue scale
    if e and e.estimated_annual_revenue:
        if e.estimated_annual_revenue >= 10_000_000:
            signals_pro.append(f"Strong revenue ({_fmt_money(e.estimated_annual_revenue)}/yr) — can sustain meaningful CTV budget")
        elif e.estimated_annual_revenue >= 2_000_000:
            signals_pro.append(f"Moderate revenue ({_fmt_money(e.estimated_annual_revenue)}/yr) — viable for CTV pilot")
        else:
            signals_con.append(f"Lower revenue ({_fmt_money(e.estimated_annual_revenue)}/yr) — may limit initial CTV budget")

    # Shopify
    if e and e.ecommerce_platform and "shopify" in (e.ecommerce_platform or "").lower():
        signals_pro.append("On Shopify — native Upscale integration available")
    elif e and e.ecommerce_platform:
        signals_con.append(f"Not on Shopify ({_esc(e.ecommerce_platform)}) — no native integration")

    # Existing CTV
    if report.competitor_detection.found:
        signals_con.append(f"Active CTV competitor client ({', '.join(report.competitor_detection.competitors_detected)}) — displacement sale")
    elif not mix.has_linear:
        signals_pro.append("No CTV presence — greenfield opportunity")

    # Ad activity
    if mix.total_ads_found >= 5:
        signals_pro.append(f"Active advertiser ({mix.total_ads_found} ads found) — established paid media practice")
    elif mix.total_ads_found == 0:
        signals_con.append("No ads detected — may not be investing in paid acquisition")

    # Competitor CTV activity
    if bi.competitors_on_ctv:
        signals_pro.append(f"Competitors on CTV ({', '.join(bi.competitors_on_ctv[:2])}) — urgency to match")

    # Contact availability
    if report.contact_intel.found and report.contact_intel.discovered_count > 0:
        signals_pro.append(f"{report.contact_intel.discovered_count} contacts discovered — outreach-ready")
    else:
        signals_con.append("No contacts discovered — requires manual prospecting")

    # CRM context
    if report.company_pulse.found and report.company_pulse.current_status:
        signals_pro.append(f"CRM status: {_esc(report.company_pulse.current_status)}")

    # Priority determination
    pro_count = len(signals_pro)
    con_count = len(signals_con)

    if score >= 70 and pro_count >= 4:
        priority = "High Priority"
        priority_icon = "&#x1f525;"
        priority_color = "var(--success)"
        bg_color = "#ECFDF5"
        border_color = "#A7F3D0"
    elif score >= 45 or pro_count >= 3:
        priority = "Medium Priority"
        priority_icon = "&#x26a0;&#xfe0f;"
        priority_color = "var(--warning)"
        bg_color = "#FFFBEB"
        border_color = "#FDE68A"
    else:
        priority = "Low Priority"
        priority_icon = "&#x274c;"
        priority_color = "var(--danger)"
        bg_color = "#FEF2F2"
        border_color = "#FECACA"

    # Justification
    if signals_pro:
        top_reasons = signals_pro[:3]
        justification = " | ".join(top_reasons)
    else:
        justification = "Insufficient positive signals for prioritization"

    pro_items = "".join(
        f'<div style="display:flex;align-items:flex-start;gap:8px;padding:6px 0;font-size:.84rem">'
        f'<span style="color:var(--success);flex-shrink:0;font-weight:700">+</span>'
        f'<span>{_esc(s)}</span></div>'
        for s in signals_pro
    )
    con_items = "".join(
        f'<div style="display:flex;align-items:flex-start;gap:8px;padding:6px 0;font-size:.84rem">'
        f'<span style="color:var(--danger);flex-shrink:0;font-weight:700">–</span>'
        f'<span>{_esc(s)}</span></div>'
        for s in signals_con
    )

    return f"""<section>
  <h2>Account Priority Signal</h2>
  <div style="padding:24px;background:{bg_color};border:2px solid {border_color};border-radius:14px;margin-bottom:20px;text-align:center">
    <div style="font-size:2rem;margin-bottom:4px">{priority_icon}</div>
    <div style="font-size:1.5rem;font-weight:800;color:{priority_color}">{priority}</div>
    <p style="font-size:.88rem;color:var(--navy);margin-top:8px">{_esc(justification)}</p>
    <div style="font-size:.78rem;color:var(--muted);margin-top:4px">Upscale Fit Score: {fit.total_score:.0f}/100 ({fit.grade})</div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
    <div>
      <h3 style="font-size:.9rem;color:var(--success);margin-bottom:10px">Positive Signals ({pro_count})</h3>
      {pro_items or '<p style="color:var(--muted);font-size:.84rem">None identified</p>'}
    </div>
    <div>
      <h3 style="font-size:.9rem;color:var(--danger);margin-bottom:10px">Risk Signals ({con_count})</h3>
      {con_items or '<p style="color:var(--muted);font-size:.84rem">None identified</p>'}
    </div>
  </div>
</section>"""


# ---------------------------------------------------------------------------
# Phase 2: Deep Research Section Builders
# ---------------------------------------------------------------------------

def _build_hiring_section(report: DomainAdReport) -> str:
    """Hiring & Growth Signals section."""
    hi = report.hiring_intel
    if not hi.found and not hi.open_jobs_count:
        return """<section>
  <h2>Hiring &amp; Growth Signals</h2>
  <p style="color:var(--muted);padding:20px 0">No hiring data available.</p>
</section>"""

    # Velocity badge
    vel = hi.hiring_velocity or "unknown"
    vel_colors = {"accelerating": "var(--success)", "stable": "var(--teal)", "slowing": "var(--warning)"}
    vel_color = vel_colors.get(vel, "var(--muted)")

    # Growth metrics
    growth_html = ""
    if hi.headcount_growth_12m is not None:
        g12 = hi.headcount_growth_12m
        g_color = "var(--success)" if g12 > 10 else "var(--teal)" if g12 > 0 else "var(--danger)"
        growth_html += (
            f'<div style="padding:16px;background:var(--bg-grey);border-radius:10px;text-align:center">'
            f'<div style="font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">12-Month Growth</div>'
            f'<div style="font-size:1.4rem;font-weight:800;color:{g_color}">{g12:+.1f}%</div></div>'
        )
    if hi.headcount_growth_24m is not None:
        g24 = hi.headcount_growth_24m
        g_color = "var(--success)" if g24 > 15 else "var(--teal)" if g24 > 0 else "var(--danger)"
        growth_html += (
            f'<div style="padding:16px;background:var(--bg-grey);border-radius:10px;text-align:center">'
            f'<div style="font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">24-Month Growth</div>'
            f'<div style="font-size:1.4rem;font-weight:800;color:{g_color}">{g24:+.1f}%</div></div>'
        )

    # Marketing jobs
    mkt_jobs_html = ""
    if hi.marketing_jobs:
        rows = "".join(
            f'<div style="padding:8px 0;border-bottom:1px solid var(--border);font-size:.84rem;display:flex;justify-content:space-between">'
            f'<span style="font-weight:600">{_esc(j.title)}</span>'
            f'<span style="color:var(--muted)">{_esc(j.location or "Remote")}</span></div>'
            for j in hi.marketing_jobs[:8]
        )
        mkt_jobs_html = (
            f'<div style="margin-top:16px">'
            f'<h3 style="font-size:.9rem;color:var(--pink);margin-bottom:10px">Marketing &amp; Growth Roles ({len(hi.marketing_jobs)})</h3>'
            f'{rows}</div>'
        )

    return f"""<section>
  <h2>Hiring &amp; Growth Signals</h2>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:20px">
    <div style="padding:16px;background:var(--bg-grey);border-radius:10px;text-align:center">
      <div style="font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">Open Jobs</div>
      <div style="font-size:1.6rem;font-weight:800;color:var(--navy)">{hi.open_jobs_count}</div>
    </div>
    <div style="padding:16px;background:var(--bg-grey);border-radius:10px;text-align:center">
      <div style="font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">Hiring Velocity</div>
      <div style="font-size:1.1rem;font-weight:700;color:{vel_color}">{vel.title()}</div>
    </div>
    {growth_html}
  </div>
  {mkt_jobs_html}
</section>"""


def _build_news_section(report: DomainAdReport) -> str:
    """Recent News & Media section."""
    news = report.recent_news
    if not news:
        return """<section>
  <h2>Recent News &amp; Media</h2>
  <p style="color:var(--muted);padding:20px 0">No recent news articles found.</p>
</section>"""

    cat_icons = {
        "funding": "&#x1f4b0;",
        "product_launch": "&#x1f680;",
        "partnership": "&#x1f91d;",
        "m_and_a": "&#x1f3e2;",
        "press": "&#x1f4f0;",
        "other": "&#x1f4cc;",
    }

    cat_labels = {
        "funding": "Funding",
        "product_launch": "Product Launch",
        "partnership": "Partnership",
        "m_and_a": "M&A",
        "press": "Press",
        "other": "Other",
    }

    # Category summary pills
    cats: dict[str, int] = {}
    for n in news:
        cats[n.category] = cats.get(n.category, 0) + 1
    cat_pills = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:4px;padding:4px 12px;'
        f'background:var(--bg-grey);border:1px solid var(--border);border-radius:8px;'
        f'font-size:.8rem;font-weight:600">{cat_icons.get(cat, "&#x1f4cc;")} '
        f'{cat_labels.get(cat, cat)} ({count})</span>'
        for cat, count in sorted(cats.items(), key=lambda x: x[1], reverse=True)
    )

    # News cards
    cards = "".join(
        f'<div style="padding:12px 0;border-bottom:1px solid var(--border)">'
        f'<div style="display:flex;align-items:flex-start;gap:10px">'
        f'<span style="font-size:1.1rem">{cat_icons.get(n.category, "&#x1f4cc;")}</span>'
        f'<div style="flex:1;min-width:0">'
        f'<div style="font-size:.88rem;font-weight:600;color:var(--navy)">'
        f'{"<a href=" + chr(34) + _esc(n.url) + chr(34) + " target=" + chr(34) + "_blank" + chr(34) + " style=" + chr(34) + "color:var(--navy);text-decoration:none" + chr(34) + ">" + _esc(n.headline) + "</a>" if n.url else _esc(n.headline)}'
        f'</div>'
        f'<div style="font-size:.75rem;color:var(--muted);margin-top:2px">'
        f'{_esc(n.source or "")}{"  ·  " if n.source and n.date else ""}{_esc(n.date or "")}'
        f'</div></div></div></div>'
        for n in news[:12]
    )

    return f"""<section>
  <h2>Recent News &amp; Media ({len(news)})</h2>
  <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px">{cat_pills}</div>
  {cards}
</section>"""


def _build_podcasts_section(report: DomainAdReport) -> str:
    """Podcasts & Thought Leadership section."""
    pods = report.podcasts
    if not pods:
        return """<section>
  <h2>Podcasts &amp; Thought Leadership</h2>
  <p style="color:var(--muted);padding:20px 0">No podcast or thought leadership appearances found.</p>
</section>"""

    cards = "".join(
        f'<div style="padding:14px;background:var(--bg-grey);border:1px solid var(--border);border-radius:10px">'
        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
        f'<span style="font-size:1.2rem">&#x1f3a7;</span>'
        f'<div style="flex:1">'
        f'<div style="font-size:.88rem;font-weight:700;color:var(--navy)">'
        f'{"<a href=" + chr(34) + _esc(p.url) + chr(34) + " target=" + chr(34) + "_blank" + chr(34) + " style=" + chr(34) + "color:var(--navy);text-decoration:none" + chr(34) + ">" + _esc(p.episode_title) + "</a>" if p.url else _esc(p.episode_title)}'
        f'</div>'
        f'<div style="font-size:.78rem;color:var(--muted)">{_esc(p.show_name)}</div>'
        f'</div></div>'
        f'<div style="font-size:.78rem;color:var(--muted)">'
        f'{_esc(p.person_name)}{"  ·  " + _esc(p.person_title) if p.person_title else ""}'
        f'{"  ·  " + _esc(p.date) if p.date else ""}'
        f'</div></div>'
        for p in pods[:10]
    )

    return f"""<section>
  <h2>Podcasts &amp; Thought Leadership ({len(pods)})</h2>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px">
    {cards}
  </div>
</section>"""


def _build_case_studies_section(report: DomainAdReport) -> str:
    """Platform Case Studies section."""
    studies = report.case_studies
    if not studies:
        return """<section>
  <h2>Platform Case Studies</h2>
  <p style="color:var(--muted);padding:20px 0">No platform case studies found for this brand.</p>
</section>"""

    platform_colors = {
        "Meta": "#1877F2",
        "Google": "#4285F4",
        "TikTok": "#000000",
        "Shopify": "#96BF48",
        "YouTube": "#FF0000",
        "Klaviyo": "#003B5C",
        "Triple Whale": "#0A6D86",
    }

    cards = "".join(
        f'<div style="padding:16px;border:1px solid var(--border);border-radius:12px;'
        f'border-left:4px solid {platform_colors.get(cs.platform, "var(--teal)")}">'
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">'
        f'<span style="font-size:.72rem;font-weight:700;padding:2px 8px;border-radius:4px;'
        f'background:{platform_colors.get(cs.platform, "var(--teal)")};color:white">{_esc(cs.platform)}</span>'
        f'</div>'
        f'<div style="font-size:.9rem;font-weight:700;color:var(--navy);margin-bottom:6px">'
        f'{"<a href=" + chr(34) + _esc(cs.url) + chr(34) + " target=" + chr(34) + "_blank" + chr(34) + " style=" + chr(34) + "color:var(--navy);text-decoration:none" + chr(34) + ">" + _esc(cs.title) + " &rarr;</a>" if cs.url else _esc(cs.title)}'
        f'</div>'
        + (f'<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:6px">'
           + "".join(f'<span style="padding:2px 8px;background:#ECFDF5;color:var(--success);'
                     f'border-radius:4px;font-size:.75rem;font-weight:600">{_esc(m)}</span>' for m in cs.key_metrics[:5])
           + '</div>' if cs.key_metrics else '')
        + (f'<p style="font-size:.82rem;color:var(--muted);line-height:1.5">{_esc(cs.summary)}</p>' if cs.summary else '')
        + '</div>'
        for cs in studies[:8]
    )

    return f"""<section>
  <h2>Platform Case Studies ({len(studies)})</h2>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:12px">
    {cards}
  </div>
</section>"""
