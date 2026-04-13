import { NextResponse } from "next/server";

const BACKEND_URL = process.env.PIPELINE_BACKEND_URL || "http://localhost:8000";

export async function GET() {
  try {
    const res = await fetch(`${BACKEND_URL}/api/reports`, {
      next: { revalidate: 30 },
    });

    if (!res.ok) {
      return NextResponse.json([]);
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    // Backend not running — return empty so the frontend shows demo data
    return NextResponse.json([]);
  }
}
