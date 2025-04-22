import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Using provided Supabase credentials
const supabaseUrl = 'https://aubulhjfeszmsheonmpy.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzUyODc0MTIsImV4cCI6MjA1MDg2MzQxMn0.ovHMLKm5nN4o7_P_Pld1vEzPpL1uKZK1xxtWn3RMMJw';
const supabase = createClient(supabaseUrl, supabaseKey);

/**
 * POST handler for sending a scheduled message immediately
 */
export async function POST(request: NextRequest) {
  console.log('API called: POST /api/telegram-scheduler/send-now');
  
  try {
    // Parse request body
    const body = await request.json();
    const { id } = body;
    
    if (!id) {
      console.error('Request missing message ID');
      return NextResponse.json({ error: 'Missing message ID', success: false }, { status: 400 });
    }
    
    console.log('Sending scheduled message immediately:', id);
    
    // First get the scheduled message details
    const { data: message, error: fetchError } = await supabase
      .from('scheduled_messages')
      .select('*')
      .eq('id', id)
      .single();
    
    if (fetchError) {
      console.error('Error fetching message from Supabase:', fetchError);
      return NextResponse.json({ 
        error: `Failed to fetch message: ${fetchError.message}`, 
        success: false,
        details: fetchError
      }, { status: 500 });
    }
    
    if (!message) {
      console.error(`Message with ID ${id} not found`);
      return NextResponse.json({ error: 'Message not found', success: false }, { status: 404 });
    }
    
    console.log('Retrieved message details:', message);
    
    // Only allow sending pending messages
    if (message.status !== 'pending') {
      console.error(`Cannot send message with status: ${message.status}`);
      return NextResponse.json(
        { 
          error: `Cannot send message with status: ${message.status}`,
          success: false
        }, 
        { status: 400 }
      );
    }
    
    // Update the scheduled_time to now so it can be picked up by the scheduler immediately
    const now = new Date().toISOString();
    console.log(`Updating message ${id} scheduled_time to ${now}`);
    
    const { error: updateError } = await supabase
      .from('scheduled_messages')
      .update({ 
        scheduled_time: now,
        // Add a flag in the metadata to indicate this was manually sent
        metadata: { 
          ...message.metadata,
          manually_sent: true,
          original_scheduled_time: message.scheduled_time 
        }
      })
      .eq('id', id);
    
    if (updateError) {
      console.error('Error updating message time in Supabase:', updateError);
      return NextResponse.json({ 
        error: `Failed to update message for immediate delivery: ${updateError.message}`,
        success: false,
        details: updateError
      }, { status: 500 });
    }
    
    console.log('Message successfully scheduled for immediate delivery');
    
    return NextResponse.json({ 
      success: true,
      message: 'Message scheduled for immediate delivery'
    });
    
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error('Unexpected error in send-now handler:', errorMessage, error);
    return NextResponse.json({ 
      error: `Error processing request: ${errorMessage}`,
      success: false 
    }, { status: 500 });
  }
} 