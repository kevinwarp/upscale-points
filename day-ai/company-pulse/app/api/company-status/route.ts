import { NextRequest, NextResponse } from 'next/server'
import { getDayAIClient } from '@/lib/dayai'
import {
  fetchOrganization,
  fetchContacts,
  fetchOpportunities,
  fetchMeetings,
  fetchMeetingContexts,
  fetchEmailThreads,
  enrichContacts,
  buildTimeline,
} from '@/lib/queries'
import { getHubSpotClient } from '@/lib/hubspot'
import {
  findCompanyByDomain,
  fetchHubSpotContacts,
  fetchHubSpotDeals,
  fetchHubSpotEngagements,
  clearHubSpotCache,
} from '@/lib/hubspot-queries'
import {
  mergeOrganization,
  mergeContacts,
  mergeOpportunities,
  mergeMeetings,
  mergeEmails,
} from '@/lib/merge'
import { computeHealthScore } from '@/lib/health'
import { sendSlackNotification } from '@/lib/slack'
import { buildLumaAttendanceMap } from '@/lib/luma'
import { computeUpscaleScore } from '@/lib/storeleads'
import { batchCheckOutreach } from '@/lib/email-status/batch'
import type { CompanyReport, OutreachSummary } from '@/lib/types'
import { withRetry } from '@/lib/retry'
import { generateReportId, saveReport } from '@/lib/report-storage'
import { generateReport } from '@/lib/generate-report'

export const runtime = 'nodejs'

/** Derive the public-facing origin (Cloud Run sets Host + X-Forwarded-Proto). */
function getPublicOrigin(request: NextRequest): string {
  const proto = request.headers.get('x-forwarded-proto') || 'https'
  const host = request.headers.get('host')
  if (host && !host.startsWith('0.0.0.0') && !host.startsWith('localhost')) {
    return `${proto}://${host}`
  }
  return process.env.PUBLIC_URL || request.nextUrl.origin
}

