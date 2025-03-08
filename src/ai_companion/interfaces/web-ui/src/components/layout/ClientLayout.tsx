'use client';

import { Box } from '@mui/material';
import { ThemeProvider } from '../providers/ThemeProvider';
import { NavigationProvider } from '../providers/NavigationProvider';
import Sidebar from './Sidebar';
import Header from './Header';
import { usePathname } from 'next/navigation';

// Define routes that should not have navigation (public routes)
const PUBLIC_ROUTES = ['/login', '/signup', '/forgot-password', '/reset-password'];

/**
 * Client layout component that handles navigation display logic
 * Adds sidebar and header to authenticated routes
 * Excludes navigation from public routes (login, etc.)
 * 
 * @param children - The page content
 * @returns The layout with conditional navigation
 */
export default function ClientLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  
  // Check if current path is a public route that should not have navigation
  const isPublicRoute = PUBLIC_ROUTES.some(route => 
    pathname === route || pathname.startsWith(`${route}/`)
  );

  // If current route is public, render without navigation
  if (isPublicRoute) {
    return (
      <ThemeProvider>
        {children}
      </ThemeProvider>
    );
  }

  // For all other routes, render with navigation (sidebar and header)
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
              pt: '72px', // Increased height for the header spacing to prevent overlap
              height: '100vh',
              overflow: 'auto',
              p: 0, // Remove default padding as each page will handle its own padding
            }}
          >
            {children}
          </Box>
        </Box>
      </NavigationProvider>
    </ThemeProvider>
  );
} 