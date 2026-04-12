"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useParams } from "next/navigation";
import { Header } from "@/components/header";
import { Footer } from "@/components/footer";
import { Logo } from "@/components/logo";

/* ── Types ──────────────────────────────────────────────────── */

interface StepStatus {
  name: string;
  label: string;
  status: "pending" | "running" | "done" | "error";
  detail?: string;
  duration_seconds?: number;
  data?: Record<string, unknown>;
}

interface RunState {
  runId: string;
  domain: string;
  status: "pending" | "running" | "done" | "error";
  steps: StepStatus[];
  pitch_url?: string;
  internal_url?: string;
  error?: string;
  company_name?: string;
  score?: number;
  grade?: string;
  elapsed_seconds?: number;
}

/* ── Pipeline steps (Phase 1 + Phase 2) ─────────────────────── */

interface StepDef {
  name: string;
  label: string;
  phase: 1 | 2;
  icon: string;
}

const PIPELINE_STEPS: StepDef[] = [
  // Phase 1 — Core Intelligence
  { name: "storeleads", label: "1. StoreLeads enrichment", phase: 1, icon: "🏪" },
  { name: "company_pulse", label: "2. CRM data lookup", phase: 1, icon: "💼" },
  { name: "contact_search", label: "3. Contact discovery", phase: 1, icon: "👥" },
  { name: "clay_enrichment", label: "4. Clay enrichment + jobs", phase: 1, icon: "🧱" },
  { name: "creative_pipeline", label: "5. AI creative generation", phase: 1, icon: "🎨" },
  { name: "voiceover", label: "6. AI voiceover generation", phase: 1, icon: "🎧" },
  { name: "browser", label: "7. Browser launch", phase: 1, icon: "🌐" },
  { name: "scrapers", label: "8. Ad scraping (iSpot + YouTube + Meta + Milled)", phase: 1, icon: "📺" },
  { name: "analysis", label: "9. Channel mix & brand intelligence", phase: 1, icon: "📊" },
  { name: "extended_scrapers", label: "10. Google Trends + competitor landscape", phase: 1, icon: "🔍" },
  { name: "competitor_enrichment", label: "11. Competitor enrichment", phase: 1, icon: "🏢" },
  // Phase 2 — Deep Research
  { name: "news_search", label: "12. News & media search", phase: 2, icon: "📰" },
  { name: "thought_leadership", label: "13. Podcasts & thought leadership", phase: 2, icon: "🎙️" },
  { name: "case_study_search", label: "14. Platform case studies", phase: 2, icon: "📋" },
  // Report Generation & Delivery
  { name: "reports", label: "15. Report generation", phase: 1, icon: "📝" },
  { name: "slack", label: "16. Slack delivery", phase: 1, icon: "💬" },
];

/* ── Status icon ────────────────────────────────────────────── */

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case "done":
      return (
        <svg
          className="w-5 h-5 text-[var(--success)]"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="m4.5 12.75 6 6 9-13.5"
          />
        </svg>
      );
    case "running":
      return (
        <span className="w-5 h-5 flex items-center justify-center">
          <span className="pulse-dot" />
        </span>
      );
    case "error":
      return (
        <svg
          className="w-5 h-5 text-[var(--danger)]"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z"
          />
        </svg>
      );
    default:
      return (
        <span className="w-5 h-5 rounded-full border-2 border-[var(--border)]" />
      );
  }
}

/* ── Grade badge ────────────────────────────────────────────── */

function GradeBadge({ grade, score }: { grade: string; score: number }) {
  const color =
    grade === "A"
      ? "var(--success)"
      : grade === "B"
        ? "var(--teal)"
        : grade === "C"
          ? "#B54708"
          : "var(--danger)";

  return (
    <div className="flex items-center gap-3">
      <div
        className="w-14 h-14 rounded-full flex items-center justify-center text-white text-xl font-bold"
        style={{ background: color }}
      >
        {grade}
      </div>
      <div>
        <div className="text-2xl font-bold" style={{ color }}>
          {score.toFixed(0)}
        </div>
        <div className="text-xs text-[var(--muted)]">Upscale Fit Score</div>
      </div>
    </div>
  );
}

/* ── Mock step data for dev mode ────────────────────────────── */

