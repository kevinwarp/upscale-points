import { NextRequest, NextResponse } from 'next/server'
import { loadReport } from '@/lib/report-storage'

export const runtime = 'nodejs'

export async function GET(
  request: NextRequest,
  { params }: { params: { reportId: string } }
) {
  const reportId = params.reportId

  if (!reportId) {
    return NextResponse.json({ error: 'Missing reportId' }, { status: 400 })
  }

  const report = loadReport(reportId)

  if (!report) {
    return NextResponse.json(
      { error: `Report not found: ${reportId}` },
      { status: 404 }
    )
  }

  return NextResponse.json(report)
}
