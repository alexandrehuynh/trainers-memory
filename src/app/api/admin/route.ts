import { createClient } from '@supabase/supabase-js';
import { NextRequest, NextResponse } from 'next/server';
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
import { cookies } from 'next/headers';

// Create a Supabase client with the service role key (only on server)
const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!, // Never expose this in client code!
  {
    auth: {
      persistSession: false,
    }
  }
);

// Example admin API route
export async function GET(request: NextRequest) {
  try {
    // Verify user is authenticated and has admin role
    const supabaseAuth = createRouteHandlerClient({ cookies });
    const { data: { session } } = await supabaseAuth.auth.getSession();
    
    if (!session) {
      return NextResponse.json(
        { error: 'Unauthorized - Not authenticated' },
        { status: 401 }
      );
    }
    
    // Verify user has admin role
    const role = session.user?.app_metadata?.role;
    if (role !== 'admin') {
      return NextResponse.json(
        { error: 'Forbidden - Admin role required', role },
        { status: 403 }
      );
    }
    
    // Perform admin operation - this bypasses RLS
    const { data, error } = await supabaseAdmin
      .from('clients')
      .select('*');
    
    if (error) {
      console.error('Admin API error:', error);
      return NextResponse.json(
        { error: 'Database error', details: error.message },
        { status: 500 }
      );
    }
    
    return NextResponse.json({ data });
  } catch (error: any) {
    console.error('Admin API exception:', error);
    return NextResponse.json(
      { error: 'Server error', details: error.message },
      { status: 500 }
    );
  }
}

// Admin API route to create user with specific role
export async function POST(request: NextRequest) {
  try {
    // Verify requester is authenticated and has admin role
    const supabaseAuth = createRouteHandlerClient({ cookies });
    const { data: { session } } = await supabaseAuth.auth.getSession();
    
    if (!session || session.user?.app_metadata?.role !== 'admin') {
      return NextResponse.json(
        { error: 'Unauthorized - Admin access required' },
        { status: 403 }
      );
    }
    
    // Parse the request body
    const { email, password, role = 'trainer' } = await request.json();
    
    if (!email || !password) {
      return NextResponse.json(
        { error: 'Bad request - email and password required' },
        { status: 400 }
      );
    }
    
    // Create user with service role client
    const { data: userData, error: userError } = await supabaseAdmin.auth.admin.createUser({
      email,
      password,
      email_confirm: true,
      app_metadata: { role }
    });
    
    if (userError) {
      console.error('Error creating user:', userError);
      return NextResponse.json(
        { error: 'Failed to create user', details: userError.message },
        { status: 500 }
      );
    }
    
    return NextResponse.json({ 
      success: true,
      message: 'User created successfully',
      user: {
        id: userData.user.id,
        email: userData.user.email,
        role
      }
    });
  } catch (error: any) {
    console.error('Exception in admin user creation:', error);
    return NextResponse.json(
      { error: 'Server error', details: error.message },
      { status: 500 }
    );
  }
} 