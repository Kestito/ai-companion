/**
 * Script to verify Supabase access using different approaches
 * Run with: node scripts/verify-supabase-access.js
 */

require('dotenv').config({ path: '.env.local' });
const { createClient } = require('@supabase/supabase-js');

// Debug logs
console.log('Starting Supabase access verification script...');
console.log('Node version:', process.version);

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_KEY;

console.log('Environment variables:');
console.log(`- NEXT_PUBLIC_SUPABASE_URL: ${supabaseUrl ? 'Set' : 'Not set'}`);
console.log(`- SUPABASE_SERVICE_KEY: ${supabaseKey ? 'Set (length: ' + (supabaseKey ? supabaseKey.length : 0) + ')' : 'Not set'}`);

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing Supabase credentials. Please check your .env.local file.');
  process.exit(1);
}

// Create client
console.log('Creating Supabase client...');
const supabase = createClient(supabaseUrl, supabaseKey, {
  auth: {
    persistSession: false,
    autoRefreshToken: false
  }
});

// Constants for schema and table names
const SCHEMA = {
  EVELINAAI: 'evelinaai',
  PUBLIC: 'public',
};

const TABLES = {
  PATIENTS: 'patients',
  CONVERSATIONS: 'conversations',
  CONVERSATION_DETAILS: 'conversation_details',
  RISK_ASSESSMENTS: 'risk_assessments',
  SCHEDULED_APPOINTMENTS: 'scheduled_appointments',
  SCHEDULED_MESSAGES: 'scheduled_messages',
  USERS: 'users',
  REPORTS: 'reports',
  LONG_TERM_MEMORY: 'long_term_memory',
  SHORT_TERM_MEMORY: 'short_term_memory',
};

// Helper functions
function getSchemaTable(tableName, schema = SCHEMA.EVELINAAI) {
  return `${schema}.${tableName}`;
}

// Try different approaches to access tables
async function verifyTableAccess() {
  console.log('\n=== Verifying table access with different approaches ===');
  
  // Test a few key tables
  const tablesToTest = [
    TABLES.PATIENTS,
    TABLES.CONVERSATIONS,
    TABLES.USERS
  ];
  
  const results = {};
  
  for (const tableName of tablesToTest) {
    results[tableName] = {};
    
    console.log(`\n--- Testing access to ${tableName} ---`);
    
    // Approach 1: Standard query with schema prefix
    console.log(`Approach 1: Schema prefix (${SCHEMA.EVELINAAI}.${tableName})`);
    try {
      const { data, error } = await supabase
        .from(`${SCHEMA.EVELINAAI}.${tableName}`)
        .select('count(*)', { count: 'exact', head: true });
      
      if (error) {
        console.error(`  Error: ${error.message}`);
        results[tableName].schemaPrefix = { success: false, error: error.message };
      } else {
        console.log(`  Success! Count: ${data}`);
        results[tableName].schemaPrefix = { success: true, data };
      }
    } catch (e) {
      console.error(`  Error: ${e.message}`);
      results[tableName].schemaPrefix = { success: false, error: e.message };
    }
    
    // Approach 2: schema() method
    console.log(`Approach 2: schema() method (.schema('${SCHEMA.EVELINAAI}').from('${tableName}'))`);
    try {
      const { data, error } = await supabase
        .schema(SCHEMA.EVELINAAI)
        .from(tableName)
        .select('count(*)', { count: 'exact', head: true });
      
      if (error) {
        console.error(`  Error: ${error.message}`);
        results[tableName].schemaMethod = { success: false, error: error.message };
      } else {
        console.log(`  Success! Count: ${data}`);
        results[tableName].schemaMethod = { success: true, data };
      }
    } catch (e) {
      console.error(`  Error: ${e.message}`);
      results[tableName].schemaMethod = { success: false, error: e.message };
    }
    
    // Approach 3: Public schema
    console.log(`Approach 3: Public schema (.from('${tableName}'))`);
    try {
      const { data, error } = await supabase
        .from(tableName)
        .select('count(*)', { count: 'exact', head: true });
      
      if (error) {
        console.error(`  Error: ${error.message}`);
        results[tableName].publicSchema = { success: false, error: error.message };
      } else {
        console.log(`  Success! Count: ${data}`);
        results[tableName].publicSchema = { success: true, data };
      }
    } catch (e) {
      console.error(`  Error: ${e.message}`);
      results[tableName].publicSchema = { success: false, error: e.message };
    }
    
    // Approach 4: Raw SQL
    console.log(`Approach 4: Raw SQL (SELECT * FROM ${SCHEMA.EVELINAAI}.${tableName})`);
    try {
      const { data, error } = await supabase
        .rpc('run_sql_query', {
          query: `SELECT COUNT(*) FROM ${SCHEMA.EVELINAAI}.${tableName}`
        });
      
      if (error) {
        console.error(`  Error: ${error.message}`);
        results[tableName].rawSql = { success: false, error: error.message };
      } else {
        console.log(`  Success! Result: ${JSON.stringify(data)}`);
        results[tableName].rawSql = { success: true, data };
      }
    } catch (e) {
      console.error(`  Error: ${e.message}`);
      results[tableName].rawSql = { success: false, error: e.message };
    }
  }

  return results;
}

