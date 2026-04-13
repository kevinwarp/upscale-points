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

# ── Persistent run store ─────────────────────────────────────────
# Maps run_id → run metadata dict. Persisted to disk as JSON so runs
# survive server restarts (uvicorn --reload, crashes, etc.).

STATUS_DIR = Path(__file__).resolve().parent / "output" / "status"
REPORTS_DIR = Path(__file__).resolve().parent / "output" / "reports"
RUNS_FILE = Path(__file__).resolve().parent / "output" / "runs.json"


def _load_runs() -> dict[str, dict[str, Any]]:
    """Load runs from disk. Returns empty dict if file doesn't exist."""
    if RUNS_FILE.exists():
        try:
            data = json.loads(RUNS_FILE.read_text())
            # Mark any previously "running" runs as interrupted
            for run_id, run in data.items():
                if run.get("status") == "running":
                    run["status"] = "error"
                    run["error"] = "Server restarted while pipeline was running"
                    run.setdefault("errors", []).append("Server restart interrupted pipeline")
            logger.info(f"Loaded {len(data)} runs from disk")
            return data
        except Exception as e:
            logger.warning(f"Could not load runs.json: {e}")
    return {}


def _save_runs() -> None:
    """Persist current runs to disk."""
    try:
        RUNS_FILE.parent.mkdir(parents=True, exist_ok=True)
        RUNS_FILE.write_text(json.dumps(RUNS, indent=2, default=str))
    except Exception as e:
        logger.warning(f"Could not save runs.json: {e}")


