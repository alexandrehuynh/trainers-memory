import { NextRequest, NextResponse } from 'next/server';
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
import { cookies } from 'next/headers';
import { validateClientData } from '@/lib/clientUtils';

export async function GET(request: NextRequest) {
  try {
    const supabase = createRouteHandlerClient({ cookies });
    
    // Ensure user is authenticated
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }
    
    // Get clients for the current user
    const { data, error } = await supabase
      .from('clients')
      .select('*')
      .eq('trainer_id', session.user.id)
      .order('created_at', { ascending: false });
    
    if (error) {
      console.error('[API] Error fetching clients:', error);
      return NextResponse.json(
        { error: error.message },
        { status: 500 }
      );
    }
    
    return NextResponse.json({ clients: data });
  } catch (error) {
    console.error('[API] Unexpected error in GET /api/clients:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const supabase = createRouteHandlerClient({ cookies });
    
    // Ensure user is authenticated
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }
    
    // Parse the request body
    const body = await request.json();
    
    // Validate client data
    try {
      const validationResult = validateClientData(body);
      if (!validationResult.success) {
        console.warn('[API] Client validation failed:', validationResult.errors);
        return NextResponse.json(
          { error: 'Validation failed', details: validationResult.errors },
          { status: 400 }
        );
      }
    } catch (validationError) {
      console.error('[API] Validation error:', validationError);
      return NextResponse.json(
        { error: 'Invalid client data' },
        { status: 400 }
      );
    }
    
    // Insert new client
    const { data, error } = await supabase
      .from('clients')
      .insert({
        ...body,
        trainer_id: session.user.id,
      })
      .select()
      .single();
    
    if (error) {
      console.error('[API] Error creating client:', error);
      
      // Handle specific error cases
      if (error.code === '23505') {
        return NextResponse.json(
          { error: 'A client with this information already exists' },
          { status: 409 }
        );
      }
      
      return NextResponse.json(
        { error: error.message },
        { status: 500 }
      );
    }
    
    return NextResponse.json({ client: data }, { status: 201 });
  } catch (error) {
    console.error('[API] Unexpected error in POST /api/clients:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function PUT(request: NextRequest) {
  try {
    const supabase = createRouteHandlerClient({ cookies });
    
    // Ensure user is authenticated
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }
    
    // Parse the request body
    const body = await request.json();
    const { id, ...clientData } = body;
    
    if (!id) {
      return NextResponse.json(
        { error: 'Client ID is required' },
        { status: 400 }
      );
    }
    
    // Validate client data
    try {
      const validationResult = validateClientData(clientData);
      if (!validationResult.success) {
        console.warn('[API] Client update validation failed:', validationResult.errors);
        return NextResponse.json(
          { error: 'Validation failed', details: validationResult.errors },
          { status: 400 }
        );
      }
    } catch (validationError) {
      console.error('[API] Validation error during update:', validationError);
      return NextResponse.json(
        { error: 'Invalid client data' },
        { status: 400 }
      );
    }
    
    // Verify client belongs to this trainer
    const { data: existingClient, error: fetchError } = await supabase
      .from('clients')
      .select('trainer_id')
      .eq('id', id)
      .single();
    
    if (fetchError) {
      if (fetchError.code === 'PGRST116') {
        return NextResponse.json(
          { error: 'Client not found' },
          { status: 404 }
        );
      }
      
      return NextResponse.json(
        { error: fetchError.message },
        { status: 500 }
      );
    }
    
    if (existingClient.trainer_id !== session.user.id) {
      return NextResponse.json(
        { error: 'Unauthorized to update this client' },
        { status: 403 }
      );
    }
    
    // Update client
    const { data, error } = await supabase
      .from('clients')
      .update(clientData)
      .eq('id', id)
      .select()
      .single();
    
    if (error) {
      console.error('[API] Error updating client:', error);
      return NextResponse.json(
        { error: error.message },
        { status: 500 }
      );
    }
    
    return NextResponse.json({ client: data });
  } catch (error) {
    console.error('[API] Unexpected error in PUT /api/clients:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
} 