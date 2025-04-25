import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Using provided Supabase credentials
const supabaseUrl = 'https://aubulhjfeszmsheonmpy.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzUyODc0MTIsImV4cCI6MjA1MDg2MzQxMn0.ovHMLKm5nN4o7_P_Pld1vEzPpL1uKZK1xxtWn3RMMJw';
const supabase = createClient(supabaseUrl, supabaseKey);

/**
 * GET handler for retrieving patients for the scheduler
 */
export async function GET(request: NextRequest) {
  console.log('API called: GET /api/patients/forNewScheduler');
  
  try {
    // Build simple query to get all patients
    let query = supabase
      .from('patients')
      .select('*');
    
    const { data, error } = await query;
    
    if (error) {
      console.error('Error querying patients for scheduler:', error);
      return NextResponse.json({ 
        patients: [],
        error: 'Failed to query patients: ' + error.message
      }, { status: 500 });
    }
    
    if (data && data.length > 0) {
      console.log(`Found ${data.length} patients for scheduler`);
      
      // Map the data to our expected format
      const processedPatients = data.map(patient => ({
        id: patient.id || '',
        name: patient.name || `${patient.first_name || ''} ${patient.last_name || ''}`.trim() || 'Unnamed',
        first_name: patient.first_name || '',
        last_name: patient.last_name || '',
        channel: patient.channel || patient.preferred_channel || '',
        email: patient.email || '',
        phone: patient.phone || '',
        created_at: patient.created_at || '',
        last_active: patient.last_active || ''
      }));
      
      return NextResponse.json({ 
        patients: processedPatients,
        count: processedPatients.length
      });
    }
    
    // If no patients found, return empty array
    console.log('No patients found');
    return NextResponse.json({ 
      patients: [],
      count: 0
    });
  } catch (error) {
    console.error('Error in GET handler:', error);
    return NextResponse.json({ 
      patients: [],
      error: 'Error processing request: ' + (error instanceof Error ? error.message : String(error))
    }, { status: 500 });
  }
} 