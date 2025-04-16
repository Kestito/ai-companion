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
  Tooltip,
  useMediaQuery,
  useTheme,
  SwipeableDrawer,
  Badge
} from '@mui/material';
import {
  Dashboard,
  People,
  Message,
  Assessment,
  CalendarMonth,
  Settings,
  ChevronLeft,
  HealthAndSafety,
  NotificationsActive,
  MedicalServices,
  BarChart,
  Chat,
  KeyboardArrowDown,
  KeyboardArrowUp
} from '@mui/icons-material';
import { useRouter, usePathname } from 'next/navigation';
import { useNavigation } from '../providers/navigationprovider';
import { ReactNode, createContext, useContext, useState, useCallback, useMemo } from 'react';

const DRAWER_WIDTH = 280;
const COLLAPSED_DRAWER_WIDTH = 72;

// Types for our navigation items
interface NavigationItem {
  id: string;
  text: string;
  icon: ReactNode;
  path: string;
  description: string;
  permissions?: string[];
  badge?: number;
  subItems?: NavigationItem[];
}

// Context for collapsible sections
interface SidebarContextType {
  expandedGroups: Record<string, boolean>;
  toggleGroup: (id: string) => void;
}

const SidebarContext = createContext<SidebarContextType>({
  expandedGroups: {},
  toggleGroup: () => {}
});

// Custom hook for sidebar navigation
export const useSidebarNavigation = () => {
  return useContext(SidebarContext);
};

// Main navigation items for the sidebar
const mainNavigationItems: NavigationItem[] = [
  { id: 'dashboard', text: 'Dashboard', icon: <Dashboard />, path: '/dashboard', description: 'Overview and statistics' },
  { id: 'patients', text: 'Patients', icon: <People />, path: '/patients', description: 'Patient management' },
  { id: 'appointments', text: 'Appointments', icon: <CalendarMonth />, path: '/appointments', description: 'Schedule management' },
  { id: 'messages', text: 'Messages', icon: <Message />, path: '/messages', description: 'Communication center', badge: 3 },
  { id: 'health-records', text: 'Health Records', icon: <HealthAndSafety />, path: '/records', description: 'Patient health data' },
  { id: 'alerts', text: 'Alerts', icon: <NotificationsActive />, path: '/alerts', description: 'Critical notifications', badge: 2 },
  { id: 'analytics', text: 'Analytics', icon: <BarChart />, path: '/analytics', description: 'Data analysis' },
  { id: 'telegram', text: 'Telegram Messages', icon: <Chat />, path: '/telegram-messages', description: 'Telegram messaging' },
];

// Bottom navigation items for settings, etc.
const bottomNavigationItems: NavigationItem[] = [
  { id: 'resources', text: 'Resources', icon: <MedicalServices />, path: '/resources', description: 'Reference materials' },
  { id: 'settings', text: 'Settings', icon: <Settings />, path: '/settings', description: 'System configuration', subItems: [
    { id: 'settings-profile', text: 'Profile Settings', icon: <Settings />, path: '/settings/profile', description: 'User profile settings' },
    { id: 'settings-system', text: 'System Settings', icon: <Settings />, path: '/settings/system', description: 'System configuration' },
  ]},
];

/**
 * Individual sidebar item component
 */
