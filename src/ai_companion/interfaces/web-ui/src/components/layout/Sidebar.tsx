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
  Tooltip
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
  BarChart
} from '@mui/icons-material';
import { useRouter, usePathname } from 'next/navigation';
import Image from 'next/image';
import { useNavigation } from '../providers/NavigationProvider';

const DRAWER_WIDTH = 280;

// Main navigation items for the sidebar
const menuItems = [
  { text: 'Dashboard', icon: <Dashboard />, path: '/dashboard', description: 'Overview and statistics' },
  { text: 'Patients', icon: <People />, path: '/patients', description: 'Patient management' },
  { text: 'Appointments', icon: <CalendarMonth />, path: '/appointments', description: 'Schedule management' },
  { text: 'Messages', icon: <Message />, path: '/messages', description: 'Communication center' },
  { text: 'Health Records', icon: <HealthAndSafety />, path: '/records', description: 'Patient health data' },
  { text: 'Alerts', icon: <NotificationsActive />, path: '/alerts', description: 'Critical notifications' },
  { text: 'Analytics', icon: <BarChart />, path: '/analytics', description: 'Data analysis' },
];

// Bottom navigation items for settings, etc.
const bottomMenuItems = [
  { text: 'Medical Resources', icon: <MedicalServices />, path: '/resources', description: 'Reference materials' },
  { text: 'Settings', icon: <Settings />, path: '/settings', description: 'System configuration' },
];

/**
 * Sidebar navigation component
 * Provides main navigation for the application
 * Can be collapsed to save space
 */
export default function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const { isSidebarOpen, toggleSidebar } = useNavigation();

  // Navigate to the selected path
  const handleNavigation = (path: string) => {
    router.push(path);
  };

  // Determine if an item is currently selected
  const isActive = (path: string) => {
    return pathname === path || pathname.startsWith(`${path}/`);
  };

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: isSidebarOpen ? DRAWER_WIDTH : 72,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: isSidebarOpen ? DRAWER_WIDTH : 72,
          boxSizing: 'border-box',
          borderRight: '1px solid',
          borderColor: 'divider',
          transition: 'width 0.2s ease-in-out',
          overflowX: 'hidden',
        },
      }}
    >
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
        {isSidebarOpen && (
          <Image
            src="/logo.svg"
            alt="AI Companion Logo"
            width={40}
            height={40}
            priority
          />
        )}
        {isSidebarOpen && (
          <Typography variant="h6" noWrap>
            AI Companion
          </Typography>
        )}
        <IconButton 
          onClick={toggleSidebar}
          sx={{ ml: isSidebarOpen ? 'auto' : 'auto' }}
          aria-label={isSidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
        >
          {isSidebarOpen ? <ChevronLeft /> : <MenuIcon />}
        </IconButton>
      </Box>

      <Divider />

      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        <List>
          {menuItems.map((item) => (
            <ListItem key={item.text} disablePadding>
              <Tooltip 
                title={!isSidebarOpen ? item.text : ""}
                placement="right"
                arrow
              >
                <ListItemButton
                  selected={isActive(item.path)}
                  onClick={() => handleNavigation(item.path)}
                  sx={{
                    minHeight: 48,
                    px: 2.5,
                    '&.Mui-selected': {
                      bgcolor: 'primary.light',
                      color: 'primary.contrastText',
                      '& .MuiListItemIcon-root': {
                        color: 'primary.contrastText',
                      },
                    },
                    '&:hover': {
                      bgcolor: 'action.hover',
                    },
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 36, color: isActive(item.path) ? 'inherit' : 'primary.main' }}>
                    {item.icon}
                  </ListItemIcon>
                  {isSidebarOpen && (
                    <ListItemText 
                      primary={item.text} 
                      secondary={item.description}
                      primaryTypographyProps={{
                        variant: 'body2',
                        fontWeight: isActive(item.path) ? 'bold' : 'medium',
                      }}
                      secondaryTypographyProps={{
                        variant: 'caption',
                        sx: { display: { xs: 'none', sm: 'block' } }
                      }}
                    />
                  )}
                </ListItemButton>
              </Tooltip>
            </ListItem>
          ))}
        </List>
      </Box>

      <Divider />

      <List>
        {bottomMenuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <Tooltip 
              title={!isSidebarOpen ? item.text : ""}
              placement="right"
              arrow
            >
              <ListItemButton
                selected={isActive(item.path)}
                onClick={() => handleNavigation(item.path)}
                sx={{
                  minHeight: 48,
                  px: 2.5,
                  '&.Mui-selected': {
                    bgcolor: 'primary.light',
                    color: 'primary.contrastText',
                    '& .MuiListItemIcon-root': {
                      color: 'primary.contrastText',
                    },
                  },
                  '&:hover': {
                    bgcolor: 'action.hover',
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 36, color: isActive(item.path) ? 'inherit' : 'primary.main' }}>
                  {item.icon}
                </ListItemIcon>
                {isSidebarOpen && (
                  <ListItemText 
                    primary={item.text} 
                    secondary={item.description}
                    primaryTypographyProps={{
                      variant: 'body2',
                      fontWeight: isActive(item.path) ? 'bold' : 'medium',
                    }}
                    secondaryTypographyProps={{
                      variant: 'caption',
                      sx: { display: { xs: 'none', sm: 'block' } }
                    }}
                  />
                )}
              </ListItemButton>
            </Tooltip>
          </ListItem>
        ))}
      </List>

      {isSidebarOpen && (
        <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
          <Stack direction="row" spacing={2} alignItems="center">
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>A</Avatar>
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="subtitle2" noWrap>
                Admin User
              </Typography>
              <Typography variant="body2" color="text.secondary" noWrap>
                admin@example.com
              </Typography>
            </Box>
          </Stack>
        </Box>
      )}
    </Drawer>
  );
} 