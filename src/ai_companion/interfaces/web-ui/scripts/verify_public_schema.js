require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');

// Add direct console logging for debugging
console.log('Script started - verify_public_schema.js');

// Access environment variables
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

console.log('Environment variables:');
console.log('- NEXT_PUBLIC_SUPABASE_URL:', supabaseUrl ? 'Set' : 'Not set');
console.log('- SUPABASE_SERVICE_KEY:', supabaseKey ? 'Set' : 'Not set');

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing environment variables:');
  if (!supabaseUrl) console.error('- NEXT_PUBLIC_SUPABASE_URL');
  if (!supabaseKey) console.error('- SUPABASE_SERVICE_KEY or NEXT_PUBLIC_SUPABASE_ANON_KEY');
  process.exit(1);
}

// Initialize Supabase client
console.log('Creating Supabase client...');
const supabase = createClient(supabaseUrl, supabaseKey);

// Tables to verify
const tables = [
  'patients',
  'conversations',
  'conversation_details',
  'short_term_memory',
  'long_term_memory',
  'scheduled_appointments',
  'risk_assessments',
  'reports'
];

async function verifyTable(tableName) {
  console.log(`\nVerifying table: ${tableName}`);
  
  try {
    // Try to select a single row from the table
    const { data, error } = await supabase
      .from(tableName)
      .select('*')
      .limit(1);
    
    if (error) {
      console.error(`❌ Error accessing ${tableName}:`, error.message);
      return false;
    }
    
    console.log(`✅ Successfully accessed ${tableName}`);
    console.log(`   Data rows: ${data ? data.length : 0}`);
    return true;
  } catch (err) {
    console.error(`❌ Exception when accessing ${tableName}:`, err.message);
    return false;
  }
}

async function main() {
  console.log('==== Public Schema Verification ====');
  console.log('Script started');
  console.log('Node version:', process.version);
  console.log('Connecting to Supabase at:', supabaseUrl);
  
  try {
    // Check connection
    console.log('\nTesting connection to Supabase...');
    const { data, error } = await supabase.from('patients').select('count').limit(1);
    
    if (error) {
      console.error('❌ Connection test failed:', error.message);
      console.error('Please check your Supabase URL and key.');
      return;
    }
    
    console.log('✅ Connected to Supabase successfully!');
    
    // Check tables in public schema
    console.log('\n==== Verifying Tables in Public Schema ====');
    
    let successCount = 0;
    let failCount = 0;
    
    for (const table of tables) {
      const success = await verifyTable(table);
      if (success) {
        successCount++;
      } else {
        failCount++;
      }
    }
    
    console.log('\n==== Verification Summary ====');
    console.log(`Total tables checked: ${tables.length}`);
    console.log(`Tables found: ${successCount}`);
    console.log(`Tables not found: ${failCount}`);
    
    if (failCount > 0) {
      console.log('\n❌ Some tables were not found in the public schema.');
      console.log('Possible reasons:');
      console.log('  - Tables haven\'t been created in the public schema yet');
      console.log('  - Tables exist but are in a different schema (e.g., evelinaai)');
      console.log('  - Permission issues with the current Supabase key');
      console.log('\nPlease run the create_public_schema_tables.sql script to create the tables in the public schema.');
    } else {
      console.log('\n✅ All tables verified successfully in the public schema!');
      console.log('Your application can now access these tables directly without a schema prefix.');
    }
    
  } catch (err) {
    console.error('Script error:', err.message);
  }
  
  console.log('\nScript completed');
}

main(); 