import type { DayAIClient } from 'day-ai-sdk/dist/src'
import type { CompanyReport } from './types'

function formatSlackParagraphs(report: CompanyReport): string[] {
  const org = report.organization
  const lines: string[] = []

  const statusEmoji =
    report.healthStatus === 'healthy'
      ? '🟢'
      : report.healthStatus === 'at_risk'
        ? '🟡'
        : '🔴'

  // ── Header ──
  lines.push(`📊 *Company Status — ${org.name}*`)
  lines.push(`Owner: ${org.ownerEmail || 'Unassigned'} | ${statusEmoji} Health: ${report.healthStatus.replace('_', ' ').toUpperCase()} (${report.healthScore}/100)`)

  // ── Deep links ──
  const links: string[] = []
  if (org.domain) {
    links.push(`<https://day.ai/view#workspaceId:27d5d483-b08d-4e1e-bb23-7a27e2ba1966,primary.objectType:native_organization,primary.objectId:${org.domain},primary.mode:object|Day AI>`)
  }
  if (report.hubspotCompanyId) {
    links.push(`<https://app.hubspot.com/contacts/48048874/company/${report.hubspotCompanyId}|HubSpot>`)
  }
  if (links.length > 0) {
    lines.push(`🔗 ${links.join(' | ')}`)
  }

  // ── Upscale Score ──
  if (report.upscaleScore) {
    const us = report.upscaleScore
    let scoreLine = `⭐ Upscale Score: ${us.totalScore}/10 (${us.tier})`
    if (us.estimatedAnnualGmv) {
      scoreLine += ` | Est. GMV: $${(us.estimatedAnnualGmv / 1_000_000).toFixed(1)}M`
    }
    if (us.industry) {
      scoreLine += ` | Industry: ${us.industry}`
    }
    lines.push(scoreLine)
  }

  // ── TL;DR ──
  if (org.currentStatus) {
    lines.push(`📝 *TL;DR:* ${org.currentStatus}`)
  }
  if (org.statusSummary && org.statusSummary.length > 0) {
    org.statusSummary.forEach((s) => lines.push(`  • ${s}`))
  }
  if (org.nextSteps) {
    const parts = org.nextSteps.split('; ')
    if (parts.length > 1) {
      lines.push('➡️ *Next Steps:*')
      parts.forEach((p) => lines.push(`  → ${p}`))
    } else {
      lines.push(`➡️ Next Steps: ${org.nextSteps}`)
    }
  }

  // ── KPIs ──
  const kpiParts: string[] = []
  if (report.daysSinceFirstContact !== undefined) {
    kpiParts.push(`${report.daysSinceFirstContact}d since first contact`)
  }
  kpiParts.push(`${report.contacts.length} contacts`)
  kpiParts.push(`${report.opportunities.length} opportunities`)
  kpiParts.push(`${report.meetings.length} meetings`)
  lines.push(`📈 ${kpiParts.join(' | ')}`)

  // ── Opportunities ──
  if (report.opportunities.length > 0) {
    lines.push(`💰 *Opportunities (${report.opportunities.length}):*`)
    report.opportunities.slice(0, 5).forEach((o) => {
      let oppLine = `  • ${o.title} — ${o.stage || 'Unknown'}`
      if (o.dealSize) oppLine += ` | $${o.dealSize.toLocaleString()}`
      if (o.probability !== undefined) oppLine += ` | ${o.probability}%`
      if (o.hubspotPipeline) oppLine += ` | ${o.hubspotPipeline}`
      lines.push(oppLine)
    })
  }

  // ── Contacts ──
  if (report.contacts.length > 0) {
    lines.push(`👥 *Contacts (${report.contacts.length}):*`)
    report.contacts.slice(0, 5).forEach((c) => {
      const name = [c.firstName, c.lastName].filter(Boolean).join(' ') || c.email
      let contactLine = `  • ${name}`
      if (c.title) contactLine += ` — ${c.title}`
      if (c.lumaEvents && c.lumaEvents.length > 0) {
        const accepted = c.lumaEvents.filter((e) => e.accepted)
        contactLine += ` | 🎟 ${accepted.length}/${c.lumaEvents.length} events`
      }
      lines.push(contactLine)
    })
    if (report.contacts.length > 5) {
      lines.push(`  ... +${report.contacts.length - 5} more`)
    }
  }

  // ── Last Meeting ──
  const lastMeeting = report.meetings[0]
  if (lastMeeting) {
    lines.push(`📅 *Last Meeting:* ${lastMeeting.title || 'Untitled'} (${lastMeeting.date ? new Date(lastMeeting.date).toLocaleDateString() : 'Unknown'})`)
    if (lastMeeting.summaryShort) lines.push(`  ${lastMeeting.summaryShort}`)
    if (lastMeeting.actionItems && lastMeeting.actionItems.length > 0) {
      lastMeeting.actionItems.slice(0, 3).forEach((a) => lines.push(`  → ${a}`))
    }
  }

  // ── Tickets ──
  if (report.tickets && report.tickets.length > 0) {
    lines.push(`🎫 *Tickets (${report.tickets.length}):*`)
    report.tickets.forEach((t) => {
      let ticketLine = `  • ${t.subject}`
      if (t.status) ticketLine += ` — ${t.status}`
      if (t.priority) ticketLine += ` [${t.priority}]`
      lines.push(ticketLine)
    })
  }

  // ── Risk Signals ──
  const risks = report.healthSignals.filter((s) => s.type === 'negative')
  if (risks.length > 0) {
    lines.push('⚠️ *Risk Signals:*')
    risks.forEach((r) => lines.push(`  • ${r.label} (${r.impact})`))
  }

  // ── Sources ──
  const hasBoth = report.contacts.some((c) => c.source === 'hubspot' || c.source === 'both')
  const hasLuma = report.contacts.some((c) => c.lumaEvents && c.lumaEvents.length > 0)
  const sources = ['Day AI']
  if (hasBoth) sources.push('HubSpot')
  if (hasLuma) sources.push('Luma')
  if (report.upscaleScore) sources.push('StoreLeads')
  lines.push(`📡 Sources: ${sources.join(' + ')}`)

  return lines
}

/**
 * Send report to Slack via Day AI SDK send_notification.
 * We join all lines into a single paragraph to avoid double-spacing.
 */
export async function sendSlackNotification(
  client: DayAIClient,
  report: CompanyReport,
  reportUrl?: string
): Promise<'sent' | 'failed' | 'skipped'> {
  const lines = formatSlackParagraphs(report)

  if (reportUrl) {
    // Extract report ID from URL (format: /report/{reportId})
    const url = new URL(reportUrl)
    const reportId = report.reportId
    const pdfUrl = `${url.origin}/api/report/${reportId}/pdf`
    
    lines.push(`\n🔗 *Links:*`)
    lines.push(`  • <${reportUrl}|View Full Report>`)
    lines.push(`  • <${pdfUrl}|Download PDF Report>`)
  }

  // Join all lines into a single string so Slack renders single-spaced
  const message = lines.join('\n')

  try {
    const result = await client.mcpCallTool('send_notification', {
      channel: 'slack',
      slackParagraphs: [message],
      reasoning: `Company status report for ${report.organization.name}`,
    })

    if (!result.success) {
      console.error('Day AI Slack notification failed:', result.error)
      return 'failed'
    }

    return 'sent'
  } catch (err) {
    console.error('Slack notification error:', err)
    return 'failed'
  }
}
