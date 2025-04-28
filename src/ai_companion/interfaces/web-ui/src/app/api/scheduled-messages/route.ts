import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import { FORCE_REAL_DATA } from '@/lib/config';

// Get Supabase credentials from environment variables
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://aubulhjfeszmsheonmpy.supabase.co';
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzUyODc0MTIsImV4cCI6MjA1MDg2MzQxMn0.ovHMLKm5nN4o7_P_Pld1vEzPpL1uKZK1xxtWn3RMMJw';

/**
 * GET handler for retrieving scheduled messages
 */
export async function GET(request: NextRequest) {
  console.log('API called: GET /api/scheduled-messages');
  const searchParams = request.nextUrl.searchParams;
  const patientId = searchParams.get('patientId');
  
  try {
    // Create Supabase client
    const supabase = createClient(supabaseUrl, supabaseKey);
    
    // Verify database connection when forcing real data
    if (FORCE_REAL_DATA) {
      try {
        const { error: healthError } = await supabase.from('health_check').select('count', { count: 'exact', head: true });
        if (healthError) {
          console.error('Database connection check failed:', healthError);
          return NextResponse.json({
            messages: [],
            error: 'Database connection error. Check configuration.'
          }, { status: 503 });
        }
      } catch (healthErr) {
        console.error('Health check error:', healthErr);
      }
    }
    
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