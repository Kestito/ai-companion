require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');

// Access environment variables
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

// Initialize Supabase client
console.log('Creating Supabase client...');
const supabase = createClient(supabaseUrl, supabaseKey);

// Create patients table in public schema
const createPatientsTableSQL = `
-- Create patients table
create table if not exists public.patients (
    id uuid primary key default gen_random_uuid(),
    email text unique,
    phone text,
    first_name text,
    last_name text,
    created_at timestamptz not null default current_timestamp,
    last_active timestamptz,
    preferred_language text default 'lt',
    subsidy_eligible boolean default false,
    legal_consents jsonb,
    support_status text check (support_status in ('active', 'pending', 'resolved'))
);

-- Add indexes for performance
create index if not exists idx_patients_email on public.patients(email);
`;

async function main() {
  try {
    console.log('Testing connection to Supabase...');
    
    console.log('Executing SQL to create patients table...');
    // Execute SQL using direct SQL query
    const { data, error } = await supabase.from('patients').select('*').limit(1);
    
    if (error && error.code === '42P01') { // Table doesn't exist
      console.log('Patients table does not exist. Creating it...');
      
      // Use rpc if available or use REST API
      try {
        const { error: sqlError } = await supabase.rpc('run_sql', { sql: createPatientsTableSQL });
        
        if (sqlError) {
          console.error('Error executing SQL via RPC:', sqlError.message);
          console.log('Please execute this SQL directly in the Supabase SQL editor:');
          console.log(createPatientsTableSQL);
        } else {
          console.log('✅ Successfully created patients table!');
        }
      } catch (rpcError) {
        console.error('Error calling RPC:', rpcError.message);
        console.log('Please execute this SQL directly in the Supabase SQL editor:');
        console.log(createPatientsTableSQL);
      }
    } else if (error) {
      console.error('Error checking patients table:', error.message);
    } else {
      console.log('✅ Patients table already exists with data rows:', data.length);
    }
    
    console.log('\nSQL for full schema creation:');
    console.log(createPatientsTableSQL);
    
  } catch (err) {
    console.error('Script error:', err.message);
  }
}

main(); 