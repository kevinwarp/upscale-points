import { NextRequest, NextResponse } from 'next/server'
import { renderToBuffer } from '@react-pdf/renderer'
import { CompanyStatusPDF } from '@/lib/pdf-report'
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

  try {
    const pdfBuffer = await renderToBuffer(<CompanyStatusPDF report={report} />)

    return new NextResponse(new Uint8Array(pdfBuffer), {
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': `attachment; filename="${report.organization.name.replace(/\s+/g, '_')}_status_report.pdf"`,
      },
    })
  } catch (error) {
    console.error('PDF generation failed:', error)
    return NextResponse.json(
      { error: 'Failed to generate PDF' },
      { status: 500 }
    )
  }
}
