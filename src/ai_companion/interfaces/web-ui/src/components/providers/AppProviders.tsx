import { ReactNode } from 'react';
import { AuthProvider } from '@/store/auth/AuthContext';

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
  // Order providers based on dependencies
  // Providers that are needed by other providers should be higher in the tree
  return (
    <AuthProvider>
      {/* Add other providers as they are created */}
      {/* <SettingsProvider> */}
      {/*   <ChatProvider> */}
            {children}
      {/*   </ChatProvider> */}
      {/* </SettingsProvider> */}
    </AuthProvider>
  );
};

export default AppProviders; 