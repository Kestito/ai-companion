'use client';

import { Box, useMediaQuery, useTheme } from '@mui/material';
import { ThemeProvider } from '../providers/themeprovider';
import { NavigationProvider } from '../providers/navigationprovider';
import Sidebar from './Sidebar';
import Header from './Header';
import { usePathname } from 'next/navigation';
import { useEffect } from 'react';
import { useNavigation } from '../providers/navigationprovider';

// Define routes that should not have navigation (public routes)
const PUBLIC_ROUTES = ['/login', '/signup', '/forgot-password', '/reset-password'];

/**
 * Client layout component that handles navigation display logic
 * Adds sidebar and header to authenticated routes
 * Excludes navigation from public routes (login, etc.)
 * Now mobile-responsive with adaptive layout
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
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  // Safe access to navigation context for SSG/SSR
  let closeSidebar = () => {};
  
  try {
    const navigation = useNavigation();
    closeSidebar = navigation.closeSidebar;
    
    // Auto-close sidebar on mobile
    useEffect(() => {
      if (isMobile) {
        closeSidebar();
      }
    }, [isMobile, closeSidebar]);

    // Auto-close sidebar on route change for mobile
    useEffect(() => {
      if (isMobile) {
        closeSidebar();
      }
    }, [pathname, isMobile, closeSidebar]);
  } catch (error) {
    // During static generation, we'll skip the effects
    console.log('Navigation context not available during static generation');
  }
  
  // Check if current path is a public route that should not have navigation
  const isPublicRoute = PUBLIC_ROUTES.some(route => 
    pathname === route || pathname.startsWith(`${route}/`)
  );

  // If current route is public, render without navigation
  if (isPublicRoute) {
    return (
      <ThemeProvider>
        <Box className="max-w-full overflow-x-hidden">
          {children}
        </Box>
      </ThemeProvider>
    );
  }

  // For all other routes, render with navigation (sidebar and header)
  return (
    <ThemeProvider>
      <NavigationProvider>
        <Box sx={{ display: 'flex', minHeight: '100vh', width: '100%', overflow: 'hidden' }}>
          <Header />
          <Sidebar />
          <Box
            component="main"
            sx={{
              flexGrow: 1,
              pt: { xs: '64px', sm: '72px' }, // Responsive header spacing
              height: '100vh',
              overflow: 'auto',
              p: 0, // Remove default padding as each page will handle its own padding
              width: '100%',
            }}
            className="max-w-full"
          >
            {children}
          </Box>
        </Box>
      </NavigationProvider>
    </ThemeProvider>
  );
} 