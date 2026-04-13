"""Script Automation Platform – Voiceover Generation

Calls the Script Automation API to generate AI voiceover audio files for a domain.
Returns a list of audio file dicts with voice, url, voice_id, and script metadata.

API: POST /generate → poll GET /status/:run_id → audio MP3 URLs (signed, 7-day expiry)
Primary voice: Chanelle (warm, conversational female) always included.
"""

import asyncio
import logging
import os
import time

import httpx

logger = logging.getLogger(__name__)

SCRIPT_API_BASE = os.getenv(
    "SCRIPT_AUTOMATION_API_URL",
    "https://script-automation-backend-irqcwi2a7q-uc.a.run.app",
)
SCRIPT_API_KEY = os.getenv(
    "SCRIPT_AUTOMATION_API_KEY",
    "2a9c5a2c212089920940b1fd67057a5fe588d6b5c3ebd4ab648d1a7cf230dc51",
)

# Defaults
DEFAULT_VOICE_COUNT = 4
DEFAULT_VOICE_KEYWORDS = ["female", "warm"]
POLL_INTERVAL = 10  # seconds
MAX_POLL_TIME = 600  # 10 minutes


async def generate_voiceover(
    domain: str,
    voice_count: int = DEFAULT_VOICE_COUNT,
    voice_keywords: list[str] | None = None,
) -> dict:
    """Start voiceover generation and poll until completion.

    Returns:
        dict with keys: run_id, status, audio_files, scripts, error
    """
    if not SCRIPT_API_KEY:
        logger.warning("SCRIPT_AUTOMATION_API_KEY not set — skipping voiceover generation")
        return {"run_id": "", "status": "skipped", "audio_files": [], "scripts": [], "error": "API key not configured"}

    keywords = voice_keywords or DEFAULT_VOICE_KEYWORDS
    headers = {
        "Authorization": f"Bearer {SCRIPT_API_KEY}",
        "Content-Type": "application/json",
    }

    result = {
        "run_id": "",
        "status": "pending",
        "audio_files": [],
        "scripts": [],
        "error": None,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # 1. Start generation
            resp = await client.post(
                f"{SCRIPT_API_BASE}/generate",
                headers=headers,
                json={
                    "domain": domain,
                    "voice_count": voice_count,
                    "voice_keywords": keywords,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            run_id = data.get("run_id", "")
            result["run_id"] = run_id
            logger.info(f"Voiceover generation started: run_id={run_id}")

            if not run_id:
                result["status"] = "error"
                result["error"] = "No run_id returned from API"
                return result

            # 2. Poll for completion
            start = time.monotonic()
            while time.monotonic() - start < MAX_POLL_TIME:
                await asyncio.sleep(POLL_INTERVAL)

                status_resp = await client.get(
                    f"{SCRIPT_API_BASE}/status/{run_id}",
                    headers={"Authorization": f"Bearer {SCRIPT_API_KEY}"},
                )
                status_resp.raise_for_status()
                status_data = status_resp.json()

                current_status = status_data.get("status", "unknown")
                result["status"] = current_status

                if current_status == "complete":
                    result["audio_files"] = status_data.get("audio_files", [])
                    result["scripts"] = status_data.get("scripts", [])
                    elapsed = round(time.monotonic() - start, 1)
                    logger.info(
                        f"Voiceover complete: {len(result['audio_files'])} audio files in {elapsed}s"
                    )
                    return result

                if current_status == "failed":
                    result["error"] = status_data.get("error", "Unknown error")
                    logger.error(f"Voiceover generation failed: {result['error']}")
                    return result

                # Log progress
                logs = status_data.get("logs", [])
                if logs:
                    latest = logs[-1]
                    logger.debug(
                        f"Voiceover [{run_id[:8]}]: {latest.get('step')} — {latest.get('message')}"
                    )

            # Timed out
            result["status"] = "timeout"
            result["error"] = f"Voiceover generation timed out after {MAX_POLL_TIME}s"
            logger.warning(result["error"])

    except httpx.HTTPStatusError as e:
        result["status"] = "error"
        result["error"] = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        logger.error(f"Voiceover API error: {result['error']}")
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        logger.error(f"Voiceover generation error: {e}")

    return result
