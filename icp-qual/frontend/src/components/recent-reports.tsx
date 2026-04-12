"use client";

import { useEffect, useState } from "react";

interface ReportSummary {
  domain: string;
  company_name: string;
  score: number;
  grade: string;
  revenue: string;
  platform: string;
  ads_found: number;
  pitch_url: string | null;
  internal_url: string | null;
  generated_at: string;
  duration_seconds: number;
}

function formatMoney(val: number | null): string {
  if (!val) return "\u2014";
  if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(1)}M`;
  if (val >= 1_000) return `$${(val / 1_000).toFixed(0)}K`;
  return `$${val.toLocaleString()}`;
}

function gradeColor(grade: string): string {
  if (grade === "A" || grade === "A+") return "tag-success";
  if (grade === "B" || grade === "B+") return "tag-teal";
  if (grade === "C") return "tag-pink";
  return "tag-danger";
}

function ReportCard({ report }: { report: ReportSummary }) {
  const initial = (report.company_name || report.domain)[0].toUpperCase();
  const date = new Date(report.generated_at).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });

  return (
    <div className="card flex flex-col gap-3">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-[var(--navy)] flex items-center justify-center text-white font-bold text-sm shrink-0">
            {initial}
          </div>
          <div>
            <h3 className="font-semibold text-[var(--navy)] text-sm leading-tight">
              {report.company_name || report.domain}
            </h3>
            <p className="text-xs text-[var(--muted)]">{report.domain}</p>
          </div>
        </div>
        <span className={`tag ${gradeColor(report.grade)}`}>{report.grade}</span>
      </div>

      <div className="grid grid-cols-3 gap-2 text-center py-2 border-t border-b border-[var(--border)]">
        <div>
          <div className="text-sm font-bold text-[var(--navy)]">{report.score}</div>
          <div className="text-[10px] text-[var(--muted)] uppercase tracking-wider">Score</div>
        </div>
        <div>
          <div className="text-sm font-bold text-[var(--navy)]">{report.revenue}</div>
          <div className="text-[10px] text-[var(--muted)] uppercase tracking-wider">Revenue</div>
        </div>
        <div>
          <div className="text-sm font-bold text-[var(--navy)]">{report.ads_found}</div>
          <div className="text-[10px] text-[var(--muted)] uppercase tracking-wider">Ads</div>
        </div>
      </div>

      <div className="flex items-center justify-between text-xs">
        <span className="text-[var(--muted)]">
          {date} &middot; {report.duration_seconds.toFixed(0)}s
        </span>
        <div className="flex gap-2">
          {report.pitch_url && (
            <a
              href={report.pitch_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[var(--teal)] font-semibold hover:underline"
            >
              Pitch &rsaquo;
            </a>
          )}
          {report.internal_url && (
            <a
              href={report.internal_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[var(--pink)] font-semibold hover:underline"
            >
              Internal &rsaquo;
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="card text-center py-12">
      <div className="text-4xl mb-3">
        <svg className="w-12 h-12 mx-auto text-[var(--muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
        </svg>
      </div>
      <h3 className="text-base font-semibold text-[var(--navy)] mb-1">No reports yet</h3>
      <p className="text-sm text-[var(--muted)]">
        Enter a domain above to generate your first ICP qualification report.
      </p>
    </div>
  );
}

// Demo data for initial display
const DEMO_REPORTS: ReportSummary[] = [
  {
    domain: "summerfridays.com",
    company_name: "Summer Fridays",
    score: 85,
    grade: "A",
    revenue: "$14.1M/mo",
    platform: "Shopify Plus",
    ads_found: 12,
    pitch_url: "https://upscale-reports-ghy5squ27q-uc.a.run.app/p/8de8cd5e1e31?passcode=923271",
    internal_url: "https://upscale-reports-ghy5squ27q-uc.a.run.app/p/d0126d118677?passcode=759748",
    generated_at: "2026-04-12T05:38:02.874Z",
    duration_seconds: 245,
  },
];

export function RecentReports() {
  const [reports, setReports] = useState<ReportSummary[]>(DEMO_REPORTS);

  useEffect(() => {
    fetch("/api/reports")
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setReports(data);
        }
      })
      .catch(() => {
        // Keep demo data on failure
      });
  }, []);

  return (
    <section id="reports" className="py-16 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-semibold text-[var(--pink)]">Recent reports</h2>
            <p className="text-sm text-[var(--muted)] mt-1">
              Latest ICP qualification runs with scores and report links
            </p>
          </div>
          <span className="text-xs text-[var(--muted)]">{reports.length} reports</span>
        </div>

        {reports.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {reports.map((report) => (
              <ReportCard key={report.domain + report.generated_at} report={report} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