const SidebarItem = ({ item, isOpen }: { item: NavigationItem, isOpen: boolean }) => {
  const router = useRouter();
  const pathname = usePathname();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { expandedGroups, toggleGroup } = useSidebarNavigation();
  
  // Navigate to the selected path
  const handleNavigation = useCallback((path: string) => {
    router.push(path);
  }, [router]);
  
  // Close sidebar on mobile after navigation
  const { closeSidebar } = useNavigation();

  // Determine if an item is currently selected
  const isActive = useCallback((path: string) => {
    return pathname === path || pathname.startsWith(`${path}/`);
  }, [pathname]);

  const hasSubItems = item.subItems && item.subItems.length > 0;
  const isExpanded = hasSubItems && expandedGroups[item.id];

  const handleItemClick = useCallback(() => {
    if (hasSubItems) {
      toggleGroup(item.id);
    } else {
      handleNavigation(item.path);
      if (isMobile) {
        closeSidebar();
      }
    }
  }, [hasSubItems, item.id, item.path, toggleGroup, handleNavigation, isMobile, closeSidebar]);

  return (
    <>
      <ListItem disablePadding sx={{ mb: 0.5 }}>
        <Tooltip
          title={!isOpen ? item.text : ''}
          placement="right"
          arrow
          disableHoverListener={isOpen}
        >
          <ListItemButton
            onClick={handleItemClick}
            selected={isActive(item.path)}
            sx={{
              borderRadius: '8px',
              justifyContent: isOpen ? 'initial' : 'center',
              px: isOpen ? 2 : 1,
              minHeight: 48,
            }}
          >
            <ListItemIcon
              sx={{
                minWidth: 0,
                mr: isOpen ? 2 : 'auto',
                justifyContent: 'center',
                color: isActive(item.path) ? 'primary.main' : 'inherit',
              }}
            >
              {item.badge ? (
                <Badge badgeContent={item.badge} color="error">
                  {item.icon}
                </Badge>
              ) : (
                item.icon
              )}
            </ListItemIcon>
            
            {isOpen && (
              <>
                <ListItemText
                  primary={item.text}
                  secondary={isOpen && !hasSubItems ? item.description : null}
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
                
                {hasSubItems && (
                  <IconButton 
                    edge="end" 
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleGroup(item.id);
                    }}
                  >
                    {isExpanded ? <KeyboardArrowUp fontSize="small" /> : <KeyboardArrowDown fontSize="small" />}
                  </IconButton>
                )}
              </>
            )}
          </ListItemButton>
        </Tooltip>
      </ListItem>
      
      {hasSubItems && isExpanded && isOpen && (
        <List component="div" disablePadding sx={{ pl: 4 }}>
          {item.subItems?.map((subItem) => (
            <ListItem key={subItem.id} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                onClick={() => {
                  handleNavigation(subItem.path);
                  if (isMobile) {
                    closeSidebar();
                  }
                }}
                selected={isActive(subItem.path)}
                sx={{
                  borderRadius: '8px',
                  minHeight: 40,
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 0,
                    mr: 2,
                    justifyContent: 'center',
                    color: isActive(subItem.path) ? 'primary.main' : 'inherit',
                  }}
                >
                  {subItem.icon}
                </ListItemIcon>
                <ListItemText
                  primary={subItem.text}
                  primaryTypographyProps={{
                    fontSize: '0.875rem',
                    fontWeight: isActive(subItem.path) ? 'bold' : 'medium',
                    color: isActive(subItem.path) ? 'primary.main' : 'inherit',
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      )}
    </>
  );
};

/**
 * Sidebar navigation component
 * Provides main navigation for the application
 * Responsive for both desktop and mobile devices
 */
export default function Sidebar() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  // For tracking expanded navigation groups
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});
  
  const toggleGroup = useCallback((id: string) => {
    setExpandedGroups(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  }, []);
  
  // Memoize the context value
  const contextValue = useMemo(() => ({
    expandedGroups,
    toggleGroup
  }), [expandedGroups, toggleGroup]);
  
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

  // Responsive drawer for mobile and desktop
  const renderDrawerContent = () => (
    <SidebarContext.Provider value={contextValue}>
      {/* Sidebar header with close button */}
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
            <Box sx={{ typography: 'h6' }}>Evelina AI</Box>
          </Box>
        )}
        <IconButton onClick={toggleSidebar} aria-label={isSidebarOpen ? "Collapse sidebar" : "Expand sidebar"}>
          <ChevronLeft />
        </IconButton>
      </Box>

      <Divider />

      {/* Main navigation items */}
      <List sx={{ px: 1 }}>
        {mainNavigationItems.map((item) => (
          <SidebarItem key={item.id} item={item} isOpen={isSidebarOpen} />
        ))}
      </List>

      <Divider sx={{ mt: 'auto' }} />

      {/* Bottom navigation items */}
      <List sx={{ px: 1 }}>
        {bottomNavigationItems.map((item) => (
          <SidebarItem key={item.id} item={item} isOpen={isSidebarOpen} />
        ))}
      </List>
    </SidebarContext.Provider>
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
            '& .MuiDrawer-paper': {
              width: DRAWER_WIDTH,
              boxSizing: 'border-box',
              border: 'none',
              boxShadow: theme.shadows[8],
            },
          }}
        >
          {renderDrawerContent()}
        </SwipeableDrawer>
      ) : (
        /* Desktop drawer (persistent) */
        <Drawer
          variant="permanent"
          open={isSidebarOpen}
          sx={{
            width: isSidebarOpen ? DRAWER_WIDTH : COLLAPSED_DRAWER_WIDTH,
            flexShrink: 0,
            transition: theme.transitions.create('width', {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.enteringScreen,
            }),
            '& .MuiDrawer-paper': {
              width: isSidebarOpen ? DRAWER_WIDTH : COLLAPSED_DRAWER_WIDTH,
              boxSizing: 'border-box',
              overflowX: 'hidden',
              transition: theme.transitions.create('width', {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.enteringScreen,
              }),
              border: 'none',
              boxShadow: theme.shadows[3],
            },
          }}
        >
          {renderDrawerContent()}
        </Drawer>
      )}
    </>
  );
} 