import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Using provided Supabase credentials
const supabaseUrl = 'https://aubulhjfeszmsheonmpy.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzUyODc0MTIsImV4cCI6MjA1MDg2MzQxMn0.ovHMLKm5nN4o7_P_Pld1vEzPpL1uKZK1xxtWn3RMMJw';
const supabase = createClient(supabaseUrl, supabaseKey);

// Scheduled messages table name without schema prefix
const SCHEDULED_MESSAGES_TABLE = 'scheduled_messages';

// POST /api/scheduled-messages/create
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { patientId, chatId, messageContent, scheduledTime, platform, priority, delivery_window_seconds, metadata } = body;
    
    if (!patientId || !messageContent || !scheduledTime) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }
    
    // Build the message object matching the schema and existing data
    const messageObject = {
      patient_id: patientId,
      message_content: messageContent,
      scheduled_time: scheduledTime,
      status: 'pending',
      platform: platform || 'telegram',
      priority: priority || 5,
      delivery_window_seconds: delivery_window_seconds || 60,
      attempts: 0,
      metadata: {
        ...metadata || {},
        platform_data: {
          chat_id: chatId // Store chat_id in platform_data.chat_id
        }
      }
    };
    
    console.log('Creating scheduled message:', messageObject);
    
    // Insert the message
    const { data, error } = await supabase
      .from(SCHEDULED_MESSAGES_TABLE)
      .insert(messageObject)
      .select()
      .single();
    
    if (error) {
      console.error('Error creating scheduled message:', error);
      return NextResponse.json(
        { error: error.message },
        { status: 500 }
      );
    }
    
    return NextResponse.json({
      success: true,
      messageData: data
    });
  } catch (error: any) {
    console.error('Failed to create scheduled message:', error);
    return NextResponse.json(
      { error: 'Failed to create scheduled message: ' + error.message },
      { status: 500 }
    );
  }
} 