"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import { Header } from "@/components/header";
import { Footer } from "@/components/footer";
import { Logo } from "@/components/logo";

interface StepStatus {
  name: string;
  label: string;
  status: "pending" | "running" | "done" | "error";
  detail?: string;
  duration_seconds?: number;
}

interface RunState {
  runId: string;
  domain: string;
  status: "pending" | "running" | "done" | "error";
  steps: StepStatus[];
  pitch_url?: string;
  internal_url?: string;
  error?: string;
}

const PIPELINE_STEPS: { name: string; label: string }[] = [
  { name: "storeleads", label: "StoreLeads enrichment" },
  { name: "clay", label: "Clay enrichment" },
  { name: "apollo", label: "Apollo contacts" },
  { name: "crunchbase", label: "Crunchbase funding" },
  { name: "ispot", label: "iSpot TV ads" },
  { name: "youtube", label: "YouTube ad library" },
  { name: "meta", label: "Meta ad library" },
  { name: "milled", label: "Milled email intel" },
  { name: "competitor", label: "Competitor analysis" },
  { name: "scoring", label: "ICP fit scoring" },
  { name: "voiceover", label: "AI voiceover generation" },
  { name: "pitch_report", label: "Pitch report" },
  { name: "internal_report", label: "Internal report" },
  { name: "slack", label: "Slack delivery" },
];

function statusIcon(status: string) {
  switch (status) {
    case "done":
      return (
        <svg className="w-5 h-5 text-[var(--success)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
        </svg>
      );
    case "running":
      return <span className="w-5 h-5 flex items-center justify-center"><span className="pulse-dot" /></span>;
    case "error":
      return (
        <svg className="w-5 h-5 text-[var(--danger)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
        </svg>
      );
    default:
      return <span className="w-5 h-5 rounded-full border-2 border-[var(--border)]" />;
  }
}

function buildMockSteps(): StepStatus[] {
  return PIPELINE_STEPS.map((s) => ({
    ...s,
    status: "pending" as const,
  }));
}

