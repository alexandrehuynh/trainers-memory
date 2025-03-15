import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getJwtToken } from '@/lib/tokenHelper';

// This middleware ensures routes are handled correctly
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Get auth token from cookie
  const token = request.cookies.get('supabase-auth-token')?.value || 
                request.cookies.get('sb-auth-token')?.value;
  
  // Define protected routes
  const isProtectedRoute = pathname.startsWith('/clients') || 
                          pathname.startsWith('/workouts');
                          
  // Redirect to signin if accessing protected route without auth
  if (isProtectedRoute && !token) {
    return NextResponse.redirect(new URL('/signin', request.url));
  }
  
  // Allow all other requests to proceed
  return NextResponse.next();
}

// Configure the matcher to focus on protected routes
export const config = {
  matcher: [
    '/clients/:path*',
    '/workouts/:path*',
  ],
}; 