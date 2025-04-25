'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Container,
  Typography,
  Box,
  Paper,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  Grid,
  CircularProgress,
  Alert,
  Divider,
  Switch,
  FormControlLabel,
  Chip,
  Link as MuiLink,
  RadioGroup,
  Radio,
  FormLabel
} from '@mui/material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import Link from 'next/link';
import HomeIcon from '@mui/icons-material/Home';
import ScheduleIcon from '@mui/icons-material/Schedule';
import SendIcon from '@mui/icons-material/Send';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import { addMinutes } from 'date-fns';

interface Patient {
  id: string;
  name: string;
  channel?: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  telegram_id?: string;
}

const messageGoals = [
  { value: 'proactive-monitoring', label: 'Proactive Monitoring' },
  { value: 'risky-patient', label: 'Risky Patient' },
  { value: 'medication-reminder', label: 'Medication Reminder' },
  { value: 'appointment-reminder', label: 'Appointment Reminder' },
];

export default function CreateScheduledMessagePage() {
  const router = useRouter();
  
  // Form state
  const [patientId, setPatientId] = useState<string>('');
  const [messageContent, setMessageContent] = useState<string>('');
  const [messageGoal, setMessageGoal] = useState<string>('proactive-monitoring');
  const [scheduledTime, setScheduledTime] = useState<Date | null>(new Date());
  const [sendTestMessage, setSendTestMessage] = useState<boolean>(false);
  const [contentType, setContentType] = useState<'manual' | 'ai'>('manual');
  const [isGeneratingContent, setIsGeneratingContent] = useState<boolean>(false);

  // Data fetching state
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState<boolean>(false);

  // Fetch patients for scheduler
  useEffect(() => {
    const fetchPatients = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/patients/forNewScheduler');
        
        if (!response.ok) {
          throw new Error(`Failed to fetch patients: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
          throw new Error(data.error);
        }
        
        setPatients(data.patients || []);
      } catch (err: any) {
        console.error('Error fetching patients:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPatients();
  }, []);

  // Generate AI content
  const generateMessageContent = async () => {
    if (!messageGoal) return;
    
    try {
      setIsGeneratingContent(true);
      const response = await fetch('/api/scheduled-messages/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messageGoal,
          patientContext: patientId ? { patientId } : undefined
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Error: ${response.status}`);
      }
      
      const result = await response.json();
      setMessageContent(result.messageContent);
    } catch (err: any) {
      console.error('Failed to generate message content:', err);
      setError(`Failed to generate content: ${err.message}`);
    } finally {
      setIsGeneratingContent(false);
    }
  };

  // Form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validate()) {
      return;
    }
    
    try {
      setSubmitting(true);
      setSubmitError(null);
      
      // Get the patient details
      const patient = patients.find(p => p.id === patientId);
      
      if (!patient) {
        throw new Error('Selected patient not found');
      }
      
      // Determine when to send the message
      let messageTime = scheduledTime;
      
      // If test message, set to 2 minutes from now
      if (sendTestMessage) {
        messageTime = addMinutes(new Date(), 2);
      }
      
      // Scheduled message data - match DB schema
      const scheduleData = {
        patientId: patient.id,
        chatId: patient.telegram_id || patient.id, // Use telegram_id if available
        messageContent: messageContent,
        scheduledTime: messageTime?.toISOString(),
        platform: 'telegram', 
        metadata: {
          source: 'web-ui',
          created_by: 'user'
        }
      };
      
      console.log('Scheduling message with data:', scheduleData);
      
      // Submit to API using our new endpoint
      const response = await fetch('/api/scheduled-messages/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(scheduleData),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Error: ${response.status}`);
      }
      
      // Success!
      setSubmitSuccess(true);
      
      // Reset form
      setTimeout(() => {
        router.push('/scheduled-messages');
      }, 2000);
    } catch (err: any) {
      console.error('Failed to schedule message:', err);
      setSubmitError(err.message);
      setSubmitSuccess(false);
    } finally {
      setSubmitting(false);
    }
  };

  // Form validation
  const validate = (): boolean => {
    if (!patientId) {
      setSubmitError('Please select a recipient');
      return false;
    }
    
    if (!messageContent) {
      setSubmitError('Please enter a message or generate one');
      return false;
    }
    
    if (!scheduledTime) {
      setSubmitError('Please select a time to send the message');
      return false;
    }
    
    if (!sendTestMessage && scheduledTime < new Date()) {
      setSubmitError('Scheduled time must be in the future');
      return false;
    }
    
    return true;
  };

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 10 }}>
          <CircularProgress sx={{ mb: 3 }} />
          <Typography>Loading patients...</Typography>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
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
          <Link 
            href="/scheduled-messages"
            style={{
              display: 'flex',
              alignItems: 'center',
              color: 'inherit',
              textDecoration: 'none',
              marginRight: '8px'
            }}
          >
            <ScheduleIcon sx={{ fontSize: 18, mr: 0.5 }} />
            Scheduled Messages
          </Link>
          <Box sx={{ mx: 1, color: 'text.secondary' }}>/</Box>
          <Typography color="text.primary">Create</Typography>
        </Box>
        
        <Typography variant="h4" component="h1" sx={{ mt: 3, mb: 2 }}>
          Schedule New Message
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Create a new scheduled message for a patient.
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {submitSuccess && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Message scheduled successfully! Redirecting...
        </Alert>
      )}

      <Paper sx={{ p: 3 }}>
        <form onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            {/* Recipient selection */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Recipient
              </Typography>
              <FormControl fullWidth error={submitError?.includes('recipient') ?? false}>
                <InputLabel id="patient-select-label">Select Patient</InputLabel>
                <Select
                  labelId="patient-select-label"
                  value={patientId}
                  onChange={(e) => setPatientId(e.target.value)}
                  label="Select Patient"
                  disabled={submitting}
                >
                  {patients.map((patient) => (
                    <MenuItem key={patient.id} value={patient.id}>
                      {patient.name || `${patient.first_name || ''} ${patient.last_name || ''}`.trim() || patient.email || 'Unnamed'}
                      {patient.channel && (
                        <Chip 
                          label={patient.channel} 
                          size="small" 
                          color="primary" 
                          sx={{ ml: 1 }}
                        />
                      )}
                    </MenuItem>
                  ))}
                </Select>
                <FormHelperText>Select the patient to receive this message</FormHelperText>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <Divider />
            </Grid>

            {/* Message content */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Message Content
              </Typography>
              
              <FormControl component="fieldset" sx={{ mb: 2 }}>
                <FormLabel component="legend">Content Type</FormLabel>
                <RadioGroup
                  row
                  value={contentType}
                  onChange={(e) => setContentType(e.target.value as 'manual' | 'ai')}
                >
                  <FormControlLabel value="manual" control={<Radio />} label="Write Message" />
                  <FormControlLabel value="ai" control={<Radio />} label="AI Generated" />
                </RadioGroup>
              </FormControl>
              
              {contentType === 'ai' && (
                <Box sx={{ mb: 3 }}>
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel id="message-goal-label">Message Goal</InputLabel>
                    <Select
                      labelId="message-goal-label"
                      value={messageGoal}
                      onChange={(e) => setMessageGoal(e.target.value)}
                      label="Message Goal"
                      disabled={submitting || isGeneratingContent}
                    >
                      {messageGoals.map((goal) => (
                        <MenuItem key={goal.value} value={goal.value}>
                          {goal.label}
                        </MenuItem>
                      ))}
                    </Select>
                    <FormHelperText>Select the goal of this message</FormHelperText>
                  </FormControl>
                  
                  <Button
                    variant="outlined"
                    startIcon={<AutoAwesomeIcon />}
                    onClick={generateMessageContent}
                    disabled={submitting || isGeneratingContent || !messageGoal}
                    sx={{ mb: 2 }}
                  >
                    {isGeneratingContent ? 'Generating...' : 'Generate Message'}
                  </Button>
                </Box>
              )}
              
              <TextField
                fullWidth
                label="Message Content"
                multiline
                rows={4}
                value={messageContent}
                onChange={(e) => setMessageContent(e.target.value)}
                disabled={submitting || (contentType === 'ai' && isGeneratingContent)}
                error={submitError?.includes('message') ?? false}
                helperText={contentType === 'manual' ? "Enter the message you'd like to send" : "Generated message content (you can edit if needed)"}
                required
              />
            </Grid>

            <Grid item xs={12}>
              <Divider />
            </Grid>

            {/* Scheduling options */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Scheduling
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={sendTestMessage}
                    onChange={(e) => setSendTestMessage(e.target.checked)}
                    disabled={submitting}
                  />
                }
                label="Send as test message (2 minutes from now)"
                sx={{ mb: 2 }}
              />
              
              {!sendTestMessage && (
                <LocalizationProvider dateAdapter={AdapterDateFns}>
                  <DateTimePicker
                    label="Scheduled Time"
                    value={scheduledTime}
                    onChange={(newValue) => setScheduledTime(newValue)}
                    disabled={submitting || sendTestMessage}
                    slotProps={{
                      textField: {
                        fullWidth: true,
                        error: submitError?.includes('time') ?? false,
                        helperText: "When should this message be sent?"
                      }
                    }}
                  />
                </LocalizationProvider>
              )}
            </Grid>

            <Grid item xs={12}>
              <Divider />
            </Grid>

            {/* Submit */}
            <Grid item xs={12}>
              {submitError && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {submitError}
                </Alert>
              )}
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Button
                  variant="outlined"
                  component={Link}
                  href="/scheduled-messages"
                  disabled={submitting}
                >
                  Cancel
                </Button>
                
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  startIcon={<SendIcon />}
                  disabled={submitting || isGeneratingContent}
                >
                  {submitting ? 'Scheduling...' : 'Schedule Message'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </form>
      </Paper>
    </Container>
  );
} 