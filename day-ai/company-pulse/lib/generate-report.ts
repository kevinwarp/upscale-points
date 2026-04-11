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
import { buildLumaAttendanceMap } from '@/lib/luma'
import { computeUpscaleScore } from '@/lib/storeleads'
import { batchCheckOutreach } from '@/lib/email-status/batch'
import type { CompanyReport, OutreachSummary } from '@/lib/types'
import { withRetry } from '@/lib/retry'
import { generateReportId, saveReport } from '@/lib/report-storage'

/** Normalize a raw domain/URL input to a bare domain (e.g. "https://foo.com/" → "foo.com") */
export function normalizeDomain(input: string): string {
  return input
    .trim()
    .replace(/^https?:\/\//, '')
    .replace(/^www\./, '')
    .split('/')[0]
    .split('?')[0]
}

export interface GenerateReportOptions {
  /** Whether to send a Slack notification after generation. Defaults to false. */
  sendSlack?: boolean
  /** Public origin used to build the report URL in the Slack notification */
  publicOrigin?: string
}

/**
 * Core report generation logic shared between the UI API and the external v1 API.
 * Returns a full CompanyReport or throws on hard failure.
 */
export async function generateReport(
  organizationId: string,
  options: GenerateReportOptions = {}
): Promise<CompanyReport> {
  const client = getDayAIClient()
  await withRetry(() => client.mcpInitialize())

  const [organization, contacts, opportunities, meetings, emails] = await withRetry(() =>
    Promise.all([
      fetchOrganization(client, organizationId),
      fetchContacts(client, organizationId),
      fetchOpportunities(client, organizationId),
      fetchMeetings(client, organizationId),
      fetchEmailThreads(client, organizationId),
    ])
  )

  if (!organization) {
    throw Object.assign(new Error(`Organization not found: ${organizationId}`), {
      code: 'NOT_FOUND',
    })
  }

  const meetingsWithContext = await fetchMeetingContexts(client, meetings)

  let mergedOrg = organization
  let mergedContacts = contacts
  let mergedOpportunities = opportunities
  let mergedMeetings = meetingsWithContext
  let mergedEmails = emails
  let hubspotCompanyId: string | undefined

  const hsClient = getHubSpotClient()
  if (hsClient) {
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
    } catch (err) {
      console.error('[generate-report] HubSpot fetch failed (continuing):', err)
    }
  }

  const enrichedContacts = enrichContacts(mergedContacts, mergedOpportunities, mergedMeetings)

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
  } catch (err) {
    console.error('[generate-report] Luma failed (continuing):', err)
  }

  let outreachSummary: OutreachSummary | undefined
  try {
    const result = await batchCheckOutreach(enrichedContacts)
    outreachSummary = result.summary
  } catch (err) {
    console.error('[generate-report] Email outreach failed (continuing):', err)
  }

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
  } catch (err) {
    console.error('[generate-report] Upscale Score failed (continuing):', err)
  }

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

  saveReport(report)

  if (options.sendSlack) {
    try {
      const { sendSlackNotification } = await import('@/lib/slack')
      const reportUrl = options.publicOrigin
        ? `${options.publicOrigin}/report/${reportId}`
        : undefined
      report.slackStatus = await sendSlackNotification(client, report, reportUrl ?? '')
    } catch (err) {
      console.error('[generate-report] Slack notification failed:', err)
      report.slackStatus = 'failed'
    }
  }

  return report
}
