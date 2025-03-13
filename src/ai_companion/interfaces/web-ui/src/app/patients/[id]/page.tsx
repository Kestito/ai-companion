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
import { scheduledChecksService } from '@/lib/api';
import ScheduledCheckForm, { ScheduledCheckFormData } from '@/components/patients/scheduledcheckform';
import { ConversationsTab } from '@/components/patients/conversationstab';

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
  
  const loadScheduledChecks = async () => {
    try {
      setLoading(true);
      // Fetch scheduled checks from the API
      const data = await scheduledChecksService.fetchScheduledChecks(patientId);
      setScheduledChecks(data);
    } catch (err) {
      console.error('Error loading scheduled checks:', err);
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
      await scheduledChecksService.createScheduledCheck({
        title: formData.title,
        description: formData.description,
        frequency: formData.frequency,
        nextScheduled: formData.nextScheduled.toISOString(),
        platform: formData.platform,
        patientId: formData.patientId
      });
      setShowForm(false);
      // Reload the scheduled checks
      await loadScheduledChecks();
    } catch (err) {
      console.error('Error creating scheduled check:', err);
      alert('Failed to create scheduled check. Please try again.');
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
        <Typography variant="h6" color="text.secondary">No scheduled checks found</Typography>
        <Button 
          variant="contained" 
          startIcon={<AddIcon />} 
          sx={{ mt: 2 }}
          onClick={() => setShowForm(true)}
        >
          Add Scheduled Check
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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6">Scheduled Health Checks</Typography>
        <Button 
          variant="contained" 
          startIcon={<AddIcon />}
          onClick={() => setShowForm(true)}
        >
          Add Check
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

export default function PatientDetailPage() {
  const router = useRouter();
  const params = useParams();
  const patientId = params.id as string;
  
  const [patient, setPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);

  useEffect(() => {
    async function loadPatient() {
      try {
        setLoading(true);
        console.log(`Attempting to fetch patient with ID: ${patientId}`);
        
        const data = await fetchPatientById(patientId);
        
        if (data) {
          console.log(`Successfully loaded patient: ${data.name}`);
          setPatient(data);
        } else {
          console.log(`No patient found with ID: ${patientId}, trying mock data`);
          // If patient not found in Supabase, try to use mock data as fallback
          import('@/lib/mockData').then(({ mockPatients }) => {
            const mockPatient = mockPatients.find(p => p.id === patientId);
            if (mockPatient) {
              console.log(`Found mock patient: ${mockPatient.name}`);
              setPatient(mockPatient);
            } else {
              console.log(`No mock patient found with ID: ${patientId}`);
              setError('Patient not found.');
            }
          }).catch(err => {
            console.error('Error loading mock data:', err);
            setError('Patient not found and mock data unavailable.');
          });
        }
      } catch (err) {
        console.error(`Error loading patient with ID ${patientId}:`, err);
        setError('Failed to load patient data. Please try again later.');
        
        // Try to fall back to mock data
        import('@/lib/mockData').then(({ mockPatients }) => {
          const mockPatient = mockPatients.find(p => p.id === patientId);
          if (mockPatient) {
            console.log(`Found mock patient after error: ${mockPatient.name}`);
            setPatient(mockPatient);
          }
        }).catch(mockErr => {
          console.error('Error loading mock data after fetch error:', mockErr);
        });
      } finally {
        setLoading(false);
      }
    }

    loadPatient();
  }, [patientId]);

  const handleChangeTab = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
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

  if (!patient) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ py: 6 }}>
          <Button startIcon={<ArrowBackIcon />} onClick={handleBack}>
            Back to Patients
          </Button>
          <Box sx={{ my: 4, textAlign: 'center' }}>
            <Typography variant="h5" gutterBottom>
              Patient Not Found
            </Typography>
            <Typography variant="body1" color="text.secondary">
              The patient you are looking for does not exist or has been removed.
            </Typography>
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
                    <Typography variant="body1" color="text.secondary" sx={{ ml: 2 }}>
                      {patient.age} years, {patient.gender ? (patient.gender.charAt(0).toUpperCase() + patient.gender.slice(1)) : 'Not specified'}
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
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs 
              value={activeTab} 
              onChange={handleChangeTab} 
              aria-label="patient tabs"
              variant="scrollable"
              scrollButtons="auto"
            >
              <Tab label="Overview" {...a11yProps(0)} />
              <Tab label="Medical Records" {...a11yProps(1)} />
              <Tab label="Conversations" {...a11yProps(2)} />
              <Tab label="Scheduled Checks" {...a11yProps(3)} />
            </Tabs>
          </Box>
          
          {/* Overview Tab */}
          <TabPanel value={activeTab} index={0}>
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
                        primary="Age & Gender" 
                        secondary={`${patient.age} years, ${patient.gender ? (patient.gender.charAt(0).toUpperCase() + patient.gender.slice(1)) : 'Not specified'}`} 
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
                    <ListItem disablePadding sx={{ pb: 1 }}>
                      <ListItemText 
                        primary="Room Number" 
                        secondary={patient.roomNumber || 'Not assigned'} 
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
                        {patient.email}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <PhoneIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                      <Typography variant="body2">
                        {patient.contactNumber}
                      </Typography>
                    </Box>
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
                        primary="Doctor" 
                        secondary={patient.doctor} 
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
          
          {/* Other tabs would be implemented similarly */}
          <TabPanel value={activeTab} index={1}>
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
          
          <TabPanel value={activeTab} index={2}>
            <ConversationsTab patientId={patientId} />
          </TabPanel>
          
          <TabPanel value={activeTab} index={3}>
            <ScheduledChecksTab patientId={patientId} />
          </TabPanel>
        </Box>
      </Box>
    </Container>
  );
} 