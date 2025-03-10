'use client';

import { Box, Container, Grid, Paper, Typography, Button, IconButton, Stack, LinearProgress, Breadcrumbs, Link, Divider, Alert } from '@mui/material';
import { 
  Notifications, 
  Person, 
  Message, 
  Assessment,
  CalendarMonth,
  TrendingUp,
  MoreVert,
  Add,
  Home as HomeIcon,
  Check as CheckIcon,
  Warning as WarningIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { fetchPatientStatistics } from '@/lib/supabase/patientService';
import { fetchRecentActivity, ActivityItem } from '@/lib/supabase/activityService';
import { fetchNotifications, Notification } from '@/lib/supabase/notificationService';
import { useLogger } from '@/hooks/useLogger';

// Default stats for initial render
const defaultStats = {
  totalPatients: 0,
  activePatients: 0,
  newPatients: 0,
  criticalPatients: 0,
  pendingAppointments: 0,
  responseRate: 0
};

const StatCard = ({ title, value, subtitle, icon, color = 'primary' }: { 
  title: string; 
  value: number | string; 
  subtitle?: string;
  icon?: React.ReactNode;
  color?: 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success';
}) => {
  const logger = useLogger({ component: 'StatCard' });
  
  useEffect(() => {
    logger.debug('StatCard rendered', { title, value, color });
  }, []);

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
          {subtitle && (
            <Typography variant="body2" color="text.secondary">
              {subtitle}
            </Typography>
          )}
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
        <MoreVert />
      </IconButton>
    </Box>
    <Stack spacing={2}>
      {items.map((item) => (
        <Box 
          key={item.id} 
          sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 2,
            p: 1.5,
            borderRadius: 1,
            bgcolor: 'background.default',
            '&:hover': {
              bgcolor: 'action.hover',
            }
          }}
        >
          <Box 
            sx={{ 
              width: 8, 
              height: 8, 
              borderRadius: '50%', 
              bgcolor: `${item.severity}.main`,
              flexShrink: 0
            }} 
          />
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
              {item.time}
            </Typography>
            <Typography variant="body1">
              <strong>{item.user}</strong> • {item.action}
            </Typography>
          </Box>
        </Box>
      ))}
    </Stack>
  </Paper>
);

const NotificationsCard = ({ notifications }: { notifications: Notification[] }) => (
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
          {notification.icon === 'warning' && <WarningIcon />}
          {notification.icon === 'event' && <CalendarMonth />}
          {notification.icon === 'update' && <InfoIcon />}
          {notification.icon === 'check_circle' && <CheckIcon />}
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
        startIcon={<Add />} 
        variant="contained" 
        color="primary"
        fullWidth
      >
        New Patient
      </Button>
      <Button 
        startIcon={<Message />} 
        variant="outlined" 
        color="primary"
        fullWidth
      >
        Send Message
      </Button>
      <Button 
        startIcon={<Assessment />} 
        variant="outlined" 
        color="secondary"
        fullWidth
      >
        Generate Report
      </Button>
    </Stack>
  </Paper>
);

// Add this new component for skeleton loaders
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
        <Box sx={{ bgcolor: 'action.hover', height: 16, width: '60%', borderRadius: 1 }} />
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

  useEffect(() => {
    loadDashboardData();
  }, []);

  async function loadDashboardData() {
    try {
      logger.info('Loading dashboard data');
      setIsLoading(true);

      // Fetch all data in parallel
      const [statistics, activity, notifs] = await Promise.all([
        logger.logMethodExecution('fetchPatientStatistics', async () => {
          return await fetchPatientStatistics();
        }),
        logger.logMethodExecution('fetchRecentActivity', async () => {
          return await fetchRecentActivity(5);
        }),
        logger.logMethodExecution('fetchNotifications', async () => {
          return await fetchNotifications(3);
        })
      ]);

      logger.debug('Dashboard data loaded', { 
        stats: statistics,
        activityCount: activity.length,
        notificationsCount: notifs.length
      });
      
      setStats(statistics);
      setRecentActivity(activity);
      setNotifications(notifs);
      setIsLoading(false);
    } catch (err) {
      const error = err as Error;
      logger.error('Failed to load dashboard data', error);
      setError(error);
      setIsLoading(false);
    }
  }

  // Log navigation events
  const handleNavigation = (path: string) => {
    logger.info('User navigating', { from: 'dashboard', to: path });
    router.push(path);
  };

  if (error) {
    logger.warn('Rendering error state', { error: error.message });
    return (
      <Container>
        <Alert severity="error">
          Failed to load dashboard data. Please try again later.
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {isLoading ? (
        <>
          <Box sx={{ mb: 4 }}>
            <Breadcrumbs aria-label="breadcrumb">
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <HomeIcon sx={{ fontSize: 16 }} />
                <Box sx={{ bgcolor: 'action.hover', height: 16, width: 40, borderRadius: 1 }} />
              </Box>
              <Box sx={{ bgcolor: 'action.hover', height: 16, width: 80, borderRadius: 1 }} />
            </Breadcrumbs>
          </Box>
          
          <Grid container spacing={3}>
            {[1, 2, 3, 4].map((index) => (
              <Grid item key={index} xs={12} md={3}>
                <StatCardSkeleton />
              </Grid>
            ))}
          </Grid>
          
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={12} md={8}>
              <ActivityCardSkeleton />
            </Grid>
            <Grid item xs={12} md={4}>
              <Stack spacing={3}>
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
                    {[1, 2, 3].map((index) => (
                      <Box key={index} sx={{ bgcolor: 'action.hover', height: 36, width: '100%', borderRadius: 1 }} />
                    ))}
                  </Stack>
                </Paper>
              </Stack>
            </Grid>
          </Grid>
        </>
      ) : (
        <>
          <Box sx={{ mb: 4 }}>
            <Breadcrumbs aria-label="breadcrumb">
              <Link
                color="inherit"
                href="/"
                onClick={(e) => {
                  e.preventDefault();
                  handleNavigation('/');
                }}
                sx={{ display: 'flex', alignItems: 'center' }}
              >
                <HomeIcon sx={{ mr: 0.5 }} fontSize="inherit" />
                Home
              </Link>
              <Typography color="text.primary">Dashboard</Typography>
            </Breadcrumbs>
          </Box>

          <Grid container spacing={3}>
            <Grid item xs={12} md={3}>
              <StatCard
                title="Total Patients"
                value={stats.totalPatients}
                subtitle="Registered patients"
                icon={<Person />}
                color="primary"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <StatCard
                title="Active Patients"
                value={stats.activePatients}
                subtitle="Currently active"
                icon={<Person />}
                color="info"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <StatCard
                title="New Patients"
                value={stats.newPatients}
                subtitle="Added in last 24h"
                icon={<Add />}
                color="success"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <StatCard
                title="Critical Patients"
                value={stats.criticalPatients}
                subtitle="Need attention"
                icon={<Notifications />}
                color="error"
              />
            </Grid>
          </Grid>

          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={12} md={8}>
              <ActivityCard title="Recent Activity" items={recentActivity} />
            </Grid>
            <Grid item xs={12} md={4}>
              <Stack spacing={3}>
                <NotificationsCard notifications={notifications} />
                <QuickActions />
              </Stack>
            </Grid>
          </Grid>
        </>
      )}
    </Container>
  );
} 