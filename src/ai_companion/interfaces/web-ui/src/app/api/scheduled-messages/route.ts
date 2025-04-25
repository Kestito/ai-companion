import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Using provided Supabase credentials
const supabaseUrl = 'https://aubulhjfeszmsheonmpy.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzUyODc0MTIsImV4cCI6MjA1MDg2MzQxMn0.ovHMLKm5nN4o7_P_Pld1vEzPpL1uKZK1xxtWn3RMMJw';
const supabase = createClient(supabaseUrl, supabaseKey);

/**
 * GET handler for retrieving scheduled messages
 */
export async function GET(request: NextRequest) {
  console.log('API called: GET /api/scheduled-messages');
  const searchParams = request.nextUrl.searchParams;
  const patientId = searchParams.get('patientId');
  
  try {
    // Query scheduled_messages table
    console.log('Querying scheduled_messages table...');
    let query = supabase
      .from('scheduled_messages')
      .select('*');
      
    if (patientId) {
      query = query.eq('patient_id', patientId);
    }
    
    // Order by scheduled_time (newest first)
    query = query.order('scheduled_time', { ascending: false });
    
    const { data, error } = await query;
    
    if (error) {
      console.error('Error querying scheduled_messages table:', error);
      return NextResponse.json({ 
        messages: [],
        error: 'Failed to query scheduled_messages table: ' + error.message
      }, { status: 500 });
    }
    
    if (data && data.length > 0) {
      console.log(`Found ${data.length} scheduled messages`);
      
      // Process the messages to ensure consistent format
      const messages = data.map(msg => ({
        ...msg,
        // Ensure these properties exist with defaults if not present
        platform: msg.platform || 'telegram',
        status: msg.status || 'pending',
        priority: msg.priority || 5
      }));
      
      return NextResponse.json({ 
        messages: messages,
        count: messages.length
      });
    }
    
    // If no data found, return empty array
    console.log('No scheduled messages found');
    return NextResponse.json({ 
      messages: [],
      count: 0
    });
  } catch (error) {
    console.error('Error in GET handler:', error);
    return NextResponse.json({ 
      messages: [],
      error: 'Error processing request: ' + (error instanceof Error ? error.message : String(error))
    }, { status: 500 });
  }
} 