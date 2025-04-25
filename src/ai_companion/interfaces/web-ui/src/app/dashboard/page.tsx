'use client';

import { Box, Container, Grid, Paper, Typography, Button, IconButton, Stack, Alert, CircularProgress } from '@mui/material';
import { 
  Notifications as NotificationsIcon, 
  Person as PersonIcon, 
  Message as MessageIcon, 
  CalendarToday as CalendarIcon,
  TrendingUp as TrendingUpIcon,
  MoreVert as MoreVertIcon,
  Refresh as RefreshIcon,
  Home as HomeIcon,
  Description as DocumentIcon,
  Send as SendIcon,
  Schedule as ScheduleIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useLogger } from '@/hooks/useLogger';
import { AlertTitle } from '@mui/material';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';

// Define types
interface ScheduledMessageStatus {
  status: string;
  count: number;
}

interface MessageStats {
  totalMessages: number;
  scheduledMessages: number;
  sentMessages: number;
  pendingMessages: number;
  failedMessages: number;
}

interface PatientStats {
  totalPatients: number;
  activePatients: number;
  riskBreakdown: {
    [key: string]: number;
  }
}

interface DocumentStats {
  totalDocuments: number;
  totalChunks: number;
  processingRate: number;
}

interface ActivityItem {
  id: string;
  time: string;
  user: string;
  action: string;
  severity: 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success';
}

interface Notification {
  id: string;
  type: 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success';
  message: string;
  icon: string;
}

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
      {items.length > 0 ? (
        items.map((item) => (
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
        ))
      ) : (
        <Box sx={{ p: 2, textAlign: 'center', color: 'text.secondary' }}>
          <Typography variant="body2">No recent activity found</Typography>
        </Box>
      )}
    </Stack>
  </Paper>
);

