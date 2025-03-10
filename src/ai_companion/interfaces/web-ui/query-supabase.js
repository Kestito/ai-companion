const { createClient } = require('@supabase/supabase-js');

// Supabase credentials from env file
const supabaseUrl = 'https://aubulhjfeszmsheonmpy.supabase.co';
// Using service role key instead of anon key
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc';

// Create Supabase client
const supabase = createClient(supabaseUrl, supabaseKey);

async function queryData() {
  console.log('Querying Supabase for evelinaai schema data...');
  console.log('===========================================');
  
  // Query users
  console.log('Users:');
  console.log('-------------------------------------------');
  const { data: users, error: usersError } = await supabase
    .from('users')
    .select('*')
    .schema('evelinaai')
    .limit(3);
  
  if (usersError) {
    console.error('Error fetching users:', usersError);
  } else {
    console.log(JSON.stringify(users, null, 2));
  }
  
  // Query conversations
  console.log('\nConversations:');
  console.log('-------------------------------------------');
  const { data: conversations, error: conversationsError } = await supabase
    .from('conversations')
    .select('*')
    .schema('evelinaai')
    .limit(3);
  
  if (conversationsError) {
    console.error('Error fetching conversations:', conversationsError);
  } else {
    console.log(JSON.stringify(conversations, null, 2));
  }
  
  // Query conversation details
  console.log('\nConversation Details:');
  console.log('-------------------------------------------');
  const { data: messages, error: messagesError } = await supabase
    .from('conversation_details')
    .select('*')
    .schema('evelinaai')
    .limit(3);
  
  if (messagesError) {
    console.error('Error fetching conversation details:', messagesError);
  } else {
    console.log(JSON.stringify(messages, null, 2));
  }
  
  // Query risk assessments
  console.log('\nRisk Assessments:');
  console.log('-------------------------------------------');
  const { data: risks, error: risksError } = await supabase
    .from('risk_assessments')
    .select('*')
    .schema('evelinaai')
    .limit(3);
  
  if (risksError) {
    console.error('Error fetching risk assessments:', risksError);
  } else {
    console.log(JSON.stringify(risks, null, 2));
  }
  
  // Query scheduled appointments
  console.log('\nScheduled Appointments:');
  console.log('-------------------------------------------');
  const { data: appointments, error: appointmentsError } = await supabase
    .from('scheduled_appointments')
    .select('*')
    .schema('evelinaai')
    .limit(3);
  
  if (appointmentsError) {
    console.error('Error fetching appointments:', appointmentsError);
  } else {
    console.log(JSON.stringify(appointments, null, 2));
  }
}

queryData().catch(console.error); 