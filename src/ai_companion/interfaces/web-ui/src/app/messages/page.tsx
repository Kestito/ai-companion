'use client';

import { useState, useEffect } from 'react';
import { getSupabaseClient, getSchemaTable } from '@/lib/supabase/client';
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
  Grid
} from '@mui/material';
import Link from 'next/link';
import AddIcon from '@mui/icons-material/Add';
import InfoIcon from '@mui/icons-material/Info';
import HomeIcon from '@mui/icons-material/Home';
import MessageIcon from '@mui/icons-material/Message';

// Define scheduled message type
type ScheduledMessage = {
  id: string;
  recipient_id: string;
  platform: string;
  message_content: string;
  scheduled_time: string;
  status: string;
  created_at: string;
  recurrence_pattern?: string | null;
};

// Convert to client component for better TypeScript compatibility
export default function MessagesPage() {
  const [messages, setMessages] = useState<ScheduledMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Schema table constant
  const SCHEDULED_MESSAGES_TABLE = getSchemaTable('scheduled_messages');
  
  useEffect(() => {
    async function fetchMessages() {
      try {
        setLoading(true);
        const supabase = getSupabaseClient();
        
        const { data, error } = await supabase
          .from(SCHEDULED_MESSAGES_TABLE)
          .select('*')
          .order('scheduled_time', { ascending: true });
          
        if (error) {
          throw error;
        }
        
        setMessages(data as ScheduledMessage[] || []);
      } catch (err: any) {
        console.error('Error fetching scheduled messages:', err);
        setError(err.message || 'Failed to load scheduled messages');
      } finally {
        setLoading(false);
      }
    }
    
    fetchMessages();
  }, [SCHEDULED_MESSAGES_TABLE]);

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
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
            <Typography color="text.primary">Messages</Typography>
          </Box>
          
          <Typography variant="h4" component="h1" gutterBottom>
            Scheduled Messages
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
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
            <Typography color="text.primary">Messages</Typography>
          </Box>
          
          <Typography variant="h4" component="h1" gutterBottom>
            Scheduled Messages
          </Typography>
        </Box>
        
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="subtitle1" component="div" fontWeight="bold">Error!</Typography>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
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
          <Typography color="text.primary">Messages</Typography>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Scheduled Messages
          </Typography>
          
          <Button 
            variant="contained" 
            color="primary" 
            startIcon={<AddIcon />}
            component={Link}
            href="/messages/new"
          >
            Create New Message
          </Button>
        </Box>
        <Typography variant="body1" color="text.secondary" paragraph>
          Manage and schedule messages to be sent to patients.
        </Typography>
      </Box>
      
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <TableContainer component={Paper} sx={{ mb: 4 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Recipient</TableCell>
                  <TableCell>Platform</TableCell>
                  <TableCell>Message</TableCell>
                  <TableCell>Scheduled Time</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {messages.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      No scheduled messages found
                    </TableCell>
                  </TableRow>
                ) : (
                  messages.map((message) => (
                    <TableRow key={message.id}>
                      <TableCell>{message.recipient_id}</TableCell>
                      <TableCell>{message.platform}</TableCell>
                      <TableCell sx={{ maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {message.message_content}
                      </TableCell>
                      <TableCell>{new Date(message.scheduled_time).toLocaleString()}</TableCell>
                      <TableCell>
                        <Chip 
                          label={message.status}
                          color={
                            message.status === 'sent' ? 'success' : 
                            message.status === 'pending' ? 'warning' : 
                            'error'
                          }
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Button 
                            variant="text" 
                            color="primary"
                            component={Link} 
                            href={`/messages/${message.id}`}
                            size="small"
                          >
                            Edit
                          </Button>
                          <Button 
                            variant="text" 
                            color="error"
                            size="small"
                          >
                            Delete
                          </Button>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>
        
        <Grid item xs={12}>
          <Paper sx={{ p: 3, bgcolor: 'background.default' }}>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
              <InfoIcon color="primary" />
              <Box>
                <Typography variant="h6" gutterBottom>About Scheduled Messages</Typography>
                <Typography variant="body2" color="text.secondary">
                  This feature allows you to schedule messages to be sent to patients at specific times.
                  You can use this for appointment reminders, check-ins, or any other automated communication needs.
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
} 