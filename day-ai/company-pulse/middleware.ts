import { getToken } from 'next-auth/jwt'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Allow NextAuth routes
  if (pathname.startsWith('/api/auth')) {
    return NextResponse.next()
  }

  // Allow Slackbot access to report pages and PDF API
  if (pathname.startsWith('/api/report/')) {
    return NextResponse.next()
  }

  // Allow v1 API routes — they use API key auth, not session auth
  if (pathname.startsWith('/api/v1/')) {
    return NextResponse.next()
  }

  // Allow login page
  if (pathname === '/login') {
    return NextResponse.next()
  }

  // Allow static assets and Next.js internals
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/favicon') ||
    pathname.endsWith('.ico') ||
    pathname.endsWith('.png') ||
    pathname.endsWith('.svg')
  ) {
    return NextResponse.next()
  }

  // Check for valid session
  const token = await getToken({
    req: request,
    secret: process.env.NEXTAUTH_SECRET,
  })

  if (!token) {
    const loginUrl = new URL('/login', request.url)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image).*)'],
}
