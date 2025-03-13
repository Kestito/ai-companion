require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');

// Log script start
console.log('==== Public Schema Setup Script ====');
console.log('This script will set up the public schema with the new structure');

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

// Function to execute SQL file
async function executeSqlFile(filename) {
  console.log(`\nExecuting SQL file: ${filename}`);
  
  try {
    const filePath = path.join(__dirname, filename);
    const sql = fs.readFileSync(filePath, 'utf8');
    
    // Execute the SQL using Supabase's stored procedure (if available)
    // Alternatively, we will need to split the SQL into separate statements
    const { data, error } = await supabase.rpc('run_sql_query', { query: sql });
    
    if (error) {
      console.error(`Error executing ${filename}:`, error.message);
      return false;
    }
    
    console.log(`✅ Successfully executed ${filename}`);
    return true;
  } catch (err) {
    console.error(`Exception when executing ${filename}:`, err.message);
    return false;
  }
}

// Main function
async function main() {
  try {
    // Test connection
    console.log('\nTesting connection to Supabase...');
    const { data, error } = await supabase.from('patients').select('count').limit(1);
    
    if (error && error.code !== 'PGRST116' && !error.message.includes('does not exist')) {
      console.error('❌ Connection test failed with unexpected error:', error.message);
      console.error('Please check your Supabase URL and key.');
      return;
    }
    
    console.log('✅ Connected to Supabase successfully!');
    
    // Execute SQL files in order
    console.log('\n==== Setting up Public Schema ====');
    
    // Step 1: Create tables in public schema
    const createTablesSuccess = await executeSqlFile('create_public_schema_tables.sql');
    if (!createTablesSuccess) {
      console.error('❌ Failed to create public schema tables. Aborting process.');
      return;
    }
    
    // Step 2: Migrate data from evelinaai schema to public schema
    const migrateDataSuccess = await executeSqlFile('migrate_to_public_schema.sql');
    if (!migrateDataSuccess) {
      console.warn('⚠️ Data migration encountered issues, but continuing with verification.');
    }
    
    // Step 3: Verify the tables
    console.log('\n==== Running Verification ====');
    const verifyProcess = require('./verify_public_schema');
    
    console.log('\n✅ Setup process completed!');
    console.log('You can now use the tables in the public schema directly without a schema prefix.');
    
  } catch (err) {
    console.error('Script error:', err.message);
  }
}

// Run the script
main(); 