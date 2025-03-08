import { AuthState, AuthAction } from './AuthTypes';

/**
 * Reducer for auth state
 * Handles state updates based on dispatched actions
 * 
 * @param state - Current auth state
 * @param action - Action dispatched
 * @returns Updated auth state
 */
export const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'SET_USER':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };
      
    case 'CLEAR_USER':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      };
      
    case 'AUTH_ERROR':
      return {
        ...state,
        error: action.payload,
        isLoading: false,
      };
      
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };
      
    default:
      return state;
  }
}; 