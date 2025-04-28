import { createClient } from '@supabase/supabase-js';
import { useEffect, useState } from 'react';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';
import { getSupabaseCredentials } from '@/lib/supabase/client';

// Get credentials from our central configuration
const { supabaseUrl, supabaseKey } = getSupabaseCredentials();

/**
 * Hook to access the Supabase client
 * 
 * IMPORTANT: This hook creates a Supabase client using createClientComponentClient
 * which is compatible with Next.js App Router and properly handles auth.
 * 
 * @returns The Supabase client instance
 */
export const useSupabase = () => {
  // Use the auth-helpers client for better Next.js integration
  const [client] = useState(() => {
    try {
      // First try to use auth-helpers with explicit credentials (preferred method)
      return createClientComponentClient({
        supabaseUrl: supabaseUrl,
        supabaseKey: supabaseKey
      });
    } catch (error) {
      // Fallback to direct client creation if auth-helpers fail
      console.warn('Falling back to direct Supabase client creation:', error);
      return createClient(supabaseUrl, supabaseKey, {
        auth: {
          persistSession: true,
          autoRefreshToken: true
        }
      });
    }
  });
  
  useEffect(() => {
    // Log issues with Supabase configuration in development
    if (process.env.NODE_ENV === 'development') {
      if (!supabaseUrl) {
        console.warn('Supabase URL is not configured.');
      }
      if (!supabaseKey) {
        console.warn('Supabase anonymous key is not configured.');
      }
    }
  }, []);
  
  return client;
}; 