// Check all available schemas in the database
async function checkAvailableSchemas() {
  console.log('\n=== Checking available schemas ===');
  
  try {
    const { data, error } = await supabase
      .rpc('run_sql_query', {
        query: `SELECT schema_name FROM information_schema.schemata`
      });
    
    if (error) {
      console.error(`Error: ${error.message}`);
      
      // Try alternative approach
      try {
        console.log('Trying to check schemas using pg_catalog...');
        const { data: altData, error: altError } = await supabase
          .rpc('run_sql_query', {
            query: `SELECT nspname FROM pg_catalog.pg_namespace`
          });
        
        if (altError) {
          console.error(`Error with alternative approach: ${altError.message}`);
          return { success: false, error: altError.message };
        } else {
          console.log(`Available schemas: ${JSON.stringify(altData)}`);
          return { success: true, data: altData };
        }
      } catch (e) {
        console.error(`Error with alternative approach: ${e.message}`);
        return { success: false, error: e.message };
      }
    } else {
      console.log(`Available schemas: ${JSON.stringify(data)}`);
      return { success: true, data };
    }
  } catch (e) {
    console.error(`Error: ${e.message}`);
    return { success: false, error: e.message };
  }
}

// Test raw query to get tables
async function checkAvailableTables() {
  console.log('\n=== Checking available tables ===');
  
  try {
    const { data, error } = await supabase
      .rpc('run_sql_query', {
        query: `
          SELECT table_schema, table_name 
          FROM information_schema.tables 
          WHERE table_schema IN ('public', 'evelinaai')
          ORDER BY table_schema, table_name
        `
      });
    
    if (error) {
      console.error(`Error: ${error.message}`);
      return { success: false, error: error.message };
    } else {
      console.log(`Available tables: ${JSON.stringify(data)}`);
      return { success: true, data };
    }
  } catch (e) {
    console.error(`Error: ${e.message}`);
    return { success: false, error: e.message };
  }
}

// Main function
async function verifySupabaseAccess() {
  try {
    // First check if the schema and tables exist
    await checkAvailableSchemas();
    await checkAvailableTables();
    
    // Then test table access with different approaches
    const tableResults = await verifyTableAccess();
    
    console.log('\n=== Summary of Results ===');
    console.log(JSON.stringify(tableResults, null, 2));
    
    // Determine best approach
    console.log('\n=== Recommended Approach ===');
    let recommendedApproach = 'unknown';
    let successCount = {
      schemaPrefix: 0,
      schemaMethod: 0,
      publicSchema: 0,
      rawSql: 0
    };
    
    // Count successes for each approach
    Object.values(tableResults).forEach(tableResult => {
      if (tableResult.schemaPrefix?.success) successCount.schemaPrefix++;
      if (tableResult.schemaMethod?.success) successCount.schemaMethod++;
      if (tableResult.publicSchema?.success) successCount.publicSchema++;
      if (tableResult.rawSql?.success) successCount.rawSql++;
    });
    
    // Find best approach
    const maxSuccesses = Math.max(
      successCount.schemaPrefix,
      successCount.schemaMethod,
      successCount.publicSchema,
      successCount.rawSql
    );
    
    if (maxSuccesses === successCount.schemaPrefix) {
      recommendedApproach = 'Schema Prefix (.from("evelinaai.table_name"))';
    } else if (maxSuccesses === successCount.schemaMethod) {
      recommendedApproach = 'Schema Method (.schema("evelinaai").from("table_name"))';
    } else if (maxSuccesses === successCount.publicSchema) {
      recommendedApproach = 'Public Schema (.from("table_name"))';
    } else if (maxSuccesses === successCount.rawSql) {
      recommendedApproach = 'Raw SQL (SELECT * FROM evelinaai.table_name)';
    }
    
    console.log(`Recommended approach: ${recommendedApproach}`);
    console.log(`Success counts: ${JSON.stringify(successCount)}`);
    
    console.log('\nVerification completed');
  } catch (error) {
    console.error('Verification failed:', error);
  }
}

// Run the verification
verifySupabaseAccess()
  .then(() => {
    console.log('\nVerification script completed successfully');
    process.exit(0);
  })
  .catch(error => {
    console.error('Script failed:', error);
    process.exit(1);
  }); 