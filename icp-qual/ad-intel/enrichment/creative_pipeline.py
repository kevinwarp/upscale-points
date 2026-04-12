"""Creative Pipeline Client

Integrates with upscale.ai's Creative Pipeline API (tvads-api) to generate
AI-powered ad creatives for a brand. The pipeline:

  1. POST /api/v1/generate  — kicks off brand research + concept + script + video generation
  2. GET  /api/v1/jobs/{id}  — polls until complete (up to ~20 min)

Returns brand brief, script, image URLs, and video URLs from multiple providers
(Veo 3 x2 takes + Higgsfield).
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

API_BASE = "https://tvads-api-irqcwi2a7q-uc.a.run.app"

# Polling config
POLL_INTERVAL_SECS = 10       # seconds between polls
MAX_POLL_DURATION_SECS = 600   # 10 minutes max wait (script+images ~3-5 min)


@dataclass
class CreativeResult:
    """Result from the Creative Pipeline."""
    job_id: str = ""
    status: str = ""              # pending, processing, complete, error, timeout
    # Brand intelligence
    brand_name: str = ""
    brand_url: str = ""
    brand_brief: str = ""
    # Script
    script: str = ""
    # Assets
    image_urls: list[str] = field(default_factory=list)
    video_urls: dict[str, list[str]] = field(default_factory=dict)  # provider -> [urls]
    voiceover_url: str = ""
    # Documents
    docx_url: str = ""
    zip_url: str = ""
    # Progress tracking
    current_step: str = ""
    progress_message: str = ""
    # Meta
    error: str | None = None
    error_code: str | None = None
    elapsed_seconds: float = 0
    created_at: str = ""


async def generate_creative(
    domain: str,
    platform: str = "CTV",
    ad_type: str = "unskippable",
    duration_seconds: int = 30,
    aspect_ratio: str = "16:9",
    generate_videos: bool = False,
    target_audience: str | None = None,
    custom_prompt: str | None = None,
    api_key: str | None = None,
) -> CreativeResult:
    """Kick off the Creative Pipeline and poll until complete.

    Args:
        domain: Brand domain (e.g. "tartecosmetics.com").
        platform: Target platform (CTV, YouTube In-Stream, etc.).
        ad_type: Ad format (unskippable, skippable, bumper-6s).
        duration_seconds: Target ad duration.
        aspect_ratio: Video aspect ratio (16:9, 9:16, 1:1).
        generate_videos: If False, returns script + images only (~2 min).
                         If True, generates full videos (~20 min).
        target_audience: Optional audience description.
        custom_prompt: Optional creative direction.
        api_key: API key (falls back to TVADS_API_KEY env var).

    Returns:
        CreativeResult with brand brief, script, image/video URLs, etc.
    """
    api_key = api_key or os.getenv("TVADS_API_KEY")
    if not api_key:
        logger.warning("TVADS_API_KEY not set — skipping creative pipeline")
        return CreativeResult(error="TVADS_API_KEY not configured")

    start = time.monotonic()
    result = CreativeResult()

    # Ensure URL format
    url = domain if domain.startswith("http") else f"https://{domain}"

    # Build request payload
    payload: dict = {
        "url": url,
        "platform": platform,
        "ad_type": ad_type,
        "duration_seconds": duration_seconds,
        "aspect_ratio": aspect_ratio,
        "generate_videos": generate_videos,
        "slack_notify": False,
    }
    if target_audience:
        payload["target_audience"] = target_audience
    if custom_prompt:
        payload["custom_prompt"] = custom_prompt

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            # Step 1: Start generation
            logger.info(f"Creative Pipeline: starting generation for {domain}...")
            resp = await client.post(
                f"{API_BASE}/api/v1/generate",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            start_data = resp.json()

            result.job_id = start_data.get("job_id", "")
            result.status = start_data.get("status", "pending")
            logger.info(
                f"Creative Pipeline: job {result.job_id} started "
                f"(status: {result.status})"
            )

            if not result.job_id:
                result.error = "No job_id returned from API"
                return result

            # Step 2: Poll until complete
            poll_start = time.monotonic()
            while time.monotonic() - poll_start < MAX_POLL_DURATION_SECS:
                await asyncio.sleep(POLL_INTERVAL_SECS)

                try:
                    poll_resp = await client.get(
                        f"{API_BASE}/api/v1/jobs/{result.job_id}",
                        headers=headers,
                    )
                    poll_resp.raise_for_status()
                    job_data = poll_resp.json()
                except httpx.HTTPError as poll_err:
                    logger.warning(f"Creative Pipeline: poll error: {poll_err}")
                    continue

                status = job_data.get("status", "")
                step = job_data.get("step", "")
                progress = job_data.get("progress", "")
                elapsed = round(time.monotonic() - poll_start)

                result.current_step = step
                result.progress_message = progress

                logger.info(
                    f"Creative Pipeline: [{elapsed}s] status={status} "
                    f"step={step} {progress}"
                )

                if status == "complete":
                    result.status = "complete"
                    _extract_result(result, job_data)
                    break
                elif status == "error":
                    result.status = "error"
                    result.error = job_data.get("error", "Unknown error")
                    result.error_code = job_data.get("error_code")
                    # Extract partial data even on error (brief/script may exist)
                    _extract_result(result, job_data)
                    break

                result.status = status

            else:
                # Timed out
                result.status = "timeout"
                result.error = f"Timed out after {MAX_POLL_DURATION_SECS}s"
                logger.warning(f"Creative Pipeline: {result.error}")

    except httpx.HTTPStatusError as e:
        result.error = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        logger.error(f"Creative Pipeline: {result.error}")
    except Exception as e:
        result.error = str(e)
        logger.error(f"Creative Pipeline: unexpected error: {e}")

    result.elapsed_seconds = round(time.monotonic() - start, 1)
    logger.info(
        f"Creative Pipeline: done in {result.elapsed_seconds}s "
        f"(status: {result.status})"
    )
    return result


def _extract_result(result: CreativeResult, job_data: dict) -> None:
    """Extract fields from the completed job response."""
    # Brand info
    brand = job_data.get("brand", {}) or {}
    result.brand_name = brand.get("name", "")
    result.brand_url = brand.get("url", "")
    result.brand_brief = brand.get("brief", "") or ""

    # Script
    result.script = job_data.get("script", "") or ""

    # Assets
    assets = job_data.get("assets", {}) or {}
    result.image_urls = assets.get("images", []) or []
    result.video_urls = assets.get("videos", {}) or {}
    result.voiceover_url = assets.get("voiceover", "") or ""

    # Documents
    docs = assets.get("documents", {}) or {}
    result.docx_url = docs.get("docx", "") or ""
    result.zip_url = docs.get("zip", "") or ""

    # Timestamps
    result.created_at = job_data.get("created_at", "")
