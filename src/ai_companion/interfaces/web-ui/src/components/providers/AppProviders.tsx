'use client';

import { ReactNode, useState } from 'react';
import { AuthProvider } from '@/store/auth/AuthContext';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

// Import other providers as they are created
// import { ChatProvider } from '@/store/chat/ChatContext';
// import { SettingsProvider } from '@/store/settings/SettingsContext';

interface AppProvidersProps {
  children: ReactNode;
}

/**
 * Combines all context providers to wrap the application
 * 
 * @param children - The application components to wrap
 * @returns Provider-wrapped application
 */
export const AppProviders = ({ children }: AppProvidersProps) => {
  // Create QueryClient inside the component to ensure it's only created on the client
  const [queryClient] = useState(() => new QueryClient());
  
  // Order providers based on dependencies
  // Providers that are needed by other providers should be higher in the tree
  return (
    <AuthProvider>
      {/* Add other providers as they are created */}
      {/* <SettingsProvider> */}
      {/*   <ChatProvider> */}
      <QueryClientProvider client={queryClient}>
        <LocalizationProvider dateAdapter={AdapterDateFns}>
          {children}
        </LocalizationProvider>
      </QueryClientProvider>
      {/*   </ChatProvider> */}
      {/* </SettingsProvider> */}
    </AuthProvider>
  );
};

export default AppProviders; 