# State Management

## Overview

This document outlines our approach to state management in the web-ui frontend. We use React Context API for global state management and local component state for UI-specific state.

## Directory Structure

```
src/
├── store/
│   ├── auth/                    # Authentication state
│   │   ├── AuthContext.tsx      # Auth context provider
│   │   ├── AuthReducer.ts       # Auth state reducer
│   │   └── AuthTypes.ts         # Auth state types
│   ├── chat/                    # Chat state
│   │   ├── ChatContext.tsx      # Chat context provider
│   │   ├── ChatReducer.ts       # Chat state reducer
│   │   └── ChatTypes.ts         # Chat state types
│   ├── settings/                # Application settings
│   │   ├── SettingsContext.tsx  # Settings context provider
│   │   ├── SettingsReducer.ts   # Settings state reducer
│   │   └── SettingsTypes.ts     # Settings state types
│   └── hooks.ts                 # Custom hooks for accessing store
```

## Context Architecture

Each domain area has its own context with a clear separation of concerns:

```typescript
// store/auth/AuthContext.tsx
import { createContext, useReducer, useEffect, ReactNode } from 'react';
import { AuthState, AuthAction, User } from './AuthTypes';
import { authReducer } from './AuthReducer';
import { getSupabaseClient } from '@/src/lib/supabase/client';

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

export const AuthContext = createContext<{
  state: AuthState;
  dispatch: React.Dispatch<AuthAction>;
}>({
  state: initialState,
  dispatch: () => null,
});

export const AuthProvider = ({ children }: { children: ReactNode }) => {
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
            throw userError;
          }
          
          dispatch({
            type: 'SET_USER',
            payload: {
              ...data.session.user,
              profile: userData,
            },
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
            console.error('Profile fetch error:', userError);
          }
          
          dispatch({
            type: 'SET_USER',
            payload: {
              ...session.user,
              profile: userData || {},
            },
          });
        } else if (event === 'SIGNED_OUT') {
          dispatch({ type: 'CLEAR_USER' });
        }
      }
    );
    
    checkSession();
    
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
```

## Reducer Pattern

Reducers manage state updates in a predictable way:

```typescript
// store/auth/AuthReducer.ts
import { AuthState, AuthAction } from './AuthTypes';

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
```

## Type Definitions

Strong typing ensures consistency and prevents errors:

```typescript
// store/auth/AuthTypes.ts
export interface Profile {
  id: string;
  username?: string;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
  [key: string]: any;
}

export interface User {
  id: string;
  email?: string;
  profile?: Profile;
  [key: string]: any;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export type AuthAction =
  | { type: 'SET_USER'; payload: User }
  | { type: 'CLEAR_USER' }
  | { type: 'AUTH_ERROR'; payload: string }
  | { type: 'SET_LOADING'; payload: boolean };
```

## Custom Hooks

Hooks simplify access to context state:

```typescript
// store/hooks.ts
import { useContext } from 'react';
import { AuthContext } from './auth/AuthContext';
import { ChatContext } from './chat/ChatContext';
import { SettingsContext } from './settings/SettingsContext';

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  const { state, dispatch } = context;
  
  return {
    user: state.user,
    isAuthenticated: state.isAuthenticated,
    isLoading: state.isLoading,
    error: state.error,
    dispatch,
    logout: () => dispatch({ type: 'CLEAR_USER' }),
    setUser: (user: User) => dispatch({ type: 'SET_USER', payload: user }),
  };
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};
```

## Provider Composition

Multiple providers are composed together in the application:

```tsx
// src/components/providers/AppProviders.tsx
import { ReactNode } from 'react';
import { AuthProvider } from '@/src/store/auth/AuthContext';
import { ChatProvider } from '@/src/store/chat/ChatContext';
import { SettingsProvider } from '@/src/store/settings/SettingsContext';

interface AppProvidersProps {
  children: ReactNode;
}

export const AppProviders = ({ children }: AppProvidersProps) => {
  return (
    <AuthProvider>
      <SettingsProvider>
        <ChatProvider>
          {children}
        </ChatProvider>
      </SettingsProvider>
    </AuthProvider>
  );
};
```

## Best Practices

1. **Context Separation**: Divide state by domain and keep contexts focused
2. **Type Safety**: Use TypeScript for all state definitions
3. **Immutability**: Never mutate state directly, always use reducers
4. **Custom Hooks**: Create hooks for accessing context state
5. **Provider Composition**: Nest providers appropriately based on dependencies
6. **Loading States**: Include loading states for asynchronous operations
7. **Error Handling**: Include error states and handling in all contexts 