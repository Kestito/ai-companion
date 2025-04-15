import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Using provided Supabase credentials
const supabaseUrl = 'https://aubulhjfeszmsheonmpy.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzUyODc0MTIsImV4cCI6MjA1MDg2MzQxMn0.ovHMLKm5nN4o7_P_Pld1vEzPpL1uKZK1xxtWn3RMMJw';
const supabase = createClient(supabaseUrl, supabaseKey);

/**
 * GET handler for retrieving patients, optionally filtering by channel type
 */
export async function GET(request: NextRequest) {
  console.log('API called: GET /api/patients');
  const searchParams = request.nextUrl.searchParams;
  const telegramOnly = searchParams.get('telegramOnly') === 'true';
  
  try {
    // Try patients table first
    console.log('Querying patients table...');
    let query = supabase
      .from('patients')
      .select('*');
      
    if (telegramOnly) {
      query = query.eq('channel', 'telegram');
    }
    
    const { data: patientsData, error: patientsError } = await query;
    
    if (patientsError) {
      console.error('Error querying patients table:', patientsError);
      return NextResponse.json({ 
        patients: [],
        error: 'Failed to query patients table: ' + patientsError.message
      }, { status: 500 });
    }
    
    if (patientsData && patientsData.length > 0) {
      console.log(`Found ${patientsData.length} patients in patients table`);
      
      // Map the data to our expected format
      const processedPatients = patientsData.map(patient => ({
        id: patient.id || '',
        name: patient.name || `${patient.first_name || ''} ${patient.last_name || ''}`.trim() || 'Unnamed',
        first_name: patient.first_name || '',
        last_name: patient.last_name || '',
        telegram_id: patient.telegram_id || '',
        channel: patient.channel || patient.preferred_channel || '',
        email: patient.email || '',
        phone: patient.phone || '',
        created_at: patient.created_at || '',
        last_active: patient.last_active || ''
      }));
      
      return NextResponse.json({ patients: processedPatients });
    }
    
    // If no data found in patients table, try conversations table
    console.log('No data in patients table, trying conversations...');
    const { data: convoData, error: convoError } = await supabase
      .from('conversations')
      .select('patient_id')
      .eq('conversation_type', 'text');
      
    if (convoError) {
      console.error('Error querying conversations table:', convoError);
    } else if (convoData && convoData.length > 0) {
      // Get unique patient IDs
      const patientIds = [...new Set(convoData.map(convo => convo.patient_id))];
      
      if (patientIds.length > 0) {
        console.log(`Found ${patientIds.length} unique patients through conversations`);
        
        // Query patients by these IDs
        const { data: patientsById, error: patientsByIdError } = await supabase
          .from('patients')
          .select('*')
          .in('id', patientIds);
          
        if (patientsByIdError) {
          console.error('Error querying patients by IDs:', patientsByIdError);
        } else if (patientsById && patientsById.length > 0) {
          const processedPatients = patientsById.map(patient => ({
            id: patient.id || '',
            name: patient.name || `${patient.first_name || ''} ${patient.last_name || ''}`.trim() || 'Unnamed',
            first_name: patient.first_name || '',
            last_name: patient.last_name || '',
            telegram_id: patient.telegram_id || '',
            channel: patient.channel || 'telegram',
            email: patient.email || '',
            phone: patient.phone || '',
            created_at: patient.created_at || '',
            last_active: patient.last_active || ''
          }));
          
          return NextResponse.json({ patients: processedPatients });
        }
      }
    }
    
    // If we still don't have data, try the messages table
    console.log('No data via conversations, trying messages table...');
    const { data: messagesData, error: messagesError } = await supabase
      .from('messages')
      .select('patient_id')
      .limit(100);
      
    if (messagesError) {
      console.error('Error querying messages table:', messagesError);
    } else if (messagesData && messagesData.length > 0) {
      // Get unique patient IDs
      const patientIds = [...new Set(messagesData.map(msg => msg.patient_id))];
      
      if (patientIds.length > 0) {
        console.log(`Found ${patientIds.length} unique patients through messages`);
        
        // Query patients by these IDs
        const { data: patientsById, error: patientsByIdError } = await supabase
          .from('patients')
          .select('*')
          .in('id', patientIds);
          
        if (patientsByIdError) {
          console.error('Error querying patients by IDs:', patientsByIdError);
        } else if (patientsById && patientsById.length > 0) {
          const processedPatients = patientsById.map(patient => ({
            id: patient.id || '',
            name: patient.name || `${patient.first_name || ''} ${patient.last_name || ''}`.trim() || 'Unnamed',
            first_name: patient.first_name || '',
            last_name: patient.last_name || '',
            telegram_id: patient.telegram_id || '',
            channel: patient.channel || 'telegram',
            email: patient.email || '',
            phone: patient.phone || '',
            created_at: patient.created_at || '',
            last_active: patient.last_active || ''
          }));
          
          return NextResponse.json({ patients: processedPatients });
        }
      }
    }
    
    // If all attempts fail, return empty array
    console.log('No patient data found in any tables');
    return NextResponse.json({ 
      patients: [],
      error: 'No patient data found in database'
    });
      
  } catch (error) {
    console.error('Error in GET handler:', error);
    return NextResponse.json({ 
      patients: [],
      error: 'Error processing request: ' + (error instanceof Error ? error.message : String(error))
    }, { status: 500 });
  }
} 