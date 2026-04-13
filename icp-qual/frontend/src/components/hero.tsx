"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export function Hero() {
  const [domain, setDomain] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!domain.trim()) return;

    const clean = domain
      .trim()
      .replace(/^https?:\/\//, "")
      .replace(/^www\./, "")
      .split("/")[0];

    setLoading(true);
    try {
      const res = await fetch("/icp/api/pipeline/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domain: clean }),
      });
      const data = await res.json();
      if (data.runId) {
        router.push(`/run/${data.runId}`);
      }
    } catch {
      setLoading(false);
    }
  }

  return (
    <section className="py-20 px-6">
      <div className="max-w-3xl mx-auto text-center">
        <div className="inline-block mb-4">
          <span className="tag tag-pink">ICP Qualification Pipeline</span>
        </div>

        <h1 className="text-4xl md:text-5xl font-bold text-[var(--navy)] leading-tight mb-6">
          Qualify any brand for{" "}
          <span className="text-[var(--pink)]">Streaming TV</span> in minutes
        </h1>

        <p className="text-lg text-[var(--muted)] max-w-2xl mx-auto mb-10 leading-relaxed">
          Enter a domain and our AI pipeline will enrich, score, and generate a
          custom CTV + YouTube proposal — complete with voiceover demos, competitive
          intel, and a full media plan.
        </p>

        <form onSubmit={handleSubmit} className="max-w-xl mx-auto">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <input
                type="text"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                placeholder="Enter a domain (e.g. summerfridays.com)"
                className="w-full pr-4 py-3 text-base"
                style={{ paddingLeft: "2.5rem" }}
                disabled={loading}
              />
              <svg
                className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--muted)]"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" strokeLinecap="round" />
              </svg>
            </div>
            <button
              type="submit"
              disabled={loading || !domain.trim()}
              className="btn btn-pink px-6 py-3 text-base disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Running...
                </span>
              ) : (
                "Qualify"
              )}
            </button>
          </div>
        </form>

        {/* Quick stats */}
        <div className="flex justify-center gap-8 mt-12 text-sm text-[var(--muted)]">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[var(--success)]" />
            14 data sources
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[var(--teal)]" />
            AI voiceover + creative
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[var(--pink)]" />
            Auto Slack delivery
          </div>
        </div>
      </div>
    </section>
  );
}