export async function GET(request: NextRequest) {
  const organizationId = request.nextUrl.searchParams.get('organization_id')
  const stream = request.nextUrl.searchParams.get('stream') === '1'

  // ── Validate ────────────────────────────────────────────────

  if (!organizationId) {
    return NextResponse.json(
      { error: 'Missing required parameter: organization_id' },
      { status: 400 }
    )
  }

  // ── Non-streaming (legacy) path ─────────────────────────────
  if (!stream) {
    return handleNonStreaming(request, organizationId)
  }

  // ── Streaming SSE path ──────────────────────────────────────
  const encoder = new TextEncoder()
  const readable = new ReadableStream({
    async start(controller) {
      let closed = false
      function sendEvent(event: string, data: unknown) {
        if (closed) return
        try {
          controller.enqueue(
            encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`)
          )
        } catch {
          closed = true
        }
      }

      try {
        // Step 1: Day AI SDK init
        sendEvent('status', { step: 'dayai_init', message: 'Connecting to Day AI…' })
        const client = getDayAIClient()
        await withRetry(() => client.mcpInitialize())
        sendEvent('status', { step: 'dayai_init', done: true })

        // Step 2: Parallel Day AI fetch
        sendEvent('status', { step: 'dayai_fetch', message: 'Fetching CRM data from Day AI…' })
        const [organization, contacts, opportunities, meetings, emails] = await withRetry(
          () =>
            Promise.all([
              fetchOrganization(client, organizationId),
              fetchContacts(client, organizationId),
              fetchOpportunities(client, organizationId),
              fetchMeetings(client, organizationId),
              fetchEmailThreads(client, organizationId),
            ])
        )
        sendEvent('status', { step: 'dayai_fetch', done: true })

        if (!organization) {
          sendEvent('error', { error: `Organization not found: ${organizationId}` })
          return
        }

        // Step 3: Meeting context
        sendEvent('status', { step: 'meetings', message: 'Loading meeting details…' })
        const meetingsWithContext = await fetchMeetingContexts(client, meetings)
        sendEvent('status', { step: 'meetings', done: true })

        // Step 4: HubSpot
        let mergedOrg = organization
        let mergedContacts = contacts
        let mergedOpportunities = opportunities
        let mergedMeetings = meetingsWithContext
        let mergedEmails = emails
        let hubspotCompanyId: string | undefined

        const hsClient = getHubSpotClient()
        if (hsClient) {
          sendEvent('status', { step: 'hubspot', message: 'Fetching HubSpot data…' })
          try {
            clearHubSpotCache()
            const hsCompany = await findCompanyByDomain(hsClient, organizationId)
            if (hsCompany) {
              hubspotCompanyId = hsCompany.companyId
              const [hsContacts, hsDeals, hsEngagements] = await Promise.all([
                fetchHubSpotContacts(hsClient, hsCompany.companyId),
                fetchHubSpotDeals(hsClient, hsCompany.companyId),
                fetchHubSpotEngagements(hsClient, hsCompany.companyId),
              ])
              mergedOrg = mergeOrganization(organization, hsCompany.orgSnapshot)
              mergedContacts = mergeContacts(contacts, hsContacts)
              mergedOpportunities = mergeOpportunities(opportunities, hsDeals)
              mergedMeetings = mergeMeetings(meetingsWithContext, hsEngagements.meetings)
              mergedEmails = mergeEmails(emails, hsEngagements.emails)
            }
            sendEvent('status', { step: 'hubspot', done: true })
          } catch (err) {
            console.error('[company-status] HubSpot fetch failed:', err)
            sendEvent('status', { step: 'hubspot', done: true, skipped: true })
          }
        }

        // Step 5: Enrich + Luma
        const enrichedContacts = enrichContacts(mergedContacts, mergedOpportunities, mergedMeetings)

        sendEvent('status', { step: 'luma', message: 'Checking Luma event attendance…' })
        try {
          const lumaMap = await buildLumaAttendanceMap()
          if (lumaMap.size > 0) {
            for (const contact of enrichedContacts) {
              const events = lumaMap.get(contact.email.toLowerCase().trim())
              if (events && events.length > 0) {
                contact.lumaEvents = events
              }
            }
          }
          sendEvent('status', { step: 'luma', done: true })
        } catch (err) {
          console.error('[company-status] Luma failed:', err)
          sendEvent('status', { step: 'luma', done: true, skipped: true })
        }

        // Step 6: Email Outreach
        sendEvent('status', { step: 'email_outreach', message: 'Checking email outreach…' })
        let outreachSummary: OutreachSummary | undefined
        try {
          const result = await batchCheckOutreach(enrichedContacts)
          outreachSummary = result.summary
          sendEvent('status', { step: 'email_outreach', done: true })
        } catch (err) {
          console.error('[company-status] Email outreach failed:', err)
          sendEvent('status', { step: 'email_outreach', done: true, skipped: true })
        }

        // Step 7: StoreLeads / Upscale Score
        sendEvent('status', { step: 'storeleads', message: 'Computing Upscale Score…' })
        let upscaleScore: CompanyReport['upscaleScore']
        try {
          const us = await computeUpscaleScore(organizationId)
          upscaleScore = {
            totalScore: us.totalScore,
            tier: us.tier,
            gmvScore: us.gmvScore,
            industryScore: us.industryScore,
            recognitionScore: us.recognitionScore,
            estimatedAnnualGmv: us.estimatedAnnualGmv,
            industry: us.industry,
            platform: us.platform,
            description: us.description,
            city: us.city,
            state: us.state,
            employees: us.employees,
          }
          sendEvent('status', { step: 'storeleads', done: true })
        } catch (err) {
          console.error('[company-status] Upscale Score failed:', err)
          sendEvent('status', { step: 'storeleads', done: true, skipped: true })
        }

        // Step 8: Health + report assembly
        sendEvent('status', { step: 'report', message: 'Building report…' })
        const health = computeHealthScore(enrichedContacts, mergedOpportunities, mergedMeetings)
        const timeline = buildTimeline(mergedMeetings, mergedEmails)

        const allDates = [
          ...mergedMeetings.map((m) => m.date).filter(Boolean),
          ...mergedEmails.map((e) => e.date).filter(Boolean),
          ...enrichedContacts.map((c) => c.lastConversationDate).filter(Boolean),
        ] as string[]
        let daysSinceFirstContact: number | undefined
        if (allDates.length > 0) {
          const earliest = allDates.sort()[0]
          daysSinceFirstContact = Math.floor(
            (Date.now() - new Date(earliest).getTime()) / (1000 * 60 * 60 * 24)
          )
        }

        const reportId = generateReportId(organizationId)
        const report: CompanyReport = {
          reportId,
          organization: mergedOrg,
          contacts: enrichedContacts,
          opportunities: mergedOpportunities,
          meetings: mergedMeetings,
          emails: mergedEmails,
          timeline,
          healthScore: health.score,
          healthStatus: health.status,
          healthSignals: health.signals,
          tickets: [],
          slackStatus: 'skipped',
          generatedAt: new Date().toISOString(),
          hubspotCompanyId,
          daysSinceFirstContact,
          upscaleScore,
          outreachSummary,
        }
        
        // Save report to disk
        saveReport(report)
        sendEvent('status', { step: 'report', done: true })

        // Step 9: Slack notification
        sendEvent('status', { step: 'slack', message: 'Sending Slack notification…' })
        const reportUrl = `${getPublicOrigin(request)}/report/${reportId}`
        try {
          report.slackStatus = await sendSlackNotification(client, report, reportUrl)
          sendEvent('status', { step: 'slack', done: true })
        } catch (err) {
          console.error('Slack notification failed:', err)
          report.slackStatus = 'failed'
          sendEvent('status', { step: 'slack', done: true, skipped: true })
        }

        // Final: send the complete report
        sendEvent('complete', report)
      } catch (err) {
        console.error('[company-status] Error:', err instanceof Error ? err.stack : err)
        sendEvent('error', {
          error: err instanceof Error ? err.message : 'Internal server error',
        })
      } finally {
        closed = true
        try { controller.close() } catch { /* already closed */ }
      }
    },
  })

  return new Response(readable, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  })
}

// ── Non-streaming handler ────────────────────────────────────────

async function handleNonStreaming(request: NextRequest, organizationId: string) {
  try {
    const report = await generateReport(organizationId, {
      sendSlack: true,
      publicOrigin: getPublicOrigin(request),
    })
    return NextResponse.json(report)
  } catch (error: any) {
    console.error('[company-status] Error:', error)
    if (error?.code === 'NOT_FOUND') {
      return NextResponse.json({ error: error.message }, { status: 404 })
    }
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Internal server error' },
      { status: 500 }
    )
  }
}
