import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// This middleware ensures routes are handled correctly
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Special handling for signin route
  if (pathname === '/signin') {
    const url = new URL('/', request.url);
    return NextResponse.rewrite(url);
  }
  
  // For all other routes, just proceed normally
  return NextResponse.next();
}

// Configure the matcher to include the signin route
export const config = {
  matcher: [
    '/',
    '/signin',
    '/login',
    '/clients/:path*',
    '/workouts/:path*',
  ],
}; 