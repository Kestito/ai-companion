'use client';

import { 
  AppBar, 
  Toolbar, 
  IconButton, 
  Typography, 
  Badge, 
  Box,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  ListItemIcon,
  Button,
  InputBase,
  Tooltip,
  useTheme
} from '@mui/material';
import { 
  Notifications,
  Settings,
  Logout,
  Person,
  Search,
  Help,
  NightsStay,
  LightMode,
  Menu as MenuIcon
} from '@mui/icons-material';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { useNavigation } from '../providers/navigationprovider';

/**
 * Application header component
 * Contains notifications, user menu, and global actions
 */
export default function Header() {
  const router = useRouter();
  const theme = useTheme();
  
  // Safe access to navigation context
  let toggleSidebar = () => {};
  try {
    // This will throw an error during static generation but work during client rendering
    const navigation = useNavigation();
    toggleSidebar = navigation.toggleSidebar;
  } catch (error) {
    // During static generation/build, we'll just use a no-op function
    console.log('Navigation context not available, using fallback');
  }
  
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [notificationAnchorEl, setNotificationAnchorEl] = useState<null | HTMLElement>(null);
  const [searchValue, setSearchValue] = useState('');
  const open = Boolean(anchorEl);
  const notificationsOpen = Boolean(notificationAnchorEl);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleNotificationClick = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleNotificationClose = () => {
    setNotificationAnchorEl(null);
  };

  const handleLogout = () => {
    // Handle logout logic here
    router.push('/login');
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchValue.trim()) {
      // Implement search functionality
      console.log(`Searching for: ${searchValue}`);
      // router.push(`/search?q=${encodeURIComponent(searchValue)}`);
    }
  };

  return (
    <AppBar 
      position="fixed" 
      color="inherit" 
      elevation={0}
      sx={{
        zIndex: theme.zIndex.drawer + 1,
        borderBottom: '1px solid',
        borderColor: 'divider',
        height: { xs: '64px', sm: '72px' }, // Responsive height
      }}
    >
      <Toolbar sx={{ 
        minHeight: { xs: '64px', sm: '72px' } // Match AppBar height
      }}>
        {/* Left section - Logo and menu toggle */}
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center',
          mr: 2
        }}>
          <IconButton
            color="inherit"
            aria-label="toggle sidebar"
            edge="start"
            onClick={toggleSidebar}
            sx={{ mr: 1 }}
          >
            <MenuIcon />
          </IconButton>
          
          <Box 
            sx={{ 
              display: { xs: 'none', sm: 'flex' },
              alignItems: 'center'
            }}
          >
            <Box sx={{ width: 32, height: 32, position: 'relative', mr: 1 }}>
              <Image
                src="/EvelinaAIlogosmall.webp"
                alt="Evelina AI Logo"
                width={32}
                height={32}
                priority
                style={{ objectFit: 'contain' }}
              />
            </Box>
            <Typography variant="h6" noWrap component="div">
              Evelina AI
            </Typography>
          </Box>
        </Box>

        {/* Center section - Search bar */}
        <Box 
          component="form" 
          onSubmit={handleSearch}
          sx={{
            display: { xs: 'none', md: 'flex' },
            flexGrow: 1,
            mx: 2,
            position: 'relative',
            borderRadius: 1,
            backgroundColor: 'action.hover',
            maxWidth: '600px',
          }}
        >
          <IconButton type="submit" sx={{ p: '10px' }} aria-label="search">
            <Search />
          </IconButton>
          <InputBase
            sx={{ ml: 1, flex: 1 }}
            placeholder="Search patients, appointments, messages..."
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
          />
        </Box>

        {/* Right section - Actions and profile */}
        <Box sx={{ display: 'flex', alignItems: 'center', ml: 'auto' }}>
          {/* Mobile search icon */}
          <IconButton 
            sx={{ 
              display: { xs: 'flex', md: 'none' },
              mr: 1
            }}
            onClick={() => {
              // Implement mobile search overlay/dialog
              console.log('Mobile search opened');
            }}
          >
            <Search />
          </IconButton>

          {/* Help button */}
          <Tooltip title="Help">
            <IconButton 
              sx={{ 
                mr: 1, 
                display: { xs: 'none', sm: 'flex' } 
              }}
              onClick={() => router.push('/help')}
            >
              <Help />
            </IconButton>
          </Tooltip>

          {/* Notifications */}
          <Tooltip title="Notifications">
            <IconButton 
              sx={{ mr: 1 }}
              onClick={handleNotificationClick}
            >
              <Badge badgeContent={4} color="error">
                <Notifications />
              </Badge>
            </IconButton>
          </Tooltip>

          {/* User profile */}
          <IconButton
            onClick={handleClick}
            aria-controls={open ? 'account-menu' : undefined}
            aria-haspopup="true"
            aria-expanded={open ? 'true' : undefined}
          >
            <Avatar 
              alt="User Profile" 
              src="/avatar-placeholder.jpg"
              sx={{ width: 32, height: 32 }}
            />
          </IconButton>
        </Box>

        {/* User Menu */}
        <Menu
          anchorEl={anchorEl}
          id="account-menu"
          open={open}
          onClose={handleClose}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        >
          <MenuItem onClick={() => { router.push('/profile'); handleClose(); }}>
            <ListItemIcon><Person fontSize="small" /></ListItemIcon>
            Profile
          </MenuItem>
          <MenuItem onClick={() => { router.push('/settings'); handleClose(); }}>
            <ListItemIcon><Settings fontSize="small" /></ListItemIcon>
            Settings
          </MenuItem>
          <Divider />
          <MenuItem onClick={handleLogout}>
            <ListItemIcon><Logout fontSize="small" /></ListItemIcon>
            Logout
          </MenuItem>
        </Menu>

        {/* Notifications Menu */}
        <Menu
          anchorEl={notificationAnchorEl}
          id="notifications-menu"
          open={notificationsOpen}
          onClose={handleNotificationClose}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          PaperProps={{
            sx: { 
              minWidth: { xs: '300px', sm: '350px' },
              maxWidth: { xs: 'calc(100vw - 32px)', sm: '400px' },
              maxHeight: '400px',
              overflow: 'auto'
            }
          }}
        >
          {/* Notifications header */}
          <Box sx={{ p: 2 }}>
            <Typography variant="subtitle1" fontWeight="bold">Notifications</Typography>
          </Box>
          <Divider />
          
          {/* Example notifications */}
          <MenuItem onClick={handleNotificationClose} sx={{ py: 1.5 }}>
            <Box sx={{ display: 'flex', flexDirection: 'column' }}>
              <Typography variant="body2" fontWeight="medium">New patient registered</Typography>
              <Typography variant="caption" color="text.secondary">5 minutes ago</Typography>
            </Box>
          </MenuItem>
          <MenuItem onClick={handleNotificationClose} sx={{ py: 1.5 }}>
            <Box sx={{ display: 'flex', flexDirection: 'column' }}>
              <Typography variant="body2" fontWeight="medium">Appointment reminder: Patient #1234</Typography>
              <Typography variant="caption" color="text.secondary">15 minutes ago</Typography>
            </Box>
          </MenuItem>
          <MenuItem onClick={handleNotificationClose} sx={{ py: 1.5 }}>
            <Box sx={{ display: 'flex', flexDirection: 'column' }}>
              <Typography variant="body2" fontWeight="medium">System update available</Typography>
              <Typography variant="caption" color="text.secondary">1 hour ago</Typography>
            </Box>
          </MenuItem>
          
          {/* View all link */}
          <Divider />
          <Box sx={{ p: 1, textAlign: 'center' }}>
            <Button 
              size="small" 
              onClick={() => { 
                router.push('/notifications'); 
                handleNotificationClose(); 
              }}
            >
              View all notifications
            </Button>
          </Box>
        </Menu>
      </Toolbar>
    </AppBar>
  );
} 