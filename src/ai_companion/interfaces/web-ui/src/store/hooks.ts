import { useContext } from 'react';
import { AuthContext } from './auth/AuthContext';
import { User } from './auth/AuthTypes';

/**
 * Hook to access auth state and actions
 * 
 * @returns Auth state and helper functions
 */
export const useAuth = () => {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  const { state, dispatch } = context;
  
  // Helper functions to simplify common auth operations
  const logout = async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    
    try {
      // Add actual logout logic here if needed
      dispatch({ type: 'CLEAR_USER' });
    } catch (error) {
      dispatch({ 
        type: 'AUTH_ERROR', 
        payload: error instanceof Error ? error.message : 'Logout error' 
      });
    }
  };
  
  const setUser = (user: User) => {
    dispatch({ type: 'SET_USER', payload: user });
  };
  
  return {
    // State properties
    user: state.user,
    isAuthenticated: state.isAuthenticated,
    isLoading: state.isLoading,
    error: state.error,
    
    // Actions
    dispatch,
    logout,
    setUser,
  };
}; 