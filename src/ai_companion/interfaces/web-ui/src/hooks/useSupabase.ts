import { createClient } from '@supabase/supabase-js';
import { useEffect, useState } from 'react';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

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
        console.warn('Supabase URL is not configured. Set NEXT_PUBLIC_SUPABASE_URL in .env.local');
      }
      if (!supabaseAnonKey) {
        console.warn('Supabase anonymous key is not configured. Set NEXT_PUBLIC_SUPABASE_ANON_KEY in .env.local');
      }
    }
  }, []);
  
  return client;
}; 