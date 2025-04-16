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
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import { useSnackbar } from 'notistack';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import RefreshIcon from '@mui/icons-material/Refresh';
import Link from 'next/link';
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
  Home as HomeIcon,
  Add as AddIcon
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
async function checkSchedulerHealth(): Promise<{
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

function ScheduledMessagesContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const patientId = searchParams.get('patientId');
  
  const [schedules, setSchedules] = useState<ScheduledMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [loadingPatients, setLoadingPatients] = useState(false);
  const [openNewDialog, setOpenNewDialog] = useState(false);
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
  
  // Load scheduled messages
  useEffect(() => {
    loadSchedules();
    checkHealth();
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

  const checkHealth = async () => {
    try {
      const status = await checkSchedulerHealth();
      setHealth(status);
    } catch (error) {
      console.error('Error checking health:', error);
      setHealth({ isRunning: false, message: 'Error checking scheduler status' });
    }
  };
  
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
      setOpenNewDialog(false);
      enqueueSnackbar('Message scheduled successfully', { variant: 'success' });
      loadSchedules();

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
      enqueueSnackbar('Schedule cancelled successfully', { variant: 'success' });
      loadSchedules();
    } catch (err) {
      console.error('Failed to cancel schedule:', err);
      enqueueSnackbar('Failed to cancel schedule', { variant: 'error' });
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
      enqueueSnackbar('Message sent successfully', { variant: 'success' });
      loadSchedules();
    } catch (err) {
      console.error('Failed to send message:', err);
      enqueueSnackbar('Failed to send message', { variant: 'error' });
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

  function closeDialog() {
    setOpenNewDialog(false);
    // Reset form
    setMessageContent('');
    setSelectedDate(new Date());
    setSelectedTime('09:00');
    setIsRecurring(false);
    setRecurringType('daily');
    setSelectedDays([1, 2, 3, 4, 5]);
    setSelectedPatient(null);
  }
  
  return (
    <Box sx={{ padding: 4 }}>
      {/* Breadcrumb navigation */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Link href="/" style={{ display: 'flex', alignItems: 'center', color: 'inherit', textDecoration: 'none', marginRight: '8px' }}>
          <HomeIcon sx={{ fontSize: 18, mr: 0.5 }} />
          Home
        </Link>
        <Box sx={{ mx: 1, color: 'text.secondary' }}>/</Box>
        <Typography color="text.primary">Scheduled Messages</Typography>
      </Box>
      
      {/* Header with title and add button */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 3, mb: 3 }}>
        <Typography variant="h4" component="h1">
          Scheduled Messages
        </Typography>
        <Button 
          variant="contained" 
          startIcon={<AddIcon />} 
          onClick={() => setOpenNewDialog(true)}
        >
          Add New Schedule
        </Button>
      </Box>
      
      {/* Page description */}
      <Typography variant="body1" color="text.secondary" paragraph>
        Manage scheduled messages and communication.
      </Typography>
      
      {/* Health status chip */}
      {!health.isRunning && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          Message scheduler is not running. Some features may be unavailable.
        </Alert>
      )}
      
      {/* Main content - Messages Table */}
      <Paper sx={{ p: 0, mb: 4, overflow: 'hidden' }}>
        {error && (
          <Alert severity="error" sx={{ mx: 3, mt: 3 }}>
            {error}
          </Alert>
        )}
        
        {success && (
          <Alert severity="success" sx={{ mx: 3, mt: 3 }}>
            {success}
          </Alert>
        )}
        
        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : schedules.length > 0 ? (
          <Box>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Patient</TableCell>
                  <TableCell>Scheduled Time</TableCell>
                  <TableCell>Message</TableCell>
                  <TableCell>Recurrence</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
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
                    <TableCell>{getStatusChip(schedule.status)}</TableCell>
                    <TableCell align="right">
                      {schedule.status === 'pending' && (
                        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
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
          </Box>
        ) : (
          <Box sx={{ textAlign: 'center', py: 6, color: 'text.secondary' }}>
            <Typography variant="h6" color="textSecondary">
              No scheduled messages found
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              Click the "Add New Schedule" button to create your first scheduled message.
            </Typography>
          </Box>
        )}
      </Paper>
      
      {/* New Schedule Dialog */}
      <Dialog 
        open={openNewDialog} 
        onClose={closeDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          New Scheduled Message
        </DialogTitle>
        <DialogContent>
          <Box component="form" onSubmit={handleCreateSchedule} sx={{ pt: 1 }}>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            
            <Autocomplete
              sx={{ mb: 3, mt: 2 }}
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
            
            <Box sx={{ textAlign: 'center', mb: 3 }}>
              <Button
                variant="contained"
                color="secondary"
                onClick={quickSend}
                startIcon={<Clock />}
              >
                Quick Send Test in 2 Minutes
              </Button>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDialog}>Cancel</Button>
          <Button 
            variant="contained"
            onClick={handleCreateSchedule}
            disabled={isLoading}
          >
            {isLoading && <CircularProgress size={20} sx={{ mr: 1 }} />}
            Schedule Message
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default function ScheduledMessagesPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ScheduledMessagesContent />
    </Suspense>
  );
} 