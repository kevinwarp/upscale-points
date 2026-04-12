import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.PIPELINE_BACKEND_URL || "http://localhost:8000";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ runId: string }> },
) {
  const { runId } = await params;

  try {
    const res = await fetch(`${BACKEND_URL}/api/pipeline/status/${runId}`, {
      cache: "no-store",
    });

    if (!res.ok) {
      return NextResponse.json(
        { error: "Run not found" },
        { status: res.status },
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { error: "Backend unavailable" },
      { status: 503 },
    );
  }
}
