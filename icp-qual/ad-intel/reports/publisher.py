"""Report Publisher

Generates both ICP internal and external pitch HTML reports, then uploads them
to the upscale-reports platform via its API. Returns shareable URLs with passcodes.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

import httpx

from models.ad_models import DomainAdReport
from reports.internal_report import generate_internal_report
from reports.pitch_report import generate_pitch_report
from scoring.upscale_fit import UpscaleFitResult, calculate_upscale_fit

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "reports"


@dataclass
class PublishedReport:
    report_type: str  # "internal" or "pitch"
    slug: str
    passcode: str
    url: str
    share_url: str


@dataclass
class PublishResult:
    domain: str
    company_name: str | None
    fit_score: float
    fit_grade: str
    internal: PublishedReport | None = None
    pitch: PublishedReport | None = None
    error: str | None = None


async def upload_html_to_platform(
    html_content: str,
    filename: str,
    api_url: str | None = None,
    api_key: str | None = None,
) -> dict | None:
    """Upload an HTML report to the upscale-reports platform.

    Returns the API response dict: {slug, passcode, url, shareUrl}
    """
    api_url = api_url or os.getenv(
        "UPSCALE_REPORTS_API_URL",
        "https://upscale-reports-ghy5squ27q-uc.a.run.app",
    )
    api_key = api_key or os.getenv(
        "UPSCALE_REPORTS_API_KEY",
        "4cdd062eb10920882324a9c53a5d02a4af787c53879beac09f9e18174395c6fb",
    )

    if not api_key:
        logger.warning("UPSCALE_REPORTS_API_KEY not set — skipping upload")
        return None

    upload_url = f"{api_url.rstrip('/')}/api/upload"

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            upload_url,
            headers={"Authorization": f"Bearer {api_key}"},
            files={"report": (filename, html_content.encode("utf-8"), "text/html")},
        )
        resp.raise_for_status()
        return resp.json()


async def publish_reports(
    report: DomainAdReport,
    upload: bool = True,
    save_local: bool = True,
) -> PublishResult:
    """Generate and optionally upload both internal and pitch reports.

    Args:
        report: The completed DomainAdReport from the pipeline.
        upload: Whether to upload to upscale-reports platform.
        save_local: Whether to save HTML files locally.

    Returns:
        PublishResult with URLs for both reports.
    """
    # Score the brand
    fit = calculate_upscale_fit(report)
    domain = report.domain
    company = report.company_name or domain

    result = PublishResult(
        domain=domain,
        company_name=company,
        fit_score=fit.total_score,
        fit_grade=fit.grade,
    )

    # Generate HTML reports — each independently so one failure doesn't block the other
    internal_html = None
    pitch_html = None

    try:
        logger.info(f"Generating internal ICP report for {domain}...")
        internal_html = generate_internal_report(report, fit)
    except Exception as e:
        logger.error(f"Internal report generation failed for {domain}: {e}")
        result.error = f"Internal report generation failed: {e}"

    try:
        logger.info(f"Generating pitch report for {domain}...")
        pitch_html = generate_pitch_report(report, fit)
    except Exception as e:
        logger.error(f"Pitch report generation failed for {domain}: {e}")
        err = f"Pitch report generation failed: {e}"
        result.error = f"{result.error}; {err}" if result.error else err

    # Save locally
    if save_local:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        if internal_html:
            internal_path = OUTPUT_DIR / f"{domain}_internal.html"
            internal_path.write_text(internal_html, encoding="utf-8")
            logger.info(f"Saved local internal report: {internal_path}")
        if pitch_html:
            pitch_path = OUTPUT_DIR / f"{domain}_pitch.html"
            pitch_path.write_text(pitch_html, encoding="utf-8")
            logger.info(f"Saved local pitch report: {pitch_path}")

    # Upload to platform
    if upload:
        internal_resp = None
        if not internal_html:
            logger.warning("Skipping internal report upload — generation failed")
        try:
            if internal_html:
                logger.info(f"Uploading internal report for {domain}...")
                internal_resp = await upload_html_to_platform(
                    internal_html,
                    f"{domain}_icp_report.html",
                )
                if internal_resp:
                    result.internal = PublishedReport(
                        report_type="internal",
                        slug=internal_resp["slug"],
                        passcode=internal_resp["passcode"],
                        url=internal_resp["url"],
                        share_url=internal_resp["shareUrl"],
                    )
                    logger.info(f"Internal report uploaded: {result.internal.share_url}")
        except Exception as e:
            logger.error(f"Failed to upload internal report: {e}")
            result.error = f"Internal upload failed: {e}"

        pitch_resp = None
        try:
            if not pitch_html:
                logger.warning("Skipping pitch report upload — generation failed")
            else:
                logger.info(f"Uploading pitch report for {domain}...")
                pitch_resp = await upload_html_to_platform(
                    pitch_html,
                    f"{domain}_streaming_proposal.html",
                )
            if pitch_resp:
                result.pitch = PublishedReport(
                    report_type="pitch",
                    slug=pitch_resp["slug"],
                    passcode=pitch_resp["passcode"],
                    url=pitch_resp["url"],
                    share_url=pitch_resp["shareUrl"],
                )
                logger.info(f"Pitch report uploaded: {result.pitch.share_url}")
        except Exception as e:
            logger.error(f"Failed to upload pitch report: {e}")
            if result.error:
                result.error += f"; Pitch upload failed: {e}"
            else:
                result.error = f"Pitch upload failed: {e}"

    return result
