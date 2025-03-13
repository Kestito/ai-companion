/**
 * Script to check the actual schema and table configuration in Supabase
 * This will help diagnose why we're getting 404 errors
 * 
 * Run with:
 * node scripts/check-schema-tables.js
 */

const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: '.env.local' });

// Tables to check (without schema prefix)
const TABLES_TO_CHECK = [
  'patients',
  'conversations',
  'conversation_details',
  'users',
  'reports',
  'risk_assessments',
  'scheduled_appointments',
  'scheduled_messages',
  'messages'
];

// Create the Supabase client
const createSupabaseClient = () => {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  
  if (!supabaseUrl || !supabaseKey) {
    throw new Error('Missing Supabase credentials in environment variables');
  }
  
  console.log(`Creating Supabase client for URL: ${supabaseUrl}`);
  return createClient(supabaseUrl, supabaseKey);
};

// Check if a schema exists
async function checkIfSchemaExists(supabase, schemaName) {
  console.log(`\nChecking if schema '${schemaName}' exists...`);
  
  try {
    // Use raw SQL to query the schema
    const { data, error } = await supabase.rpc('check_schema_exists', { schema_name: schemaName });
    
    if (error) {
      console.log(`❌ Error checking schema: ${error.message}`);
      
      // Try an alternative approach
      const { data: schemaInfo, error: schemaError } = await supabase.from('information_schema.schemata')
        .select('schema_name')
        .eq('schema_name', schemaName);
      
      if (schemaError) {
        console.log(`❌ Alternative approach also failed: ${schemaError.message}`);
        return false;
      }
      
      const exists = Array.isArray(schemaInfo) && schemaInfo.length > 0;
      console.log(`${exists ? '✅' : '❌'} Schema '${schemaName}' ${exists ? 'exists' : 'does not exist'}`);
      return exists;
    }
    
    console.log(`${data ? '✅' : '❌'} Schema '${schemaName}' ${data ? 'exists' : 'does not exist'}`);
    return data;
  } catch (error) {
    console.log(`❌ Exception checking schema: ${error.message}`);
    return false;
  }
}

// Check tables in a schema
async function checkTablesInSchema(supabase, schemaName, tables) {
  console.log(`\nChecking tables in schema '${schemaName}'...`);
  
  for (const table of tables) {
    try {
      console.log(`\nTesting table: ${table}`);
      
      // Try method 1: Using direct table name (if search_path includes the schema)
      console.log(`Method 1: Using direct table name '${table}'`);
      try {
        const { data: data1, error: error1 } = await supabase
          .from(table)
          .select('*', { count: 'exact', head: true });
        
        if (error1) {
          console.log(`❌ Method 1 failed: ${error1.message}`);
        } else {
          console.log(`✅ Method 1 success! Count: ${data1.length}`);
        }
      } catch (err) {
        console.log(`❌ Method 1 exception: ${err.message}`);
      }
      
      // Try method 2: Using schema.table name
      console.log(`Method 2: Using schema.table name '${schemaName}.${table}'`);
      try {
        const { data: data2, error: error2 } = await supabase
          .from(`${schemaName}.${table}`)
          .select('*', { count: 'exact', head: true });
        
        if (error2) {
          console.log(`❌ Method 2 failed: ${error2.message}`);
        } else {
          console.log(`✅ Method 2 success! Count: ${data2.length}`);
        }
      } catch (err) {
        console.log(`❌ Method 2 exception: ${err.message}`);
      }
      
      // Try method 3: Using schema() method
      console.log(`Method 3: Using schema() method with schema('${schemaName}').from('${table}')`);
      try {
        const { data: data3, error: error3 } = await supabase
          .schema(schemaName)
          .from(table)
          .select('*', { count: 'exact', head: true });
        
        if (error3) {
          console.log(`❌ Method 3 failed: ${error3.message}`);
        } else {
          console.log(`✅ Method 3 success! Count: ${data3.length}`);
        }
      } catch (err) {
        console.log(`❌ Method 3 exception: ${err.message}`);
      }
      
    } catch (error) {
      console.log(`❌ General error testing table '${table}': ${error.message}`);
    }
  }
}

