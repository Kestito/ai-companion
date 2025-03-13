require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

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

// Helper function to run a command
function runCommand(command, args) {
  console.log(`Running command: ${command} ${args.join(' ')}`);
  const result = spawnSync(command, args, { stdio: 'inherit' });
  if (result.error) {
    console.error('Error running command:', result.error);
    return false;
  }
  return result.status === 0;
}

async function convertToPublicSchema() {
  console.log('\n========== SCHEMA CONVERSION PROCESS ==========');
  console.log('Converting from EVELINAAI schema to PUBLIC schema...');
  
  // Step 1: Verify permissions and access
  console.log('\n--- STEP 1: Verify current database access ---');
  const verifyResult = runCommand('node', ['scripts/verify-schema-access.js']);
  if (!verifyResult) {
    console.warn('⚠️ Verification script encountered issues, but proceeding with conversion...');
  }
  
  // Step 2: Create tables in public schema
  console.log('\n--- STEP 2: Create tables in PUBLIC schema ---');
  try {
    // Execute the SQL using direct RPC call
    const sqlFilePath = path.join(__dirname, 'create_all_tables.sql');
    const sqlContent = fs.readFileSync(sqlFilePath, 'utf8');
    
    console.log('Executing SQL script to create tables...');
    const { data, error } = await supabase.rpc('run_sql_query', { 
      query: sqlContent 
    });
    
    if (error) {
      console.error('Error executing SQL script:', error.message);
      console.log('\nContinuing with the process. You may need to manually execute the SQL script.');
    } else {
      console.log('✅ SQL script executed successfully!');
    }
  } catch (err) {
    console.error('Error creating tables:', err.message);
    console.log('Continuing with the process. You may need to manually create the tables.');
  }
  
  // Step 3: Grant necessary permissions
  console.log('\n--- STEP 3: Grant permissions on PUBLIC schema ---');
  const permissionSQL = `
    GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
    GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO anon, authenticated, service_role;
  `;
  
  try {
    console.log('Granting permissions...');
    const { data, error } = await supabase.rpc('run_sql_query', { 
      query: permissionSQL 
    });
    
    if (error) {
      console.error('Error granting permissions:', error.message);
      console.log('\nYou may need to manually grant permissions using the SQL editor.');
    } else {
      console.log('✅ Permissions granted successfully!');
    }
  } catch (err) {
    console.error('Error granting permissions:', err.message);
    console.log('You may need to manually grant permissions using the SQL editor.');
  }
  
  // Step 4: Migrate data from evelinaai to public (if exists)
  console.log('\n--- STEP 4: Migrate data from EVELINAAI to PUBLIC schema ---');
  
  const migrationSQL = `
  DO $$
  DECLARE
      schema_exists BOOLEAN;
  BEGIN
      SELECT EXISTS(
          SELECT 1 FROM information_schema.schemata WHERE schema_name = 'evelinaai'
      ) INTO schema_exists;

      IF NOT schema_exists THEN
          RAISE NOTICE 'evelinaai schema does not exist. Nothing to migrate.';
          RETURN;
      END IF;
      
      -- Attempt to migrate patients
      BEGIN
          INSERT INTO public.patients 
          SELECT * FROM evelinaai.patients
          ON CONFLICT (id) DO NOTHING;
          RAISE NOTICE 'Migrated patients data';
      EXCEPTION WHEN OTHERS THEN
          RAISE NOTICE 'Error migrating patients: %', SQLERRM;
      END;
      
      -- Attempt to migrate other tables (add more as needed)
      BEGIN
          INSERT INTO public.conversations 
          SELECT * FROM evelinaai.conversations
          ON CONFLICT (id) DO NOTHING;
          RAISE NOTICE 'Migrated conversations data';
      EXCEPTION WHEN OTHERS THEN
          RAISE NOTICE 'Error migrating conversations: %', SQLERRM;
      END;
      
      RAISE NOTICE 'Migration completed!';
  END $$;
  `;
  
  try {
    console.log('Migrating data if available...');
    const { data, error } = await supabase.rpc('run_sql_query', { 
      query: migrationSQL 
    });
    
    if (error) {
      console.error('Error running migration:', error.message);
    } else {
      console.log('✅ Migration script executed successfully!');
    }
  } catch (err) {
    console.error('Error running migration:', err.message);
  }
  
  // Step 5: Verify everything is working
  console.log('\n--- STEP 5: Verify PUBLIC schema setup ---');
  
  // Run the public schema verification
  console.log('Verifying public schema access...');
  const publicVerifyResult = runCommand('node', ['scripts/verify_public_schema.js']);
  
  if (!publicVerifyResult) {
    console.warn('⚠️ Verification of PUBLIC schema encountered issues. Please check manually.');
  }
  
  console.log('\n========== SCHEMA CONVERSION COMPLETED ==========');
  console.log('Remember to update your code to use the PUBLIC schema.');
  console.log('The client.ts file has been updated to use PUBLIC as the default schema.');
}

// Run the conversion process
console.log('Starting schema conversion process...');
convertToPublicSchema().then(() => {
  console.log('\nProcess completed.');
}); 