export default function RunPage() {
  const { runId } = useParams<{ runId: string }>();
  const [run, setRun] = useState<RunState>({
    runId: runId || "",
    domain: "",
    status: "pending",
    steps: buildMockSteps(),
  });
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // If this is a mock run (no backend), simulate step progression
  const isMock = runId?.startsWith("dev-");

  useEffect(() => {
    if (isMock) {
      // Simulate pipeline steps every 2s
      let idx = 0;
      setRun((prev) => ({
        ...prev,
        domain: "demo-domain.com",
        status: "running",
      }));

      intervalRef.current = setInterval(() => {
        setRun((prev) => {
          const steps = [...prev.steps];
          // Complete current step
          if (idx > 0 && steps[idx - 1]) {
            steps[idx - 1] = {
              ...steps[idx - 1],
              status: "done",
              duration_seconds: Math.round(Math.random() * 20 + 2),
            };
          }
          // Start next step
          if (idx < steps.length) {
            steps[idx] = { ...steps[idx], status: "running" };
          }

          const allDone = idx >= steps.length;
          if (allDone && intervalRef.current) {
            clearInterval(intervalRef.current);
          }

          return {
            ...prev,
            steps,
            status: allDone ? "done" : "running",
            pitch_url: allDone
              ? "https://upscale-reports-ghy5squ27q-uc.a.run.app/p/8de8cd5e1e31?passcode=923271"
              : undefined,
            internal_url: allDone
              ? "https://upscale-reports-ghy5squ27q-uc.a.run.app/p/d0126d118677?passcode=759748"
              : undefined,
          };
        });
        idx++;
      }, 2000);

      return () => {
        if (intervalRef.current) clearInterval(intervalRef.current);
      };
    }

    // Real polling
    async function poll() {
      try {
        const res = await fetch(`/api/pipeline/status/${runId}`);
        if (res.ok) {
          const data = await res.json();
          setRun(data);
          if (data.status === "done" || data.status === "error") {
            if (intervalRef.current) clearInterval(intervalRef.current);
          }
        }
      } catch {
        // Keep polling
      }
    }

    poll();
    intervalRef.current = setInterval(poll, 3000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [runId, isMock]);

  const completedCount = run.steps.filter((s) => s.status === "done").length;
  const progress = Math.round((completedCount / run.steps.length) * 100);

  return (
    <div className="flex flex-col min-h-screen bg-white">
      <Header />
      <main className="flex-1 py-12 px-6">
        <div className="max-w-3xl mx-auto">
          {/* Run header */}
          <div className="flex items-center gap-4 mb-8">
            <div className="w-12 h-12 rounded-lg bg-[var(--navy)] flex items-center justify-center">
              <Logo size="small" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-[var(--navy)]">
                Pipeline run
              </h1>
              <p className="text-sm text-[var(--muted)]">
                {run.domain || runId}{" "}
                <span className="ml-2 text-xs font-mono text-[var(--muted)]">
                  {runId}
                </span>
              </p>
            </div>
          </div>

          {/* Progress bar */}
          <div className="card mb-8">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-semibold text-[var(--navy)]">
                {run.status === "done"
                  ? "Complete"
                  : run.status === "error"
                    ? "Error"
                    : "Running..."}
              </span>
              <span className="text-sm font-bold text-[var(--pink)]">
                {progress}%
              </span>
            </div>
            <div className="w-full h-2 bg-[var(--bg-grey)] rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${progress}%`,
                  background:
                    run.status === "error"
                      ? "var(--danger)"
                      : "linear-gradient(90deg, var(--pink), var(--teal))",
                }}
              />
            </div>
            <p className="text-xs text-[var(--muted)] mt-2">
              {completedCount} of {run.steps.length} steps completed
            </p>
          </div>

          {/* Steps list */}
          <div className="card">
            <h2 className="text-base font-semibold text-[var(--navy)] mb-4">
              Pipeline steps
            </h2>
            <div className="space-y-1">
              {run.steps.map((step, i) => (
                <div
                  key={step.name}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                    step.status === "running"
                      ? "bg-[var(--pink-light)]"
                      : step.status === "done"
                        ? "bg-[var(--bg-grey)]"
                        : ""
                  }`}
                >
                  {statusIcon(step.status)}
                  <span className="text-xs font-bold text-[var(--pink)] w-6">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span
                    className={`text-sm flex-1 ${
                      step.status === "done"
                        ? "text-[var(--muted)]"
                        : step.status === "running"
                          ? "text-[var(--navy)] font-semibold"
                          : "text-[var(--navy)]"
                    }`}
                  >
                    {step.label}
                  </span>
                  {step.duration_seconds != null && (
                    <span className="text-xs text-[var(--muted)]">
                      {step.duration_seconds.toFixed(0)}s
                    </span>
                  )}
                  {step.status === "running" && (
                    <span className="text-xs text-[var(--pink)] font-medium animate-pulse">
                      processing
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Report links — shown when done */}
          {run.status === "done" && (run.pitch_url || run.internal_url) && (
            <div className="card mt-6 bg-[var(--pink-light)] border-[var(--pink)]">
              <h2 className="text-base font-semibold text-[var(--pink)] mb-4">
                Reports ready
              </h2>
              <div className="flex gap-4">
                {run.pitch_url && (
                  <a
                    href={run.pitch_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-pink text-sm"
                  >
                    View pitch report
                  </a>
                )}
                {run.internal_url && (
                  <a
                    href={run.internal_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-teal text-sm"
                  >
                    View internal report
                  </a>
                )}
              </div>
            </div>
          )}

          {/* Error state */}
          {run.status === "error" && run.error && (
            <div className="card mt-6 bg-[var(--danger-light)] border-[var(--danger)]">
              <h2 className="text-base font-semibold text-[var(--danger)] mb-2">
                Pipeline error
              </h2>
              <p className="text-sm text-[var(--navy)]">{run.error}</p>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
