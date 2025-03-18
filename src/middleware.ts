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
  
  // Get auth token from cookies - using only our standardized format
  const authCookie = request.cookies.get('supabase-auth-token');
  
  // Check for a valid session in the cookie
  const hasSession = authCookie?.value && authCookie.value.includes('access_token');
  
  // For debugging - log what cookies we found
  if (process.env.NODE_ENV === 'development') {
    console.log('Auth check on route ' + pathname + ':', {
      hasAuthCookie: !!authCookie,
      hasValidTokenStructure: hasSession,
      cookieCount: request.cookies.getAll().length
    });
  }
  
  // Only redirect to signin if no valid auth cookie exists
  if (!hasSession) {
    if (process.env.NODE_ENV === 'development') {
      console.log(`No valid session found, redirecting from ${pathname} to /signin`);
    }
    return NextResponse.redirect(new URL('/signin', request.url));
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