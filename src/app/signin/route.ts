import { NextRequest, NextResponse } from 'next/server';

// This file ensures that Next.js properly registers the /signin route

export function GET(request: NextRequest) {
  // This just passes through to the page component
  return NextResponse.next();
} 