'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { pdf } from '@react-pdf/renderer'
import type { CompanyReport } from '@/lib/types'
import { CompanyStatusPDF } from '@/lib/pdf-report'
import StatusHeader from '@/components/StatusHeader'
import KPICards from '@/components/KPICards'
import ContactsTable from '@/components/ContactsTable'
import OpportunitySummary from '@/components/OpportunitySummary'
import MeetingsTimeline from '@/components/MeetingsTimeline'
import ActivityTimeline from '@/components/ActivityTimeline'
import SourceBadge from '@/components/SourceBadge'

function LoadingSkeleton() {
  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="skeleton h-32 w-full mb-6" />
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="skeleton h-24 w-full" />
        ))}
      </div>
      <div className="skeleton h-10 w-96 mb-6" />
      <div className="skeleton h-64 w-full" />
    </div>
  )
}

function ErrorDisplay({ error, reportId }: { error: string; reportId: string }) {
  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="glass-elevated rounded-2xl p-8 text-center border-red-500/30">
        <div className="text-4xl mb-4">⚠️</div>
        <h2 className="text-xl font-semibold text-red-400 mb-2">Failed to Load Report</h2>
        <p className="text-white/70 mb-4">{error}</p>
        <p className="text-sm text-white/40">Report ID: {reportId}</p>
      </div>
    </div>
  )
}

