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
  Stack
} from '@mui/material';
import {
  Dashboard,
  People,
  Message,
  Assessment,
  CalendarMonth,
  Settings,
  Menu as MenuIcon,
  ChevronLeft
} from '@mui/icons-material';
import { useRouter, usePathname } from 'next/navigation';
import Image from 'next/image';
import { useNavigation } from '../providers/NavigationProvider';

const DRAWER_WIDTH = 280;

const menuItems = [
  { text: 'Dashboard', icon: <Dashboard />, path: '/dashboard' },
  { text: 'Users', icon: <People />, path: '/users' },
  { text: 'Messages', icon: <Message />, path: '/messages' },
  { text: 'Analytics', icon: <Assessment />, path: '/analytics' },
  { text: 'Schedule', icon: <CalendarMonth />, path: '/schedule' },
];

const bottomMenuItems = [
  { text: 'Settings', icon: <Settings />, path: '/settings' },
];

export default function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const { isSidebarOpen, toggleSidebar } = useNavigation();

  const handleNavigation = (path: string) => {
    router.push(path);
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
            alt="Evelina AI Logo"
            width={40}
            height={40}
            priority
          />
        )}
        {isSidebarOpen && (
          <Typography variant="h6" noWrap>
            Evelina AI
          </Typography>
        )}
        <IconButton 
          onClick={toggleSidebar}
          sx={{ ml: isSidebarOpen ? 'auto' : 'auto' }}
        >
          {isSidebarOpen ? <ChevronLeft /> : <MenuIcon />}
        </IconButton>
      </Box>

      <Divider />

      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        <List>
          {menuItems.map((item) => (
            <ListItem key={item.text} disablePadding>
              <ListItemButton
                selected={pathname === item.path}
                onClick={() => handleNavigation(item.path)}
                sx={{
                  minHeight: 48,
                  px: 2.5,
                  '&.Mui-selected': {
                    bgcolor: 'action.selected',
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 36 }}>
                  {item.icon}
                </ListItemIcon>
                {isSidebarOpen && <ListItemText primary={item.text} />}
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Box>

      <Divider />

      <List>
        {bottomMenuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={pathname === item.path}
              onClick={() => handleNavigation(item.path)}
              sx={{
                minHeight: 48,
                px: 2.5,
                '&.Mui-selected': {
                  bgcolor: 'action.selected',
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 36 }}>
                {item.icon}
              </ListItemIcon>
              {isSidebarOpen && <ListItemText primary={item.text} />}
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      {isSidebarOpen && (
        <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
          <Stack direction="row" spacing={2} alignItems="center">
            <Avatar sx={{ width: 32, height: 32 }}>A</Avatar>
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="subtitle2" noWrap>
                Admin User
              </Typography>
              <Typography variant="body2" color="text.secondary" noWrap>
                admin@evelina.ai
              </Typography>
            </Box>
          </Stack>
        </Box>
      )}
    </Drawer>
  );
} 