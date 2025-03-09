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
  Home as HomeIcon
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { fetchPatientStatistics } from '@/lib/supabase/patientService';

// Mock data - Will be replaced by Supabase data
const mockData = {
  stats: {
    activeUsers: 148,
    newToday: 27,
    responseRate: 92,
    pendingAppointments: 12,
    criticalAlerts: 3,
  },
  recentActivity: [
    { time: '09:45', user: 'Dr. J. Smith', action: 'Updated patient medication', severity: 'info' },
    { time: '09:32', user: 'Dr. A. Jonaitis', action: 'Completed consultation', severity: 'success' },
    { time: '09:17', user: 'Dr. L. Petrauskas', action: 'Flagged critical condition', severity: 'error' },
    { time: '08:54', user: 'Nurse Wilson', action: 'Recorded vital signs', severity: 'info' },
    { time: '08:30', user: 'System', action: 'Daily health reports generated', severity: 'info' },
  ],
  notifications: [
    { type: 'error', message: '3 patients require immediate attention', icon: 'warning' },
    { type: 'warning', message: '5 upcoming appointments in next hour', icon: 'event' },
    { type: 'info', message: 'New treatment protocol available', icon: 'update' },
  ]
};

const StatCard = ({ title, value, subtitle, icon, color = 'primary' }: { 
  title: string; 
  value: number | string; 
  subtitle?: string;
  icon?: React.ReactNode;
  color?: 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success';
}) => (
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

const ActivityCard = ({ title, items }: { title: string; items: any[] }) => (
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
      {items.map((item, index) => (
        <Box 
          key={index} 
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

const NotificationsCard = ({ notifications }: { notifications: any[] }) => (
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
      {notifications.map((notification, index) => (
        <Box 
          key={index} 
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
          {notification.icon === 'warning' && <Notifications />}
          {notification.icon === 'event' && <CalendarMonth />}
          {notification.icon === 'update' && <TrendingUp />}
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

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState(mockData.stats);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch dashboard statistics from Supabase
  useEffect(() => {
    async function loadDashboardData() {
      try {
        setLoading(true);
        const patientStats = await fetchPatientStatistics();
        
        if (patientStats) {
          setStats({
            ...mockData.stats, // Keep other stats for now
            activeUsers: patientStats.activeUsers,
            pendingAppointments: patientStats.pendingAppointments,
            criticalAlerts: patientStats.criticalAlerts,
          });
        }
      } catch (err) {
        console.error('Error loading dashboard data:', err);
        setError('Failed to load dashboard data');
        // Keep using mock data as fallback
      } finally {
        setLoading(false);
      }
    }

    loadDashboardData();
  }, []);

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 4, mt: 6 }}>
        {/* Page header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, pt: 3 }}>
          <Box>
            <Breadcrumbs aria-label="breadcrumb" sx={{ mb: 1 }}>
              <Link underline="hover" color="inherit" href="/" sx={{ display: 'flex', alignItems: 'center' }}>
                <HomeIcon sx={{ mr: 0.5 }} fontSize="inherit" />
                Home
              </Link>
              <Typography color="text.primary" sx={{ display: 'flex', alignItems: 'center' }}>
                <Assessment sx={{ mr: 0.5 }} fontSize="inherit" />
                Dashboard
              </Typography>
            </Breadcrumbs>
            <Typography variant="h4" component="h1" gutterBottom fontWeight="500">
              Dashboard
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Welcome back! Here's an overview of your medical practice.
            </Typography>
          </Box>
        </Box>

        <Divider sx={{ mb: 4 }} />

        {loading ? (
          <Box sx={{ width: '100%', mt: 4 }}>
            <LinearProgress />
            <Typography sx={{ mt: 2, textAlign: 'center' }}>Loading dashboard data...</Typography>
          </Box>
        ) : error ? (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        ) : (
          <Grid container spacing={3}>
            {/* Stats Section */}
            <Grid item xs={12} md={4}>
              <StatCard 
                title="Active Patients"
                value={stats.activeUsers}
                icon={<Person sx={{ fontSize: 24 }} />}
                color="primary"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <StatCard 
                title="Pending Appointments"
                value={stats.pendingAppointments}
                icon={<CalendarMonth sx={{ fontSize: 24 }} />}
                color="warning"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <StatCard 
                title="Critical Alerts"
                value={stats.criticalAlerts}
                icon={<Notifications sx={{ fontSize: 24 }} />}
                color="error"
              />
            </Grid>

            {/* Activity Section */}
            <Grid item xs={12} md={8}>
              <ActivityCard 
                title="Recent Activity"
                items={mockData.recentActivity}
              />
            </Grid>

            {/* Notifications Section */}
            <Grid item xs={12} md={4}>
              <Stack spacing={3}>
                <NotificationsCard notifications={mockData.notifications} />
                <QuickActions />
              </Stack>
            </Grid>
          </Grid>
        )}
      </Box>
    </Container>
  );
} 