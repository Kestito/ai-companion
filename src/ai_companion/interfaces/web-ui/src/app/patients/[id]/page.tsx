'use client';

import { useState, useEffect } from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  Paper, 
  Grid, 
  Breadcrumbs, 
  Link, 
  Button, 
  Tabs, 
  Tab, 
  Divider, 
  Chip, 
  Avatar,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Skeleton,
  Icon
} from '@mui/material';
import { 
  Home as HomeIcon, 
  Person as PersonIcon, 
  Edit as EditIcon, 
  Print as PrintIcon, 
  Share as ShareIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  Event as EventIcon,
  LocalHospital as LocalHospitalIcon,
  HealthAndSafety as HealthAndSafetyIcon,
  ArrowBack as ArrowBackIcon,
  ArrowDropUp as ArrowDropUpIcon,
  ArrowDropDown as ArrowDropDownIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Repeat as RepeatIcon,
  Add as AddIcon
} from '@mui/icons-material';
import { useParams, useRouter } from 'next/navigation';
import { PatientStatusIndicator } from '@/components/patients/patientstatusindicator';
import { Patient } from '@/lib/supabase/types';
import { ScheduledCheck } from '@/lib/supabase/types';
import { 
  fetchPatientById, 
  fetchPatientRiskAssessments,
  fetchPatientAppointments,
} from '@/lib/supabase/patientService';
import { scheduledChecksService, scheduleService } from '@/lib/api';
import ScheduledCheckForm, { ScheduledCheckFormData } from '@/components/patients/scheduledcheckform';
import { ConversationsTab } from '@/components/patients/conversationstab';

