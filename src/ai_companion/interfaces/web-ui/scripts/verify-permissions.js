/**
 * This script verifies that the schema permissions have been properly granted
 * Run with: node scripts/verify-permissions.js
 */

require('dotenv').config({ path: '.env.local' });
const { createClient } = require('@supabase/supabase-js');

// Debug logs
console.log('Starting schema permissions verification script...');
console.log('Node version:', process.version);

// Initialize Supabase credentials
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_KEY;

console.log('Environment variables:');
console.log(`- NEXT_PUBLIC_SUPABASE_URL: ${supabaseUrl ? 'Set' : 'Not set'}`);
console.log(`- SUPABASE_SERVICE_KEY: ${supabaseKey ? 'Set (length: ' + (supabaseKey ? supabaseKey.length : 0) + ')' : 'Not set'}`);

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing Supabase credentials. Please check your .env.local file.');
  process.exit(1);
}

// Constants for schema and table names
const SCHEMA = {
  EVELINAAI: 'evelinaai',
  PUBLIC: 'public',
};

const TABLES = {
  PATIENTS: 'patients',
  CONVERSATIONS: 'conversations',
  USERS: 'users',
  SCHEDULED_MESSAGES: 'scheduled_messages',
};

// Create client
console.log('Creating Supabase client...');
const supabase = createClient(supabaseUrl, supabaseKey, {
  auth: {
    persistSession: false,
    autoRefreshToken: false
  }
});

// Helper function to get schema table
function getSchemaTable(tableName, schema = SCHEMA.EVELINAAI) {
  return `${schema}.${tableName}`;
}

/**
 * Check schema permissions
 */
async function checkSchemaPermissions() {
  console.log('\n=== Checking Schema Permissions ===');
  
  // 1. Check if USAGE privilege has been granted
  console.log('\n1. Checking USAGE privilege on schema');
  try {
    const { data: usageData, error: usageError } = await supabase.rpc('run_sql_query', {
      query: `SELECT has_schema_privilege('public', 'evelinaai', 'USAGE') as has_usage`
    });
    
    if (usageError) {
      console.error(`Error checking USAGE privilege:`, usageError.message);
      console.log('Trying alternative approach...');
      
      // Try a direct access to check if we can access the schema
      const { error: accessError } = await supabase
        .from('evelinaai.patients')
        .select('count(*)', { count: 'exact', head: true });
      
      if (accessError && accessError.message.includes('permission denied')) {
        console.error('✗ USAGE privilege NOT granted correctly');
        console.error(`  Error: ${accessError.message}`);
      } else if (accessError && accessError.message.includes('relation')) {
        console.log('✓ USAGE privilege likely granted (can see schema but table might not exist)');
        console.log(`  Table error: ${accessError.message}`);
      } else if (!accessError) {
        console.log('✓ USAGE privilege granted (can access schema and table)');
      }
    } else {
      const hasUsage = usageData?.[0]?.has_usage === true;
      
      if (hasUsage) {
        console.log('✓ USAGE privilege granted successfully');
      } else {
        console.error('✗ USAGE privilege NOT granted');
        console.log('  Result:', usageData);
      }
    }
  } catch (error) {
    console.error('Error checking USAGE privilege:', error);
  }
  
  // 2. Check if SELECT privileges have been granted
  console.log('\n2. Checking SELECT privileges on tables');
  
  // For each table, try to access it
  for (const tableName of Object.values(TABLES)) {
    console.log(`\nTable: ${tableName}`);
    
    try {
      const schemaTable = getSchemaTable(tableName);
      const { data, error } = await supabase
        .from(schemaTable)
        .select('count(*)', { count: 'exact', head: true });
      
      if (error) {
        if (error.message.includes('permission denied')) {
          console.error(`✗ SELECT privilege NOT granted on ${schemaTable}`);
          console.error(`  Error: ${error.message}`);
        } else if (error.message.includes('relation')) {
          console.log(`ℹ Cannot verify SELECT privilege on ${schemaTable} (table might not exist)`);
          console.log(`  Error: ${error.message}`);
        } else {
          console.error(`✗ Error accessing ${schemaTable}: ${error.message}`);
        }
      } else {
        console.log(`✓ SELECT privilege granted on ${schemaTable}`);
        console.log(`  Result: Count = ${data}`);
      }
    } catch (error) {
      console.error(`Error checking SELECT privilege on ${tableName}:`, error);
    }
  }
  
  // 3. Check schema search path
  console.log('\n3. Checking schema search path');
  try {
    const { data: searchPathData, error: searchPathError } = await supabase.rpc('run_sql_query', {
      query: `SHOW search_path;`
    });
    
    if (searchPathError) {
      console.error(`Error checking search path:`, searchPathError.message);
    } else {
      console.log('Current search path:', searchPathData);
      
      // Check if evelinaai is in the search path
      const searchPath = searchPathData?.[0]?.search_path || '';
      if (searchPath.includes('evelinaai')) {
        console.log('✓ evelinaai schema is in the search path');
      } else {
        console.log('ℹ evelinaai schema is NOT in the search path');
        console.log('  This is okay if you access tables with explicit schema prefix.');
      }
    }
  } catch (error) {
    console.error('Error checking search path:', error);
  }
  
  // 4. Summary of recommended approach
  console.log('\n=== Recommended Approach ===');
  console.log('Based on permission checks, use the schema prefix approach:');
  console.log(`  .from('${SCHEMA.EVELINAAI}.table_name')`);
  console.log('This is the most reliable way to access tables in evelinaai schema.');
}

/**
 * Main function
 */
async function main() {
  try {
    await checkSchemaPermissions();
    console.log('\nPermission verification completed successfully');
  } catch (error) {
    console.error('Script failed:', error);
  }
}

// Run the script
main()
  .then(() => process.exit(0))
  .catch(error => {
    console.error('Script failed:', error);
    process.exit(1);
  }); 