RUNS: dict[str, dict[str, Any]] = _load_runs()


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
    Top-level try/except ensures any uncaught error still marks the run as failed.
    """
    try:
        RUNS[run_id]["status"] = "running"
        RUNS[run_id]["started_at"] = datetime.now(timezone.utc).isoformat()
        _save_runs()

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

        # ── Stage 2b: Save report JSON for regeneration ────────────
        if report:
            try:
                from utils.json_formatter import save_report
                save_report(report, filename=f"{domain}_report.json")
            except Exception as e:
                logger.warning(f"Report JSON save failed for {run_id}: {e}")

        # ── Stage 3: Report generation & upload ─────────────────────
        pitch_failed_sections = []
        if report:
            status.step_start("reports", "Generating reports...", progress=85)
            try:
                result = await publish_reports(report, upload=True, save_local=True)
                internal_url = result.internal.share_url if result.internal else None
                pitch_url = result.pitch.share_url if result.pitch else None
                pitch_failed_sections = result.pitch_failed_sections or []
                detail = []
                if internal_url:
                    detail.append("Internal")
                if pitch_url:
                    detail.append("Pitch")
                status.step_complete("reports", f"Reports: {' + '.join(detail) or 'generated'} uploaded", progress=90, data={
                    "internal_url": internal_url,
                    "pitch_url": pitch_url,
                })
            except Exception as e:
                logger.warning(f"Report publishing failed for {run_id}: {e}")
                errors.append(f"Reports: {e}")
                status.step_error("reports", "Report generation failed", error=str(e), progress=90)
        else:
            status.step_start("reports", "Skipped — no report data", progress=85)
            status.step_complete("reports", "Skipped — no report data", progress=90)

        # ── Stage 4: Slack delivery (always runs, even on error) ────
        status.step_start("slack", "Sending Slack notification...", progress=92)
        try:
            slack_main = None
            slack_threads = []
            if report and fit:
                try:
                    slack_main, slack_threads = build_slack_messages(
                        report, fit,
                        internal_url=internal_url,
                        pitch_url=pitch_url,
                        call_tracker=call_tracker,
                        pitch_failed_sections=pitch_failed_sections if pitch_failed_sections else None,
                    )
                except Exception as msg_err:
                    logger.warning(f"build_slack_messages failed for {run_id}: {msg_err}")
                    errors.append(f"Slack message build: {msg_err}")
            if not slack_main:
                # Fallback: simple message when pipeline failed or message build crashed
                error_summary = "; ".join(errors) if errors else "Unknown error"
                score_line = f"\n*Score: {fit.total_score}/100 ({fit.grade})*" if fit else ""
                slack_main = (
                    f":{'warning' if report else 'x'}: *ICP Qualification {'Partial' if report else 'Failed'}: {domain}*"
                    f"{score_line}\n"
                    f"\n"
                    f"*Errors:*\n"
                    f"```{error_summary}```\n"
                    f"_Run ID: {run_id}_"
                )
                if internal_url:
                    slack_threads.append(f":memo: <{internal_url}|Internal Report>")
                if pitch_url:
                    slack_threads.append(f":dart: <{pitch_url}|Pitch Report>")
            await post_to_slack(slack_main, slack_threads)
            status.step_complete("slack", "Slack notification sent", progress=95)
        except Exception as e:
            logger.warning(f"Slack delivery failed for {run_id}: {e}")
            errors.append(f"Slack: {e}")
            status.step_error("slack", "Slack delivery failed", error=str(e), progress=95)

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
        _save_runs()

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

    except Exception as e:
        # Catch-all: any uncaught error marks run as failed
        logger.exception(f"FATAL: Pipeline task crashed for {run_id}: {e}")
        RUNS[run_id].update({
            "status": "error",
            "error": f"Fatal error: {e}",
            "errors": [f"Fatal: {e}"],
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
        _save_runs()


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
    _save_runs()

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
                    elif evt.get("event") == "step_progress":
                        # Heartbeat: update label but keep status as running
                        step_map[step_name]["label"] = evt.get("label", step_map[step_name].get("label", step_name))
                        if evt.get("duration_ms"):
                            step_map[step_name]["duration_seconds"] = evt["duration_ms"] / 1000
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


SLACK_PENDING_DIR = Path(__file__).resolve().parent / "output" / "slack_pending"


@app.get("/api/slack/pending")
async def list_pending_slack():
    """List Slack messages awaiting MCP delivery."""
    if not SLACK_PENDING_DIR.exists():
        return []
    pending = []
    for f in sorted(SLACK_PENDING_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            if data.get("status") == "pending":
                data["filename"] = f.name
                pending.append(data)
        except Exception:
            pass
    return pending


@app.post("/api/slack/sent/{filename}")
async def mark_slack_sent(filename: str, permalink: str = ""):
    """Mark a pending Slack message as sent (called after MCP delivery)."""
    filepath = SLACK_PENDING_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Pending message not found")
    data = json.loads(filepath.read_text())
    data["status"] = "sent"
    data["sent_at"] = datetime.now(timezone.utc).isoformat()
    if permalink:
        data["permalink"] = permalink
    filepath.write_text(json.dumps(data, indent=2))
    return {"ok": True}


class RegenPitchRequest(BaseModel):
    domain: str
    config: dict = {}


@app.post("/api/pitch/regenerate")
async def regenerate_pitch(req: RegenPitchRequest):
    """Regenerate a pitch report with custom config overrides."""
    domain = req.domain.strip().lower().replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
    if not domain:
        raise HTTPException(status_code=400, detail="Missing domain")

    # Find the most recent completed run for this domain
    matching_run = None
    for run_id, run in sorted(RUNS.items(), key=lambda x: x[1].get("created_at", ""), reverse=True):
        if run.get("domain") == domain and run.get("status") == "done":
            matching_run = run
            break

    if not matching_run:
        raise HTTPException(status_code=404, detail=f"No completed run found for {domain}")

    try:
        from reports.pitch_report import generate_pitch_report, PitchConfig
        from reports.publisher import upload_html_to_platform
        from scoring.upscale_fit import calculate_upscale_fit

        # Load the saved report data
        report_path = REPORTS_DIR / f"{domain}_report.json"
        if not report_path.exists():
            raise HTTPException(status_code=404, detail=f"Report data not found for {domain}. Run the pipeline again.")

        from models.ad_models import DomainAdReport
        report = DomainAdReport.model_validate_json(report_path.read_text())

        # If company_name is overridden, try to load creative pipeline data from that company's report
        cfg_company = req.config.get("company_name", "")
        if cfg_company:
            # Try common domain patterns for the overridden company
            for alt_domain in [f"{cfg_company.lower().replace(' ', '')}.com", f"{cfg_company.lower()}.com"]:
                alt_path = REPORTS_DIR / f"{alt_domain}_report.json"
                if alt_path.exists():
                    try:
                        alt_report = DomainAdReport.model_validate_json(alt_path.read_text())
                        # Merge ALL data from the alt company's report
                        if alt_report.creative_pipeline and alt_report.creative_pipeline.found:
                            report.creative_pipeline = alt_report.creative_pipeline
                        if alt_report.enrichment:
                            report.enrichment = alt_report.enrichment
                        if alt_report.channel_mix:
                            report.channel_mix = alt_report.channel_mix
                        if alt_report.brand_intel:
                            report.brand_intel = alt_report.brand_intel
                        if alt_report.milled_intel:
                            report.milled_intel = alt_report.milled_intel
                        if alt_report.recent_news:
                            report.recent_news = alt_report.recent_news
                        # Merge ad platform data and audio files
                        report.meta_ads = alt_report.meta_ads
                        report.ispot_ads = alt_report.ispot_ads
                        report.youtube_ads = alt_report.youtube_ads
                        report.audio_files = alt_report.audio_files
                        report.company_name = alt_report.company_name or cfg_company
                        logger.info(f"Merged full report data from {alt_domain}")
                        break
                    except Exception as e:
                        logger.warning(f"Failed to load alt report {alt_domain}: {e}")

        fit = calculate_upscale_fit(report)

        # Build PitchConfig from request
        config = PitchConfig.from_dict(req.config)

        # Generate pitch HTML with overrides
        pitch_html, failed_sections = generate_pitch_report(report, fit, config=config)

        # Upload
        resp = await upload_html_to_platform(pitch_html, f"{domain}_streaming_proposal.html")
        if resp:
            pitch_url = resp["shareUrl"]
            # Update run data
            matching_run["pitch_url"] = pitch_url
            if failed_sections:
                matching_run["pitch_failed_sections"] = failed_sections
            _save_runs()
            result = {"ok": True, "pitch_url": pitch_url}
            if failed_sections:
                result["failed_sections"] = failed_sections
            return result
        else:
            return {"ok": False, "error": "Upload failed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Pitch regeneration failed for {domain}: {e}")
        return {"ok": False, "error": str(e)}


@app.get("/health")
async def health():
    return {"status": "ok", "runs": len(RUNS)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