const MOCK_STEP_DATA: Record<string, { detail: string; data?: Record<string, unknown> }> = {
  storeleads: { detail: "Shopify Plus · $2.4M/yr revenue · 45 employees", data: { revenue: "$2.4M/yr" } },
  company_pulse: { detail: "CRM: Active (85/100), 3 contacts, 1 deal", data: {} },
  contact_search: { detail: "4 contacts found: VP Marketing, Head of Growth, Creative Director", data: { count: 4 } },
  clay_enrichment: { detail: "3 competitors · Subscription model · 12% headcount growth · 5 open jobs", data: { jobs: 5 } },
  creative_pipeline: { detail: "4 images, 2 videos generated", data: {} },
  voiceover: { detail: "3 AI voiceover demos generated (male, female, neutral)", data: { voices: 3 } },
  browser: { detail: "Browser ready", data: {} },
  scrapers: { detail: "iSpot: 0, YouTube: 3, Meta: 12, Milled: 48 ads", data: { ads: 63 } },
  analysis: { detail: "3 platforms, 63 ads total", data: {} },
  extended_scrapers: { detail: "Trends: rising, Competitors: 5, Wayback: high", data: {} },
  competitor_enrichment: { detail: "5 competitors enriched · 2 active on CTV", data: { competitors: 5 } },
  news_search: { detail: "3 recent news articles · New product launch detected", data: { articles: 3 } },
  thought_leadership: { detail: "2 podcast appearances by founder", data: { podcasts: 2 } },
  case_study_search: { detail: "1 Shopify case study found with performance metrics", data: { studies: 1 } },
  reports: { detail: "Pitch + Internal reports generated and uploaded", data: {} },
  slack: { detail: "Delivered to #sales with executive summary", data: {} },
};

/* ── Build initial step state ───────────────────────────────── */

function buildInitialSteps(): StepStatus[] {
  return PIPELINE_STEPS.map((s) => ({
    name: s.name,
    label: s.label,
    status: "pending" as const,
  }));
}

/* ── Main component ─────────────────────────────────────────── */

