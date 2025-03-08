/**
 * Authentication Types
 * Contains types related to user authentication and authorization
 */

/**
 * User authentication state
 */
export interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  error: string | null;
}

/**
 * User profile information
 */
export interface User {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  role: UserRole;
  avatar?: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * Available user roles
 */
export enum UserRole {
  ADMIN = 'admin',
  USER = 'user',
  GUEST = 'guest',
}

/**
 * Login credentials
 */
export interface LoginCredentials {
  email: string;
  password: string;
}

/**
 * Registration data
 */
export interface RegistrationData {
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
}

/**
 * Auth provider props
 */
export interface AuthProviderProps {
  children: React.ReactNode;
} 