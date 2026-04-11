import fs from 'fs'
import path from 'path'
import type { CompanyReport } from './types'

// Vercel serverless has a read-only filesystem; /tmp is the only writable path.
// Locally (or on GCP Cloud Run) we use data/reports under the project root.
const REPORTS_DIR = process.env.VERCEL
  ? path.join('/tmp', 'reports')
  : path.join(process.cwd(), 'data', 'reports')

// Ensure reports directory exists
function ensureReportsDir() {
  if (!fs.existsSync(REPORTS_DIR)) {
    fs.mkdirSync(REPORTS_DIR, { recursive: true })
  }
}

/**
 * Generate a unique report ID based on timestamp and organization
 */
export function generateReportId(organizationId: string): string {
  const timestamp = Date.now()
  const orgSlug = organizationId.replace(/[^a-z0-9]/gi, '-').toLowerCase()
  return `${orgSlug}-${timestamp}`
}

/**
 * Save a report to disk
 */
export function saveReport(report: CompanyReport): void {
  ensureReportsDir()
  const filePath = path.join(REPORTS_DIR, `${report.reportId}.json`)
  fs.writeFileSync(filePath, JSON.stringify(report, null, 2), 'utf-8')
}

/**
 * Load a report from disk
 */
export function loadReport(reportId: string): CompanyReport | null {
  try {
    const filePath = path.join(REPORTS_DIR, `${reportId}.json`)
    if (!fs.existsSync(filePath)) {
      return null
    }
    const data = fs.readFileSync(filePath, 'utf-8')
    return JSON.parse(data) as CompanyReport
  } catch (err) {
    console.error(`Failed to load report ${reportId}:`, err)
    return null
  }
}

/**
 * List all reports for an organization
 */
export function listReports(organizationId: string): Array<{ reportId: string; generatedAt: string }> {
  ensureReportsDir()
  const orgSlug = organizationId.replace(/[^a-z0-9]/gi, '-').toLowerCase()
  const files = fs.readdirSync(REPORTS_DIR)
  
  return files
    .filter((f) => f.startsWith(orgSlug) && f.endsWith('.json'))
    .map((f) => {
      const reportId = f.replace('.json', '')
      const filePath = path.join(REPORTS_DIR, f)
      const stats = fs.statSync(filePath)
      return {
        reportId,
        generatedAt: stats.mtime.toISOString(),
      }
    })
    .sort((a, b) => b.generatedAt.localeCompare(a.generatedAt))
}
