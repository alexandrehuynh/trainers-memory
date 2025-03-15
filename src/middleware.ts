import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// This middleware ensures routes are handled correctly
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Simply return the request for now - this just ensures routes are registered properly
  return NextResponse.next();
}

// Configure the matcher to include the signin route
export const config = {
  matcher: [
    '/',
    '/signin',
    '/clients/:path*',
    '/workouts/:path*',
  ],
}; 