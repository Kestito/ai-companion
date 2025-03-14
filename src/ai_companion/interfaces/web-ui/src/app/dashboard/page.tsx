'use client';

import { Box, Container, Grid, Paper, Typography, Button, IconButton, Stack, Divider, Alert, Card, CardContent, Badge } from '@mui/material';
import { 
  Notifications as NotificationsIcon, 
  Person as PersonIcon, 
  Message as MessageIcon, 
  CalendarToday as CalendarIcon,
  TrendingUp as TrendingUpIcon,
  MoreVert as MoreVertIcon,
  Add as AddIcon,
  Home as HomeIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchPatientStatistics } from '@/lib/supabase/patientService';
import { fetchRecentActivity, ActivityItem } from '@/lib/supabase/activityService';
import { fetchNotifications, Notification } from '@/lib/supabase/notificationService';
import { useLogger } from '@/hooks/useLogger';
import { AlertTitle } from '@mui/material';

// Default stats for initial render
const defaultStats = {
  totalPatients: 0,
  activePatients: 0,
  newPatients: 0,
  criticalPatients: 0,
  pendingAppointments: 0,
  responseRate: 0
};

const StatCard = ({ title, value, icon, color = 'primary' }: { 
  title: string; 
  value: number | string; 
  icon?: React.ReactNode;
  color?: 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success';
}) => {
  return (
    <Paper
      elevation={0}
      sx={{
        p: 3,
        height: '100%',
        bgcolor: 'background.paper',
        borderRadius: 2,
        border: '1px solid',
        borderColor: 'divider',
        position: 'relative',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          width: '4px',
          height: '100%',
          bgcolor: `${color}.main`,
        }
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {title}
          </Typography>
          <Typography variant="h3" component="div" gutterBottom fontWeight="500">
            {value}
          </Typography>
        </Box>
        {icon && (
          <Box sx={{ 
            p: 1, 
            borderRadius: 2, 
            bgcolor: `${color}.lighter`,
            color: `${color}.main`
          }}>
            {icon}
          </Box>
        )}
      </Box>
    </Paper>
  );
};

const ActivityCard = ({ title, items }: { title: string; items: ActivityItem[] }) => (
  <Paper
    elevation={0}
    sx={{
      p: 3,
      height: '100%',
      bgcolor: 'background.paper',
      borderRadius: 2,
      border: '1px solid',
      borderColor: 'divider',
    }}
  >
    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
      <Typography variant="h6">{title}</Typography>
      <IconButton size="small">
        <MoreVertIcon />
      </IconButton>
    </Box>
    <Stack spacing={2}>
      {items.map((item) => (
        <Box 
          key={item.id} 
          sx={{ 
            display: 'flex', 
            alignItems: 'flex-start', 
            gap: 2,
            p: 1.5,
            borderRadius: 1,
            bgcolor: 'background.default',
            '&:hover': {
              bgcolor: 'action.hover',
            },
            borderBottom: '1px solid',
            borderColor: 'divider',
            '&:last-child': {
              borderBottom: 'none'
            }
          }}
        >
          <Box 
            sx={{ 
              width: 8, 
              height: 8, 
              borderRadius: '50%', 
              bgcolor: `${item.severity}.main`,
              flexShrink: 0,
              mt: 1
            }} 
          />
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
              {item.time}
            </Typography>
            <Typography variant="body1">
              <Box component="span" fontWeight="fontWeightMedium">{item.user}</Box> • {item.action}
            </Typography>
          </Box>
        </Box>
      ))}
    </Stack>
  </Paper>
);

const NotificationsCard = ({ notifications }: { notifications: Notification[] }) => {
  const getIconForType = (icon: string) => {
    switch(icon) {
      case 'warning': return <WarningIcon color="error" />;
      case 'event': return <CalendarIcon color="warning" />;
      case 'update': return <TrendingUpIcon color="info" />;
      default: return <NotificationsIcon color="primary" />;
    }
  };

  return (
    <Paper
      elevation={0}
      sx={{
        p: 3,
        height: '100%',
        bgcolor: 'background.paper',
        borderRadius: 2,
        border: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Typography variant="h6" gutterBottom>
        Notifications
      </Typography>
      <Stack spacing={2}>
        {notifications.map((notification) => (
          <Box 
            key={notification.id} 
            sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 2,
              p: 2,
              borderRadius: 1,
              bgcolor: `${notification.type}.lighter`,
              color: `${notification.type}.main`,
              border: 1,
              borderColor: `${notification.type}.light`
            }}
          >
            {getIconForType(notification.icon)}
            <Typography variant="body2" color="inherit">
              {notification.message}
            </Typography>
          </Box>
        ))}
      </Stack>
      <Button
        fullWidth
        variant="outlined"
        sx={{ mt: 3 }}
        color="primary"
      >
        View All Notifications
      </Button>
    </Paper>
  );
};

const QuickActions = () => (
  <Paper
    elevation={0}
    sx={{
      p: 3,
      height: '100%',
      bgcolor: 'background.paper',
      borderRadius: 2,
      border: '1px solid',
      borderColor: 'divider',
    }}
  >
    <Typography variant="h6" gutterBottom>
      Quick Actions
    </Typography>
    <Stack spacing={2}>
      <Button 
        startIcon={<AddIcon />} 
        variant="contained" 
        color="primary"
        fullWidth
        size="large"
      >
        New Patient
      </Button>
      <Button 
        startIcon={<MessageIcon />} 
        variant="outlined" 
        color="primary"
        fullWidth
        size="large"
      >
        Send Message
      </Button>
    </Stack>
  </Paper>
);

const StatCardSkeleton = () => (
  <Paper
    elevation={0}
    sx={{
      p: 3,
      height: '100%',
      bgcolor: 'background.paper',
      borderRadius: 2,
      border: '1px solid',
      borderColor: 'divider',
      position: 'relative',
      overflow: 'hidden',
    }}
  >
    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
      <Box width="100%">
        <Box sx={{ bgcolor: 'action.hover', height: 20, width: '50%', borderRadius: 1, mb: 2 }} />
        <Box sx={{ bgcolor: 'action.hover', height: 40, width: '40%', borderRadius: 1, mb: 2 }} />
      </Box>
      <Box sx={{ 
        p: 1, 
        borderRadius: 2, 
        bgcolor: 'action.hover',
        width: 40,
        height: 40
      }} />
    </Box>
  </Paper>
);

const ActivityCardSkeleton = () => (
  <Paper
    elevation={0}
    sx={{
      p: 3,
      height: '100%',
      bgcolor: 'background.paper',
      borderRadius: 2,
      border: '1px solid',
      borderColor: 'divider',
    }}
  >
    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
      <Box sx={{ bgcolor: 'action.hover', height: 24, width: '30%', borderRadius: 1 }} />
      <Box sx={{ bgcolor: 'action.hover', height: 24, width: 24, borderRadius: '50%' }} />
    </Box>
    <Stack spacing={2}>
      {[1, 2, 3, 4, 5].map((index) => (
        <Box 
          key={index} 
          sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 2,
            p: 1.5,
            borderRadius: 1,
            bgcolor: 'background.default',
            borderBottom: '1px solid',
            borderColor: 'divider',
            '&:last-child': {
              borderBottom: 'none'
            }
          }}
        >
          <Box 
            sx={{ 
              width: 8, 
              height: 8, 
              borderRadius: '50%', 
              bgcolor: 'action.hover',
              flexShrink: 0
            }} 
          />
          <Box sx={{ flexGrow: 1 }}>
            <Box sx={{ bgcolor: 'action.hover', height: 16, width: '20%', borderRadius: 1, mb: 1 }} />
            <Box sx={{ bgcolor: 'action.hover', height: 20, width: '80%', borderRadius: 1 }} />
          </Box>
        </Box>
      ))}
    </Stack>
  </Paper>
);

