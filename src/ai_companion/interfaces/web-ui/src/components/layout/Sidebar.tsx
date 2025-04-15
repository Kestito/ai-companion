'use client';

import { 
  Box, 
  Drawer, 
  List, 
  ListItem, 
  ListItemButton, 
  ListItemIcon, 
  ListItemText,
  IconButton,
  Divider,
  Avatar,
  Typography,
  Stack,
  Tooltip,
  useMediaQuery,
  useTheme,
  SwipeableDrawer
} from '@mui/material';
import {
  Dashboard,
  People,
  Message,
  Assessment,
  CalendarMonth,
  Settings,
  Menu as MenuIcon,
  ChevronLeft,
  HealthAndSafety,
  NotificationsActive,
  MedicalServices,
  BarChart,
  Chat
} from '@mui/icons-material';
import { useRouter, usePathname } from 'next/navigation';
import Image from 'next/image';
import { useNavigation } from '../providers/navigationprovider';
import { useEffect } from 'react';

const DRAWER_WIDTH = 280;
const COLLAPSED_DRAWER_WIDTH = 72;

// Main navigation items for the sidebar
const menuItems = [
  { text: 'Dashboard', icon: <Dashboard />, path: '/dashboard', description: 'Overview and statistics' },
  { text: 'Patients', icon: <People />, path: '/patients', description: 'Patient management' },
  { text: 'Appointments', icon: <CalendarMonth />, path: '/appointments', description: 'Schedule management' },
  { text: 'Messages', icon: <Message />, path: '/messages', description: 'Communication center' },
  { text: 'Health Records', icon: <HealthAndSafety />, path: '/records', description: 'Patient health data' },
  { text: 'Alerts', icon: <NotificationsActive />, path: '/alerts', description: 'Critical notifications' },
  { text: 'Analytics', icon: <BarChart />, path: '/analytics', description: 'Data analysis' },
  { text: 'Telegram Messages', icon: <Chat />, path: '/telegram-messages', description: 'Telegram messaging' },
];

// Bottom navigation items for settings, etc.
const bottomMenuItems = [
  { text: 'Resources', icon: <MedicalServices />, path: '/resources', description: 'Reference materials' },
  { text: 'Settings', icon: <Settings />, path: '/settings', description: 'System configuration' },
];

/**
 * Sidebar navigation component
 * Provides main navigation for the application
 * Responsive for both desktop and mobile devices
 */