// Define a ScheduledMessage interface matching the backend structure
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

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`patient-tabpanel-${index}`}
      aria-labelledby={`patient-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ py: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `patient-tab-${index}`,
    'aria-controls': `patient-tabpanel-${index}`,
  };
}

/**
 * Component to display scheduled checks for a patient
 */
function ScheduledChecksTab({ patientId }: { patientId: string }) {
  const [scheduledChecks, setScheduledChecks] = useState<ScheduledCheck[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  const loadScheduledChecks = async () => {
    try {
      setLoading(true);
      setErrorMessage(null);
      // Fetch scheduled checks from the API
      const data = await scheduledChecksService.fetchScheduledChecks(patientId);
      setScheduledChecks(data);
    } catch (err) {
      console.error('Error loading scheduled checks:', err);
      setErrorMessage('Unable to load scheduled checks. Please try again later.');
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    loadScheduledChecks();
  }, [patientId]);
  
  const handleAddCheck = async (formData: ScheduledCheckFormData) => {
    try {
      setFormSubmitting(true);
      setErrorMessage(null);
      
      // Add a small delay to show loading state
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Create the scheduled check
      const result = await scheduledChecksService.createScheduledCheck({
        title: formData.title,
        description: formData.description,
        frequency: formData.frequency,
        nextScheduled: formData.nextScheduled.toISOString(),
        platform: formData.platform,
        patientId: formData.patientId
      });
      
      // Show success message
      setSuccessMessage('Scheduled check created successfully!');
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setSuccessMessage(null);
      }, 3000);
      
      setShowForm(false);
      
      // Reload the scheduled checks
      await loadScheduledChecks();
    } catch (err) {
      console.error('Error creating scheduled check:', err);
      setErrorMessage('Failed to create scheduled check. Please try again.');
      
      // Clear error message after 5 seconds
      setTimeout(() => {
        setErrorMessage(null);
      }, 5000);
    } finally {
      setFormSubmitting(false);
    }
  };
  
  const getFrequencyIcon = (frequency: string) => {
    switch (frequency.toLowerCase()) {
      case 'daily':
        return <RepeatIcon fontSize="small" sx={{ color: '#1976d2' }} />;
      case 'weekly':
        return <RepeatIcon fontSize="small" sx={{ color: '#9c27b0' }} />;
      case 'monthly':
        return <RepeatIcon fontSize="small" sx={{ color: '#ed6c02' }} />;
      default:
        return <ScheduleIcon fontSize="small" />;
    }
  };
  
  const getPlatformIcon = (platform: string) => {
    switch (platform.toLowerCase()) {
      case 'whatsapp':
        return <Icon className="fa-brands fa-whatsapp" sx={{ color: '#25D366' }} />;
      case 'telegram':
        return <Icon className="fa-brands fa-telegram" sx={{ color: '#0088cc' }} />;
      case 'sms':
        return <Icon className="fa-solid fa-sms" sx={{ color: '#5C5C5C' }} />;
      case 'email':
        return <Icon className="fa-solid fa-envelope" sx={{ color: '#DB4437' }} />;
      default:
        return <Icon className="fa-solid fa-comment" />;
    }
  };
  
  if (loading) {
    return (
      <Box sx={{ pt: 2 }}>
        <Skeleton variant="rectangular" height={100} sx={{ mb: 2 }} />
        <Skeleton variant="rectangular" height={100} sx={{ mb: 2 }} />
        <Skeleton variant="rectangular" height={100} />
      </Box>
    );
  }
  
  if (scheduledChecks.length === 0) {
    return (
      <Box sx={{ pt: 2, textAlign: 'center' }}>
        {errorMessage && (
          <Paper 
            sx={{ 
              mb: 2, 
              p: 2, 
              bgcolor: 'error.light', 
              color: 'error.contrastText',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between' 
            }}
          >
            {errorMessage}
            <IconButton 
              size="small" 
              color="inherit" 
              onClick={() => setErrorMessage(null)}
            >
              <Icon>close</Icon>
            </IconButton>
          </Paper>
        )}
        
        {successMessage && (
          <Paper 
            sx={{ 
              mb: 2, 
              p: 2, 
              bgcolor: 'success.light', 
              color: 'success.contrastText',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between' 
            }}
          >
            {successMessage}
            <IconButton 
              size="small" 
              color="inherit" 
              onClick={() => setSuccessMessage(null)}
            >
              <Icon>close</Icon>
            </IconButton>
          </Paper>
        )}
        
        <Typography variant="h6" color="text.secondary">No scheduled checks found</Typography>
        <Button 
          variant="contained" 
          startIcon={<AddIcon />} 
          sx={{ mt: 2 }}
          onClick={() => setShowForm(true)}
          disabled={formSubmitting}
        >
          {formSubmitting ? "Adding..." : "Add Scheduled Check"}
        </Button>
        
        <ScheduledCheckForm
          open={showForm}
          onClose={() => setShowForm(false)}
          onSubmit={handleAddCheck}
          patientId={patientId}
        />
      </Box>
    );
  }
  
  return (
    <Box sx={{ pt: 2 }}>
      {errorMessage && (
        <Paper 
          sx={{ 
            mb: 2, 
            p: 2, 
            bgcolor: 'error.light', 
            color: 'error.contrastText',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between' 
          }}
        >
          {errorMessage}
          <IconButton 
            size="small" 
            color="inherit" 
            onClick={() => setErrorMessage(null)}
          >
            <Icon>close</Icon>
          </IconButton>
        </Paper>
      )}
      
      {successMessage && (
        <Paper 
          sx={{ 
            mb: 2, 
            p: 2, 
            bgcolor: 'success.light', 
            color: 'success.contrastText',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between' 
          }}
        >
          {successMessage}
          <IconButton 
            size="small" 
            color="inherit" 
            onClick={() => setSuccessMessage(null)}
          >
            <Icon>close</Icon>
          </IconButton>
        </Paper>
      )}
      
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6">Scheduled Health Checks</Typography>
        <Button 
          variant="contained" 
          startIcon={<AddIcon />}
          onClick={() => setShowForm(true)}
          disabled={formSubmitting}
        >
          {formSubmitting ? 'Adding...' : 'Add Check'}
        </Button>
      </Box>
      
      {scheduledChecks.map((check) => (
        <Paper key={check.id} sx={{ mb: 2, overflow: 'hidden' }}>
          <Box 
            sx={{
              p: 2,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Avatar sx={{ bgcolor: 'primary.light', mr: 2 }}>
                <ScheduleIcon />
              </Avatar>
              <Box>
                <Typography variant="subtitle1">
                  {check.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {check.description}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
                    {getFrequencyIcon(check.frequency)}
                    <Typography variant="caption" sx={{ ml: 0.5 }}>
                      {check.frequency.charAt(0).toUpperCase() + check.frequency.slice(1)}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    {getPlatformIcon(check.platform)}
                    <Typography variant="caption" sx={{ ml: 0.5 }}>
                      {check.platform.charAt(0).toUpperCase() + check.platform.slice(1)}
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </Box>
            <Box sx={{ textAlign: 'right' }}>
              <Chip 
                label={check.status} 
                color={check.status === 'completed' ? 'success' : 'primary'}
                size="small"
                sx={{ mb: 1 }}
              />
              <Typography variant="caption" display="block">
                Next: {new Date(check.nextScheduled).toLocaleDateString()}
              </Typography>
            </Box>
          </Box>
        </Paper>
      ))}
      
      <ScheduledCheckForm
        open={showForm}
        onClose={() => setShowForm(false)}
        onSubmit={handleAddCheck}
        patientId={patientId}
      />
    </Box>
  );
}

/**
 * Component to display scheduled messages for a patient
 */
function ScheduledMessagesTab({ patientId }: { patientId: string }) {
  const [scheduledMessages, setScheduledMessages] = useState<ScheduledMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  const loadScheduledMessages = async () => {
    try {
      setLoading(true);
      setErrorMessage(null);
      
      // Fetch scheduled messages from the API with patientId query parameter
      const response = await fetch(`/api/scheduled-messages?patientId=${patientId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch scheduled messages: ${response.status}`);
      }
      
      const data = await response.json();
      setScheduledMessages(data.messages || []);
    } catch (err) {
      console.error('Error loading scheduled messages:', err);
      setErrorMessage('Unable to load scheduled messages. Please try again later.');
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    loadScheduledMessages();
  }, [patientId]);
  
  const getPlatformIcon = (platform: string) => {
    switch (platform?.toLowerCase()) {
      case 'whatsapp':
        return <Icon className="fa-brands fa-whatsapp" sx={{ color: '#25D366' }} />;
      case 'telegram':
        return <Icon className="fa-brands fa-telegram" sx={{ color: '#0088cc' }} />;
      case 'sms':
        return <Icon className="fa-solid fa-sms" sx={{ color: '#5C5C5C' }} />;
      case 'email':
        return <Icon className="fa-solid fa-envelope" sx={{ color: '#DB4437' }} />;
      default:
        return <Icon className="fa-solid fa-comment" />;
    }
  };
  
  if (loading) {
    return (
      <Box sx={{ pt: 2 }}>
        <Skeleton variant="rectangular" height={100} sx={{ mb: 2 }} />
        <Skeleton variant="rectangular" height={100} sx={{ mb: 2 }} />
        <Skeleton variant="rectangular" height={100} />
      </Box>
    );
  }
  
  if (scheduledMessages.length === 0) {
    return (
      <Box sx={{ pt: 2, textAlign: 'center' }}>
        {errorMessage && (
          <Paper 
            sx={{ 
              mb: 2, 
              p: 2, 
              bgcolor: 'error.light', 
              color: 'error.contrastText',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between' 
            }}
          >
            {errorMessage}
            <IconButton 
              size="small" 
              color="inherit" 
              onClick={() => setErrorMessage(null)}
            >
              <Icon>close</Icon>
            </IconButton>
          </Paper>
        )}
        
        <Typography variant="h6" color="text.secondary">No scheduled messages found</Typography>
        <Typography variant="body2" color="text.secondary">
          Schedule messages for this patient from the messages page.
        </Typography>
        <Button
          component={Link}
          href="/scheduled-messages/create"
          variant="outlined"
          sx={{ mt: 2 }}
          startIcon={<ScheduleIcon />}
        >
          Create Message
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      {errorMessage && (
        <Paper 
          sx={{ 
            mb: 2, 
            p: 2, 
            bgcolor: 'error.light', 
            color: 'error.contrastText',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between' 
          }}
        >
          {errorMessage}
          <IconButton 
            size="small" 
            color="inherit" 
            onClick={() => setErrorMessage(null)}
          >
            <Icon>close</Icon>
          </IconButton>
        </Paper>
      )}
      
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          component={Link}
          href={`/scheduled-messages/create?patientId=${patientId}`}
          variant="contained"
          startIcon={<AddIcon />}
        >
          Add Message
        </Button>
      </Box>
      
      <Box>
        {scheduledMessages.map((message) => (
          <Paper 
            key={message.id}
            sx={{ 
              mb: 2, 
              p: 2, 
              borderLeft: 3, 
              borderColor: message.status === 'pending' ? 'warning.main' : 
                           message.status === 'sent' ? 'success.main' : 
                           message.status === 'failed' ? 'error.main' : 'grey.400'
            }}
          >
            <Grid container spacing={2}>
              <Grid item>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  {getPlatformIcon(message.platform)}
                </Avatar>
              </Grid>
              <Grid item xs>
                <Typography variant="subtitle1" fontWeight="medium">
                  {message.message_content?.length > 50 ? message.message_content.substring(0, 50) + '...' : message.message_content}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Scheduled for: {new Date(message.scheduled_time).toLocaleString()}
                </Typography>
                {message.recurrence_pattern && (
                  <Typography variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center' }}>
                    <RepeatIcon fontSize="small" sx={{ mr: 0.5 }} />
                    Repeats: {message.recurrence_pattern}
                  </Typography>
                )}
              </Grid>
              <Grid item>
                <Chip 
                  label={message.status}
                  color={
                    message.status === 'pending' ? 'warning' : 
                    message.status === 'sent' ? 'success' : 
                    message.status === 'failed' ? 'error' : 'default'
                  }
                  size="small"
                />
              </Grid>
            </Grid>
          </Paper>
        ))}
      </Box>
    </Box>
  );
}

export default function PatientDetailPage() {
  const router = useRouter();
  const params = useParams();
  const patientId = params.id as string;
  
  const [patient, setPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    async function loadPatient() {
      try {
        setLoading(true);
        console.log(`Attempting to fetch patient with ID: ${patientId}`);
        
        // Fetch from database only - no mock data fallback
        const data = await fetchPatientById(patientId);
        
        if (data && data.name) {
          console.log(`Successfully loaded patient: ${data.name}`);
          setPatient(data);
        } else {
          console.log(`No patient found with ID: ${patientId}`);
          setError('Patient not found. The patient you are looking for does not exist or has been removed.');
        }
      } catch (err) {
        console.error(`Error loading patient with ID ${patientId}:`, err);
        setError('Failed to load patient data. Please try again later.');
      } finally {
        setLoading(false);
      }
    }

    loadPatient();
  }, [patientId]);

  const handleChangeTab = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleBack = () => {
    router.push('/patients');
  };

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ py: 6 }}>
          <Skeleton variant="text" width={300} height={40} />
          <Skeleton variant="text" width={200} />
          <Box sx={{ mt: 4 }}>
            <Skeleton variant="rectangular" height={200} />
          </Box>
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 6 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Link
            href="/patients"
            style={{
              display: 'flex',
              alignItems: 'center',
              color: 'inherit',
              textDecoration: 'none',
              marginRight: '8px'
            }}
          >
            <ArrowBackIcon sx={{ fontSize: 18, mr: 0.5 }} />
            Back to Patients
          </Link>
        </Box>
        
        <Paper sx={{ p: 4, textAlign: 'center', maxWidth: 600, mx: 'auto', mt: 6 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Patient Not Found
          </Typography>
          
          <Typography color="text.secondary" paragraph>
            {error}
          </Typography>
          
          <Button 
            variant="contained" 
            startIcon={<ArrowBackIcon />} 
            onClick={handleBack}
            sx={{ mt: 2 }}
          >
            Return to Patient List
          </Button>
        </Paper>
      </Container>
    );
  }

  if (!patient) {
    return (
      <Container maxWidth="lg" sx={{ py: 6 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Link
            href="/patients"
            style={{
              display: 'flex',
              alignItems: 'center',
              color: 'inherit',
              textDecoration: 'none',
              marginRight: '8px'
            }}
          >
            <ArrowBackIcon sx={{ fontSize: 18, mr: 0.5 }} />
            Back to Patients
          </Link>
        </Box>
        
        <Paper sx={{ p: 4, textAlign: 'center', maxWidth: 600, mx: 'auto', mt: 6 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Patient Not Found
          </Typography>
          
          <Typography color="text.secondary" paragraph>
            The patient you are looking for does not exist or has been removed.
          </Typography>
          
          <Button 
            variant="contained" 
            startIcon={<ArrowBackIcon />} 
            onClick={handleBack}
            sx={{ mt: 2 }}
          >
            Return to Patient List
          </Button>
        </Paper>
      </Container>
    );
  }

  if (!loading && patient) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ py: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Button 
              startIcon={<ArrowBackIcon />} 
              onClick={handleBack}
              sx={{ mr: 2 }}
            >
              Back to Patients
            </Button>
            <Breadcrumbs aria-label="breadcrumb">
              <Link href="/">
                <Typography 
                  color="inherit" 
                  sx={{ 
                    display: 'flex', 
                    alignItems: 'center',
                    textDecoration: 'none',
                    '&:hover': { textDecoration: 'underline' }
                  }}
                >
                  <HomeIcon sx={{ mr: 0.5 }} fontSize="inherit" />
                  Home
                </Typography>
              </Link>
              <Link href="/patients">
                <Typography 
                  color="inherit"
                  sx={{ 
                    display: 'flex', 
                    alignItems: 'center',
                    textDecoration: 'none',
                    '&:hover': { textDecoration: 'underline' }
                  }}
                >
                  <PersonIcon sx={{ mr: 0.5 }} fontSize="inherit" />
                  Patients
                </Typography>
              </Link>
              <Typography color="text.primary" sx={{ display: 'flex', alignItems: 'center' }}>
                {patient?.name || 'Patient Details'}
              </Typography>
            </Breadcrumbs>
          </Box>
          
          <Paper sx={{ p: 3, mb: 4 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar 
                  sx={{ 
                    width: 80, 
                    height: 80, 
                    bgcolor: 'primary.main',
                    fontSize: '2rem',
                    mr: 3
                  }}
                >
                  {patient?.name ? patient.name.charAt(0) : 'P'}
                </Avatar>
                <Box>
                  <Typography variant="h4" component="h1" gutterBottom>
                    {patient?.name || 'Unknown Patient'}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <PatientStatusIndicator status={patient?.status || 'unknown'} />
                    <Typography variant="body1" sx={{ ml: 1 }}>
                      Patient ID: {patient?.id ? patient.id.substring(0, 8) : 'Unknown'}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <EmailIcon fontSize="small" sx={{ mr: 0.5, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">
                      {patient?.platform && 
                        (patient.platform.includes('"platform":"telegram"') || 
                         patient.platform.includes('"platform": "telegram"') ||
                         patient.platform.includes('"platform":"web-ui"') ||
                         patient.platform.includes('{"platform":"web-ui"')) ? 
                        'No Email' : (patient?.email || 'No Email')}
                    </Typography>
                    {patient?.phone && (
                      <>
                        <Box component="span" sx={{ mx: 1 }}>•</Box>
                        <PhoneIcon fontSize="small" sx={{ mr: 0.5, color: 'text.secondary' }} />
                        <Typography variant="body2" color="text.secondary">
                          {patient.phone}
                        </Typography>
                      </>
                    )}
                  </Box>
                </Box>
              </Box>
              
              <Box>
                <Button 
                  variant="outlined" 
                  startIcon={<EditIcon />}
                  component={Link}
                  href={`/patients/${patient?.id}/edit`}
                  sx={{ mr: 1 }}
                >
                  Edit
                </Button>
                <Button 
                  variant="outlined" 
                  startIcon={<PrintIcon />}
                  sx={{ mr: 1 }}
                >
                  Print
                </Button>
                <Button 
                  variant="outlined" 
                  startIcon={<ShareIcon />}
                >
                  Share
                </Button>
              </Box>
            </Box>
          </Paper>
          
          {/* Patient Information Tabs */}
          <Box sx={{ width: '100%' }}>
            <Tabs 
              value={tabValue} 
              onChange={handleChangeTab}
              sx={{ 
                mb: 2,
                borderBottom: 1,
                borderColor: 'divider'
              }}
            >
              <Tab label="Overview" {...a11yProps(0)} />
              <Tab label="Medical Records" {...a11yProps(1)} />
              <Tab label="Conversations" {...a11yProps(2)} />
              <Tab label="Scheduled Messages" {...a11yProps(3)} />
            </Tabs>
            
            <TabPanel value={tabValue} index={0}>
              <Grid container spacing={3}>
                {/* Patient details card */}
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2, height: '100%' }}>
                    <Typography variant="h6" gutterBottom>
                      Patient Details
                    </Typography>
                    <Divider sx={{ mb: 2 }} />
                    
                    <List disablePadding>
                      <ListItem disablePadding sx={{ pb: 1 }}>
                        <ListItemText 
                          primary="Full Name" 
                          secondary={patient.name} 
                          primaryTypographyProps={{ color: 'text.secondary', variant: 'body2' }}
                          secondaryTypographyProps={{ color: 'text.primary', variant: 'body1' }}
                        />
                      </ListItem>
                      <ListItem disablePadding sx={{ pb: 1 }}>
                        <ListItemText 
                          primary="Patient ID" 
                          secondary={patient.id} 
                          primaryTypographyProps={{ color: 'text.secondary', variant: 'body2' }}
                          secondaryTypographyProps={{ color: 'text.primary', variant: 'body1' }}
                        />
                      </ListItem>
                      <ListItem disablePadding sx={{ pb: 1 }}>
                        <ListItemText 
                          primary="Admission Date" 
                          secondary={new Date(patient.admissionDate).toLocaleDateString()} 
                          primaryTypographyProps={{ color: 'text.secondary', variant: 'body2' }}
                          secondaryTypographyProps={{ color: 'text.primary', variant: 'body1' }}
                        />
                      </ListItem>
                    </List>
                    
                    <Divider sx={{ my: 2 }} />
                    
                    <Typography variant="subtitle2" gutterBottom>
                      Contact Information
                    </Typography>
                    
                    <Box sx={{ mt: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <EmailIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                        <Typography variant="body2">
                          {patient.platform && 
                            (patient.platform.includes('"platform":"telegram"') || 
                             patient.platform.includes('"platform": "telegram"') ||
                             patient.platform.includes('"platform":"web-ui"') ||
                             patient.platform.includes('{"platform":"web-ui"')) ? 
                            'No Email' : (patient.email || 'No Email')}
                        </Typography>
                      </Box>
                      {patient.contactNumber && (
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <PhoneIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                          <Typography variant="body2">
                            {patient.contactNumber}
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  </Paper>
                </Grid>
                
                {/* Medical Info Card */}
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2, height: '100%' }}>
                    <Typography variant="h6" gutterBottom>
                      Medical Information
                    </Typography>
                    <Divider sx={{ mb: 2 }} />
                    
                    <List disablePadding>
                      <ListItem disablePadding sx={{ pb: 1 }}>
                        <ListItemText 
                          primary="Status" 
                          secondary={<PatientStatusIndicator status={patient.status} />} 
                          primaryTypographyProps={{ color: 'text.secondary', variant: 'body2' }}
                        />
                      </ListItem>
                      <ListItem disablePadding sx={{ pb: 1 }}>
                        <ListItemText 
                          primary="Diagnosis" 
                          secondary={patient.diagnosis} 
                          primaryTypographyProps={{ color: 'text.secondary', variant: 'body2' }}
                          secondaryTypographyProps={{ color: 'text.primary', variant: 'body1' }}
                        />
                      </ListItem>
                      <ListItem disablePadding sx={{ pb: 1 }}>
                        <ListItemText 
                          primary="Last Updated" 
                          secondary={new Date(patient.updated_at || Date.now()).toLocaleDateString()} 
                          primaryTypographyProps={{ color: 'text.secondary', variant: 'body2' }}
                          secondaryTypographyProps={{ color: 'text.primary', variant: 'body1' }}
                        />
                      </ListItem>
                    </List>
                    
                    {/* Medical history section - commented out until data is available
                    {patient.medicalHistory && patient.medicalHistory.length > 0 && (
                      <>
                        <Divider sx={{ my: 2 }} />
                        <Typography variant="subtitle2" gutterBottom>
                          Medical History
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                          {patient.medicalHistory.map((item: string, index: number) => (
                            <Chip 
                              key={index} 
                              label={item} 
                              size="small" 
                              variant="outlined" 
                            />
                          ))}
                        </Box>
                      </>
                    )}
                    
                    {patient.currentMedications && patient.currentMedications.length > 0 && (
                      <>
                        <Divider sx={{ my: 2 }} />
                        <Typography variant="subtitle2" gutterBottom>
                          Current Medications
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                          {patient.currentMedications.map((item, index) => (
                            <Chip 
                              key={index} 
                              label={item} 
                              size="small" 
                              color="primary"
                              variant="outlined" 
                            />
                          ))}
                        </Box>
                      </>
                    )}
                    */}
                  </Paper>
                </Grid>
              </Grid>
            </TabPanel>
            
            <TabPanel value={tabValue} index={1}>
              <Paper sx={{ p: 3, textAlign: 'center' }}>
                <LocalHospitalIcon sx={{ fontSize: 60, color: 'primary.light', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Medical Records
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  The medical records for this patient will be displayed here.
                </Typography>
              </Paper>
            </TabPanel>
            
            <TabPanel value={tabValue} index={2}>
              <ConversationsTab patientId={patientId} />
            </TabPanel>
            
            <TabPanel value={tabValue} index={3}>
              <ScheduledMessagesTab patientId={patientId} />
            </TabPanel>
          </Box>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 8, mt: 6 }}>
        {/* Breadcrumbs navigation */}
        <Box sx={{ mb: 3, mt: 3 }}>
          <Breadcrumbs aria-label="breadcrumb">
            <Link underline="hover" color="inherit" href="/" sx={{ display: 'flex', alignItems: 'center' }}>
              <HomeIcon sx={{ mr: 0.5 }} fontSize="inherit" />
              Home
            </Link>
            <Link 
              underline="hover" 
              color="inherit" 
              href="/patients" 
              sx={{ display: 'flex', alignItems: 'center' }}
            >
              <PersonIcon sx={{ mr: 0.5 }} fontSize="inherit" />
              Patients
            </Link>
            <Typography color="text.primary">
              {patient.name}
            </Typography>
          </Breadcrumbs>
        </Box>

        {/* Patient header with key details */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={8}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar 
                  sx={{ 
                    width: 80, 
                    height: 80, 
                    bgcolor: 'primary.main',
                    mr: 2
                  }}
                >
                  {patient.name.charAt(0)}
                </Avatar>
                <Box>
                  <Typography variant="h4">
                    {patient.name}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                    <PatientStatusIndicator status={patient.status} />
                    <Typography variant="body1" color="text.secondary" sx={{ ml: 2 }}>
                      ID: {patient.id}
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', justifyContent: { xs: 'flex-start', md: 'flex-end' }, gap: 1 }}>
                <Button 
                  variant="outlined" 
                  startIcon={<ArrowBackIcon />} 
                  onClick={handleBack}
                >
                  Back
                </Button>
                <Button 
                  variant="outlined" 
                  startIcon={<PrintIcon />}
                >
                  Print
                </Button>
                <Button 
                  variant="contained" 
                  startIcon={<EditIcon />}
                  onClick={() => router.push(`/patients/${patient.id}/edit`)}
                >
                  Edit
                </Button>
              </Box>
            </Grid>
          </Grid>
        </Paper>
        
        {/* Patient Information Tabs */}
        <Box sx={{ width: '100%' }}>
          <Tabs 
            value={tabValue} 
            onChange={handleChangeTab}
            sx={{ 
              mb: 2,
              borderBottom: 1,
              borderColor: 'divider'
            }}
          >
            <Tab label="Overview" {...a11yProps(0)} />
            <Tab label="Medical Records" {...a11yProps(1)} />
            <Tab label="Conversations" {...a11yProps(2)} />
            <Tab label="Scheduled Messages" {...a11yProps(3)} />
          </Tabs>
          
          <TabPanel value={tabValue} index={0}>
            <Grid container spacing={3}>
              {/* Patient details card */}
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2, height: '100%' }}>
                  <Typography variant="h6" gutterBottom>
                    Patient Details
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  
                  <List disablePadding>
                    <ListItem disablePadding sx={{ pb: 1 }}>
                      <ListItemText 
                        primary="Full Name" 
                        secondary={patient.name} 
                        primaryTypographyProps={{ color: 'text.secondary', variant: 'body2' }}
                        secondaryTypographyProps={{ color: 'text.primary', variant: 'body1' }}
                      />
                    </ListItem>
                    <ListItem disablePadding sx={{ pb: 1 }}>
                      <ListItemText 
                        primary="Patient ID" 
                        secondary={patient.id} 
                        primaryTypographyProps={{ color: 'text.secondary', variant: 'body2' }}
                        secondaryTypographyProps={{ color: 'text.primary', variant: 'body1' }}
                      />
                    </ListItem>
                    <ListItem disablePadding sx={{ pb: 1 }}>
                      <ListItemText 
                        primary="Admission Date" 
                        secondary={new Date(patient.admissionDate).toLocaleDateString()} 
                        primaryTypographyProps={{ color: 'text.secondary', variant: 'body2' }}
                        secondaryTypographyProps={{ color: 'text.primary', variant: 'body1' }}
                      />
                    </ListItem>
                  </List>
                  
                  <Divider sx={{ my: 2 }} />
                  
                  <Typography variant="subtitle2" gutterBottom>
                    Contact Information
                  </Typography>
                  
                  <Box sx={{ mt: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <EmailIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                      <Typography variant="body2">
                        {patient.platform && 
                          (patient.platform.includes('"platform":"telegram"') || 
                           patient.platform.includes('"platform": "telegram"') ||
                           patient.platform.includes('"platform":"web-ui"') ||
                           patient.platform.includes('{"platform":"web-ui"')) ? 
                          'No Email' : (patient.email || 'No Email')}
                      </Typography>
                    </Box>
                    {patient.contactNumber && (
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <PhoneIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                        <Typography variant="body2">
                          {patient.contactNumber}
                        </Typography>
                      </Box>
                    )}
                  </Box>
                </Paper>
              </Grid>
              
              {/* Medical Info Card */}
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2, height: '100%' }}>
                  <Typography variant="h6" gutterBottom>
                    Medical Information
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  
                  <List disablePadding>
                    <ListItem disablePadding sx={{ pb: 1 }}>
                      <ListItemText 
                        primary="Status" 
                        secondary={<PatientStatusIndicator status={patient.status} />} 
                        primaryTypographyProps={{ color: 'text.secondary', variant: 'body2' }}
                      />
                    </ListItem>
                    <ListItem disablePadding sx={{ pb: 1 }}>
                      <ListItemText 
                        primary="Diagnosis" 
                        secondary={patient.diagnosis} 
                        primaryTypographyProps={{ color: 'text.secondary', variant: 'body2' }}
                        secondaryTypographyProps={{ color: 'text.primary', variant: 'body1' }}
                      />
                    </ListItem>
                    <ListItem disablePadding sx={{ pb: 1 }}>
                      <ListItemText 
                        primary="Last Updated" 
                        secondary={new Date(patient.updated_at || Date.now()).toLocaleDateString()} 
                        primaryTypographyProps={{ color: 'text.secondary', variant: 'body2' }}
                        secondaryTypographyProps={{ color: 'text.primary', variant: 'body1' }}
                      />
                    </ListItem>
                  </List>
                  
                  {/* Medical history section - commented out until data is available
                  {patient.medicalHistory && patient.medicalHistory.length > 0 && (
                    <>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="subtitle2" gutterBottom>
                        Medical History
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                        {patient.medicalHistory.map((item: string, index: number) => (
                          <Chip 
                            key={index} 
                            label={item} 
                            size="small" 
                            variant="outlined" 
                          />
                        ))}
                      </Box>
                    </>
                  )}
                  
                  {patient.currentMedications && patient.currentMedications.length > 0 && (
                    <>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="subtitle2" gutterBottom>
                        Current Medications
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                        {patient.currentMedications.map((item, index) => (
                          <Chip 
                            key={index} 
                            label={item} 
                            size="small" 
                            color="primary"
                            variant="outlined" 
                          />
                        ))}
                      </Box>
                    </>
                  )}
                  */}
                </Paper>
              </Grid>
            </Grid>
          </TabPanel>
          
          <TabPanel value={tabValue} index={1}>
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <LocalHospitalIcon sx={{ fontSize: 60, color: 'primary.light', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Medical Records
              </Typography>
              <Typography variant="body1" color="text.secondary">
                The medical records for this patient will be displayed here.
              </Typography>
            </Paper>
          </TabPanel>
          
          <TabPanel value={tabValue} index={2}>
            <ConversationsTab patientId={patientId} />
          </TabPanel>
          
          <TabPanel value={tabValue} index={3}>
            <ScheduledMessagesTab patientId={patientId} />
          </TabPanel>
        </Box>
      </Box>
    </Container>
  );
} 