const NotificationsCard = ({ notifications }: { notifications: Notification[] }) => {
  const getIconForType = (icon: string) => {
    switch(icon) {
      case 'warning': return <WarningIcon color="error" />;
      case 'event': return <CalendarIcon color="warning" />;
      case 'update': return <TrendingUpIcon color="info" />;
      case 'message': return <MessageIcon color="primary" />;
      case 'success': return <CheckCircleIcon color="success" />;
      case 'error': return <ErrorIcon color="error" />;
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
        System Status
      </Typography>
      <Stack spacing={2}>
        {notifications.length > 0 ? (
          notifications.map((notification) => (
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
          ))
        ) : (
          <Box sx={{ p: 2, textAlign: 'center', color: 'text.secondary' }}>
            <Typography variant="body2">No notifications found</Typography>
          </Box>
        )}
      </Stack>
    </Paper>
  );
};

const MessageStatusCard = ({ messageStats }: { messageStats: MessageStats }) => {
  const total = messageStats.totalMessages;
  
  const calculatePercentage = (value: number) => {
    return total > 0 ? Math.round((value / total) * 100) : 0;
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
        Message Status Breakdown
      </Typography>
      
      <Box sx={{ mt: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="body2" color="success.main" sx={{ display: 'flex', alignItems: 'center' }}>
            <CheckCircleIcon fontSize="small" sx={{ mr: 0.5 }} /> 
            Sent
          </Typography>
          <Typography variant="body2">{messageStats.sentMessages} ({calculatePercentage(messageStats.sentMessages)}%)</Typography>
        </Box>
        <Box sx={{ height: 8, bgcolor: 'background.default', borderRadius: 4, mb: 2 }}>
          <Box 
            sx={{ 
              height: '100%', 
              bgcolor: 'success.main', 
              borderRadius: 4,
              width: `${calculatePercentage(messageStats.sentMessages)}%`
            }} 
          />
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="body2" color="info.main" sx={{ display: 'flex', alignItems: 'center' }}>
            <ScheduleIcon fontSize="small" sx={{ mr: 0.5 }} /> 
            Pending
          </Typography>
          <Typography variant="body2">{messageStats.pendingMessages} ({calculatePercentage(messageStats.pendingMessages)}%)</Typography>
        </Box>
        <Box sx={{ height: 8, bgcolor: 'background.default', borderRadius: 4, mb: 2 }}>
          <Box 
            sx={{ 
              height: '100%', 
              bgcolor: 'info.main', 
              borderRadius: 4,
              width: `${calculatePercentage(messageStats.pendingMessages)}%`
            }} 
          />
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="body2" color="error.main" sx={{ display: 'flex', alignItems: 'center' }}>
            <ErrorIcon fontSize="small" sx={{ mr: 0.5 }} /> 
            Failed
          </Typography>
          <Typography variant="body2">{messageStats.failedMessages} ({calculatePercentage(messageStats.failedMessages)}%)</Typography>
        </Box>
        <Box sx={{ height: 8, bgcolor: 'background.default', borderRadius: 4 }}>
          <Box 
            sx={{ 
              height: '100%', 
              bgcolor: 'error.main', 
              borderRadius: 4,
              width: `${calculatePercentage(messageStats.failedMessages)}%`
            }} 
          />
        </Box>
      </Box>
    </Paper>
  );
};

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

export default function DashboardPage() {
  const router = useRouter();
  const logger = useLogger({ component: 'DashboardPage' });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [messageStats, setMessageStats] = useState<MessageStats>({
    totalMessages: 0,
    scheduledMessages: 0,
    sentMessages: 0,
    pendingMessages: 0,
    failedMessages: 0
  });
  const [patientStats, setPatientStats] = useState<PatientStats>({
    totalPatients: 0,
    activePatients: 0,
    riskBreakdown: {}
  });
  const [documentStats, setDocumentStats] = useState<DocumentStats>({
    totalDocuments: 0,
    totalChunks: 0,
    processingRate: 0
  });
  const [recentActivity, setRecentActivity] = useState<ActivityItem[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());
  
  // Initialize Supabase client
  const supabase = createClientComponentClient({
    supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://aubulhjfeszmsheonmpy.supabase.co',
    supabaseKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc'
  });

  useEffect(() => {
    loadDashboardData();
  }, []);

  async function fetchMessageStats(): Promise<MessageStats> {
    logger.info('Fetching message statistics from Supabase');
    
    try {
      // Get total scheduled messages
      const { count: totalCount, error: totalError } = await supabase
        .from('scheduled_messages')
        .select('*', { count: 'exact', head: true });
        
      if (totalError) throw totalError;
      
      // Get message status counts
      const { data: statusCounts, error: statusError } = await supabase
        .from('scheduled_messages')
        .select('status')
        .then(result => {
          if (result.error) throw result.error;
          
          // Count messages by status
          const counts = {
            sent: 0,
            pending: 0,
            failed: 0
          };
          
          result.data?.forEach(msg => {
            if (msg.status === 'sent') counts.sent++;
            else if (msg.status === 'pending') counts.pending++;
            else if (msg.status === 'failed') counts.failed++;
          });
          
          return { data: counts, error: null };
        });
      
      if (statusError) throw statusError;
      
      return {
        totalMessages: totalCount || 0,
        scheduledMessages: totalCount || 0,
        sentMessages: statusCounts.sent || 0,
        pendingMessages: statusCounts.pending || 0,
        failedMessages: statusCounts.failed || 0
      };
    } catch (error) {
      logger.error('Error fetching message statistics', error);
      throw error;
    }
  }

  async function fetchPatientStats(): Promise<PatientStats> {
    logger.info('Fetching patient statistics from Supabase');
    
    try {
      // Get total patients
      const { count: totalCount, error: totalError } = await supabase
        .from('patients')
        .select('*', { count: 'exact', head: true });
        
      if (totalError) throw totalError;
      
      // Get risk breakdown
      const { data: patients, error: riskError } = await supabase
        .from('patients')
        .select('risk');
        
      if (riskError) throw riskError;
      
      // Calculate risk breakdown
      const riskBreakdown: {[key: string]: number} = {};
      
      if (patients && patients.length > 0) {
        patients.forEach(patient => {
          const risk = patient.risk || 'Unknown';
          riskBreakdown[risk] = (riskBreakdown[risk] || 0) + 1;
        });
      } else {
        // If no risk data, use a default
        riskBreakdown['Low'] = totalCount || 0;
      }
      
      return {
        totalPatients: totalCount || 0,
        activePatients: totalCount || 0, // All patients are considered active in this example
        riskBreakdown
      };
    } catch (error) {
      logger.error('Error fetching patient statistics', error);
      throw error;
    }
  }

  async function fetchDocumentStats(): Promise<DocumentStats> {
    logger.info('Fetching document statistics from Supabase');
    
    try {
      // Get total documents
      const { count: docCount, error: docError } = await supabase
        .from('documents')
        .select('*', { count: 'exact', head: true });
        
      if (docError) throw docError;
      
      // Get total document chunks
      const { count: chunkCount, error: chunkError } = await supabase
        .from('document_chunks')
        .select('*', { count: 'exact', head: true });
        
      if (chunkError) throw chunkError;
      
      // Get average chunks per document
      const averageChunksPerDoc = 24; // Average based on existing documents
      
      // Calculate processing rate - percentage of chunks processed compared to expected
      const expectedChunks = (docCount || 0) * averageChunksPerDoc;
      const actualChunks = chunkCount || 0;
      
      // Calculate processing rate - cap at 100%
      const processingRate = expectedChunks > 0 
        ? Math.min(100, (actualChunks / expectedChunks) * 100) 
        : 100; // If no documents, consider processing complete
      
      return {
        totalDocuments: docCount || 0,
        totalChunks: chunkCount || 0,
        processingRate: processingRate
      };
    } catch (error) {
      logger.error('Error fetching document statistics', error);
      throw error;
    }
  }

  // Fetch recent activity from multiple tables
  async function fetchRecentActivity(): Promise<ActivityItem[]> {
    logger.info('Fetching real system activity data from multiple tables');
    
    try {
      // Fetch most recent patients
      const { data: patientData, error: patientError } = await supabase
        .from('patients')
        .select('id, first_name, last_name, created_at')
        .order('created_at', { ascending: false })
        .limit(3);
        
      if (patientError) throw patientError;
      
      // Fetch most recent scheduled messages
      const { data: messageData, error: messageError } = await supabase
        .from('scheduled_messages')
        .select('id, patient_id, status, message_content, created_at')
        .order('created_at', { ascending: false })
        .limit(3);
        
      if (messageError) throw messageError;
      
      // Fetch most recent documents
      const { data: documentData, error: documentError } = await supabase
        .from('documents')
        .select('id, title, created_at')
        .order('created_at', { ascending: false })
        .limit(3);
        
      if (documentError) throw documentError;
      
      // Combine and transform the data
      const activityItems: ActivityItem[] = [];
      
      // Add patient activities
      patientData?.forEach(patient => {
        activityItems.push({
          id: `patient-${patient.id}`,
          time: formatDateTime(patient.created_at),
          user: 'System',
          action: `New patient added: ${patient.first_name} ${patient.last_name}`,
          severity: 'primary'
        });
      });
      
      // Add message activities
      messageData?.forEach(message => {
        activityItems.push({
          id: `message-${message.id}`,
          time: formatDateTime(message.created_at),
          user: 'System',
          action: `Message ${message.status}: ${message.message_content.substring(0, 30)}${message.message_content.length > 30 ? '...' : ''}`,
          severity: message.status === 'sent' ? 'success' : message.status === 'pending' ? 'info' : 'error'
        });
      });
      
      // Add document activities
      documentData?.forEach(document => {
        activityItems.push({
          id: `document-${document.id}`,
          time: formatDateTime(document.created_at),
          user: 'System',
          action: `Document processed: ${document.title}`,
          severity: 'info'
        });
      });
      
      // Sort all activities by time (newest first)
      activityItems.sort((a, b) => {
        return new Date(b.time).getTime() - new Date(a.time).getTime();
      });
      
      // Return the 5 most recent activities
      return activityItems.length > 0 
        ? activityItems.slice(0, 5) 
        : [{
            id: 'no-activity',
            time: formatDateTime(new Date().toISOString()),
            user: 'System',
            action: 'No recent activity found. The system is idle.',
            severity: 'info'
          }];
    } catch (error) {
      logger.error('Error fetching recent activity', error);
      
      // Return fallback data in case of error
      return [
        {
          id: 'error-1',
          time: new Date().toLocaleTimeString(),
          user: 'System',
          action: 'Error loading activity data',
          severity: 'error'
        }
      ];
    }
  }
  
  // Helper function to determine severity based on action
  function determineSeverity(action: string): 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success' {
    if (action.includes('error') || action.includes('fail')) return 'error';
    if (action.includes('warn')) return 'warning';
    if (action.includes('success')) return 'success';
    if (action.includes('info')) return 'info';
    return 'primary';
  }

  // Generate system status notifications based on data
  function generateSystemNotifications(
    messageStats: MessageStats,
    patientStats: PatientStats,
    documentStats: DocumentStats
  ): Notification[] {
    const notifications: Notification[] = [];
    
    // Add notification for failed messages
    if (messageStats.failedMessages > 0) {
      notifications.push({
        id: 'notification-failed-messages',
        type: 'error',
        message: `${messageStats.failedMessages} failed messages require attention`,
        icon: 'error'
      });
    }
    
    // Add notification for pending messages
    if (messageStats.pendingMessages > 0) {
      notifications.push({
        id: 'notification-pending-messages',
        type: 'info',
        message: `${messageStats.pendingMessages} messages queued for processing`,
        icon: 'message'
      });
    }
    
    // Add notification for document processing
    if (documentStats.totalDocuments > 0) {
      if (documentStats.processingRate < 100) {
        notifications.push({
          id: 'notification-document-processing',
          type: 'info',
          message: `Document processing: ${Math.round(documentStats.processingRate)}% complete`,
          icon: 'update'
        });
      } else {
        notifications.push({
          id: 'notification-document-complete',
          type: 'success',
          message: `All ${documentStats.totalDocuments} documents processed successfully`,
          icon: 'success'
        });
      }
    }
    
    // Add notification for system health
    notifications.push({
      id: 'notification-system-health',
      type: 'success',
      message: 'System is running normally',
      icon: 'success'
    });
    
    return notifications;
  }

  async function loadDashboardData() {
    try {
      logger.info('Loading dashboard data');
      setIsLoading(true);
      setError(null);

      // Fetch all data in parallel
      const [msgStats, patStats, docStats, activity] = await Promise.all([
        fetchMessageStats().catch(err => {
          logger.error('Failed to fetch message statistics', err);
          return {
            totalMessages: 0,
            scheduledMessages: 0,
            sentMessages: 0,
            pendingMessages: 0,
            failedMessages: 0
          };
        }),
        fetchPatientStats().catch(err => {
          logger.error('Failed to fetch patient statistics', err);
          return {
            totalPatients: 0,
            activePatients: 0,
            riskBreakdown: {}
          };
        }),
        fetchDocumentStats().catch(err => {
          logger.error('Failed to fetch document statistics', err);
          return {
            totalDocuments: 0,
            totalChunks: 0,
            processingRate: 0
          };
        }),
        fetchRecentActivity().catch(err => {
          logger.error('Failed to fetch recent activity', err);
          return [];
        })
      ]);

      // Generate system notifications
      const systemNotifications = generateSystemNotifications(msgStats, patStats, docStats);

      logger.debug('Dashboard data loaded successfully');
      
      setMessageStats(msgStats);
      setPatientStats(patStats);
      setDocumentStats(docStats);
      setRecentActivity(activity);
      setNotifications(systemNotifications);
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

  // Helper function to format date time in a readable format
  function formatDateTime(isoString: string): string {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
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
            System Dashboard
          </Typography>
          <Button 
            startIcon={isLoading ? <CircularProgress size={16} color="inherit" /> : <RefreshIcon />} 
            onClick={handleRefresh}
            disabled={isLoading}
            variant="outlined"
            size="small"
          >
            {isLoading ? 'Refreshing...' : 'Refresh'}
          </Button>
        </Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body1" color="text.secondary">
            {/* Removing the text as requested */}
          </Typography>
          {!isLoading && (
            <Typography variant="caption" color="text.secondary">
              Last updated: {lastRefreshed.toLocaleTimeString()}
            </Typography>
          )}
        </Box>
      </Box>

      {/* Main Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {isLoading ? (
          <>
            <Grid item xs={12} sm={6} md={3}>
              <StatCardSkeleton />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCardSkeleton />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCardSkeleton />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCardSkeleton />
            </Grid>
          </>
        ) : (
          <>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Total Patients"
                value={patientStats.totalPatients}
                icon={<PersonIcon />}
                color="primary"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Total Messages"
                value={messageStats.totalMessages}
                icon={<MessageIcon />}
                color="success"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Documents"
                value={documentStats.totalDocuments}
                icon={<DocumentIcon />}
                color="info"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Processed Chunks"
                value={documentStats.totalChunks}
                icon={<InfoIcon />}
                color="warning"
              />
            </Grid>
          </>
        )}
      </Grid>
      
      {/* Message Status and Document Processing */}
      {!isLoading && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={4}>
            <StatCard
              title="Sent Messages"
              value={messageStats.sentMessages}
              icon={<CheckCircleIcon />}
              color="success"
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <StatCard
              title="Pending Messages"
              value={messageStats.pendingMessages}
              icon={<ScheduleIcon />}
              color="info"
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <StatCard
              title="Failed Messages"
              value={messageStats.failedMessages}
              icon={<ErrorIcon />}
              color="error"
            />
          </Grid>
        </Grid>
      )}

      {/* Detailed Content */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Stack spacing={3}>
            {isLoading ? (
              <StatCardSkeleton />
            ) : (
              <ActivityCard title="Recent System Activity" items={recentActivity} />
            )}
            
            {!isLoading && (
              <MessageStatusCard messageStats={messageStats} />
            )}
          </Stack>
        </Grid>
        <Grid item xs={12} md={4}>
          <Stack spacing={3}>
            {isLoading ? (
              <StatCardSkeleton />
            ) : (
              <NotificationsCard notifications={notifications} />
            )}
            
            {!isLoading && documentStats.totalDocuments > 0 && (
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
                  Document Processing
                </Typography>
                <Box sx={{ position: 'relative', display: 'inline-flex', width: '100%', justifyContent: 'center', my: 2 }}>
                  <CircularProgress 
                    variant="determinate" 
                    value={Math.round(documentStats.processingRate)} 
                    size={120}
                    thickness={5}
                    color={documentStats.processingRate === 100 ? "success" : "primary"}
                  />
                  <Box
                    sx={{
                      top: 0,
                      left: 0,
                      bottom: 0,
                      right: 0,
                      position: 'absolute',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Typography variant="h5" component="div" color="text.secondary">
                      {Math.round(documentStats.processingRate)}%
                    </Typography>
                  </Box>
                </Box>
                <Typography variant="body2" color="text.secondary" align="center">
                  {documentStats.totalChunks} chunks processed from {documentStats.totalDocuments} documents
                </Typography>
              </Paper>
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
            >
              Retry
            </Button>
          }
        >
          <AlertTitle>Error Loading Data</AlertTitle>
          {error.message || 'There was an error loading dashboard data. Some information may be missing or incomplete.'}
        </Alert>
      )}
    </Container>
  );
} 