export default function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  // Safe access to navigation context
  let isSidebarOpen = !isMobile;
  let toggleSidebar = () => {};
  let closeSidebar = () => {};
  
  try {
    // This will throw an error during static generation but work during client rendering
    const navigation = useNavigation();
    isSidebarOpen = navigation.isSidebarOpen;
    toggleSidebar = navigation.toggleSidebar;
    closeSidebar = navigation.closeSidebar;
  } catch (error) {
    // During static generation/build, we'll just use fallback values
    console.log('Navigation context not available, using fallbacks');
  }

  // Navigate to the selected path
  const handleNavigation = (path: string) => {
    router.push(path);
    // Auto close on mobile after navigation
    if (isMobile) {
      closeSidebar();
    }
  };

  // Determine if an item is currently selected
  const isActive = (path: string) => {
    return pathname === path || pathname.startsWith(`${path}/`);
  };

  // Responsive drawer for mobile and desktop
  const renderDrawerContent = () => (
    <>
      {/* Sidebar header with logo and close button */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: isSidebarOpen ? 'space-between' : 'center',
          padding: isSidebarOpen ? theme.spacing(0, 2) : theme.spacing(1),
          height: { xs: '64px', sm: '72px' }, // Match header height
          overflow: 'hidden',
        }}
      >
        {isSidebarOpen && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
            }}
          >
            {/* Logo removed */}
          </Box>
        )}
        <IconButton onClick={toggleSidebar}>
          <ChevronLeft />
        </IconButton>
      </Box>

      <Divider />

      {/* Main navigation items */}
      <List sx={{ px: 1 }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
            <Tooltip
              title={!isSidebarOpen ? item.text : ''}
              placement="right"
              arrow
              disableHoverListener={isSidebarOpen}
            >
              <ListItemButton
                onClick={() => handleNavigation(item.path)}
                selected={isActive(item.path)}
                sx={{
                  borderRadius: '8px',
                  justifyContent: isSidebarOpen ? 'initial' : 'center',
                  px: isSidebarOpen ? 2 : 1,
                  minHeight: 48,
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 0,
                    mr: isSidebarOpen ? 2 : 'auto',
                    justifyContent: 'center',
                    color: isActive(item.path)
                      ? 'primary.main'
                      : 'inherit',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                {isSidebarOpen && (
                  <ListItemText
                    primary={item.text}
                    secondary={isSidebarOpen ? item.description : null}
                    primaryTypographyProps={{
                      fontWeight: isActive(item.path) ? 'bold' : 'medium',
                      color: isActive(item.path) ? 'primary.main' : 'inherit',
                      noWrap: true,
                    }}
                    secondaryTypographyProps={{
                      noWrap: true,
                      fontSize: '0.75rem',
                    }}
                  />
                )}
              </ListItemButton>
            </Tooltip>
          </ListItem>
        ))}
      </List>

      <Divider sx={{ mt: 'auto' }} />

      {/* Bottom navigation items */}
      <List sx={{ px: 1 }}>
        {bottomMenuItems.map((item) => (
          <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
            <Tooltip
              title={!isSidebarOpen ? item.text : ''}
              placement="right"
              arrow
              disableHoverListener={isSidebarOpen}
            >
              <ListItemButton
                onClick={() => handleNavigation(item.path)}
                selected={isActive(item.path)}
                sx={{
                  borderRadius: '8px',
                  justifyContent: isSidebarOpen ? 'initial' : 'center',
                  px: isSidebarOpen ? 2 : 1,
                  minHeight: 48,
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 0,
                    mr: isSidebarOpen ? 2 : 'auto',
                    justifyContent: 'center',
                    color: isActive(item.path)
                      ? 'primary.main'
                      : 'inherit',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                {isSidebarOpen && (
                  <ListItemText
                    primary={item.text}
                    primaryTypographyProps={{
                      fontWeight: isActive(item.path) ? 'bold' : 'medium',
                      color: isActive(item.path) ? 'primary.main' : 'inherit',
                      noWrap: true,
                    }}
                  />
                )}
              </ListItemButton>
            </Tooltip>
          </ListItem>
        ))}
      </List>
    </>
  );

  // Render different drawer types for mobile vs desktop
  return (
    <>
      {/* Mobile drawer (swipeable with backdrop) */}
      {isMobile ? (
        <SwipeableDrawer
          open={isSidebarOpen}
          onOpen={toggleSidebar}
          onClose={closeSidebar}
          disableBackdropTransition={!isMobile}
          disableDiscovery={isMobile}
          sx={{
            width: DRAWER_WIDTH,
            flexShrink: 0,
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': {
              width: DRAWER_WIDTH,
              boxSizing: 'border-box',
              border: 'none',
              boxShadow: '0 4px 20px 0 rgba(0,0,0,0.12)',
            },
          }}
        >
          {renderDrawerContent()}
        </SwipeableDrawer>
      ) : (
        // Desktop drawer (persistent)
        <Drawer
          variant="permanent"
          sx={{
            width: isSidebarOpen ? DRAWER_WIDTH : COLLAPSED_DRAWER_WIDTH,
            flexShrink: 0,
            display: { xs: 'none', md: 'block' },
            transition: theme.transitions.create(['width'], {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.enteringScreen,
            }),
            '& .MuiDrawer-paper': {
              width: isSidebarOpen ? DRAWER_WIDTH : COLLAPSED_DRAWER_WIDTH,
              boxSizing: 'border-box',
              border: 'none',
              boxShadow: '0 4px 20px 0 rgba(0,0,0,0.07)',
              overflow: 'hidden',
              transition: theme.transitions.create(['width'], {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.enteringScreen,
              }),
            },
          }}
        >
          {renderDrawerContent()}
        </Drawer>
      )}
    </>
  );
} 