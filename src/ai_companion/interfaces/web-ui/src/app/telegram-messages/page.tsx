'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Alert from '@mui/material/Alert';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Checkbox from '@mui/material/Checkbox';
import Chip from '@mui/material/Chip';
import Grid from '@mui/material/Grid';
import CircularProgress from '@mui/material/CircularProgress';
import Autocomplete from '@mui/material/Autocomplete';
import AlertTitle from '@mui/material/AlertTitle';
import { useSnackbar } from 'notistack';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import RefreshIcon from '@mui/icons-material/Refresh';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';

import { ScheduledMessage, getScheduledMessages, createScheduledMessage, updateScheduledMessage, cancelScheduledMessage, sendScheduledMessageNow } from '@/services/telegramSchedulerService';
import { format, parseISO } from 'date-fns';
import { 
  CalendarToday, 
  Warning as AlertCircle, 
  CheckCircle, 
  AccessTime as Clock,
} from '@mui/icons-material';

const WEEKDAYS = [
  { id: 0, name: 'Sunday' },
  { id: 1, name: 'Monday' },
  { id: 2, name: 'Tuesday' },
  { id: 3, name: 'Wednesday' },
  { id: 4, name: 'Thursday' },
  { id: 5, name: 'Friday' },
  { id: 6, name: 'Saturday' },
];

interface Patient {
  id: string;
  name: string;
  first_name?: string;
  last_name?: string;
  telegram_id?: string;
  phone?: string;
  email?: string;
}

async function fetchPatients(): Promise<Patient[]> {
  try {
    const response = await fetch('/api/patients?telegramOnly=true');
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    const data = await response.json();
    console.log('Fetched patients:', data.patients);
    return data.patients || [];
  } catch (error) {
    console.error('Failed to fetch patients:', error);
    return [];
  }
}

// Update the health check service function
async function checkTelegramSchedulerHealth(): Promise<{
  isRunning: boolean; 
  message: string;
  lastRun?: string;
  pendingMessages?: number;
  recentMessages?: any[];
  pendingMessagesDetails?: any[];
}> {
  try {
    // Use the backend API URL from environment variable if available
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
    console.log('Using API URL:', apiUrl); // Debug log
    
    // Make sure URL ends with trailing slash if needed
    const baseUrl = apiUrl.endsWith('/') ? apiUrl : `${apiUrl}/`;
    const endpoint = `${baseUrl}monitor/health/telegram-scheduler-status`;
    
    console.log('Fetching from endpoint:', endpoint); // Debug log
    
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      console.error(`Error response from scheduler status endpoint: ${response.status} ${response.statusText}`);
      return { 
        isRunning: false, 
        message: `Could not connect to health endpoint: ${response.status} ${response.statusText}`
      };
    }
    
    const data = await response.json();
    console.log('Telegram scheduler status response:', data); // Debug log
    
    return { 
      isRunning: data.status === 'running', 
      message: data.message || 'Scheduler status checked successfully',
      lastRun: data.last_run,
      pendingMessages: data.pending_messages,
      recentMessages: data.recent_messages,
      pendingMessagesDetails: data.pending_messages_details
    };
  } catch (error) {
    console.error('Failed to check scheduler health:', error);
    return { 
      isRunning: false, 
      message: `Failed to connect to health endpoint: ${error instanceof Error ? error.message : String(error)}`
    };
  }
}

async function sendMessage(messageId: string): Promise<{ success: boolean; message: string }> {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
    const baseUrl = apiUrl.endsWith('/') ? apiUrl : `${apiUrl}/`;
    const endpoint = `${baseUrl}monitor/telegram/send-message?message_id=${messageId}`;
    
    console.log(`Sending message ${messageId} via endpoint: ${endpoint}`);
    
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      console.error(`Error response: ${response.status} ${response.statusText}`);
      return { 
        success: false, 
        message: `Failed to send message: ${response.status} ${response.statusText}` 
      };
    }
    
    const data = await response.json();
    console.log('Send message response:', data);
    
    return { 
      success: data.status === 'success', 
      message: data.message 
    };
  } catch (error) {
    console.error('Failed to send message:', error);
    return { 
      success: false, 
      message: `Error: ${error instanceof Error ? error.message : String(error)}` 
    };
  }
}

function TelegramMessagesContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const patientId = searchParams.get('patientId');
  
  const [activeTab, setActiveTab] = useState(0);
  const [schedules, setSchedules] = useState<ScheduledMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [loadingPatients, setLoadingPatients] = useState(false);
  
  // Form states
  const [messageContent, setMessageContent] = useState('');
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date());
  const [selectedTime, setSelectedTime] = useState('09:00');
  const [isRecurring, setIsRecurring] = useState(false);
  const [recurringType, setRecurringType] = useState<'daily' | 'weekly' | 'monthly'>('daily');
  const [selectedDays, setSelectedDays] = useState<number[]>([1, 2, 3, 4, 5]); // Monday-Friday by default
  
  // Add a patientInfo object to store patient names mapped by ID
  const [patientInfo, setPatientInfo] = useState<Record<string, string>>({});
  
  const { enqueueSnackbar } = useSnackbar();
  
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };
  
  // Load scheduled messages
  useEffect(() => {
    loadSchedules();
  }, [patientId]);
  
  // Load patients data
  useEffect(() => {
    async function loadPatients() {
      setLoadingPatients(true);
      try {
        const data = await fetchPatients();
        setPatients(data);
        
        // Create a map of patient IDs to names for display in the table
        const patientMap: Record<string, string> = {};
        data.forEach(patient => {
          const name = patient.name || 
            `${patient.first_name || ''} ${patient.last_name || ''}`.trim();
          patientMap[patient.id] = name;
        });
        setPatientInfo(patientMap);
        
        // If patientId is specified in URL, select that patient
        if (patientId) {
          const foundPatient = data.find(p => p.id === patientId);
          if (foundPatient) {
            setSelectedPatient(foundPatient);
          }
        }
      } catch (err) {
        console.error('Failed to load patients:', err);
      } finally {
        setLoadingPatients(false);
      }
    }
    
    loadPatients();
  }, [patientId]);
  
  async function loadSchedules() {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await getScheduledMessages(patientId || undefined);
      setSchedules(data);
    } catch (err) {
      console.error('Failed to load schedules:', err);
      setError('Failed to load scheduled messages. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }
  
  // Function to create a new scheduled message
  const handleCreateSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    if (!selectedPatient) {
      setError('Please select a patient');
      setIsLoading(false);
      return;
    }

    try {
      console.log('Creating schedule with data:', {
        patientId: selectedPatient.id,
        messageContent,
        scheduledTime: selectedDate?.toISOString(),
        recurrence: isRecurring ? {
          type: recurringType,
          days: selectedDays
        } : null
      });

      const response = await fetch('/api/telegram-scheduler', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          patientId: selectedPatient.id,
          messageContent,
          scheduledTime: selectedDate?.toISOString(),
          recurrence: isRecurring ? {
            type: recurringType,
            days: selectedDays
          } : null
        }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to create scheduled message');
      }

      console.log('Schedule created successfully:', data);
      
      // Clear form and refresh schedules
      setMessageContent('');
      setSelectedDate(new Date());
      setIsRecurring(false);
      setRecurringType('daily');
      setSelectedDays([]);
      fetchScheduledMessages();

    } catch (error) {
      console.error('Error creating schedule:', error);
      setError(error instanceof Error ? error.message : 'Failed to create scheduled message');
    } finally {
      setIsLoading(false);
    }
  };
  
  async function handleCancelSchedule(id: string) {
    if (!confirm('Are you sure you want to cancel this scheduled message?')) {
      return;
    }
    
    setIsLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      await cancelScheduledMessage(id);
      setSuccess('Schedule cancelled successfully!');
      loadSchedules();
    } catch (err) {
      console.error('Failed to cancel schedule:', err);
      setError('Failed to cancel schedule. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }
  
  // Add function to handle sending a message immediately
  async function handleSendNowSchedule(id: string) {
    if (!confirm('Are you sure you want to send this message now?')) {
      return;
    }
    
    setIsLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      await sendScheduledMessageNow(id);
      setSuccess('Message sent successfully!');
      loadSchedules();
    } catch (err) {
      console.error('Failed to send message:', err);
      setError('Failed to send message. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }
  
  function getStatusChip(status: string) {
    switch (status) {
      case 'pending':
        return <Chip label="Pending" color="warning" variant="outlined" />;
      case 'sent':
        return <Chip label="Sent" color="success" variant="outlined" />;
      case 'failed':
        return <Chip label="Failed" color="error" variant="outlined" />;
      case 'cancelled':
        return <Chip label="Cancelled" color="default" variant="outlined" />;
      default:
        return <Chip label={status} />;
    }
  }
  
  function toggleDaySelection(dayId: number) {
    setSelectedDays(prev => 
      prev.includes(dayId) 
        ? prev.filter(id => id !== dayId)
        : [...prev, dayId]
    );
  }
  
  // Add new function to set time to 2 minutes from now
  function setTwoMinutesFromNow() {
    const now = new Date();
    now.setMinutes(now.getMinutes() + 2);
    
    // Set the date
    setSelectedDate(now);
    
    // Format the time as HH:MM
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    setSelectedTime(`${hours}:${minutes}`);
  }
  
  // Add function to set a default test message
  function setDefaultMessage() {
    setMessageContent('This is a test message scheduled to be sent in 2 minutes.');
  }
  
  // Add a quick send function that combines setting default message and 2-minute timer
  function quickSend() {
    // Set default message
    setDefaultMessage();
    
    // Set time to 2 minutes from now
    setTwoMinutesFromNow();
    
    // If no patient is selected and there are patients available, select the first one
    if (!selectedPatient && patients.length > 0) {
      setSelectedPatient(patients[0]);
    }
  }
  
  // Function to fetch scheduled messages
  const fetchScheduledMessages = async () => {
    setIsLoading(true);
    try {
      console.log('Fetching scheduled messages...');
      const response = await fetch('/api/telegram-scheduler');
      if (!response.ok) {
        throw new Error(`Failed to fetch scheduled messages: ${response.status} ${response.statusText}`);
      }
      const data = await response.json();
      console.log('Received scheduled messages:', data);
      
      // Check if data contains schedules or messages property
      const schedulesList = data.schedules || data.messages || [];
      setSchedules(schedulesList);
      
      // Update patient names mapping
      const patientIds = schedulesList.map((schedule: any) => schedule.patient_id);
      
      if (patientIds.length > 0) {
        await fetchPatientNames(patientIds);
      }
    } catch (error) {
      console.error('Error fetching scheduled messages:', error);
      setError('Failed to load scheduled messages');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Function to fetch patient names by IDs
  const fetchPatientNames = async (patientIds: string[]) => {
    if (!patientIds.length) return;
    
    try {
      console.log('Fetching patient names for IDs:', patientIds);
      const response = await fetch(`/api/patients?ids=${patientIds.join(',')}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch patient names: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Received patient data:', data);
      
      // Create a mapping of patient IDs to names
      const newPatientNames: Record<string, string> = {};
      data.patients.forEach((patient: any) => {
        newPatientNames[patient.id] = patient.name || `Patient ${patient.id}`;
      });
      
      setPatientInfo(prevNames => ({
        ...prevNames,
        ...newPatientNames
      }));
    } catch (error) {
      console.error('Error fetching patient names:', error);
    }
  };
  
  // Add TelegramSchedulerHealth component inside TelegramMessagesContent
  function TelegramSchedulerHealth() {
    const [health, setHealth] = useState<{
      isRunning: boolean; 
      message: string;
      lastRun?: string;
      pendingMessages?: number;
      recentMessages?: any[];
      pendingMessagesDetails?: any[];
    }>({ 
      isRunning: false, 
      message: 'Checking status...' 
    });
    const [loading, setLoading] = useState(true);
    const [expanded, setExpanded] = useState(false);
    const [showPendingMessages, setShowPendingMessages] = useState(false);

    const checkHealth = async () => {
      setLoading(true);
      try {
        const status = await checkTelegramSchedulerHealth();
        setHealth(status);
        
        // Auto-expand if there are pending messages and scheduler is not running
        if (!status.isRunning && status.pendingMessagesDetails && status.pendingMessagesDetails.length > 0) {
          setExpanded(true);
          setShowPendingMessages(true);
        }
      } catch (error) {
        console.error('Error checking health:', error);
        setHealth({ isRunning: false, message: 'Error checking scheduler status' });
      } finally {
        setLoading(false);
      }
    };

    useEffect(() => {
      checkHealth();
      // Check health every 30 seconds
      const interval = setInterval(checkHealth, 30000);
      return () => clearInterval(interval);
    }, []);

    // Format the time
    const formatTime = (isoTime?: string) => {
      if (!isoTime) return 'Unknown';
      try {
        return format(parseISO(isoTime), 'MMM d, yyyy h:mm:ss a');
      } catch (e) {
        return isoTime;
      }
    };

    return (
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {health.isRunning ? (
              <CheckCircle color="success" sx={{ mr: 1 }} />
            ) : (
              <AlertCircle color="error" sx={{ mr: 1 }} />
            )}
            <Box>
              <Typography variant="subtitle1">
                Telegram Scheduler Status: {health.isRunning ? 'Running' : 'Not Running'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {health.message}
              </Typography>
              {!health.isRunning && health.pendingMessages && health.pendingMessages > 0 && (
                <Typography variant="body2" color="error" sx={{ fontWeight: 'bold', mt: 1 }}>
                  ⚠️ There are {health.pendingMessages} pending messages waiting to be sent!
                </Typography>
              )}
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              startIcon={loading ? <CircularProgress size={20} /> : <RefreshIcon />}
              onClick={checkHealth}
              disabled={loading}
              size="small"
            >
              Refresh
            </Button>
            <Button
              size="small"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? 'Less Details' : 'More Details'}
            </Button>
            {expanded && health.pendingMessagesDetails && health.pendingMessagesDetails.length > 0 && (
              <Button
                size="small"
                color="primary"
                variant={showPendingMessages ? "contained" : "outlined"}
                onClick={() => setShowPendingMessages(!showPendingMessages)}
              >
                {showPendingMessages ? 'Hide Pending' : 'Show Pending'}
              </Button>
            )}
          </Box>
        </Box>
        
        {expanded && (
          <Box sx={{ mt: 2, pl: 4 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="body2">
                  <strong>Last Run:</strong> {formatTime(health.lastRun)}
                </Typography>
                <Typography variant="body2">
                  <strong>Pending Messages:</strong> {health.pendingMessages !== undefined ? health.pendingMessages : 'Unknown'}
                </Typography>
              </Grid>
              
              {showPendingMessages && health.pendingMessagesDetails && health.pendingMessagesDetails.length > 0 && (
                <Grid item xs={12}>
                  <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold', color: 'error.main' }}>
                    Pending Messages ({health.pendingMessagesDetails.length}):
                  </Typography>
                  <Table size="small" sx={{ mb: 3 }}>
                    <TableHead>
                      <TableRow>
                        <TableCell>Scheduled For</TableCell>
                        <TableCell>Patient</TableCell>
                        <TableCell>Message</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {health.pendingMessagesDetails.map((msg) => (
                        <TableRow key={msg.id}>
                          <TableCell>{msg.formatted_time || formatTime(msg.scheduled_time)}</TableCell>
                          <TableCell>{msg.patient_name || msg.patient_id}</TableCell>
                          <TableCell sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {msg.message_content}
                          </TableCell>
                          <TableCell>
                            <Chip 
                              size="small" 
                              label={msg.status} 
                              color={msg.status === 'pending' ? 'warning' : 'default'}
                            />
                          </TableCell>
                          <TableCell>
                            <Button
                              variant="contained"
                              color="primary"
                              size="small"
                              onClick={async () => {
                                try {
                                  // Show loading state
                                  setIsLoading(true);
                                  
                                  // Send the message
                                  const result = await sendMessage(msg.id);
                                  
                                  // Show result in notification
                                  if (result.success) {
                                    enqueueSnackbar('Message sent successfully', { variant: 'success' });
                                    
                                    // Refresh data
                                    const healthStatus = await checkTelegramSchedulerHealth();
                                    setHealth(healthStatus);
                                  } else {
                                    enqueueSnackbar(`Failed to send: ${result.message}`, { variant: 'error' });
                                  }
                                } catch (error) {
                                  console.error('Error sending message:', error);
                                  enqueueSnackbar(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, { variant: 'error' });
                                } finally {
                                  setIsLoading(false);
                                }
                              }}
                              disabled={isLoading}
                            >
                              Send Now
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Grid>
              )}
              
              {health.recentMessages && health.recentMessages.length > 0 && (
                <Grid item xs={12}>
                  <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>
                    Recent Messages:
                  </Typography>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Time</TableCell>
                        <TableCell>Patient</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Message</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {health.recentMessages.map((msg) => (
                        <TableRow key={msg.id}>
                          <TableCell>
                            {formatTime(msg.processed_at || msg.last_attempt_time)}
                          </TableCell>
                          <TableCell>{patientInfo[msg.patient_id] || msg.patient_id}</TableCell>
                          <TableCell>{getStatusChip(msg.status)}</TableCell>
                          <TableCell sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {msg.message_content}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Grid>
              )}

              {!health.isRunning && (
                <Grid item xs={12}>
                  <Alert severity="warning" sx={{ mt: 2 }}>
                    <AlertTitle>Scheduler Not Running</AlertTitle>
                    <Typography variant="body2">
                      The Telegram scheduler is not running. This service should be running in Azure as a Container App.
                    </Typography>
                    <Box component="ol" sx={{ mt: 1, pl: 2 }}>
                      <li>Contact your system administrator to ensure the Telegram scheduler Container App is properly deployed</li>
                      <li>If you're a system administrator, check the Azure Portal:</li>
                      <Box component="ul" sx={{ pl: 2 }}>
                        <li>Go to Azure Portal and navigate to Container Apps</li>
                        <li>Look for the container app named "telegram-scheduler-app"</li>
                        <li>Check the logs and status of the container app</li>
                        <li>If needed, restart the container app or redeploy using deploy.ps1 with -ForceUpdate</li>
                      </Box>
                    </Box>
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      If you're running a local development environment, you can still use one of these methods:
                    </Typography>
                    <Box component="ul" sx={{ pl: 2, mt: 0.5 }}>
                      <li><Box component="code">powershell.exe -ExecutionPolicy Bypass -File ".\src\ai_companion\interfaces\telegram\start_scheduler.ps1"</Box> (Windows)</li>
                      <li><Box component="code">bash ./src/ai_companion/interfaces/telegram/check_scheduler.sh start</Box> (Linux)</li>
                    </Box>
                  </Alert>
                </Grid>
              )}
            </Grid>
          </Box>
        )}
      </Paper>
    );
  }
  
  return (
    <Box sx={{ padding: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Telegram Message Scheduler
      </Typography>
      
      {/* Add the health status component */}
      <TelegramSchedulerHealth />
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab label="Scheduled Messages" />
          <Tab label="Create New Schedule" />
        </Tabs>
      </Box>
      
      <div role="tabpanel" hidden={activeTab !== 0}>
        {activeTab === 0 && (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Scheduled Messages
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              View and manage scheduled Telegram messages
            </Typography>
            
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            
            {success && (
              <Alert severity="success" sx={{ mb: 2 }}>
                {success}
              </Alert>
            )}
            
            {isLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
                <CircularProgress />
              </Box>
            ) : schedules.length > 0 ? (
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Patient</TableCell>
                    <TableCell>Scheduled Time</TableCell>
                    <TableCell>Message</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Recurrence</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {schedules.map((schedule) => (
                    <TableRow key={schedule.id}>
                      <TableCell>
                        {patientInfo[schedule.patient_id] || 'Unknown Patient'}
                      </TableCell>
                      <TableCell>
                        {format(parseISO(schedule.scheduled_time), 'MMM d, yyyy h:mm a')}
                      </TableCell>
                      <TableCell sx={{ maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {schedule.message_content}
                      </TableCell>
                      <TableCell>{getStatusChip(schedule.status)}</TableCell>
                      <TableCell>
                        {schedule.recurrence ? (
                          <span>
                            {schedule.recurrence.type === 'daily' && 'Daily'}
                            {schedule.recurrence.type === 'weekly' && 'Weekly'}
                            {schedule.recurrence.type === 'monthly' && 'Monthly'}
                            {schedule.recurrence.days && ` (${schedule.recurrence.days.map(d => WEEKDAYS[d].name.slice(0, 3)).join(', ')})`}
                            {` at ${schedule.recurrence.time}`}
                          </span>
                        ) : (
                          <span>One-time</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {schedule.status === 'pending' && (
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Button
                              variant="contained"
                              size="small"
                              color="primary"
                              onClick={() => handleSendNowSchedule(schedule.id)}
                            >
                              Send Now
                            </Button>
                          <Button
                            variant="outlined"
                            size="small"
                            onClick={() => handleCancelSchedule(schedule.id)}
                          >
                            Cancel
                          </Button>
                          </Box>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <Box sx={{ textAlign: 'center', py: 4, color: 'text.secondary' }}>
                No scheduled messages found
              </Box>
            )}
            
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
              <Button variant="outlined" onClick={loadSchedules} disabled={isLoading}>
                {isLoading ? <CircularProgress size={20} sx={{ mr: 1 }} /> : <Clock sx={{ mr: 1 }} />}
                Refresh
              </Button>
            </Box>
          </Paper>
        )}
      </div>
      
      <div role="tabpanel" hidden={activeTab !== 1}>
        {activeTab === 1 && (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Create New Schedule
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Schedule a new message to be sent via Telegram
            </Typography>
            
            <form onSubmit={handleCreateSchedule}>
              <Box sx={{ mb: 3 }}>
                {error && (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                  </Alert>
                )}
                
                {success && (
                  <Alert severity="success" sx={{ mb: 2 }}>
                    {success}
                  </Alert>
                )}
                
                <Autocomplete
                  sx={{ mb: 3 }}
                  options={patients}
                  loading={loadingPatients}
                  value={selectedPatient}
                  onChange={(e, newValue) => setSelectedPatient(newValue)}
                  getOptionLabel={(option) => {
                    const fullName = option.name || 
                      `${option.first_name || ''} ${option.last_name || ''}`.trim();
                    
                    const additionalInfo = [];
                    if (option.phone) additionalInfo.push(`Phone: ${option.phone}`);
                    if (option.email) additionalInfo.push(`Email: ${option.email}`);
                    
                    return additionalInfo.length > 0
                      ? `${fullName} (${additionalInfo.join(', ')})`
                      : fullName;
                  }}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="Select Patient"
                      required
                      InputProps={{
                        ...params.InputProps,
                        endAdornment: (
                          <>
                            {loadingPatients ? <CircularProgress size={20} /> : null}
                            {params.InputProps.endAdornment}
                          </>
                        ),
                      }}
                    />
                  )}
                />
                
                <TextField
                  fullWidth
                  label="Message Content"
                  multiline
                  rows={4}
                  value={messageContent}
                  onChange={(e) => setMessageContent(e.target.value)}
                  required
                  sx={{ mb: 1 }}
                />
                <Box sx={{ mb: 3, display: 'flex', justifyContent: 'flex-end' }}>
                  <Button 
                    variant="text"
                    color="primary"
                    onClick={setDefaultMessage}
                    size="small"
                  >
                    Use Test Message
                  </Button>
                </Box>
                
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Date"
                      type="date"
                      value={selectedDate ? selectedDate.toISOString().split('T')[0] : ''}
                      onChange={(e) => setSelectedDate(new Date(e.target.value))}
                      InputLabelProps={{ shrink: true }}
                      required
                    />
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Time"
                      type="time"
                      value={selectedTime}
                      onChange={(e) => setSelectedTime(e.target.value)}
                      InputLabelProps={{ shrink: true }}
                      required
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <Button 
                      variant="outlined" 
                      color="secondary" 
                      onClick={setTwoMinutesFromNow}
                      startIcon={<Clock />}
                      sx={{ mt: 1 }}
                    >
                      Send in 2 minutes
                    </Button>
                  </Grid>
                </Grid>
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={isRecurring}
                      onChange={(e) => setIsRecurring(e.target.checked)}
                    />
                  }
                  label="Recurring Message"
                  sx={{ mb: 2 }}
                />
                
                {isRecurring && (
                  <Box sx={{ mb: 3 }}>
                    <FormControl fullWidth sx={{ mb: 2 }}>
                      <InputLabel>Recurrence Pattern</InputLabel>
                      <Select
                        value={recurringType}
                        label="Recurrence Pattern"
                        onChange={(e) => setRecurringType(e.target.value as 'daily' | 'weekly' | 'monthly')}
                      >
                        <MenuItem value="daily">Daily</MenuItem>
                        <MenuItem value="weekly">Weekly</MenuItem>
                        <MenuItem value="monthly">Monthly</MenuItem>
                      </Select>
                    </FormControl>
                    
                    {recurringType === 'weekly' && (
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Days of Week
                        </Typography>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          {WEEKDAYS.map((day) => (
                            <Box key={day.id} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                              <Checkbox
                                checked={selectedDays.includes(day.id)}
                                onChange={() => toggleDaySelection(day.id)}
                              />
                              <Typography variant="caption">
                                {day.name.slice(0, 3)}
                              </Typography>
                            </Box>
                          ))}
                        </Box>
                      </Box>
                    )}
                  </Box>
                )}
              </Box>
              
              <Box sx={{ mb: 4, mt: 2, display: 'flex', justifyContent: 'center' }}>
                <Button
                  variant="contained"
                  color="secondary"
                  onClick={quickSend}
                  startIcon={<Clock />}
                  size="large"
                  sx={{ px: 4, py: 1 }}
                >
                  Quick Send Test Message in 2 Minutes
                </Button>
              </Box>
              
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
                <Button
                  variant="outlined"
                  onClick={() => router.back()}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="contained" disabled={isLoading}>
                  {isLoading && <CircularProgress size={20} sx={{ mr: 1 }} />}
                  Schedule Message
                </Button>
              </Box>
            </form>
          </Paper>
        )}
      </div>
    </Box>
  );
}

export default function TelegramMessagesPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <TelegramMessagesContent />
    </Suspense>
  );
} 