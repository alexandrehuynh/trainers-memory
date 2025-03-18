import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
import { cookies } from 'next/headers';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // Create a Supabase client for the server
    const supabase = createRouteHandlerClient({ cookies });
    
    // Get the session data
    const { data, error } = await supabase.auth.getSession();
    
    // Retrieve local storage keys if possible
    const storageInfo = {
      note: "Storage cannot be directly accessed server-side"
    };
    
    return NextResponse.json({
      timestamp: new Date().toISOString(),
      path: request.url,
      hasSession: !!data.session,
      error: error?.message || null,
      sessionExpiry: data.session?.expires_at 
        ? new Date(data.session.expires_at * 1000).toISOString() 
        : null,
      user: data.session?.user 
        ? {
            id: data.session.user.id,
            email: data.session.user.email,
            role: data.session.user.app_metadata?.role || null,
          } 
        : null,
      storageInfo,
      cookies: {
        hasAuthCookie: request.cookies.has('supabase.auth.token'),
      },
    });
  } catch (e) {
    console.error('Error in debug-session route:', e);
    return NextResponse.json(
      { error: 'Error checking session', details: (e as Error).message },
      { status: 500 }
    );
  }
} 