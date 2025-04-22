import { createClient } from '@supabase/supabase-js';
import { useEffect, useState } from 'react';

// Hardcoded Supabase credentials
const supabaseUrl = 'https://aubulhjfeszmsheonmpy.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc';

/**
 * Hook to access the Supabase client
 * @returns The Supabase client instance
 */
export const useSupabase = () => {
  const [client] = useState(() => createClient(supabaseUrl, supabaseAnonKey));
  
  useEffect(() => {
    // Log issues with Supabase configuration in development
    if (process.env.NODE_ENV === 'development') {
      if (!supabaseUrl) {
        console.warn('Supabase URL is not configured.');
      }
      if (!supabaseAnonKey) {
        console.warn('Supabase anonymous key is not configured.');
      }
    }
  }, []);
  
  return client;
}; 