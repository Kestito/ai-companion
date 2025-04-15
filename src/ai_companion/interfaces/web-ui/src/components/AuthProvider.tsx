'use client';

import React, { createContext, useState, useEffect, useContext } from 'react';

// Simple AuthContext with basic user info
interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

// Create context with default values
const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  login: async () => {},
  logout: () => {},
});

// Hook to use the auth context
export const useAuth = () => useContext(AuthContext);

// Auth Provider component
export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing login session
    const checkAuthStatus = async () => {
      try {
        // For now, just simulate authentication
        // In a real app, you would check session cookies, tokens, etc.
        const mockUser = {
          id: 'user-1',
          name: 'Test User',
          email: 'test@example.com',
          role: 'admin',
        };
        
        // Simulate already logged in
        setUser(mockUser);
        setIsLoading(false);
      } catch (error) {
        console.error('Auth check failed:', error);
        setUser(null);
        setIsLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  // Login function
  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      // In a real app, this would be an API call to authenticate
      // Simulating successful login with mock data
      const mockUser = {
        id: 'user-1',
        name: 'Test User',
        email,
        role: 'admin',
      };
      
      setUser(mockUser);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // Logout function
  const logout = () => {
    setUser(null);
    // In a real app, you would also clear cookies/localStorage
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
} 