import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// This middleware ensures routes are handled correctly
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Define protected routes
  const isProtectedRoute = pathname.startsWith('/clients') || 
                          pathname.startsWith('/workouts');
  
  if (!isProtectedRoute) {
    // If it's not a protected route, allow access
    return NextResponse.next();
  }
  
  // Get auth tokens from cookies - check multiple possible cookie names used by Supabase
  const supabaseCookie = request.cookies.get('supabase-auth-token');
  const sbAuthCookie = request.cookies.get('sb-auth-token');
  const authCookie = request.cookies.get('sb-access-token');
  
  // Extract project ref if available for more specific cookie names
  const projectRef = process.env.NEXT_PUBLIC_SUPABASE_URL?.match(/([^/.]+)\.supabase/)?.[1];
  const projectSpecificCookie = projectRef ? request.cookies.get(`sb-${projectRef}-auth-token`) : null;
  
  // Check for Supabase session cookie - this is usually the most reliable indicator
  const hasSession = 
    (supabaseCookie?.value && supabaseCookie.value.includes('access_token')) || 
    (sbAuthCookie?.value && sbAuthCookie.value.includes('access_token')) || 
    (authCookie?.value && authCookie.value.includes('access_token')) ||
    (projectSpecificCookie?.value && projectSpecificCookie.value.includes('access_token'));
  
  // For debugging - log what cookies we found
  if (process.env.NODE_ENV === 'development') {
    console.log('Auth cookies check on route ' + pathname + ':', {
      supabaseCookie: supabaseCookie?.value ? supabaseCookie.value.substring(0, 20) + '...' : null,
      sbAuthCookie: sbAuthCookie?.value ? sbAuthCookie.value.substring(0, 20) + '...' : null,
      authCookie: authCookie?.value ? authCookie.value.substring(0, 20) + '...' : null,
      projectSpecificCookie: projectSpecificCookie?.value ? projectSpecificCookie.value.substring(0, 20) + '...' : null,
      hasSession,
      projectRef
    });
  }
  
  // Try to parse auth token content to see if it contains an access token object
  let hasValidToken = hasSession;
  
  if (!hasValidToken && sbAuthCookie?.value) {
    try {
      const tokenData = JSON.parse(decodeURIComponent(sbAuthCookie.value));
      if (tokenData && (tokenData.access_token || tokenData.token)) {
        hasValidToken = true;
      }
    } catch (e) {
      // Invalid JSON in cookie, continue with normal flow
      console.error('Error parsing auth cookie:', e);
    }
  }
  
  // Only redirect to signin if no valid auth cookie exists
  if (!hasValidToken) {
    console.log(`No valid session found, redirecting from ${pathname} to /signin`);
    return NextResponse.redirect(new URL('/signin', request.url));
  }
  
  // If development mode is enabled, enable detailed logging
  if (process.env.NODE_ENV === 'development') {
    console.log(`Allowed access to ${pathname} - user has valid session`);
  }
  
  // Allow the request to proceed to protected route
  return NextResponse.next();
}

// Configure the matcher to focus only on protected routes
export const config = {
  matcher: [
    '/clients/:path*',
    '/workouts/:path*',
  ],
}; 