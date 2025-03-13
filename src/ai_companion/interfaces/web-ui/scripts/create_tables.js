require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');

// Access environment variables
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing environment variables:');
  if (!supabaseUrl) console.error('- NEXT_PUBLIC_SUPABASE_URL');
  if (!supabaseKey) console.error('- SUPABASE_SERVICE_KEY or NEXT_PUBLIC_SUPABASE_ANON_KEY');
  process.exit(1);
}

// Initialize Supabase client
console.log('Creating Supabase client...');
const supabase = createClient(supabaseUrl, supabaseKey);

async function executeSQL() {
  try {
    console.log('\n========== PUBLIC SCHEMA TABLE CREATION ==========');
    console.log('Reading SQL file...');
    
    // Read the SQL file
    const sqlFilePath = path.join(__dirname, 'create_all_tables.sql');
    const sqlContent = fs.readFileSync(sqlFilePath, 'utf8');
    
    console.log('SQL file loaded successfully.');
    console.log('Connecting to Supabase...');
    
    // Execute the SQL using direct RPC call
    console.log('Executing SQL script...');
    const { data, error } = await supabase.rpc('run_sql_query', { 
      query: sqlContent 
    });
    
    if (error) {
      console.error('Error executing SQL script with RPC call:', error.message);
      console.log('\nIf RPC failed, you need to execute the SQL directly in the Supabase SQL editor.');
      console.log('1. Go to your Supabase dashboard at: https://app.supabase.com/project/_/sql');
      console.log('2. Copy and paste the following SQL:');
      console.log('----------');
      console.log(sqlContent);
      console.log('----------');
    } else {
      console.log('✅ SQL script executed successfully!');
      console.log('Tables have been created in the PUBLIC schema.');
      
      // Verify if tables exist
      console.log('\nVerifying tables...');
      await verifyTables();
    }
  } catch (err) {
    console.error('Script error:', err.message);
    process.exit(1);
  }
}

async function verifyTables() {
  const tables = [
    'patients',
    'conversations',
    'conversation_details',
    'short_term_memory',
    'long_term_memory',
    'scheduled_appointments',
    'risk_assessments',
    'reports',
    'scheduled_messages',
    'messages'
  ];
  
  let successCount = 0;
  
  for (const table of tables) {
    try {
      const { data, error } = await supabase
        .from(table)
        .select('count')
        .limit(1);
      
      if (error) {
        console.error(`❌ Table '${table}' might not exist or is not accessible:`, error.message);
      } else {
        console.log(`✅ Table '${table}' exists and is accessible.`);
        successCount++;
      }
    } catch (err) {
      console.error(`❌ Error verifying table '${table}':`, err.message);
    }
  }
  
  console.log(`\nVerification complete: ${successCount}/${tables.length} tables are accessible.`);
  
  if (successCount < tables.length) {
    console.log('\nNOTE: Some tables might not be accessible. Possible reasons:');
    console.log('1. SQL execution errors creating those tables');
    console.log('2. Permission issues for the current user');
    console.log('3. Search path configuration issues');
    
    console.log('\nTo grant permissions, execute:');
    console.log('GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;');
    console.log('GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;');
    console.log('ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO anon, authenticated, service_role;');
  } else {
    console.log('\n✅ All tables have been successfully created and are accessible!');
    console.log('Your application can now use the PUBLIC schema with these tables.');
  }
}

// Execute the main function
console.log('Starting table creation process...');
executeSQL().then(() => {
  console.log('\nProcess completed.');
}); 