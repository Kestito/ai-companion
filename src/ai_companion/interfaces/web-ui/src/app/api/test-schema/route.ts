import { createClient } from '@supabase/supabase-js';
import { NextResponse } from 'next/server';

// Skip error if environment variables are not available (dev mode)
let supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
let supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

export async function GET() {
  if (!supabaseUrl || !supabaseKey) {
    return NextResponse.json({
      error: 'Missing environment variables',
      missing: {
        NEXT_PUBLIC_SUPABASE_URL: !supabaseUrl,
        NEXT_PUBLIC_SUPABASE_ANON_KEY: !supabaseKey
      }
    }, { status: 500 });
  }

  const supabase = createClient(supabaseUrl, supabaseKey);
  const results = [];

  // Check if public schema exists (it should always exist)
  try {
    const { data: schemaData, error: schemaError } = await supabase
      .from('information_schema.schemata')
      .select('schema_name')
      .eq('schema_name', 'public')
      .single();
    
    results.push({
      test: 'schema_exists',
      success: !schemaError && schemaData,
      error: schemaError?.message,
      data: schemaData
    });
  } catch (err: any) {
    results.push({
      test: 'schema_exists',
      success: false,
      error: err.message
    });
  }

  // Check tables in schema
  try {
    const { data: tablesData, error: tablesError } = await supabase
      .from('information_schema.tables')
      .select('table_name')
      .eq('table_schema', 'public');
    
    results.push({
      test: 'list_tables',
      success: !tablesError,
      error: tablesError?.message,
      data: tablesData
    });
  } catch (err: any) {
    results.push({
      test: 'list_tables',
      success: false,
      error: err.message
    });
  }

  // Try using schema() method
  try {
    const { data, error } = await supabase
      .schema('public')
      .from('patients')
      .select('*')
      .limit(1);
      
    results.push({
      test: 'schema_method',
      success: !error,
      error: error?.message,
      data: data && data.length > 0 ? '[Data available]' : data
    });
  } catch (err: any) {
    results.push({
      test: 'schema_method',
      success: false,
      error: err.message
    });
  }

  // Try using schema.table prefix
  try {
    const { data, error } = await supabase
      .from('public.patients')
      .select('*')
      .limit(1);
      
    results.push({
      test: 'schema_prefix',
      success: !error,
      error: error?.message,
      data: data && data.length > 0 ? '[Data available]' : data
    });
  } catch (err: any) {
    results.push({
      test: 'schema_prefix',
      success: false,
      error: err.message
    });
  }

  // Try using direct table access
  try {
    const { data, error } = await supabase
      .from('patients')
      .select('*')
      .limit(1);
      
    results.push({
      test: 'direct_access',
      success: !error,
      error: error?.message,
      data: data && data.length > 0 ? '[Data available]' : data
    });
  } catch (err: any) {
    results.push({
      test: 'direct_access',
      success: false,
      error: err.message
    });
  }

  // Check permissions
  const permissions = {
    url: supabaseUrl,
    key_length: supabaseKey.length,
    project_ref: supabaseUrl.split('.')[0].replace('https://', '')
  };

  return NextResponse.json({
    results,
    permissions
  });
} 