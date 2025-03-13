import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import { v4 as uuidv4 } from 'uuid';

// Avoid using imported helper functions that might have "use server" directives
// Instead, create a direct client here
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

// Scheduled messages table name without schema prefix
const SCHEDULED_MESSAGES_TABLE = 'scheduled_messages';

// GET /api/scheduled-messages
export async function GET(request: NextRequest) {
  try {
    const supabase = await createSupabaseClient();
    
    const { data, error } = await supabase
      .from(SCHEDULED_MESSAGES_TABLE)
      .select('*')
      .order('scheduled_time', { ascending: true });
    
    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json(
      { error: 'Failed to fetch scheduled messages: ' + error.message },
      { status: 500 }
    );
  }
}

// POST /api/scheduled-messages
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const supabase = await createSupabaseClient();
    
    // Validate required fields
    if (!body.recipientId || !body.platform || !body.message || !body.scheduledTime) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }
    
    const messageData = {
      id: uuidv4(),
      recipient_id: body.recipientId,
      platform: body.platform.toLowerCase(),
      message_content: body.message,
      scheduled_time: body.scheduledTime,
      recurrence_pattern: body.recurrence || null,
      status: 'pending',
      created_at: new Date().toISOString(),
    };
    
    const { data, error } = await supabase
      .from(SCHEDULED_MESSAGES_TABLE)
      .insert(messageData)
      .select()
      .single();
    
    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json(
      { error: 'Failed to create scheduled message: ' + error.message },
      { status: 500 }
    );
  }
} 