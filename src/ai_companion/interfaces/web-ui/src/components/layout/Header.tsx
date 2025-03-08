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
  LightMode
} from '@mui/icons-material';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

/**
 * Application header component
 * Contains notifications, user menu, and global actions
 */
export default function Header() {
  const router = useRouter();
  const theme = useTheme();
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
        zIndex: (theme) => theme.zIndex.drawer + 1,
        borderBottom: '1px solid',
        borderColor: 'divider',
        height: '64px',
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between', minHeight: '64px', px: 2 }}>
        {/* Search bar */}
        <Box
          component="form"
          onSubmit={handleSearch}
          sx={{ 
            display: 'flex',
            alignItems: 'center',
            backgroundColor: theme.palette.grey[100],
            borderRadius: 2,
            px: 2,
            maxWidth: 400,
            width: { xs: '100%', sm: 300, md: 400 },
            mx: { xs: 0, md: 2 }
          }}
        >
          <InputBase
            placeholder="Search patients, records..."
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            sx={{ flexGrow: 1 }}
            inputProps={{ 'aria-label': 'search' }}
          />
          <IconButton type="submit" aria-label="search">
            <Search />
          </IconButton>
        </Box>
        
        {/* Right-side actions */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title="Help & Resources">
            <IconButton 
              color="inherit"
              onClick={() => router.push('/help')}
              size="medium"
            >
              <Help />
            </IconButton>
          </Tooltip>

          <Tooltip title="Notifications">
            <IconButton 
              size="medium" 
              color="inherit"
              onClick={handleNotificationClick}
              aria-controls={notificationsOpen ? 'notification-menu' : undefined}
              aria-haspopup="true"
              aria-expanded={notificationsOpen ? 'true' : undefined}
            >
              <Badge badgeContent={3} color="error">
                <Notifications />
              </Badge>
            </IconButton>
          </Tooltip>

          <Tooltip title="User Account">
            <IconButton
              onClick={handleClick}
              size="small"
              aria-controls={open ? 'account-menu' : undefined}
              aria-haspopup="true"
              aria-expanded={open ? 'true' : undefined}
            >
              <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>A</Avatar>
            </IconButton>
          </Tooltip>
        </Box>
      </Toolbar>

      {/* Notifications Menu */}
      <Menu
        anchorEl={notificationAnchorEl}
        id="notification-menu"
        open={notificationsOpen}
        onClose={handleNotificationClose}
        onClick={handleNotificationClose}
        PaperProps={{
          elevation: 0,
          sx: {
            overflow: 'visible',
            filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.08))',
            mt: 1.5,
            width: 320,
            '& .MuiMenuItem-root': {
              px: 2,
              py: 1,
              borderBottom: '1px solid',
              borderColor: 'divider',
            },
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
          <Typography variant="subtitle1" fontWeight="bold">Notifications</Typography>
        </Box>
        
        <MenuItem onClick={() => router.push('/alerts/1')}>
          <Box sx={{ display: 'flex', flexDirection: 'column' }}>
            <Typography variant="body2" fontWeight="bold">
              Patient Alert: Critical Condition
            </Typography>
            <Typography variant="caption" color="text.secondary">
              John Smith - Blood pressure critical - 10 min ago
            </Typography>
          </Box>
        </MenuItem>
        
        <MenuItem onClick={() => router.push('/appointments')}>
          <Box sx={{ display: 'flex', flexDirection: 'column' }}>
            <Typography variant="body2" fontWeight="bold">
              Upcoming Appointment
            </Typography>
            <Typography variant="caption" color="text.secondary">
              In 15 minutes with Dr. Johnson - Room 302
            </Typography>
          </Box>
        </MenuItem>
        
        <MenuItem onClick={() => router.push('/messages')}>
          <Box sx={{ display: 'flex', flexDirection: 'column' }}>
            <Typography variant="body2" fontWeight="bold">
              New Message
            </Typography>
            <Typography variant="caption" color="text.secondary">
              From: Dr. Wilson - Regarding patient #12345
            </Typography>
          </Box>
        </MenuItem>
        
        <Box sx={{ p: 2, textAlign: 'center' }}>
          <Button 
            onClick={() => router.push('/notifications')}
            size="small"
            sx={{ width: '100%' }}
          >
            View All Notifications
          </Button>
        </Box>
      </Menu>

      {/* User Account Menu */}
      <Menu
        anchorEl={anchorEl}
        id="account-menu"
        open={open}
        onClose={handleClose}
        onClick={handleClose}
        PaperProps={{
          elevation: 0,
          sx: {
            overflow: 'visible',
            filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.08))',
            mt: 1.5,
            '& .MuiMenuItem-root': {
              px: 2,
              py: 1,
            },
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <Box sx={{ px: 2, py: 1 }}>
          <Typography variant="subtitle2">Admin User</Typography>
          <Typography variant="body2" color="text.secondary">
            admin@example.com
          </Typography>
        </Box>
        <Divider />
        <MenuItem onClick={() => router.push('/profile')}>
          <ListItemIcon>
            <Person fontSize="small" />
          </ListItemIcon>
          Profile
        </MenuItem>
        <MenuItem onClick={() => router.push('/settings')}>
          <ListItemIcon>
            <Settings fontSize="small" />
          </ListItemIcon>
          Settings
        </MenuItem>
        <MenuItem>
          <ListItemIcon>
            {theme.palette.mode === 'dark' ? (
              <LightMode fontSize="small" />
            ) : (
              <NightsStay fontSize="small" />
            )}
          </ListItemIcon>
          {theme.palette.mode === 'dark' ? 'Light' : 'Dark'} Mode
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleLogout}>
          <ListItemIcon>
            <Logout fontSize="small" />
          </ListItemIcon>
          Logout
        </MenuItem>
      </Menu>
    </AppBar>
  );
} 