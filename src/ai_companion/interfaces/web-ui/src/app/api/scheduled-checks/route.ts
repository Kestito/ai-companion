import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Create a direct client here to avoid "use server" directive issues
const createSupabaseClient = async () => {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  
  if (!supabaseUrl || !supabaseKey) {
    throw new Error('Missing Supabase credentials');
  }
  
  return createClient(supabaseUrl, supabaseKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false
    }
  });
};

// Table name without schema prefix since we're using the public schema
const SCHEDULED_CHECKS_TABLE = 'scheduled_checks';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const patientId = searchParams.get('patientId');
    
    if (!patientId) {
      return NextResponse.json(
        { error: 'Patient ID is required' },
        { status: 400 }
      );
    }
    
    const supabase = await createSupabaseClient();
    
    const { data, error } = await supabase
      .from(SCHEDULED_CHECKS_TABLE)
      .select('*')
      .eq('patient_id', patientId)
      .order('next_scheduled', { ascending: true });
    
    if (error) {
      return NextResponse.json(
        { error: 'Failed to fetch scheduled checks: ' + error.message },
        { status: 500 }
      );
    }
    
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json(
      { error: 'Internal server error: ' + error.message },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Validate required fields
    if (!body.title || !body.patientId || !body.nextScheduled || !body.frequency || !body.platform) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }
    
    const supabase = await createSupabaseClient();
    
    const { data, error } = await supabase
      .from(SCHEDULED_CHECKS_TABLE)
      .insert([{
        title: body.title,
        description: body.description || '',
        frequency: body.frequency,
        next_scheduled: new Date(body.nextScheduled).toISOString(),
        status: 'pending',
        platform: body.platform,
        patient_id: body.patientId
      }])
      .select()
      .single();
    
    if (error) {
      return NextResponse.json(
        { error: 'Failed to create scheduled check: ' + error.message },
        { status: 500 }
      );
    }
    
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json(
      { error: 'Internal server error: ' + error.message },
      { status: 500 }
    );
  }
} 