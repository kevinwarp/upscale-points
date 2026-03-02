// ── Organization ──────────────────────────────────────────────

export interface OrgSnapshot {
  objectId: string
  name: string
  domain: string
  industry?: string
  annualRevenue?: number
  ownerEmail?: string
  description?: string
  aiDescription?: string
  statusSummary?: string[]
  currentStatus?: string
  nextSteps?: string
  warmth?: number
  hasOpportunity?: boolean
  employeeCount?: number
  location?: string
}

// ── Data source ──────────────────────────────────────────────

export type DataSource = 'day_ai' | 'hubspot' | 'both'

// ── Contact ──────────────────────────────────────────────────

export interface LumaEventAttendance {
  eventName: string
  eventDate?: string
  status: string
  accepted: boolean
}

export interface ContactOutreach {
  provider: 'beehiiv' | 'instantly'
  sent: boolean | null
  opened: boolean | null
  clicked: boolean | null
  confidence: 'high' | 'medium' | 'low'
  lastContactDate?: string
  campaignName?: string
}

export interface ContactEntry {
  objectId: string
  email: string
  firstName?: string
  lastName?: string
  title?: string
  phone?: string
  lifecycleStage?: string
  totalConversions: number       // computed from opportunity roles
  lastConversationDate?: string  // derived from most recent meeting attendance
  lumaEvents?: LumaEventAttendance[]
  outreach?: ContactOutreach[]
  source?: DataSource
}

// ── Opportunity ──────────────────────────────────────────────

export interface OpportunityEntry {
  objectId: string
  title: string
  stage?: string
  stageId?: string
  dealSize?: number
  ownerEmail?: string
  closeDate?: string
  probability?: number
  daysInStage?: number
  currentStatus?: string
  lastActivityDate?: string
  pipelineTitle?: string
  hubspotPipeline?: string
  hubspotDealStage?: string
  source?: DataSource
}

// ── Meeting ──────────────────────────────────────────────────

export interface MeetingEntry {
  objectId: string
  title?: string
  date?: string
  attendees?: string[]
  duration?: string
  summaryShort?: string
  summaryLong?: string
  keyPoints?: string[]
  topic?: string
  notes?: string
  // Populated from get_meeting_recording_context
  actionItems?: string[]
  fullContext?: string
  source?: DataSource
}

// ── Email Thread ─────────────────────────────────────────────

export interface EmailThreadEntry {
  objectId: string
  summary?: string
  allEmails?: string[]
  allDomains?: string[]
  date?: string
  title?: string
  source?: DataSource
}

// ── Ticket ──────────────────────────────────────────────

export interface TicketEntry {
  objectId: string
  subject: string
  status?: string
  priority?: string
  category?: string
  createdAt?: string
  lastUpdated?: string
  content?: string
  source?: DataSource
}

// ── Timeline ─────────────────────────────────────────────

export interface TimelineEvent {
  type: 'meeting' | 'email'
  date: string
  title: string
  summary?: string
  participants?: string[]
  objectId: string
  actionItems?: string[]
}

// ── Health ────────────────────────────────────────────────────

export type HealthStatus = 'healthy' | 'at_risk' | 'critical'

export interface HealthResult {
  score: number
  status: HealthStatus
  signals: HealthSignal[]
}

export interface HealthSignal {
  label: string
  impact: number
  type: 'positive' | 'negative'
}

// ── Aggregated Report ────────────────────────────────────────

export interface OutreachSummary {
  totalChecked: number
  instantly: { found: number; sent: number; opened: number }
  beehiiv: { found: number; sent: number; opened: number }
}

export interface CompanyReport {
  reportId: string
  organization: OrgSnapshot
  contacts: ContactEntry[]
  opportunities: OpportunityEntry[]
  meetings: MeetingEntry[]
  emails: EmailThreadEntry[]
  timeline: TimelineEvent[]
  healthScore: number
  healthStatus: HealthStatus
  healthSignals: HealthSignal[]
  tickets: TicketEntry[]
  slackStatus: 'sent' | 'failed' | 'skipped'
  generatedAt: string
  hubspotCompanyId?: string
  daysSinceFirstContact?: number
  outreachSummary?: OutreachSummary
  upscaleScore?: {
    totalScore: number
    tier: string
    gmvScore: number
    industryScore: number
    recognitionScore: number
    estimatedAnnualGmv: number | null
    industry: string | null
    platform?: string
    description?: string
    city?: string
    state?: string
    employees?: number
  }
}
