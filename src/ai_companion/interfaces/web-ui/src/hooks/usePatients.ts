import { useState, useEffect } from 'react';
import { useSupabase } from './useSupabase';

export interface Patient {
  id: string;
  name: string;
  email: string;
  phone?: string;
  age?: number;
  gender?: string;
  status?: string;
  created_at: string;
  updated_at?: string;
  preferred_language?: string;
  support_status?: string;
}

export function usePatients() {
  const supabase = useSupabase();
  const [patients, setPatients] = useState<Patient[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function fetchPatients() {
      try {
        setIsLoading(true);
        
        const { data, error } = await supabase
          .from('patients')
          .select('*');

        if (error) {
          throw new Error(error.message);
        }

        setPatients(data || []);
      } catch (err) {
        console.error('Error fetching patients:', err);
        setError(err as Error);
      } finally {
        setIsLoading(false);
      }
    }

    fetchPatients();
  }, [supabase]);

  return { patients, isLoading, error };
} 