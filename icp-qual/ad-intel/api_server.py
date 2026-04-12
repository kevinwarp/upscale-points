"""FastAPI backend bridge for the ICP Qualification Pipeline frontend.

Exposes endpoints that the Next.js app proxies to:
  POST /api/pipeline/start   — kick off a pipeline run
  GET  /api/pipeline/status/{run_id} — poll step-by-step progress
  GET  /api/reports           — list recent completed reports

Runs the Python pipeline as a background asyncio task and streams
status via the existing StatusReporter JSONL files.

Usage:
    uvicorn api_server:app --port 8000 --reload
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("api_server")

app = FastAPI(title="Upscale ICP Pipeline API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory run store ──────────────────────────────────────────
# Maps run_id → run metadata dict
RUNS: dict[str, dict[str, Any]] = {}

STATUS_DIR = Path(__file__).resolve().parent / "output" / "status"
REPORTS_DIR = Path(__file__).resolve().parent / "output" / "reports"


# ── Models ───────────────────────────────────────────────────────

class StartRequest(BaseModel):
    domain: str


class StartResponse(BaseModel):
    runId: str
    domain: str
    status: str


# ── Pipeline runner ──────────────────────────────────────────────

async def _run_pipeline_task(run_id: str, domain: str) -> None:
    """Run the full pipeline in the background.

    Each stage is wrapped individually so errors don't prevent subsequent
    stages from running. Errors are collected and still delivered to Slack.
    """
    RUNS[run_id]["status"] = "running"
    RUNS[run_id]["started_at"] = datetime.now(timezone.utc).isoformat()

    from orchestrator import run_pipeline
    from utils.status_reporter import StatusReporter
    from scoring.upscale_fit import calculate_upscale_fit
    from reports.publisher import publish_reports
    from utils.slack_delivery import build_slack_messages, post_to_slack

    status = StatusReporter(domain, output_dir=str(STATUS_DIR / run_id))
    errors: list[str] = []
    report = None
    call_tracker = None
    fit = None
    internal_url = None
    pitch_url = None

    # ── Stage 1: Pipeline (data collection) ─────────────────────
    try:
        report, call_tracker = await run_pipeline(
            domain=domain,
            headless=True,
            status=status,
        )
    except Exception as e:
        logger.exception(f"Pipeline data collection failed for {run_id}: {e}")
        errors.append(f"Pipeline: {e}")

    # ── Stage 2: Scoring ────────────────────────────────────────
    if report:
        try:
            fit = calculate_upscale_fit(report)
        except Exception as e:
            logger.warning(f"Scoring failed for {run_id}: {e}")
            errors.append(f"Scoring: {e}")

    # ── Stage 3: Report generation & upload ─────────────────────
    if report:
        try:
            result = await publish_reports(report, upload=True, save_local=True)
            internal_url = result.internal.share_url if result.internal else None
            pitch_url = result.pitch.share_url if result.pitch else None
        except Exception as e:
            logger.warning(f"Report publishing failed for {run_id}: {e}")
            errors.append(f"Reports: {e}")

    # ── Stage 4: Slack delivery ─────────────────────────────────
    if report:
        try:
            slack_main, slack_threads = build_slack_messages(
                report, fit,
                internal_url=internal_url,
                pitch_url=pitch_url,
                call_tracker=call_tracker,
            )
            await post_to_slack(slack_main, slack_threads)
        except Exception as e:
            logger.warning(f"Slack delivery failed for {run_id}: {e}")
            errors.append(f"Slack: {e}")

    # ── Final status update ─────────────────────────────────────
    final_status = "done" if report else "error"
    if errors and report:
        final_status = "done"  # partial success — still mark done

    run_update: dict[str, Any] = {
        "status": final_status,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "domain": domain,
    }

    if errors:
        run_update["errors"] = errors
        run_update["error"] = "; ".join(errors)

    if report:
        run_update["company_name"] = report.company_name
        if fit:
            run_update["score"] = fit.total_score
            run_update["grade"] = fit.grade
        run_update["pitch_url"] = pitch_url
        run_update["internal_url"] = internal_url
        try:
            run_update["revenue"] = report.enrichment.estimated_annual_revenue if report.enrichment else None
            run_update["ads_found"] = len(report.ispot_ads.ads) + len(report.youtube_ads.ads) + len(report.meta_ads.ads)
        except Exception:
            run_update["revenue"] = None
            run_update["ads_found"] = 0

    RUNS[run_id].update(run_update)

    try:
        if fit:
            status.pipeline_complete(
                fit_score=fit.total_score,
                fit_grade=fit.grade,
                internal_url=internal_url,
                pitch_url=pitch_url,
            )
        else:
            status.pipeline_complete()
    except Exception:
        pass


# ── Endpoints ────────────────────────────────────────────────────

@app.post("/api/pipeline/start", response_model=StartResponse)
async def start_pipeline(req: StartRequest):
    domain = req.domain.strip().lower()
    if not domain:
        raise HTTPException(status_code=400, detail="Missing domain")

    # Clean domain
    domain = domain.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]

    run_id = f"run-{uuid.uuid4().hex[:12]}"
    RUNS[run_id] = {
        "runId": run_id,
        "domain": domain,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # Kick off pipeline as background task
    asyncio.create_task(_run_pipeline_task(run_id, domain))

    return StartResponse(runId=run_id, domain=domain, status="pending")


@app.get("/api/pipeline/status/{run_id}")
async def pipeline_status(run_id: str):
    if run_id not in RUNS:
        raise HTTPException(status_code=404, detail="Run not found")

    run = RUNS[run_id]

    # Read JSONL status file for step-by-step progress
    status_dir = STATUS_DIR / run_id
    steps = []
    if status_dir.exists():
        jsonl_files = list(status_dir.glob("*.jsonl"))
        if jsonl_files:
            events = []
            for f in jsonl_files:
                for line in f.read_text().splitlines():
                    if line.strip():
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass

            # Build step statuses from events
            step_map: dict[str, dict] = {}
            for evt in events:
                step_name = evt.get("step")
                if step_name:
                    if step_name not in step_map:
                        step_map[step_name] = {
                            "name": step_name,
                            "label": evt.get("label", step_name),
                            "status": "pending",
                        }
                    if evt.get("event") == "step_start":
                        step_map[step_name]["status"] = "running"
                        step_map[step_name]["label"] = evt.get("label", step_name)
                    elif evt.get("event") == "step_complete":
                        step_map[step_name]["status"] = "done"
                        step_map[step_name]["label"] = evt.get("label", step_name)
                        if evt.get("duration_ms"):
                            step_map[step_name]["duration_seconds"] = evt["duration_ms"] / 1000
                        # Pass detail and data through to frontend
                        if evt.get("data"):
                            step_map[step_name]["data"] = evt["data"]
                            if evt["data"].get("detail"):
                                step_map[step_name]["detail"] = evt["data"]["detail"]
                    elif evt.get("event") == "step_error":
                        step_map[step_name]["status"] = "error"
                        step_map[step_name]["detail"] = evt.get("error") or evt.get("label", "")

            steps = list(step_map.values())

    # Compute elapsed seconds
    elapsed_seconds = None
    if run.get("started_at"):
        try:
            started = datetime.fromisoformat(run["started_at"])
            if run.get("completed_at"):
                ended = datetime.fromisoformat(run["completed_at"])
                elapsed_seconds = (ended - started).total_seconds()
            else:
                elapsed_seconds = (datetime.now(timezone.utc) - started).total_seconds()
        except Exception:
            pass

    return {
        **run,
        "steps": steps,
        "elapsed_seconds": elapsed_seconds,
    }


@app.get("/api/reports")
async def list_reports():
    """Return recent pipeline reports for the dashboard."""
    reports = []

    for run_id, run in sorted(RUNS.items(), key=lambda x: x[1].get("created_at", ""), reverse=True):
        if run.get("status") != "done":
            continue
        reports.append({
            "domain": run.get("domain", ""),
            "company_name": run.get("company_name", run.get("domain", "")),
            "score": run.get("score", 0),
            "grade": run.get("grade", ""),
            "revenue": run.get("revenue", "—"),
            "platform": "",
            "ads_found": run.get("ads_found", 0),
            "pitch_url": run.get("pitch_url"),
            "internal_url": run.get("internal_url"),
            "generated_at": run.get("completed_at", run.get("created_at", "")),
            "duration_seconds": 0,
        })

    return reports[:20]


@app.get("/health")
async def health():
    return {"status": "ok", "runs": len(RUNS)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
