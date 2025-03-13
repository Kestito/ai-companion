require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');

// Access environment variables
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing environment variables:');
  if (!supabaseUrl) console.error('- NEXT_PUBLIC_SUPABASE_URL');
  if (!supabaseKey) console.error('- SUPABASE_SERVICE_KEY');
  process.exit(1);
}

// Initialize Supabase client
console.log('Creating Supabase client...');
const supabase = createClient(supabaseUrl, supabaseKey);

async function listTables() {
  console.log('Listing tables in evelinaai schema...');
  
  try {
    // Query to list all tables in the evelinaai schema
    const { data, error } = await supabase
      .from('information_schema.tables')
      .select('table_name')
      .eq('table_schema', 'evelinaai');
    
    if (error) {
      console.error('Error listing tables:', error.message);
      return;
    }
    
    if (data && data.length > 0) {
      console.log('Tables in evelinaai schema:');
      data.forEach(table => {
        console.log(`- ${table.table_name}`);
      });
    } else {
      console.log('No tables found in evelinaai schema');
    }
  } catch (err) {
    console.error('Exception when listing tables:', err.message);
  }
}

async function testTableSchemaMethod(tableName) {
  console.log(`\nTesting access to table using schema() method: evelinaai.${tableName}`);
  
  try {
    // Try to select a single row from the table using schema() method
    const { data, error } = await supabase
      .schema('evelinaai')
      .from(tableName)
      .select('*')
      .limit(1);
    
    if (error) {
      console.error(`Error accessing with schema() method:`, error.message);
      return false;
    }
    
    console.log(`Successfully accessed using schema() method`);
    console.log(`Data:`, data);
    return true;
  } catch (err) {
    console.error(`Exception using schema() method:`, err.message);
    return false;
  }
}

async function testTableSchemaPrefix(tableName) {
  console.log(`\nTesting access to table using prefix: evelinaai.${tableName}`);
  
  try {
    // Try to select a single row from the table using schema prefix
    const { data, error } = await supabase
      .from(`evelinaai.${tableName}`)
      .select('*')
      .limit(1);
    
    if (error) {
      console.error(`Error accessing with prefix:`, error.message);
      return false;
    }
    
    console.log(`Successfully accessed using schema prefix`);
    console.log(`Data:`, data);
    return true;
  } catch (err) {
    console.error(`Exception using schema prefix:`, err.message);
    return false;
  }
}

async function testTableDirect(tableName) {
  console.log(`\nTesting direct access to table: ${tableName}`);
  
  try {
    // Try to select a single row from the table directly
    const { data, error } = await supabase
      .from(tableName)
      .select('*')
      .limit(1);
    
    if (error) {
      console.error(`Error accessing directly:`, error.message);
      return false;
    }
    
    console.log(`Successfully accessed directly`);
    console.log(`Data:`, data);
    return true;
  } catch (err) {
    console.error(`Exception accessing directly:`, err.message);
    return false;
  }
}

async function main() {
  console.log('Script started');
  console.log('Node version:', process.version);
  console.log('Testing connection to Supabase...');
  
  try {
    // Simple test query to verify connection
    const { data, error } = await supabase.from('information_schema.schemata').select('schema_name').limit(5);
    
    if (error) {
      console.error('Connection test failed:', error.message);
      return;
    }
    
    console.log('Connected to Supabase successfully!');
    console.log('Available schemas:', data.map(s => s.schema_name).join(', '));
    
    // List tables in evelinaai schema
    await listTables();
    
    // Test specific tables with different methods
    const tablesToTest = [
      'patients',
      'conversations',
      'reports'
    ];
    
    console.log('\n=== TESTING ACCESS METHODS ===');
    
    for (const table of tablesToTest) {
      console.log(`\n== Testing table: ${table} ==`);
      
      // Test with schema() method
      const schemaMethodWorks = await testTableSchemaMethod(table);
      
      // Test with schema prefix
      const schemaPrefixWorks = await testTableSchemaPrefix(table);
      
      // Test direct access
      const directAccessWorks = await testTableDirect(table);
      
      console.log(`\nSummary for ${table}:`);
      console.log(`- schema() method: ${schemaMethodWorks ? 'WORKS' : 'FAILS'}`);
      console.log(`- schema prefix: ${schemaPrefixWorks ? 'WORKS' : 'FAILS'}`);
      console.log(`- direct access: ${directAccessWorks ? 'WORKS' : 'FAILS'}`);
    }
    
  } catch (err) {
    console.error('Script error:', err.message);
  }
  
  console.log('\nScript completed');
}

main(); 