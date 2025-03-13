/**
 * This script uses the Supabase REST API directly to inspect database structure
 * Run with: node scripts/inspect-db.js
 */

require('dotenv').config({ path: '.env.local' });
const fetch = require('node-fetch');

// Debug logs
console.log('Starting database inspection script...');
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

/**
 * Fetch data from Supabase REST API
 * @param {string} path - API path
 * @param {Object} options - Fetch options
 * @returns {Promise<Object>} - Response data
 */
async function fetchFromSupabase(path, options = {}) {
  const url = `${supabaseUrl}/rest/v1/${path}`;
  const headers = {
    'apikey': supabaseKey,
    'Authorization': `Bearer ${supabaseKey}`,
    'Content-Type': 'application/json',
    ...options.headers
  };

  console.log(`Making request to: ${url}`);
  
  try {
    const response = await fetch(url, {
      ...options,
      headers
    });

    if (!response.ok) {
      const text = await response.text();
      console.error(`Error response (${response.status}):`, text);
      return { error: { status: response.status, message: text } };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    console.error('Fetch error:', error);
    return { error: { message: error.message } };
  }
}

/**
 * Try to fetch table info using public API
 */
async function listPublicTables() {
  console.log('\n=== Listing public tables ===');
  
  // Try patients table
  const tables = ['patients', 'conversations', 'users', 'scheduled_messages'];
  
  for (const table of tables) {
    console.log(`\nTrying to access "${table}" table...`);
    
    // Try in public schema
    console.log(`\n- Direct access (.from('${table}'))`);
    const result = await fetchFromSupabase(table, {
      headers: {
        'Range': '0-0',
        'Prefer': 'count=exact'
      }
    });
    
    if (result.error) {
      console.log(`  Error: ${JSON.stringify(result.error)}`);
    } else {
      console.log(`  Success! Count: ${result.data.length}`);
      console.log(`  Sample fields: ${Object.keys(result.data[0] || {}).join(', ')}`);
    }
    
    // Try with schema prefix
    console.log(`\n- With schema prefix (.from('evelinaai.${table}'))`);
    const schemaResult = await fetchFromSupabase(`evelinaai.${table}`, {
      headers: {
        'Range': '0-0',
        'Prefer': 'count=exact'
      }
    });
    
    if (schemaResult.error) {
      console.log(`  Error: ${JSON.stringify(schemaResult.error)}`);
    } else {
      console.log(`  Success! Count: ${schemaResult.data.length}`);
      console.log(`  Sample fields: ${Object.keys(schemaResult.data[0] || {}).join(', ')}`);
    }
    
    // Try with schema header
    console.log(`\n- With schema header`);
    const headerResult = await fetchFromSupabase(table, {
      headers: {
        'Range': '0-0',
        'Prefer': 'count=exact',
        'Accept-Profile': 'evelinaai'
      }
    });
    
    if (headerResult.error) {
      console.log(`  Error: ${JSON.stringify(headerResult.error)}`);
    } else {
      console.log(`  Success! Count: ${headerResult.data.length}`);
      console.log(`  Sample fields: ${Object.keys(headerResult.data[0] || {}).join(', ')}`);
    }
  }
}

/**
 * Check if the Supabase REST API is accessible
 */
async function checkRestApiAccess() {
  console.log('\n=== Checking Supabase REST API access ===');
  
  try {
    // Just try to hit the root endpoint
    const response = await fetch(`${supabaseUrl}/rest/v1/`, {
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
      }
    });
    
    const status = response.status;
    const contentType = response.headers.get('content-type');
    let data;
    
    try {
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }
    } catch (e) {
      data = `Error parsing response: ${e.message}`;
    }
    
    console.log(`REST API status: ${status}`);
    console.log(`REST API response: ${JSON.stringify(data)}`);
    
    if (status >= 200 && status < 300) {
      console.log('✓ REST API is accessible');
    } else {
      console.error('✗ REST API returned error status');
    }
  } catch (error) {
    console.error('✗ Failed to access REST API:', error.message);
  }
}

/**
 * Test a basic auth query
 */
async function checkAuthAccess() {
  console.log('\n=== Checking auth access ===');
  
  try {
    const response = await fetch(`${supabaseUrl}/auth/v1/user`, {
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
      }
    });
    
    const status = response.status;
    let data;
    
    try {
      data = await response.json();
    } catch (e) {
      data = `Error parsing response: ${e.message}`;
    }
    
    console.log(`Auth API status: ${status}`);
    console.log(`Auth API response: ${typeof data === 'object' ? JSON.stringify(data) : data}`);
    
    if (status >= 200 && status < 300) {
      console.log('✓ Auth API is accessible');
    } else {
      console.error('✗ Auth API returned error status');
    }
  } catch (error) {
    console.error('✗ Failed to access Auth API:', error.message);
  }
}

/**
 * Main function to run all checks
 */
async function main() {
  try {
    // First check general API access
    await checkRestApiAccess();
    await checkAuthAccess();
    
    // Then try to list tables
    await listPublicTables();
    
    console.log('\nInspection completed successfully');
  } catch (error) {
    console.error('Inspection failed:', error);
  }
}

// Run the script
main()
  .then(() => process.exit(0))
  .catch(error => {
    console.error('Script failed:', error);
    process.exit(1);
  }); 