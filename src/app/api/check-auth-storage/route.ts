import { NextRequest, NextResponse } from 'next/server';
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
import { cookies } from 'next/headers';

/**
 * API endpoint to check authentication storage and session status
 * Useful for debugging authentication issues
 */
export async function GET(request: NextRequest) {
  try {
    // Create Supabase client for server-side operation
    const supabase = createRouteHandlerClient({ cookies });
    
    // Check server-side session
    const { data, error } = await supabase.auth.getSession();
    
    // Get auth-related cookie names
    const cookieNames = Array.from(cookies().getAll())
      .filter(cookie => 
        cookie.name.includes('auth') || 
        cookie.name.includes('supabase') ||
        cookie.name.includes('sb-')
      )
      .map(cookie => cookie.name);
    
    // Return diagnostic information
    return NextResponse.json({
      timestamp: new Date().toISOString(),
      server: {
        hasSession: !!data.session,
        error: error?.message || null,
        sessionExpiry: data.session?.expires_at 
          ? new Date(data.session.expires_at * 1000).toISOString() 
          : null,
        userId: data.session?.user?.id || null,
        cookieNames
      },
      storageKey: 'supabase.auth.token', // The standardized key we're using
      supportMessage: "Please check your browser's localStorage for 'supabase.auth.token' to verify client-side storage"
    });
  } catch (e) {
    console.error('Error in check-auth-storage route:', e);
    return NextResponse.json(
      { error: 'Error checking auth storage', details: (e as Error).message },
      { status: 500 }
    );
  }
} 