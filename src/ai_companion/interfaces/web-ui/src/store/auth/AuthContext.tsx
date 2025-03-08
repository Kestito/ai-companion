"use client";

import { createContext, useReducer, useEffect, ReactNode } from 'react';
import { AuthState, AuthAction, User } from './AuthTypes';
import { authReducer } from './AuthReducer';
import { getSupabaseClient } from '@/lib/supabase/client';

// Initial auth state
const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

// Create auth context
export const AuthContext = createContext<{
  state: AuthState;
  dispatch: React.Dispatch<AuthAction>;
}>({
  state: initialState,
  dispatch: () => null,
});

interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Auth provider component to wrap the application
 * Manages authentication state and listens for auth changes
 */
export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [state, dispatch] = useReducer(authReducer, initialState);
  
  useEffect(() => {
    const supabase = getSupabaseClient();
    
    // Check for existing session
    const checkSession = async () => {
      try {
        const { data, error } = await supabase.auth.getSession();
        
        if (error) {
          throw error;
        }
        
        if (data?.session) {
          // Get user profile data
          const { data: userData, error: userError } = await supabase
            .from('profiles')
            .select('*')
            .eq('id', data.session.user.id)
            .single();
            
          if (userError) {
            console.warn('Profile fetch error:', userError);
          }
          
          dispatch({
            type: 'SET_USER',
            payload: {
              ...data.session.user,
              profile: userData || undefined,
            } as User,
          });
        } else {
          dispatch({ type: 'CLEAR_USER' });
        }
      } catch (error) {
        console.error('Session check error:', error);
        dispatch({ 
          type: 'AUTH_ERROR', 
          payload: error instanceof Error ? error.message : 'Authentication error' 
        });
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };
    
    // Subscribe to auth changes
    const { data: authListener } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (event === 'SIGNED_IN' && session) {
          // Get user profile data
          const { data: userData, error: userError } = await supabase
            .from('profiles')
            .select('*')
            .eq('id', session.user.id)
            .single();
            
          if (userError) {
            console.warn('Profile fetch error:', userError);
          }
          
          dispatch({
            type: 'SET_USER',
            payload: {
              ...session.user,
              profile: userData || undefined,
            } as User,
          });
        } else if (event === 'SIGNED_OUT') {
          dispatch({ type: 'CLEAR_USER' });
        }
      }
    );
    
    // Check session on mount
    checkSession();
    
    // Cleanup subscription on unmount
    return () => {
      authListener.subscription.unsubscribe();
    };
  }, []);
  
  return (
    <AuthContext.Provider value={{ state, dispatch }}>
      {children}
    </AuthContext.Provider>
  );
}; 