export default function CachedReportPage() {
  const params = useParams()
  const reportId = params.reportId as string

  const [report, setReport] = useState<CompanyReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadReport() {
      try {
        const response = await fetch(`/api/report/${reportId}`)
        if (!response.ok) {
          const data = await response.json()
          setError(data.error || `HTTP ${response.status}`)
          setLoading(false)
          return
        }
        const data = await response.json()
        setReport(data)
        setLoading(false)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load report')
        setLoading(false)
      }
    }
    loadReport()
  }, [reportId])

  if (loading) return <LoadingSkeleton />
  if (error) return <ErrorDisplay error={error} reportId={reportId} />
  if (!report) return <ErrorDisplay error="No data returned" reportId={reportId} />

  function downloadContactsCsv() {
    if (!report) return
    const headers = [
      'Name',
      'Title',
      'Email',
      'Phone',
      'Lifecycle Stage',
      'Conversions',
      'Last Conversation',
      'Source',
    ]
    const rows = report.contacts.map((c) => [
      [c.firstName, c.lastName].filter(Boolean).join(' ') || c.email,
      c.title || '',
      c.email,
      c.phone || '',
      c.lifecycleStage || '',
      String(c.totalConversions),
      c.lastConversationDate || '',
      c.source || '',
    ])
    const csv = [headers, ...rows]
      .map((r) => r.map((v) => `"${v.replace(/"/g, '""')}"`).join(','))
      .join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${report.organization.name.replace(/\s+/g, '_')}_contacts.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  function downloadMeetingNotesMd() {
    if (!report) return
    const lines: string[] = [
      `# Meeting Notes — ${report.organization.name}`,
      `Generated: ${new Date(report.generatedAt).toLocaleString()}`,
      '',
    ]
    for (const m of report.meetings) {
      lines.push(`## ${m.title || 'Untitled Meeting'}`)
      if (m.date) lines.push(`**Date:** ${new Date(m.date).toLocaleString()}`)
      if (m.attendees?.length) lines.push(`**Attendees:** ${m.attendees.join(', ')}`)
      if (m.topic) lines.push(`**Topic:** ${m.topic}`)
      if (m.source) lines.push(`**Source:** ${m.source}`)
      lines.push('')
      if (m.summaryShort) lines.push(`> ${m.summaryShort}`, '')
      if (m.keyPoints?.length) {
        lines.push('### Key Points')
        m.keyPoints.forEach((p) => lines.push(`- ${p}`))
        lines.push('')
      }
      if (m.actionItems?.length) {
        lines.push('### Action Items')
        m.actionItems.forEach((a) => lines.push(`- [ ] ${a}`))
        lines.push('')
      }
      if (m.notes) {
        lines.push('### Notes', '', m.notes, '')
      }
      if (m.summaryLong) {
        lines.push('### Full Summary', '', m.summaryLong, '')
      }
      lines.push('---', '')
    }
    const md = lines.join('\n')
    const blob = new Blob([md], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${report.organization.name.replace(/\s+/g, '_')}_meeting_notes.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  async function downloadPdfReport() {
    if (!report) return
    try {
      const blob = await pdf(<CompanyStatusPDF report={report} />).toBlob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${report.organization.name.replace(/\s+/g, '_')}_status_report.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to generate PDF:', err)
      alert('Failed to generate PDF. Please try again.')
    }
  }

  return (
    <main className="min-h-screen p-4 sm:p-6">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Cached Report Banner */}
        <div className="glass-panel rounded-lg p-3 border-l-4 border-blue-500/50">
          <p className="text-sm text-white/70">
            📅 Cached report generated {new Date(report.generatedAt).toLocaleString()}
          </p>
        </div>

        {/* Download PDF Button */}
        <div className="flex justify-end">
          <button
            onClick={downloadPdfReport}
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            Download PDF Report
          </button>
        </div>

        <StatusHeader report={report} />
        <KPICards report={report} />

        {/* TL;DR Summary */}
        {(report.organization.currentStatus || report.organization.statusSummary?.length) && (
          <section>
            <div className="glass-panel rounded-xl p-5 border-l-4 border-blue-500/50">
              <h2 className="text-lg font-semibold text-white mb-2">TL;DR</h2>
              {report.organization.currentStatus && (
                <p className="text-sm text-white/80 leading-relaxed">
                  {report.organization.currentStatus}
                </p>
              )}
              {report.organization.statusSummary && report.organization.statusSummary.length > 0 && (
                <ul className="mt-3 space-y-1">
                  {report.organization.statusSummary.map((item, i) => (
                    <li key={i} className="text-sm text-white/70 flex gap-2">
                      <span className="text-blue-400 flex-shrink-0">•</span>
                      {item}
                    </li>
                  ))}
                </ul>
              )}
              {report.organization.nextSteps && (
                <div className="mt-3 pt-3 border-t border-white/5">
                  <span className="text-xs font-medium text-white/50">Next Steps: </span>
                  <span className="text-sm text-white/70">{report.organization.nextSteps}</span>
                </div>
              )}
            </div>
          </section>
        )}

        {/* Company Snapshot */}
        <section>
          <div className="glass-panel rounded-xl p-5">
            <h2 className="text-lg font-semibold text-white mb-3">Company Snapshot</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-white/50">Organization</span>
                <p className="text-white/90 font-medium">{report.organization.name}</p>
              </div>
              <div>
                <span className="text-white/50">Owner</span>
                <p className="text-white/90">{report.organization.ownerEmail || '—'}</p>
              </div>
              <div>
                <span className="text-white/50">Industry</span>
                <p className="text-white/90">{report.organization.industry || '—'}</p>
              </div>
              {report.opportunities[0]?.stage && (
                <div>
                  <span className="text-white/50">Current Stage</span>
                  <p className="text-white/90">{report.opportunities[0].stage}</p>
                </div>
              )}
              {report.organization.annualRevenue && (
                <div>
                  <span className="text-white/50">Annual Revenue</span>
                  <p className="text-white/90">
                    ${report.organization.annualRevenue.toLocaleString()}
                  </p>
                </div>
              )}
              {report.organization.employeeCount && (
                <div>
                  <span className="text-white/50">Employees</span>
                  <p className="text-white/90">{report.organization.employeeCount.toLocaleString()}</p>
                </div>
              )}
              {report.organization.location && (
                <div>
                  <span className="text-white/50">Location</span>
                  <p className="text-white/90">{report.organization.location}</p>
                </div>
              )}
            </div>

            {/* StoreLeads enrichment */}
            {report.upscaleScore && (
              <div className="mt-4 pt-4 border-t border-white/5">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-sm font-medium text-white/60">StoreLeads Data</h3>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
                  {report.upscaleScore.estimatedAnnualGmv && (
                    <div>
                      <span className="text-white/50">Est. Annual GMV</span>
                      <p className="text-white/90 font-medium">
                        ${Math.round(report.upscaleScore.estimatedAnnualGmv).toLocaleString()}
                      </p>
                    </div>
                  )}
                  {report.upscaleScore.platform && (
                    <div>
                      <span className="text-white/50">Platform</span>
                      <p className="text-white/90">{report.upscaleScore.platform}</p>
                    </div>
                  )}
                  {report.upscaleScore.employees && (
                    <div>
                      <span className="text-white/50">Employees</span>
                      <p className="text-white/90">{report.upscaleScore.employees.toLocaleString()}</p>
                    </div>
                  )}
                  {(report.upscaleScore.city || report.upscaleScore.state) && (
                    <div>
                      <span className="text-white/50">Location</span>
                      <p className="text-white/90">
                        {[report.upscaleScore.city, report.upscaleScore.state]
                          .filter(Boolean)
                          .join(', ')}
                      </p>
                    </div>
                  )}
                  {report.upscaleScore.industry && (
                    <div>
                      <span className="text-white/50">Industry</span>
                      <p className="text-white/90">{report.upscaleScore.industry}</p>
                    </div>
                  )}
                </div>
                {report.upscaleScore.description && (
                  <p className="mt-3 text-xs text-white/60 leading-relaxed">
                    {report.upscaleScore.description}
                  </p>
                )}
              </div>
            )}

            {/* HubSpot deal pipeline info */}
            {report.opportunities[0]?.hubspotPipeline && (
              <div className="mt-4 pt-4 border-t border-white/5">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-sm font-medium text-white/60">HubSpot Pipeline</h3>
                  <SourceBadge source="hubspot" />
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-white/50">Pipeline</span>
                    <p className="text-white/90">{report.opportunities[0].hubspotPipeline}</p>
                  </div>
                  {report.opportunities[0].hubspotDealStage && (
                    <div>
                      <span className="text-white/50">Deal Stage</span>
                      <p className="text-white/90">{report.opportunities[0].hubspotDealStage}</p>
                    </div>
                  )}
                  {report.opportunities[0].probability !== undefined && (
                    <div>
                      <span className="text-white/50">Win Probability</span>
                      <p className="text-white/90">{report.opportunities[0].probability}%</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Opportunities */}
        {report.opportunities.length > 0 && (
          <section>
            <h2 className="text-lg font-semibold text-white mb-3">
              Opportunities
              <span className="ml-2 text-sm font-normal text-white/40">
                ({report.opportunities.length})
              </span>
            </h2>
            <OpportunitySummary opportunities={report.opportunities} />
          </section>
        )}

        {/* Email Outreach Summary */}
        {report.outreachSummary && (
          <section>
            <div className="glass-panel rounded-xl p-5">
              <h2 className="text-lg font-semibold text-white mb-3">Email Outreach</h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-white/50">Contacts Checked</span>
                  <p className="text-white/90 font-medium">
                    {report.outreachSummary.totalChecked}
                  </p>
                </div>
                {report.outreachSummary.instantly.found > 0 && (
                  <div>
                    <span className="text-white/50">Instantly</span>
                    <p className="text-white/90">
                      {report.outreachSummary.instantly.found} found · {report.outreachSummary.instantly.sent} sent · {report.outreachSummary.instantly.opened} opened
                    </p>
                  </div>
                )}
                {report.outreachSummary.beehiiv.found > 0 && (
                  <div>
                    <span className="text-white/50">beehiiv</span>
                    <p className="text-white/90">
                      {report.outreachSummary.beehiiv.found} found · {report.outreachSummary.beehiiv.sent} sent · {report.outreachSummary.beehiiv.opened} opened
                    </p>
                  </div>
                )}
              </div>
              {report.outreachSummary.instantly.found === 0 &&
                report.outreachSummary.beehiiv.found === 0 && (
                  <p className="text-sm text-white/40 mt-2">
                    No contacts found in Instantly or beehiiv
                  </p>
                )}
            </div>
          </section>
        )}

        {/* Contacts */}
        {report.contacts.length > 0 && (
          <section>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-white">
                Contacts
                <span className="ml-2 text-sm font-normal text-white/40">
                  ({report.contacts.length})
                </span>
              </h2>
              <button
                onClick={downloadContactsCsv}
                className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-medium text-white/60 hover:text-white/90 transition-colors"
              >
                ⬇ Download CSV
              </button>
            </div>
            <ContactsTable contacts={report.contacts} />

            {/* Per-contact outreach badges */}
            {report.contacts.some((c) => c.outreach && c.outreach.length > 0) && (
              <div className="mt-4 space-y-2">
                <h3 className="text-sm font-medium text-white/60">Outreach by Contact</h3>
                {report.contacts
                  .filter((c) => c.outreach && c.outreach.length > 0)
                  .map((c, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-3 px-4 py-2.5 rounded-lg bg-white/[0.02] text-sm"
                    >
                      <span className="text-white/80 min-w-[140px] truncate">
                        {[c.firstName, c.lastName].filter(Boolean).join(' ') || c.email}
                      </span>
                      <div className="flex gap-2 flex-wrap">
                        {c.outreach!.map((o, j) => (
                          <span
                            key={j}
                            className={`px-2 py-0.5 rounded text-xs font-medium ${
                              o.provider === 'instantly'
                                ? 'bg-purple-500/20 text-purple-300'
                                : 'bg-amber-500/20 text-amber-300'
                            }`}
                          >
                            {o.provider}
                            {o.sent && ' · sent'}
                            {o.opened && ' · opened'}
                            {o.clicked && ' · clicked'}
                          </span>
                        ))}
                        {c.outreach!.some((o) => o.campaignName) && (
                          <span className="text-white/30 text-xs truncate">
                            {c.outreach!.find((o) => o.campaignName)?.campaignName}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </section>
        )}

        {/* Meetings */}
        {report.meetings.length > 0 && (
          <section>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-white">
                Meetings
                <span className="ml-2 text-sm font-normal text-white/40">
                  ({report.meetings.length})
                </span>
              </h2>
              <button
                onClick={downloadMeetingNotesMd}
                className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-medium text-white/60 hover:text-white/90 transition-colors"
              >
                ⬇ Download Notes (.md)
              </button>
            </div>
            <MeetingsTimeline meetings={report.meetings} />
          </section>
        )}

        {/* Activity Timeline */}
        {report.timeline && report.timeline.length > 0 && (
          <section>
            <h2 className="text-lg font-semibold text-white mb-3">
              Activity Timeline
              <span className="ml-2 text-sm font-normal text-white/40">
                ({report.timeline.length})
              </span>
            </h2>
            <ActivityTimeline events={report.timeline} />
          </section>
        )}

        {/* Footer */}
        <div className="mt-8 pb-8 text-center text-xs text-white/30">
          <p>
            Generated {new Date(report.generatedAt).toLocaleString()} | Slack:{' '}
            {report.slackStatus} | Powered by{' '}
            <a
              href="https://day.ai"
              target="_blank"
              rel="noopener noreferrer"
              className="text-white/50 hover:text-white/70 transition-colors"
            >
              Day AI
            </a>
          </p>
        </div>
      </div>
    </main>
  )
}
