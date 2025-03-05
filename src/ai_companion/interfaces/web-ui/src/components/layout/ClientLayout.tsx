'use client';

import { Box } from '@mui/material';
import { ThemeProvider } from '../providers/ThemeProvider';
import { NavigationProvider } from '../providers/NavigationProvider';
import Sidebar from './Sidebar';
import Header from './Header';
import { usePathname } from 'next/navigation';

const PUBLIC_ROUTES = ['/login'];

export default function ClientLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isPublicRoute = PUBLIC_ROUTES.includes(pathname);

  if (isPublicRoute) {
    return (
      <ThemeProvider>
        {children}
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider>
      <NavigationProvider>
        <Box sx={{ display: 'flex', minHeight: '100vh' }}>
          <Header />
          <Sidebar />
          <Box
            component="main"
            sx={{
              flexGrow: 1,
              pt: '64px', // Height of the header
              height: '100vh',
              overflow: 'auto',
            }}
          >
            {children}
          </Box>
        </Box>
      </NavigationProvider>
    </ThemeProvider>
  );
} 