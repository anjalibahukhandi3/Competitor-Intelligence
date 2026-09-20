import { NextResponse } from 'next/server'

// Paths that are always publicly accessible
const PUBLIC_PATHS = ['/', '/auth/login', '/auth/register', '/auth/forgot-password']

// Paths that redirect to /dashboard when user is already authenticated
const AUTH_ONLY_PATHS = ['/auth/login', '/auth/register', '/auth/forgot-password']

export function middleware(request) {
  const { pathname } = request.nextUrl

  // Pass through Next.js internals and static assets immediately
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname === '/favicon.ico' ||
    pathname.includes('.')
  ) {
    return NextResponse.next()
  }

  // Read the access token written by api.js via js-cookie (client-side cookie)
  const token = request.cookies.get('access_token')?.value ?? null
  const isAuthenticated = Boolean(token && token.length > 0)

  // Authenticated user trying to hit a login/register page → send to dashboard
  if (isAuthenticated && AUTH_ONLY_PATHS.includes(pathname)) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  // Unauthenticated user trying to access a protected page → send to login
  if (!isAuthenticated && !PUBLIC_PATHS.includes(pathname)) {
    return NextResponse.redirect(new URL('/auth/login', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
