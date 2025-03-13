'use client';

import { useEffect, useState } from 'react';
import { getSupabaseClient, TableAccessMethod, PUBLIC_SCHEMA } from '@/lib/supabase/client';

interface TestResult {
  method: string;
  success: boolean;
  error?: string;
  data?: any;
}

interface ApiTestResult {
  test: string;
  success: boolean;
  error?: string;
  data?: any;
}

export default function TestSchemaPage() {
  const [clientResults, setClientResults] = useState<TestResult[]>([]);
  const [apiResults, setApiResults] = useState<ApiTestResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [apiLoading, setApiLoading] = useState(true);
  
  // Fetch API test results
  useEffect(() => {
    async function fetchApiResults() {
      setApiLoading(true);
      try {
        const response = await fetch('/api/test-schema');
        if (!response.ok) {
          throw new Error('API response was not ok');
        }
        const data = await response.json();
        setApiResults(data.results || []);
      } catch (err) {
        console.error('Error fetching API results:', err);
      } finally {
        setApiLoading(false);
      }
    }
    
    fetchApiResults();
  }, []);
  
  // Run client-side tests
  useEffect(() => {
    async function runTests() {
      setIsLoading(true);
      const testResults: TestResult[] = [];
      const supabase = getSupabaseClient();
      
      // Try using schema() method
      try {
        const { data, error } = await supabase
          .schema(PUBLIC_SCHEMA)
          .from('patients')
          .select('*')
          .limit(1);
          
        testResults.push({
          method: 'schema() method',
          success: !error,
          error: error?.message,
          data: data
        });
      } catch (err: any) {
        testResults.push({
          method: 'schema() method',
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
          
        testResults.push({
          method: 'schema.table prefix',
          success: !error,
          error: error?.message,
          data: data
        });
      } catch (err: any) {
        testResults.push({
          method: 'schema.table prefix',
          success: false,
          error: err.message
        });
      }
      
      // Try direct table access
      try {
        const { data, error } = await supabase
          .from('patients')
          .select('*')
          .limit(1);
          
        testResults.push({
          method: 'direct table access',
          success: !error,
          error: error?.message,
          data: data
        });
      } catch (err: any) {
        testResults.push({
          method: 'direct table access',
          success: false,
          error: err.message
        });
      }
      
      setClientResults(testResults);
      setIsLoading(false);
    }
    
    runTests();
  }, []);
  
  // Get recommendations
  const workingMethod = clientResults.find(r => r.success)?.method;
  const serverWorkingMethod = 
    apiResults.find(r => r.test === 'schema_method' && r.success) ? 'schema() method' :
    apiResults.find(r => r.test === 'schema_prefix' && r.success) ? 'schema.table prefix' :
    apiResults.find(r => r.test === 'raw_sql' && r.success) ? 'raw SQL' : null;
  
  const schemaExists = apiResults.find(r => r.test === 'schema_exists')?.success;
  const tablesData = apiResults.find(r => r.test === 'list_tables')?.data;
  
  return (
    <div className="container mx-auto py-10">
      <h1 className="text-2xl font-bold mb-5">Schema Access Test</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Client-side tests */}
        <div>
          <h2 className="text-xl font-semibold mb-4">Client-Side Tests</h2>
          
          {isLoading ? (
            <div className="text-center p-4 bg-gray-50 rounded">Testing schema access methods...</div>
          ) : (
            <div className="space-y-4">
              {clientResults.map((result, index) => (
                <div 
                  key={index}
                  className={`p-4 rounded-lg border ${
                    result.success 
                      ? 'bg-green-50 border-green-200' 
                      : 'bg-red-50 border-red-200'
                  }`}
                >
                  <h3 className="font-bold">
                    {result.method}: {result.success ? 'SUCCESS' : 'FAILED'}
                  </h3>
                  
                  {result.error && (
                    <div className="mt-2">
                      <p className="text-red-700 font-semibold text-sm">Error:</p>
                      <pre className="bg-gray-100 p-2 rounded mt-1 text-xs overflow-x-auto">
                        {result.error}
                      </pre>
                    </div>
                  )}
                  
                  {result.success && result.data && result.data.length > 0 && (
                    <div className="mt-2">
                      <p className="text-green-700 font-semibold text-sm">Data Found ✓</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Server-side tests */}
        <div>
          <h2 className="text-xl font-semibold mb-4">Server-Side Tests</h2>
          
          {apiLoading ? (
            <div className="text-center p-4 bg-gray-50 rounded">Loading server test results...</div>
          ) : (
            <div className="space-y-4">
              {apiResults.map((result, index) => (
                <div 
                  key={index}
                  className={`p-4 rounded-lg border ${
                    result.success 
                      ? 'bg-green-50 border-green-200' 
                      : 'bg-red-50 border-red-200'
                  }`}
                >
                  <h3 className="font-bold">
                    {result.test}: {result.success ? 'SUCCESS' : 'FAILED'}
                  </h3>
                  
                  {result.error && (
                    <div className="mt-2">
                      <p className="text-red-700 font-semibold text-sm">Error:</p>
                      <pre className="bg-gray-100 p-2 rounded mt-1 text-xs overflow-x-auto">
                        {result.error}
                      </pre>
                    </div>
                  )}
                  
                  {result.success && result.data && (
                    <div className="mt-2">
                      <p className="text-green-700 font-semibold text-sm">Data:</p>
                      {result.test === 'list_tables' && Array.isArray(result.data) ? (
                        <ul className="text-sm mt-1 pl-5 list-disc">
                          {result.data.map((item: any, i: number) => (
                            <li key={i}>{item.table_name}</li>
                          ))}
                        </ul>
                      ) : (
                        <pre className="bg-gray-100 p-2 rounded mt-1 text-xs overflow-x-auto">
                          {JSON.stringify(result.data, null, 2)}
                        </pre>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      
      {/* Recommendations */}
      <div className="bg-blue-50 p-6 rounded-lg border border-blue-200 mt-8">
        <h2 className="text-xl font-bold">Recommendations</h2>
        
        <div className="mt-4 space-y-4">
          {schemaExists === false && (
            <div className="p-4 bg-yellow-50 rounded border border-yellow-200">
              <p className="font-bold text-yellow-800">Using Public Schema</p>
              <p className="mt-2">
                We're now using the 'public' schema for all tables. Make sure your tables exist in the public schema.
              </p>
              <ol className="list-decimal ml-5 mt-2">
                <li>Verify permissions by running the following SQL in Supabase SQL Editor:</li>
                <pre className="bg-gray-100 p-3 rounded mt-2 text-sm overflow-x-auto">
{`GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO anon, authenticated, service_role;`}
                </pre>
                <li>Check that your tables exist in the public schema:</li>
                <pre className="bg-gray-100 p-3 rounded mt-2 text-sm overflow-x-auto">
{`SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE';`}
                </pre>
              </ol>
            </div>
          )}
          
          {schemaExists && tablesData && Array.isArray(tablesData) && tablesData.length === 0 && (
            <div className="p-4 bg-yellow-50 rounded border border-yellow-200">
              <p className="font-bold text-amber-800">Schema exists but has no tables!</p>
              <p className="mt-2">
                The 'evelinaai' schema exists but doesn't have any tables. You should:
              </p>
              <ol className="list-decimal ml-5 mt-2">
                <li>Create tables in the schema, or</li>
                <li>Move existing tables from public schema to evelinaai schema</li>
              </ol>
              <pre className="bg-gray-100 p-3 rounded mt-2 text-sm overflow-x-auto">
{`-- Example of creating a table in the evelinaai schema
CREATE TABLE evelinaai.patients (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- OR move an existing table from public to evelinaai
ALTER TABLE public.patients SET SCHEMA evelinaai;`}
              </pre>
            </div>
          )}
          
          <div className="p-4 bg-white rounded border">
            <p className="font-bold">Access Method Recommendation:</p>
            <div className="mt-2">
              <p>
                Client-side: {workingMethod ? 
                  <span className="text-green-700 font-semibold">{workingMethod}</span> : 
                  <span className="text-red-700">No working method found</span>
                }
              </p>
              <p className="mt-1">
                Server-side: {serverWorkingMethod ? 
                  <span className="text-green-700 font-semibold">{serverWorkingMethod}</span> : 
                  <span className="text-red-700">No working method found</span>
                }
              </p>
            </div>
            
            {workingMethod && (
              <div className="mt-4 p-3 bg-green-50 rounded">
                <p className="font-semibold">Update your code to use {workingMethod}:</p>
                <pre className="bg-gray-100 p-3 rounded mt-2 text-sm overflow-x-auto">
                  {workingMethod === 'schema() method' ?
                    `// Using schema() method
const { data, error } = await supabase
  .schema('evelinaai')
  .from('patients')
  .select('*');` :
                    
                    workingMethod === 'schema.table prefix' ?
                    `// Using schema.table prefix
const { data, error } = await supabase
  .from('evelinaai.patients')
  .select('*');` :
                    
                    `// Using direct table access (if search_path is configured)
const { data, error } = await supabase
  .from('patients')
  .select('*');`
                  }
                </pre>
                <p className="mt-3 text-sm">
                  Update the client.ts file to set the default access method to {
                    workingMethod === 'schema() method' ? 'TableAccessMethod.SCHEMA_METHOD' :
                    workingMethod === 'schema.table prefix' ? 'TableAccessMethod.SCHEMA_PREFIX' :
                    'TableAccessMethod.PUBLIC'
                  }
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Working Methods */}
      <div className="mt-8">
        <h2 className="text-xl font-bold mb-4">Working Methods</h2>
        
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="font-bold">Client-side:</h3>
          <p className="mt-2">
            {workingMethod ? 
              `✅ The '${workingMethod}' works in the browser.` : 
              '❌ No schema access method works in the browser.'}
          </p>
          
          <h3 className="font-bold mt-4">Server-side:</h3>
          <p className="mt-2">
            {serverWorkingMethod ? 
              `✅ The '${serverWorkingMethod}' works on the server.` : 
              '❌ No schema access method works on the server.'}
          </p>
          
          <div className="mt-6 p-4 bg-green-50 rounded border border-green-200">
            <h3 className="font-bold text-green-800">Recommended Code Pattern:</h3>
            <pre className="bg-gray-100 p-3 rounded mt-2 text-sm overflow-x-auto">
{`// Import the necessary functions from client.ts
import { getSupabaseClient, TABLE_NAMES } from '@/lib/supabase/client';

// Function to fetch data
async function fetchData() {
  const supabase = getSupabaseClient();
  
  // Direct table access is recommended
  const { data, error } = await supabase
    .from(TABLE_NAMES.PATIENTS)  // Use constants for table names
    .select('*');
    
  if (error) {
    console.error('Error fetching data:', error);
    return null;
  }
  
  return data;
}`}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
} 