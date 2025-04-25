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

// Scheduled messages table name without schema prefix
const SCHEDULED_MESSAGES_TABLE = 'scheduled_messages';

// POST /api/scheduler/send-now
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { messageId } = body;
    
    if (!messageId) {
      return NextResponse.json(
        { error: 'Missing message ID' },
        { status: 400 }
      );
    }
    
    const supabase = await createSupabaseClient();
    
    // Get the current message data
    const { data: messageData, error: fetchError } = await supabase
      .from(SCHEDULED_MESSAGES_TABLE)
      .select('*')
      .eq('id', messageId)
      .single();
    
    if (fetchError) {
      console.error('Error fetching message:', fetchError);
      return NextResponse.json(
        { error: fetchError.message },
        { status: 500 }
      );
    }
    
    if (!messageData) {
      return NextResponse.json(
        { error: 'Message not found' },
        { status: 404 }
      );
    }
    
    // Update metadata to indicate manual sending
    const metadata = {
      ...messageData.metadata,
      manually_sent: true,
      original_scheduled_time: messageData.scheduled_time
    };
    
    // Update the message status to 'sent'
    const { error: updateError } = await supabase
      .from(SCHEDULED_MESSAGES_TABLE)
      .update({
        status: 'sent',
        metadata: metadata
      })
      .eq('id', messageId);
    
    if (updateError) {
      console.error('Error updating message status:', updateError);
      return NextResponse.json(
        { error: updateError.message },
        { status: 500 }
      );
    }
    
    return NextResponse.json({
      success: true,
      message: 'Message marked as sent',
      id: messageId
    });
  } catch (error: any) {
    console.error('Failed to send message:', error);
    return NextResponse.json(
      { error: 'Failed to send message: ' + error.message },
      { status: 500 }
    );
  }
} 