const NotificationsCardSkeleton = () => (
  <Paper
    elevation={0}
    sx={{
      p: 3,
      height: '100%',
      bgcolor: 'background.paper',
      borderRadius: 2,
      border: '1px solid',
      borderColor: 'divider',
    }}
  >
    <Box sx={{ bgcolor: 'action.hover', height: 24, width: '40%', borderRadius: 1, mb: 3 }} />
    <Stack spacing={2}>
      {[1, 2, 3].map((index) => (
        <Box 
          key={index} 
          sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 2,
            p: 2,
            borderRadius: 1,
            bgcolor: 'action.hover',
          }}
        >
          <Box sx={{ bgcolor: 'background.paper', height: 24, width: 24, borderRadius: '50%' }} />
          <Box sx={{ bgcolor: 'background.paper', height: 16, width: '80%', borderRadius: 1 }} />
        </Box>
      ))}
    </Stack>
    <Box sx={{ bgcolor: 'action.hover', height: 36, width: '100%', borderRadius: 1, mt: 3 }} />
  </Paper>
);

export default function DashboardPage() {
  const router = useRouter();
  const logger = useLogger({ component: 'DashboardPage' });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [stats, setStats] = useState(defaultStats);
  const [recentActivity, setRecentActivity] = useState<ActivityItem[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());

  useEffect(() => {
    loadDashboardData();
  }, []);

  async function loadDashboardData() {
    try {
      logger.info('Loading dashboard data');
      setIsLoading(true);
      setError(null);

      // Fetch all data in parallel with error handling for each request
      const [statistics, activity, notifs] = await Promise.all([
        fetchPatientStatistics().catch(err => {
          logger.error('Failed to fetch patient statistics', err);
          throw new Error(`Failed to load statistics: ${err.message}`);
        }),
        fetchRecentActivity(5).catch(err => {
          logger.error('Failed to fetch recent activity', err);
          throw new Error(`Failed to load activity: ${err.message}`);
        }),
        fetchNotifications(3).catch(err => {
          logger.error('Failed to fetch notifications', err);
          throw new Error(`Failed to load notifications: ${err.message}`);
        })
      ]);

      logger.debug('Dashboard data loaded', { 
        statsLoaded: Object.keys(statistics).length > 0,
        activityCount: activity.length,
        notificationsCount: notifs.length
      });
      
      setStats(statistics);
      setRecentActivity(activity);
      setNotifications(notifs);
      setLastRefreshed(new Date());
      setIsLoading(false);
    } catch (err) {
      const error = err as Error;
      logger.error('Failed to load dashboard data', error);
      setError(error);
      setIsLoading(false);
    }
  }

  const handleRefresh = () => {
    logger.info('User manually refreshing dashboard data');
    loadDashboardData();
  };

  const handleNavigation = (path: string) => {
    logger.info('User navigating', { from: 'dashboard', to: path });
    router.push(path);
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 5 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Link 
            href="/"
            style={{
              display: 'flex',
              alignItems: 'center',
              color: 'inherit',
              textDecoration: 'none',
              marginRight: '8px'
            }}
          >
            <HomeIcon sx={{ fontSize: 18, mr: 0.5 }} />
            Home
          </Link>
          <Box sx={{ mx: 1, color: 'text.secondary' }}>/</Box>
          <Typography color="text.primary">Dashboard</Typography>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 3, mb: 2 }}>
          <Typography variant="h4" component="h1">
            Dashboard
          </Typography>
          <Button 
            startIcon={<RefreshIcon />} 
            onClick={handleRefresh}
            disabled={isLoading}
            variant="outlined"
            size="small"
          >
            Refresh
          </Button>
        </Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Typography variant="body1" color="text.secondary">
            Welcome back! Here's an overview of your medical practice.
          </Typography>
          {!isLoading && (
            <Typography variant="caption" color="text.secondary">
              Last updated: {lastRefreshed.toLocaleTimeString()}
            </Typography>
          )}
        </Box>
      </Box>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        {isLoading ? (
          <>
            <Grid item xs={12} md={4}>
              <StatCardSkeleton />
            </Grid>
            <Grid item xs={12} md={4}>
              <StatCardSkeleton />
            </Grid>
            <Grid item xs={12} md={4}>
              <StatCardSkeleton />
            </Grid>
          </>
        ) : (
          <>
            <Grid item xs={12} md={4}>
              <StatCard
                title="Active Patients"
                value={stats.activePatients}
                icon={<PersonIcon />}
                color="primary"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <StatCard
                title="Pending Appointments"
                value={stats.pendingAppointments}
                icon={<CalendarIcon />}
                color="warning"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <StatCard
                title="Critical Alerts"
                value={stats.criticalPatients}
                icon={<NotificationsIcon />}
                color="error"
              />
            </Grid>
          </>
        )}
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          {isLoading ? (
            <ActivityCardSkeleton />
          ) : (
            <ActivityCard title="Recent Activity" items={recentActivity} />
          )}
        </Grid>
        <Grid item xs={12} md={4}>
          <Stack spacing={3}>
            {isLoading ? (
              <>
                <NotificationsCardSkeleton />
                <Paper
                  elevation={0}
                  sx={{
                    p: 3,
                    height: '100%',
                    bgcolor: 'background.paper',
                    borderRadius: 2,
                    border: '1px solid',
                    borderColor: 'divider',
                  }}
                >
                  <Box sx={{ bgcolor: 'action.hover', height: 24, width: '40%', borderRadius: 1, mb: 3 }} />
                  <Stack spacing={2}>
                    {[1, 2].map((index) => (
                      <Box key={index} sx={{ bgcolor: 'action.hover', height: 40, width: '100%', borderRadius: 1 }} />
                    ))}
                  </Stack>
                </Paper>
              </>
            ) : (
              <>
                <NotificationsCard notifications={notifications} />
                <QuickActions />
              </>
            )}
          </Stack>
        </Grid>
      </Grid>

      {error && (
        <Alert 
          severity="error" 
          sx={{ mt: 3 }}
          action={
            <Button 
              color="inherit" 
              size="small" 
              onClick={handleRefresh}
              startIcon={<RefreshIcon />}
            >
              Retry
            </Button>
          }
        >
          <AlertTitle>Error Loading Data</AlertTitle>
          {error.message || 'There was an error loading dashboard data. The page may show partial information.'}
          <Typography variant="caption" component="div" sx={{ mt: 1 }}>
            Some data might be shown from local cache or fallback values.
          </Typography>
        </Alert>
      )}
    </Container>
  );
} 