/**
 * This script verifies access to the evelinaai schema tables
 * Run with: node scripts/verify-evelinaai-schema.js
 */

require('dotenv').config({ path: '.env.local' });
const { createClient } = require('@supabase/supabase-js');

// Debug logs
console.log('Script started');
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

async function verifySchema() {
  console.log('Verifying access to evelinaai schema...');

  try {
    console.log(`Connecting to Supabase at: ${supabaseUrl}`);
    
    // First check if we can connect to the database
    console.log('Testing connection to Supabase...');
    try {
      const { data: connectionData, error: connectionError } = await supabase.auth.getSession();
      
      if (connectionError) {
        console.error('Failed to connect to Supabase:', connectionError.message);
      } else {
        console.log('Connected to Supabase successfully!');
      }
    } catch (e) {
      console.error('Error during connection test:', e);
    }

    // Check if the schema exists using raw SQL
    console.log('\nVerifying schema existence with raw SQL...');
    try {
      const { data: schemaData, error: schemaError } = await supabase.rpc('execute_sql', {
        query: `SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'evelinaai'`
      });
      
      if (schemaError) {
        console.log('Error checking schema with raw SQL:', schemaError.message);
        
        // Try alternative method
        console.log('Trying alternative method to check schema...');
        const { data: altData, error: altError } = await supabase
          .from('_rpc')
          .select('*')
          .rpc('execute_sql', {
            query: `SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'evelinaai'`
          });
          
        if (altError) {
          console.log('Error with alternative method:', altError.message);
        } else {
          console.log('Schema check result (alternative):', altData);
        }
      } else {
        console.log('Schema check result:', schemaData);
        if (schemaData && schemaData.length > 0) {
          console.log('✓ evelinaai schema exists');
        } else {
          console.log('⚠️ evelinaai schema does not exist');
        }
      }
    } catch (e) {
      console.error('Error during schema check:', e);
    }

    // List of tables to verify in the evelinaai schema
    const tables = [
      'conversation_details',
      'conversations',
      'long_term_memory',
      'patients',
      'reports',
      'risk_assessments',
      'scheduled_appointments',
      'short_term_memory'
    ];

    // Verify each table using raw SQL
    console.log('\nVerifying tables using raw SQL...');
    for (const table of tables) {
      console.log(`\nVerifying table: ${table}`);
      
      try {
        // Try to query the table with raw SQL
        const { data, error } = await supabase.rpc('execute_sql', {
          query: `SELECT * FROM evelinaai.${table} LIMIT 1`
        });
        
        if (error) {
          console.log(`Error accessing table ${table}:`, error.message);
          
          // Try alternative method
          const { data: altData, error: altError } = await supabase
            .from('_rpc')
            .select('*')
            .rpc('execute_sql', {
              query: `SELECT * FROM evelinaai.${table} LIMIT 1`
            });
            
          if (altError) {
            console.log(`Error with alternative method for ${table}:`, altError.message);
          } else {
            console.log(`✓ Successfully accessed table: ${table} (alternative method)`);
            console.log(`  Found ${altData ? altData.length : 0} records`);
            if (altData && altData.length > 0 && altData[0].result) {
              const result = JSON.parse(altData[0].result);
              console.log(`  Sample fields: ${Object.keys(result[0]).join(', ')}`);
            } else {
              console.log(`  Table is empty or no result format`);
            }
          }
        } else {
          console.log(`✓ Successfully accessed table: ${table}`);
          console.log(`  Found ${data ? data.length : 0} records`);
          if (data && data.length > 0) {
            console.log(`  Sample fields: ${Object.keys(data[0]).join(', ')}`);
          } else {
            console.log(`  Table is empty`);
          }
        }
      } catch (e) {
        console.error(`Error during table verification for ${table}:`, e);
      }
    }

    // Try using the REST API directly
    console.log('\nTrying REST API approach...');
    try {
      const response = await fetch(`${supabaseUrl}/rest/v1/patients?select=*&limit=1`, {
        headers: {
          'apikey': supabaseKey,
          'Authorization': `Bearer ${supabaseKey}`,
          'Accept-Profile': 'evelinaai'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('REST API with Accept-Profile success!');
        console.log(`Found ${data.length} records`);
      } else {
        console.log('REST API with Accept-Profile failed:', await response.text());
      }
    } catch (e) {
      console.error('Error during REST API test:', e);
    }

    console.log('\nSchema verification completed');
  } catch (error) {
    console.error('Error verifying schema:', error);
  }
}

// Run the verification
console.log('Starting verification...');
verifySchema()
  .then(() => {
    console.log('Verification script completed');
    process.exit(0);
  })
  .catch(error => {
    console.error('Script failed:', error);
    process.exit(1);
  }); 