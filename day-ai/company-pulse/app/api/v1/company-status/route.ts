import { NextRequest, NextResponse } from 'next/server'
import { generateReport, normalizeDomain } from '@/lib/generate-report'

export const runtime = 'nodejs'

/**
 * GET /api/v1/company-status?domain=example.com
 *
 * Returns a full CompanyReport as JSON.
 *
 * Authentication:
 *   Authorization: Bearer <API_KEY>
 *   — or —
 *   x-api-key: <API_KEY>
 *
 * Query parameters:
 *   domain        (required) Company domain, e.g. "example.com". Accepts full
 *                 URLs — "https://example.com/path" is normalized to "example.com".
 *   send_slack    (optional) Pass "1" to send a Slack notification after generation.
 */
export async function GET(request: NextRequest) {
  // ── Auth ────────────────────────────────────────────────────
  const apiKey = process.env.API_KEY
  if (!apiKey) {
    return jsonError(500, 'SERVER_ERROR', 'API key not configured on server')
  }

  const providedKey =
    request.headers.get('x-api-key') ||
    request.headers.get('authorization')?.replace(/^Bearer\s+/i, '')

  if (!providedKey || providedKey !== apiKey) {
    return jsonError(401, 'UNAUTHORIZED', 'Invalid or missing API key')
  }

  // ── Params ──────────────────────────────────────────────────
  const rawDomain = request.nextUrl.searchParams.get('domain')
  if (!rawDomain) {
    return jsonError(400, 'INVALID_REQUEST', 'Missing required parameter: domain')
  }

  const domain = normalizeDomain(rawDomain)
  if (!domain || !domain.includes('.')) {
    return jsonError(400, 'INVALID_REQUEST', `Invalid domain: "${rawDomain}"`)
  }

  const sendSlack = request.nextUrl.searchParams.get('send_slack') === '1'

  // ── Generate ────────────────────────────────────────────────
  const startedAt = Date.now()
  console.log(`[v1/company-status] domain=${domain} sendSlack=${sendSlack}`)

  try {
    const report = await generateReport(domain, { sendSlack })

    console.log(`[v1/company-status] domain=${domain} duration=${Date.now() - startedAt}ms`)
    return NextResponse.json(report)
  } catch (error: any) {
    const duration = Date.now() - startedAt
    console.error(`[v1/company-status] domain=${domain} error=${error?.code} duration=${duration}ms`, error)

    if (error?.code === 'NOT_FOUND') {
      return jsonError(404, 'NOT_FOUND', error.message)
    }
    return jsonError(500, 'SERVER_ERROR', error instanceof Error ? error.message : 'Internal server error')
  }
}

// ── Helper ───────────────────────────────────────────────────

function jsonError(status: number, code: string, message: string) {
  return NextResponse.json({ error: { code, message } }, { status })
}
