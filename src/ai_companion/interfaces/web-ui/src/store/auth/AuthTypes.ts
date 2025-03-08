/**
 * Auth state types for the authentication context
 */

// User profile information
export interface UserProfile {
  id: string;
  username?: string;
  avatar_url?: string;
  bio?: string;
  created_at: string;
  updated_at: string;
}

// User data with authentication info
export interface User {
  id: string;
  email?: string;
  profile?: UserProfile;
  last_sign_in_at?: string;
  app_metadata?: Record<string, any>;
  user_metadata?: Record<string, any>;
  created_at?: string;
}

// Auth state for the context
export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// Auth action types for the reducer
export type AuthAction =
  | { type: 'SET_USER'; payload: User }
  | { type: 'CLEAR_USER' }
  | { type: 'AUTH_ERROR'; payload: string }
  | { type: 'SET_LOADING'; payload: boolean }; 