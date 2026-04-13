import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.PIPELINE_BACKEND_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const { domain } = await request.json();

    if (!domain || typeof domain !== "string") {
      return NextResponse.json(
        { error: "Missing or invalid domain" },
        { status: 400 },
      );
    }

    // Forward to the Python FastAPI backend
    const res = await fetch(`${BACKEND_URL}/api/pipeline/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ domain }),
    });

    if (!res.ok) {
      const text = await res.text();
      return NextResponse.json(
        { error: `Backend error: ${text}` },
        { status: res.status },
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    console.error("Pipeline start error:", err);
    return NextResponse.json(
      { error: "Pipeline backend is not reachable. Please ensure the API server is running on port 8000." },
      { status: 503 },
    );
  }
}