// Check if the schema tables exist in the public schema
async function checkTablesInPublic(supabase, tables) {
  console.log(`\nChecking tables in 'public' schema...`);
  
  for (const table of tables) {
    try {
      const { data, error } = await supabase
        .from(`public.${table}`)
        .select('*', { count: 'exact', head: true });
      
      if (error) {
        console.log(`❌ Table 'public.${table}' error: ${error.message}`);
      } else {
        console.log(`✅ Table 'public.${table}' exists! Count: ${data.length}`);
      }
    } catch (error) {
      console.log(`❌ Error checking 'public.${table}': ${error.message}`);
    }
  }
}

// List all tables the user has access to
async function listAccessibleTables(supabase) {
  console.log(`\nListing all accessible tables...`);
  
  try {
    const { data, error } = await supabase
      .from('information_schema.tables')
      .select('table_schema, table_name')
      .eq('table_type', 'BASE TABLE');
    
    if (error) {
      console.log(`❌ Error listing tables: ${error.message}`);
      return;
    }
    
    if (!data || data.length === 0) {
      console.log('No tables found that you have access to.');
      return;
    }
    
    console.log(`Found ${data.length} tables that you have access to:`);
    
    // Group tables by schema
    const tablesBySchema = {};
    data.forEach(table => {
      if (!tablesBySchema[table.table_schema]) {
        tablesBySchema[table.table_schema] = [];
      }
      tablesBySchema[table.table_schema].push(table.table_name);
    });
    
    // Print tables by schema
    Object.keys(tablesBySchema).forEach(schema => {
      console.log(`\nSchema: ${schema}`);
      tablesBySchema[schema].forEach(table => {
        console.log(`  - ${table}`);
      });
    });
  } catch (error) {
    console.log(`❌ Exception listing tables: ${error.message}`);
  }
}

// Run the checks
async function runChecks() {
  console.log('Starting schema and table checks...');
  console.log('================================\n');
  
  try {
    const supabase = createSupabaseClient();
    
    // Check if our target schema exists
    const schemaName = 'evelinaai';
    const schemaExists = await checkIfSchemaExists(supabase, schemaName);
    
    if (schemaExists) {
      // Check tables in our schema
      await checkTablesInSchema(supabase, schemaName, TABLES_TO_CHECK);
    } else {
      console.log(`\n⚠️ Schema '${schemaName}' doesn't exist. Checking tables in 'public' schema instead...`);
      await checkTablesInPublic(supabase, TABLES_TO_CHECK);
    }
    
    // List all tables the user has access to
    await listAccessibleTables(supabase);
    
    console.log('\n================================');
    console.log('Schema and table checks completed.');
    
    if (!schemaExists) {
      console.log('\n⚠️ IMPORTANT: The expected schema does not exist.');
      console.log('You need to create the schema and tables, or modify your application to use the tables in the public schema.');
      console.log('\nTo create the schema in Supabase, run:');
      console.log('CREATE SCHEMA evelinaai;');
      console.log('\nThen grant access:');
      console.log('GRANT USAGE ON SCHEMA evelinaai TO anon, authenticated, service_role;');
      console.log('GRANT ALL ON ALL TABLES IN SCHEMA evelinaai TO anon, authenticated, service_role;');
      console.log('ALTER DEFAULT PRIVILEGES IN SCHEMA evelinaai GRANT ALL ON TABLES TO anon, authenticated, service_role;');
    }
  } catch (error) {
    console.error('❌ Error running checks:', error.message);
  }
}

// Run the program
runChecks().catch(error => {
  console.error('Unhandled error:', error);
  process.exit(1);
}); 