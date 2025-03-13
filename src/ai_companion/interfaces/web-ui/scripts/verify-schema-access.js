/**
 * This script verifies different approaches for accessing the evelinaai schema
 * Run with: node scripts/verify-schema-access.js
 */

require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');

console.log('Starting schema access verification...');
console.log('Node version:', process.version);

// Check if environment variables are set
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('Environment variables not set:');
  if (!supabaseUrl) console.error('- NEXT_PUBLIC_SUPABASE_URL is missing');
  if (!supabaseKey) console.error('- SUPABASE_SERVICE_KEY or NEXT_PUBLIC_SUPABASE_ANON_KEY is missing');
  process.exit(1);
}

console.log('Environment variables set:');
console.log('- NEXT_PUBLIC_SUPABASE_URL is set');
console.log('- SUPABASE_SERVICE_KEY/NEXT_PUBLIC_SUPABASE_ANON_KEY is set');

// Initialize Supabase client
const supabase = createClient(supabaseUrl, supabaseKey);

// List of tables to check in public schema
const TABLES = [
  'patients',
  'conversations',
  'conversation_details',
  'short_term_memory', 
  'long_term_memory',
  'risk_assessments',
  'scheduled_appointments',
  'reports',
  'scheduled_messages',
  'messages'
];

async function checkSchemaPrivileges() {
  console.log('\nChecking PUBLIC schema privileges...');
  
  try {
    // Check USAGE privilege on schema using run_sql_query function
    const { data, error } = await supabase.rpc('run_sql_query', {
      query: "SELECT has_schema_privilege(current_user, 'public', 'USAGE') as has_usage;"
    });
    
    if (error) {
      console.error('Error checking schema privileges with RPC:', error.message);
      console.log('Trying alternative approach...');
      
      // If direct SQL failed, try to access a table in the schema
      const { data: testData, error: testError } = await supabase
        .from('patients')
        .select('count')
        .limit(1);
      
      if (testError && testError.code === '42501') {
        console.error('❌ No USAGE privilege on public schema');
        return false;
      } else if (testError) {
        // If error is not permission denied, table might not exist
        console.log('ℹ️ Could not verify schema privileges directly');
      } else {
        console.log('✅ PUBLIC schema is accessible');
        return true;
      }
    } else {
      const hasUsage = data[0]?.has_usage;
      if (hasUsage) {
        console.log('✅ PUBLIC schema has USAGE privilege');
        return true;
      } else {
        console.error('❌ No USAGE privilege on PUBLIC schema');
        return false;
      }
    }
  } catch (err) {
    console.error('Error checking schema privileges:', err.message);
  }
  
  return false;
}

async function checkTablePrivileges() {
  console.log('\nChecking table access in PUBLIC schema...');
  
  let accessibleTables = 0;
  
  for (const tableName of TABLES) {
    try {
      console.log(`\nChecking table: public.${tableName}`);
      
      // Try simple select
      const { data, error } = await supabase
        .from(tableName)
        .select('*')
        .limit(1);
      
      if (error) {
        if (error.code === '42P01') {
          console.error(`❌ Table public.${tableName} does not exist`);
        } else if (error.code === '42501') {
          console.error(`❌ No SELECT privilege on public.${tableName}`);
        } else {
          console.error(`❌ Error accessing public.${tableName}: ${error.message}`);
        }
      } else {
        accessibleTables++;
        console.log(`✅ Successfully accessed public.${tableName}`);
        console.log(`   Number of rows retrieved: ${data.length}`);
      }
    } catch (err) {
      console.error(`❌ Exception when accessing public.${tableName}:`, err.message);
    }
  }
  
  console.log(`\nAccessible tables: ${accessibleTables}/${TABLES.length}`);
  return accessibleTables;
}

async function checkSearchPath() {
  console.log('\nChecking search_path setting...');
  
  try {
    const { data, error } = await supabase.rpc('run_sql_query', {
      query: "SHOW search_path;"
    });
    
    if (error) {
      console.error('Error checking search_path:', error.message);
    } else {
      const searchPath = data[0]?.search_path;
      console.log(`Current search_path: ${searchPath}`);
      
      if (searchPath && searchPath.includes('public')) {
        console.log('✅ PUBLIC schema is in the search path');
        return true;
      } else {
        console.log('⚠️ PUBLIC schema is not explicitly in the search path');
        console.log('   This is usually fine as public is included by default');
        return true;
      }
    }
  } catch (err) {
    console.error('Error checking search path:', err.message);
  }
  
  return false;
}

async function main() {
  console.log('\n===== PUBLIC Schema Access Verification =====\n');
  
  const schemaAccessible = await checkSchemaPrivileges();
  const accessibleTables = await checkTablePrivileges();
  const searchPathOK = await checkSearchPath();
  
  console.log('\n===== Verification Summary =====');
  
  if (schemaAccessible) {
    console.log('✅ PUBLIC schema is accessible');
  } else {
    console.log('❌ PUBLIC schema access issues detected');
  }
  
  console.log(`${accessibleTables}/${TABLES.length} tables are accessible`);
  
  if (searchPathOK) {
    console.log('✅ Search path configuration is suitable');
  }
  
  console.log('\nRecommendation:');
  if (accessibleTables === 0) {
    console.log('❗ Table access completely failed. Please verify that:');
    console.log('  1. Tables have been created in the public schema');
    console.log('  2. Your service role key has proper permissions');
    console.log('  3. Run these SQL commands to grant access:');
    console.log('     GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;');
    console.log('     GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;');
    console.log('     ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO anon, authenticated, service_role;');
  } else if (accessibleTables < TABLES.length) {
    console.log('⚠️ Some tables are not accessible. Consider:');
    console.log('  1. Creating missing tables in the public schema');
    console.log('  2. Ensuring permissions are granted for all tables');
  } else {
    console.log('✅ All tables in the public schema are accessible!');
  }
  
  console.log('\nVerification process completed.');
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1); 