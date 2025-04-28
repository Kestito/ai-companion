'use client';

import { useEffect, useState } from 'react';
import { 
  Typography, 
  Box, 
  Paper, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Button, 
  Chip, 
  CircularProgress, 
  Alert, 
  Container,
  Link as MuiLink,
  Grid
} from '@mui/material';
import Link from 'next/link';
import ScheduleIcon from '@mui/icons-material/Schedule';
import InfoIcon from '@mui/icons-material/Info';
import CodeIcon from '@mui/icons-material/Code';
import HomeIcon from '@mui/icons-material/Home';
import SendIcon from '@mui/icons-material/Send';
import { FORCE_REAL_DATA } from '@/lib/config';

interface ScheduledMessage {
  id: string;
  patient_id?: string;
  recipient_id: string;
  platform: string;
  message_content: string;
  scheduled_time: string;
  template_key?: string;
  parameters?: any;
  recurrence_pattern?: any;
  status: string;
  error_message?: string;
  sent_at?: string;
  failed_at?: string;
  created_at: string;
  updated_at?: string;
  attempts?: number;
  priority?: number;
}

export default function ScheduledMessagesPage() {
  const [messages, setMessages] = useState<ScheduledMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sendingMessage, setSendingMessage] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    const fetchScheduledMessages = async () => {
      try {
        setLoading(true);
        
        // Use the API endpoint
        console.log('Fetching scheduled messages from API endpoint');
        const response = await fetch('/api/scheduled-messages');
        
        if (!response.ok) {
          throw new Error(`Failed to fetch scheduled messages: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Scheduled messages data from API:', data);
        
        if (data.error) {
          throw new Error(data.error);
        }
        
        setMessages(data.messages || []);
        
        // If we got an empty array in production where we're forcing real data
        // and this might be an error, show a more specific error message
        if (FORCE_REAL_DATA && data.messages && data.messages.length === 0) {
          console.warn('No scheduled messages found but real data is required');
          // Don't set error to allow the UI to show the empty state
        }
      } catch (err: any) {
        console.error('Error fetching scheduled messages:', err);
        setError(err.message);
        
        // In production with forced real data, don't retry more than 3 times
        if (FORCE_REAL_DATA && retryCount < 3) {
          setRetryCount(prev => prev + 1);
          setTimeout(() => {
            fetchScheduledMessages();
          }, 3000); // Retry after 3 seconds
        }
      } finally {
        setLoading(false);
      }
    };

    fetchScheduledMessages();
  }, [retryCount]);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'sent':
        return 'success';
      case 'pending':
        return 'warning';
      case 'failed':
        return 'error';
      case 'cancelled':
        return 'default';
      default:
        return 'default';
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString();
    } catch (e) {
      return 'Invalid date';
    }
  };

  const handleSendNow = async (messageId: string) => {
    if (sendingMessage === messageId) return; // Prevent double-clicks
    
    try {
      setSendingMessage(messageId);
      
      const response = await fetch('/api/scheduled-messages/send-now', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ messageId }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Error: ${response.status}`);
      }
      
      const result = await response.json();
      
      // Update the local state to reflect the message as sent
      setMessages(prevMessages => 
        prevMessages.map(msg => 
          msg.id === messageId 
            ? { ...msg, status: 'sent' } 
            : msg
        )
      );
      
      console.log('Message sent successfully:', result);
    } catch (err: any) {
      console.error('Failed to send message:', err);
      alert(`Failed to send message: ${err.message}`);
    } finally {
      setSendingMessage(null);
    }
  };

  if (loading) {
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
            <Typography color="text.primary">Scheduled Messages</Typography>
          </Box>
          
          <Typography variant="h4" component="h1" sx={{ mt: 3, mb: 2 }}>
            Scheduled Messages
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
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
            <Typography color="text.primary">Scheduled Messages</Typography>
          </Box>
          
          <Typography variant="h4" component="h1" sx={{ mt: 3, mb: 2 }}>
            Scheduled Messages
          </Typography>
        </Box>
        
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="subtitle1" fontWeight="bold">Error loading scheduled messages</Typography>
          <Typography variant="body2">{error}</Typography>
          
          {FORCE_REAL_DATA ? (
            <Typography variant="body2" sx={{ mt: 2, fontWeight: 'bold' }}>
              This application is configured to require real data. Mock data is disabled.
            </Typography>
          ) : (
            <Typography variant="body2" sx={{ mt: 2 }}>Make sure the scheduled_messages table exists in your Supabase database and the API endpoint is working.</Typography>
          )}
          
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2">Troubleshooting steps:</Typography>
            <Box component="ul" sx={{ pl: 2, mt: 1 }}>
              <Box component="li" sx={{ mb: 0.5 }}>Verify that the 'scheduled_messages' table exists in the 'public' schema</Box>
              <Box component="li" sx={{ mb: 0.5 }}>Ensure your Supabase client has permissions to access this table</Box>
              <Box component="li" sx={{ mb: 0.5 }}>
                Check that the API routes are properly implemented for scheduled messages
              </Box>
              <Box component="li">
                Visit <MuiLink component={Link} href="/test-schema">Schema Test Page</MuiLink> to diagnose schema access methods
              </Box>
            </Box>
          </Box>
          
          {retryCount > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2">
                Retry attempt {retryCount}/3 failed. Please check your database configuration.
              </Typography>
            </Box>
          )}
          
          {FORCE_REAL_DATA && retryCount >= 3 && (
            <Button 
              variant="outlined" 
              color="primary"
              onClick={() => setRetryCount(0)}
              sx={{ mt: 2 }}
            >
              Try Again
            </Button>
          )}
        </Alert>
      </Container>
    );
  }

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
          <Typography color="text.primary">Scheduled Messages</Typography>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 3 }}>
          <Typography variant="h4" component="h1" sx={{ mb: 2 }}>
            Scheduled Messages
          </Typography>
          
          <Button 
            variant="contained" 
            color="primary" 
            startIcon={<ScheduleIcon />}
            component={Link}
            href="/scheduled-messages/create"
            sx={{ borderRadius: '20px' }}
          >
            Schedule New Message
          </Button>
        </Box>
        <Typography variant="body1" color="text.secondary" paragraph sx={{ mb: 4 }}>
          Manage scheduled messages across different platforms.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          {messages.length === 0 ? (
            <Paper sx={{ textAlign: 'center', py: 5, px: 2 }}>
              <Typography color="text.secondary" sx={{ mb: 2 }}>
                No scheduled messages found in the database.
              </Typography>
              <Typography variant="body2">
                Use the "Schedule New Message" button to create your first scheduled message.
              </Typography>
            </Paper>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>Recipient</TableCell>
                    <TableCell>Platform</TableCell>
                    <TableCell>Message</TableCell>
                    <TableCell>Scheduled For</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Created At</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {messages.map((message) => (
                    <TableRow key={message.id} hover>
                      <TableCell>
                        {message.id && message.id.substring(0, 8)}...
                      </TableCell>
                      <TableCell>
                        {message.patient_id || 'N/A'}
                      </TableCell>
                      <TableCell>
                        {message.platform || 'N/A'}
                      </TableCell>
                      <TableCell>
                        {message.message_content ? 
                          (message.message_content.length > 50 
                            ? `${message.message_content.substring(0, 50)}...` 
                            : message.message_content) 
                          : 'N/A'}
                      </TableCell>
                      <TableCell>
                        {formatDate(message.scheduled_time)}
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={message.status || 'Unknown'} 
                          color={getStatusColor(message.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {formatDate(message.created_at)}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="text"
                          color="primary"
                          startIcon={<SendIcon />}
                          onClick={() => handleSendNow(message.id)}
                          disabled={message.status === 'sent' || sendingMessage === message.id}
                          size="small"
                        >
                          {sendingMessage === message.id ? 'Sending...' : 'Send Now'}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Grid>
      </Grid>
    </Container>
  );
} 