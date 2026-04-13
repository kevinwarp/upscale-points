"""Real-time Pipeline Status Reporter

Emits JSONL events to a status file so a frontend can display live
pipeline progress. Each line is a self-contained JSON object.

Usage:
    status = StatusReporter("example.com", output_dir="output/status")
    status.emit("pipeline_start", label="Starting pipeline...")
    status.step_start("storeleads", "Enriching via Store Leads...")
    status.step_complete("storeleads", "Store Leads complete", data={...})
    status.pipeline_complete(fit_score=84.8, duration_ms=35000)

Events are appended to: output/status/{domain}.jsonl

Frontend polling pattern:
    GET /status/{domain}.jsonl → parse each line as JSON
    Last line with event="pipeline_complete" means done.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

STATUS_DIR = Path(__file__).resolve().parent.parent / "output" / "status"


class StatusReporter:
    """Emits pipeline status events as JSONL for frontend consumption."""

    def __init__(self, domain: str, output_dir: str | Path | None = None):
        self.domain = domain
        self.output_dir = Path(output_dir) if output_dir else STATUS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.status_file = self.output_dir / f"{domain}.jsonl"
        self._step_timers: dict[str, float] = {}
        self._start_time: float | None = None

        # Clear any previous status file for this domain
        if self.status_file.exists():
            self.status_file.unlink()

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _elapsed_ms(self) -> int | None:
        if self._start_time is None:
            return None
        return int((time.monotonic() - self._start_time) * 1000)

    def emit(
        self,
        event: str,
        step: str | None = None,
        label: str = "",
        progress: int = 0,
        duration_ms: int | None = None,
        data: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> dict:
        """Emit a status event. Writes to JSONL file and logs."""
        entry = {
            "ts": self._now_iso(),
            "event": event,
            "domain": self.domain,
            "step": step,
            "label": label,
            "progress": progress,
            "elapsed_ms": self._elapsed_ms(),
        }
        if duration_ms is not None:
            entry["duration_ms"] = duration_ms
        if data:
            entry["data"] = data
        if error:
            entry["error"] = error

        line = json.dumps(entry, default=str)

        # Append to status file
        with open(self.status_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

        # Also log for console visibility
        if event == "step_complete":
            dur = f" ({duration_ms}ms)" if duration_ms else ""
            logger.info(f"[STATUS] {label}{dur}")
        elif event == "step_error":
            logger.error(f"[STATUS] {label}: {error}")
        elif event in ("pipeline_start", "pipeline_complete"):
            logger.info(f"[STATUS] {label}")
        else:
            logger.info(f"[STATUS] {label}")

        return entry

    def pipeline_start(self, label: str | None = None) -> dict:
        """Emit pipeline_start event. Resets all timers."""
        self._start_time = time.monotonic()
        self._step_timers.clear()
        return self.emit(
            "pipeline_start",
            label=label or f"Starting ICP pipeline for {self.domain}",
            progress=0,
        )

    def step_start(self, step: str, label: str, progress: int = 0) -> dict:
        """Emit step_start event and begin timing."""
        self._step_timers[step] = time.monotonic()
        return self.emit("step_start", step=step, label=label, progress=progress)

    def step_complete(
        self,
        step: str,
        label: str,
        progress: int = 0,
        data: dict[str, Any] | None = None,
    ) -> dict:
        """Emit step_complete event with duration."""
        duration_ms = None
        if step in self._step_timers:
            duration_ms = int((time.monotonic() - self._step_timers[step]) * 1000)
            del self._step_timers[step]
        return self.emit(
            "step_complete",
            step=step,
            label=label,
            progress=progress,
            duration_ms=duration_ms,
            data=data,
        )

    def step_error(self, step: str, label: str, error: str, progress: int = 0) -> dict:
        """Emit step_error event."""
        duration_ms = None
        if step in self._step_timers:
            duration_ms = int((time.monotonic() - self._step_timers[step]) * 1000)
            del self._step_timers[step]
        return self.emit(
            "step_error",
            step=step,
            label=label,
            progress=progress,
            duration_ms=duration_ms,
            error=error,
        )

    def pipeline_complete(
        self,
        fit_score: float | None = None,
        fit_grade: str | None = None,
        duration_ms: int | None = None,
        internal_url: str | None = None,
        pitch_url: str | None = None,
    ) -> dict:
        """Emit pipeline_complete event."""
        if duration_ms is None and self._start_time:
            duration_ms = int((time.monotonic() - self._start_time) * 1000)

        data: dict[str, Any] = {}
        if fit_score is not None:
            data["fit_score"] = fit_score
        if fit_grade:
            data["fit_grade"] = fit_grade
        if internal_url:
            data["internal_report_url"] = internal_url
        if pitch_url:
            data["pitch_report_url"] = pitch_url

        return self.emit(
            "pipeline_complete",
            label=f"Pipeline complete for {self.domain}",
            progress=100,
            duration_ms=duration_ms,
            data=data or None,
        )

    def clay_start(self) -> dict:
        """Emit Clay enrichment start."""
        return self.step_start("clay_enrichment", "Starting Clay MCP enrichment...", progress=75)

    def clay_complete(self, data: dict[str, Any] | None = None) -> dict:
        """Emit Clay enrichment complete."""
        return self.step_complete(
            "clay_enrichment",
            "Clay enrichment complete",
            progress=80,
            data=data,
        )

    def reports_start(self) -> dict:
        """Emit report generation start."""
        return self.step_start("reports", "Generating HTML reports...", progress=85)

    def reports_complete(
        self,
        internal_url: str | None = None,
        pitch_url: str | None = None,
    ) -> dict:
        """Emit report generation/upload complete."""
        data = {}
        if internal_url:
            data["internal_url"] = internal_url
        if pitch_url:
            data["pitch_url"] = pitch_url
        return self.step_complete(
            "reports",
            "Reports generated and uploaded",
            progress=90,
            data=data or None,
        )

    def slack_start(self) -> dict:
        """Emit Slack delivery start."""
        return self.step_start("slack", "Sending to #sales...", progress=92)

    def slack_complete(self, message_url: str | None = None) -> dict:
        """Emit Slack delivery complete."""
        data = {"message_url": message_url} if message_url else None
        return self.step_complete("slack", "Slack delivery complete", progress=95, data=data)

    def step_progress(self, step: str, label: str, progress: int = 0, data: dict[str, Any] | None = None) -> dict:
        """Emit a heartbeat/progress update for a running step."""
        duration_ms = None
        if step in self._step_timers:
            duration_ms = int((time.monotonic() - self._step_timers[step]) * 1000)
        return self.emit(
            "step_progress",
            step=step,
            label=label,
            progress=progress,
            duration_ms=duration_ms,
            data=data,
        )

    @staticmethod
    def read_status(domain: str, output_dir: str | Path | None = None) -> list[dict]:
        """Read all status events for a domain. Utility for frontend."""
        d = Path(output_dir) if output_dir else STATUS_DIR
        path = d / f"{domain}.jsonl"
        if not path.exists():
            return []
        events = []
        for line in path.read_text(encoding="utf-8").strip().split("\n"):
            if line:
                events.append(json.loads(line))
        return events

    @staticmethod
    def get_latest_status(domain: str, output_dir: str | Path | None = None) -> dict | None:
        """Get the most recent status event. Utility for frontend."""
        events = StatusReporter.read_status(domain, output_dir)
        return events[-1] if events else None