export default function RunPage() {
  const { runId } = useParams<{ runId: string }>();
  const [run, setRun] = useState<RunState>({
    runId: runId || "",
    domain: "",
    status: "pending",
    steps: buildInitialSteps(),
  });
  const [activeTab, setActiveTab] = useState<"steps" | "summary">("steps");
  const [elapsedTimer, setElapsedTimer] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isMock = runId?.startsWith("dev-");

  // Elapsed time counter
  useEffect(() => {
    if (run.status === "running") {
      timerRef.current = setInterval(() => {
        setElapsedTimer((prev) => prev + 1);
      }, 1000);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [run.status]);

  const formatDuration = useCallback((seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
  }, []);

  useEffect(() => {
    if (isMock) {
      // Simulate pipeline with Phase 2 steps + data
      let idx = 0;
      setRun((prev) => ({
        ...prev,
        domain: "demo-brand.com",
        company_name: "Demo Brand Co",
        status: "running",
      }));

      intervalRef.current = setInterval(() => {
        setRun((prev) => {
          const steps = [...prev.steps];

          // Complete current step
          if (idx > 0 && steps[idx - 1]) {
            const mockData = MOCK_STEP_DATA[steps[idx - 1].name];
            steps[idx - 1] = {
              ...steps[idx - 1],
              status: "done",
              duration_seconds: Math.round(Math.random() * 20 + 2),
              detail: mockData?.detail,
              data: mockData?.data as Record<string, unknown> | undefined,
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
            score: allDone ? 74 : undefined,
            grade: allDone ? "B" : undefined,
            company_name: "Demo Brand Co",
            pitch_url: allDone
              ? "#demo-pitch"
              : undefined,
            internal_url: allDone
              ? "#demo-internal"
              : undefined,
          };
        });
        idx++;
      }, 1800);

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
          // Merge backend steps onto known PIPELINE_STEPS so numbering/icons are preserved
          const knownSteps = buildInitialSteps();
          const backendMap = new Map<string, StepStatus>();
          for (const s of (data.steps || [])) {
            backendMap.set(s.name, s);
          }
          // Update known steps with backend data, keep label from PIPELINE_STEPS
          const mergedSteps = knownSteps.map((ks) => {
            const bs = backendMap.get(ks.name);
            if (bs) {
              backendMap.delete(ks.name);
              return { ...ks, status: bs.status, detail: bs.detail, duration_seconds: bs.duration_seconds, data: bs.data };
            }
            return ks;
          });
          // Append any unknown backend steps (numbered from next available)
          let nextNum = mergedSteps.length + 1;
          for (const [, bs] of backendMap) {
            mergedSteps.push({ ...bs, label: bs.label?.match(/^\d+\./) ? bs.label : `${nextNum}. ${bs.label || bs.name}` });
            nextNum++;
          }
          data.steps = mergedSteps;
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
  const runningStep = run.steps.find((s) => s.status === "running");

  // Group steps by phase
  const phase1Steps = run.steps.filter((_, i) => PIPELINE_STEPS[i]?.phase === 1);
  const phase2Steps = run.steps.filter((_, i) => PIPELINE_STEPS[i]?.phase === 2);

  // Summary data from completed steps
  const getStepData = (name: string) =>
    run.steps.find((s) => s.name === name);

  return (
    <div className="flex flex-col min-h-screen bg-white">
      <Header />
      <main className="flex-1 py-12 px-6">
        <div className="max-w-4xl mx-auto">
          {/* ── Run header ── */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-[var(--navy)] flex items-center justify-center">
                <Logo size="small" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-[var(--navy)]">
                  {run.company_name || "Pipeline run"}
                </h1>
                <p className="text-sm text-[var(--muted)]">
                  {run.domain || runId}{" "}
                  <span className="ml-2 text-xs font-mono text-[var(--muted)]">
                    {runId}
                  </span>
                </p>
              </div>
            </div>
            {/* Elapsed timer */}
            <div className="text-right">
              <div className="text-xs text-[var(--muted)] uppercase tracking-wide">
                Elapsed
              </div>
              <div className="text-lg font-bold text-[var(--navy)] font-mono">
                {formatDuration(
                  run.status === "done"
                    ? run.elapsed_seconds || elapsedTimer
                    : elapsedTimer,
                )}
              </div>
            </div>
          </div>

          {/* ── Progress bar ── */}
          <div className="card mb-6">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <span className="text-sm font-semibold text-[var(--navy)]">
                  {run.status === "done"
                    ? "✅ Complete"
                    : run.status === "error"
                      ? "❌ Error"
                      : runningStep
                        ? `${PIPELINE_STEPS.find((s) => s.name === runningStep.name)?.icon || "⏳"} ${runningStep.label}`
                        : "Starting..."}
                </span>
                {run.status === "running" && (
                  <span className="text-xs text-[var(--pink)] font-medium animate-pulse">
                    processing
                  </span>
                )}
              </div>
              <span className="text-sm font-bold text-[var(--pink)]">
                {progress}%
              </span>
            </div>
            <div className="w-full h-3 bg-[var(--bg-grey)] rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700 ease-out"
                style={{
                  width: `${progress}%`,
                  background:
                    run.status === "error"
                      ? "var(--danger)"
                      : "linear-gradient(90deg, var(--pink), var(--teal))",
                }}
              />
            </div>
            <div className="flex justify-between mt-2">
              <p className="text-xs text-[var(--muted)]">
                {completedCount} of {run.steps.length} steps completed
              </p>
              {run.status === "done" && run.score != null && (
                <span className="tag tag-success">
                  Fit Score: {run.score.toFixed(0)} ({run.grade})
                </span>
              )}
            </div>
          </div>

          {/* ── Tab bar ── */}
          <div className="flex gap-1 mb-6 bg-[var(--bg-grey)] p-1 rounded-lg w-fit">
            <button
              onClick={() => setActiveTab("steps")}
              className={`px-4 py-1.5 rounded-md text-sm font-semibold transition-colors ${
                activeTab === "steps"
                  ? "bg-white text-[var(--navy)] shadow-sm"
                  : "text-[var(--muted)] hover:text-[var(--navy)]"
              }`}
            >
              Pipeline Steps
            </button>
            <button
              onClick={() => setActiveTab("summary")}
              className={`px-4 py-1.5 rounded-md text-sm font-semibold transition-colors ${
                activeTab === "summary"
                  ? "bg-white text-[var(--navy)] shadow-sm"
                  : "text-[var(--muted)] hover:text-[var(--navy)]"
              }`}
            >
              Qualification Summary
            </button>
          </div>

          {/* ── Steps tab ── */}
          {activeTab === "steps" && (
            <div className="space-y-6">
              {/* Phase 1 */}
              <div className="card">
                <div className="flex items-center gap-2 mb-4">
                  <h2 className="text-base font-semibold text-[var(--navy)]">
                    Core Intelligence
                  </h2>
                  <span className="tag tag-pink">Phase 1</span>
                </div>
                <div className="space-y-0.5">
                  {phase1Steps.map((step) => {
                    const def = PIPELINE_STEPS.find((s) => s.name === step.name);
                    const globalIdx = PIPELINE_STEPS.findIndex((s) => s.name === step.name);
                    return (
                      <div
                        key={step.name}
                        className={`flex items-start gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                          step.status === "running"
                            ? "bg-[var(--pink-light)]"
                            : step.status === "done"
                              ? "bg-[var(--bg-grey)]"
                              : ""
                        }`}
                      >
                        <div className="mt-0.5">
                          <StatusIcon status={step.status} />
                        </div>
                        <span className="text-xs font-bold text-[var(--pink)] w-6 mt-0.5">
                          {String(globalIdx + 1).padStart(2, "0")}
                        </span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm">{def?.icon}</span>
                            <span
                              className={`text-sm ${
                                step.status === "done"
                                  ? "text-[var(--muted)]"
                                  : step.status === "running"
                                    ? "text-[var(--navy)] font-semibold"
                                    : "text-[var(--navy)]"
                              }`}
                            >
                              {step.label}
                            </span>
                          </div>
                          {step.detail && step.status === "done" && (
                            <p className="text-xs text-[var(--muted)] mt-0.5 ml-7">
                              {step.detail}
                            </p>
                          )}
                        </div>
                        {step.duration_seconds != null && (
                          <span className="text-xs text-[var(--muted)] mt-0.5">
                            {step.duration_seconds.toFixed(0)}s
                          </span>
                        )}
                        {step.status === "running" && (
                          <span className="text-xs text-[var(--pink)] font-medium animate-pulse mt-0.5">
                            processing
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Phase 2 */}
              <div className="card">
                <div className="flex items-center gap-2 mb-4">
                  <h2 className="text-base font-semibold text-[var(--navy)]">
                    Deep Research
                  </h2>
                  <span className="tag tag-teal">Phase 2</span>
                </div>
                <div className="space-y-0.5">
                  {phase2Steps.map((step) => {
                    const def = PIPELINE_STEPS.find((s) => s.name === step.name);
                    const globalIdx = PIPELINE_STEPS.findIndex((s) => s.name === step.name);
                    return (
                      <div
                        key={step.name}
                        className={`flex items-start gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                          step.status === "running"
                            ? "bg-[#E0F7FA]"
                            : step.status === "done"
                              ? "bg-[var(--bg-grey)]"
                              : ""
                        }`}
                      >
                        <div className="mt-0.5">
                          <StatusIcon status={step.status} />
                        </div>
                        <span className="text-xs font-bold text-[var(--teal)] w-6 mt-0.5">
                          {String(globalIdx + 1).padStart(2, "0")}
                        </span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm">{def?.icon}</span>
                            <span
                              className={`text-sm ${
                                step.status === "done"
                                  ? "text-[var(--muted)]"
                                  : step.status === "running"
                                    ? "text-[var(--navy)] font-semibold"
                                    : "text-[var(--navy)]"
                              }`}
                            >
                              {step.label}
                            </span>
                          </div>
                          {step.detail && step.status === "done" && (
                            <p className="text-xs text-[var(--muted)] mt-0.5 ml-7">
                              {step.detail}
                            </p>
                          )}
                        </div>
                        {step.duration_seconds != null && (
                          <span className="text-xs text-[var(--muted)] mt-0.5">
                            {step.duration_seconds.toFixed(0)}s
                          </span>
                        )}
                        {step.status === "running" && (
                          <span className="text-xs text-[var(--teal)] font-medium animate-pulse mt-0.5">
                            researching
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* ── Summary tab ── */}
          {activeTab === "summary" && (
            <div className="space-y-6">
              {run.status !== "done" ? (
                <div className="card text-center py-12">
                  <div className="text-4xl mb-4">⏳</div>
                  <h3 className="text-lg font-semibold text-[var(--navy)] mb-2">
                    Pipeline still running
                  </h3>
                  <p className="text-sm text-[var(--muted)]">
                    The qualification summary will appear here once all steps
                    are complete.
                  </p>
                </div>
              ) : (
                <>
                  {/* Score + Grade */}
                  {run.score != null && run.grade && (
                    <div className="card">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-sm text-[var(--muted)] mb-2">
                            ICP Qualification Result
                          </h3>
                          <GradeBadge grade={run.grade} score={run.score} />
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-semibold text-[var(--navy)]">
                            {run.company_name || run.domain}
                          </div>
                          <div className="text-xs text-[var(--muted)]">
                            {run.domain}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Key findings grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[
                      {
                        label: "Ads Found",
                        value:
                          (getStepData("meta")?.data?.ads as number || 0) +
                          (getStepData("youtube")?.data?.ads as number || 0) +
                          (getStepData("ispot")?.data?.ads as number || 0),
                        icon: "📺",
                      },
                      {
                        label: "Contacts",
                        value: getStepData("contacts")?.data?.count || 0,
                        icon: "👥",
                      },
                      {
                        label: "Competitors",
                        value: getStepData("competitor")?.data?.competitors || 0,
                        icon: "🔍",
                      },
                      {
                        label: "Open Jobs",
                        value: getStepData("clay")?.data?.jobs || 0,
                        icon: "💼",
                      },
                    ].map((kpi) => (
                      <div key={kpi.label} className="card text-center">
                        <div className="text-2xl mb-1">{kpi.icon}</div>
                        <div className="text-2xl font-bold text-[var(--navy)]">
                          {typeof kpi.value === "number" ? kpi.value : "—"}
                        </div>
                        <div className="text-xs text-[var(--muted)]">
                          {kpi.label}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Step-by-step findings */}
                  <div className="card">
                    <h3 className="text-base font-semibold text-[var(--navy)] mb-4">
                      Key Findings
                    </h3>
                    <div className="space-y-3">
                      {run.steps
                        .filter((s) => s.status === "done" && s.detail)
                        .map((step) => {
                          const def = PIPELINE_STEPS.find(
                            (d) => d.name === step.name,
                          );
                          return (
                            <div
                              key={step.name}
                              className="flex items-start gap-3 py-2 border-b border-[var(--border)] last:border-0"
                            >
                              <span className="text-sm">{def?.icon}</span>
                              <div className="flex-1">
                                <div className="text-sm font-semibold text-[var(--navy)]">
                                  {step.label}
                                </div>
                                <div className="text-xs text-[var(--muted)] mt-0.5">
                                  {step.detail}
                                </div>
                              </div>
                              {step.duration_seconds != null && (
                                <span className="text-xs text-[var(--muted)]">
                                  {step.duration_seconds.toFixed(0)}s
                                </span>
                              )}
                            </div>
                          );
                        })}
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* ── Report delivery cards — shown when done ── */}
          {run.status === "done" && (run.pitch_url || run.internal_url) && (
            <div className="mt-8">
              <h2 className="text-lg font-bold text-[var(--navy)] mb-4">
                📄 Reports Delivered
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {run.pitch_url && (
                  <div className="card border-2 border-[var(--pink)] bg-[var(--pink-light)]">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 rounded-lg bg-[var(--pink)] flex items-center justify-center text-white text-lg">
                        🎯
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-[var(--navy)]">
                          Pitch Report
                        </h3>
                        <p className="text-xs text-[var(--muted)]">
                          Client-facing proposal with creative showcase
                        </p>
                      </div>
                    </div>
                    <p className="text-xs text-[var(--muted)] mb-4">
                      Includes ad spend estimates, competitive analysis, Vimeo
                      creative showcase, and personalized CTV proposal.
                    </p>
                    <div className="flex gap-2">
                      <a
                        href={run.pitch_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-pink text-xs flex-1"
                      >
                        Open Pitch Report →
                      </a>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(run.pitch_url || "");
                        }}
                        className="btn btn-outline text-xs"
                        title="Copy link"
                      >
                        📋
                      </button>
                    </div>
                  </div>
                )}
                {run.internal_url && (
                  <div className="card border-2 border-[var(--teal)]">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 rounded-lg bg-[var(--teal)] flex items-center justify-center text-white text-lg">
                        📝
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-[var(--navy)]">
                          Internal Report
                        </h3>
                        <p className="text-xs text-[var(--muted)]">
                          Full data + AI synthesis for sales team
                        </p>
                      </div>
                    </div>
                    <p className="text-xs text-[var(--muted)] mb-4">
                      Includes media maturity, buying committee, call talk
                      track, account priority, and all pipeline intelligence.
                    </p>
                    <div className="flex gap-2">
                      <a
                        href={run.internal_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-teal text-xs flex-1"
                      >
                        Open Internal Report →
                      </a>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(
                            run.internal_url || "",
                          );
                        }}
                        className="btn btn-outline text-xs"
                        title="Copy link"
                      >
                        📋
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── Error state ── */}
          {run.status === "error" && run.error && (
            <div className="card mt-6 bg-[var(--danger-light)] border-2 border-[var(--danger)]">
              <h2 className="text-base font-semibold text-[var(--danger)] mb-2">
                ❌ Pipeline error
              </h2>
              <p className="text-sm text-[var(--navy)]">{run.error}</p>
              <button
                onClick={() => window.location.reload()}
                className="btn btn-outline text-xs mt-4"
              >
                Retry
              </button>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
