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
  ArrowDropDown as ArrowDropDownIcon
} from '@mui/icons-material';
import { useParams, useRouter } from 'next/navigation';
import { PatientStatusIndicator } from '@/components/patients/patientstatusindicator';
import { Patient } from '@/lib/supabase/types';
import { 
  fetchPatientById, 
  fetchPatientConversations, 
  fetchConversationMessages, 
  fetchPatientRiskAssessments,
  fetchPatientAppointments
} from '@/lib/supabase/patientService';

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
 * Component to display conversation messages
 */
function ConversationMessages({ conversationId }: { conversationId: string }) {
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadMessages = async () => {
      try {
        setLoading(true);
        const data = await fetchConversationMessages(conversationId);
        setMessages(data);
      } catch (err) {
        console.error('Error loading messages:', err);
      } finally {
        setLoading(false);
      }
    };
    
    loadMessages();
  }, [conversationId]);
  
  if (loading) return <Skeleton variant="rectangular" height={200} />;
  
  if (messages.length === 0) {
    return <Typography>No messages found for this conversation.</Typography>;
  }
  
  return (
    <Paper sx={{ p: 2, mb: 2, maxHeight: 300, overflow: 'auto' }}>
      {messages.map((message) => (
        <Box 
          key={message.id} 
          sx={{
            py: 1,
            px: 2,
            mb: 1,
            borderRadius: 2,
            backgroundColor: message.sender === 'user' ? 'primary.light' : 'secondary.light',
            color: message.sender === 'user' ? 'primary.contrastText' : 'secondary.contrastText',
            alignSelf: message.sender === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: '80%',
            position: 'relative',
            ml: message.sender === 'user' ? 'auto' : 0
          }}
        >
          <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
            {message.sender === 'user' ? 'Patient' : 'Evelina AI'}
          </Typography>
          <Typography variant="body1">{message.message_content}</Typography>
          <Typography variant="caption" sx={{ display: 'block', textAlign: 'right', mt: 1 }}>
            {new Date(message.sent_at).toLocaleString()}
          </Typography>
        </Box>
      ))}
    </Paper>
  );
}

/**
 * Component to display all conversations for a patient
 */
function ConversationsTab({ patientId }: { patientId: string }) {
  const [conversations, setConversations] = useState<any[]>([]);
  const [expandedConversation, setExpandedConversation] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadConversations = async () => {
      try {
        setLoading(true);
        const data = await fetchPatientConversations(patientId);
        setConversations(data);
      } catch (err) {
        console.error('Error loading conversations:', err);
      } finally {
        setLoading(false);
      }
    };
    
    loadConversations();
  }, [patientId]);
  
  const handleExpandConversation = (conversationId: string) => {
    if (expandedConversation === conversationId) {
      setExpandedConversation(null);
    } else {
      setExpandedConversation(conversationId);
    }
  };
  
  const getPlatformIcon = (platform: string) => {
    switch (platform.toLowerCase()) {
      case 'whatsapp':
        return <Icon className="fa-brands fa-whatsapp" sx={{ color: '#25D366' }} />;
      case 'telegram':
        return <Icon className="fa-brands fa-telegram" sx={{ color: '#0088cc' }} />;
      case 'chainlit':
        return <Icon className="fa-solid fa-comments" />;
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
  
  if (conversations.length === 0) {
    return (
      <Box sx={{ pt: 2, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary">No conversations found</Typography>
      </Box>
    );
  }
  
  return (
    <Box sx={{ pt: 2 }}>
      <Typography variant="h6" gutterBottom>Patient Conversations</Typography>
      
      {conversations.map((conversation) => (
        <Paper key={conversation.id} sx={{ mb: 2, overflow: 'hidden' }}>
          <Box 
            sx={{
              p: 2,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              cursor: 'pointer',
              '&:hover': { bgcolor: 'action.hover' }
            }}
            onClick={() => handleExpandConversation(conversation.id)}
          >
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              {getPlatformIcon(conversation.platform)}
              <Box sx={{ ml: 2 }}>
                <Typography variant="subtitle1">
                  {conversation.platform.charAt(0).toUpperCase() + conversation.platform.slice(1)} Conversation
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Started: {new Date(conversation.start_time).toLocaleString()}
                </Typography>
              </Box>
            </Box>
            <Box>
              <Chip 
                label={conversation.status} 
                color={conversation.status === 'active' ? 'success' : 'default'}
                size="small"
              />
              <IconButton size="small" sx={{ ml: 1 }}>
                {expandedConversation === conversation.id ? 
                  <ArrowDropUpIcon /> : <ArrowDropDownIcon />
                }
              </IconButton>
            </Box>
          </Box>
          
          {expandedConversation === conversation.id && (
            <Box sx={{ px: 2, pb: 2 }}>
              <Divider sx={{ mb: 2 }} />
              <ConversationMessages conversationId={conversation.id} />
            </Box>
          )}
        </Paper>
      ))}
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
        const data = await fetchPatientById(patientId);
        
        if (data) {
          setPatient(data);
        } else {
          // If patient not found in Supabase, try to use mock data as fallback
          import('@/lib/mockData').then(({ mockPatients }) => {
            const mockPatient = mockPatients.find(p => p.id === patientId);
            if (mockPatient) {
              setPatient(mockPatient);
            } else {
              setError('Patient not found.');
            }
          });
        }
      } catch (err) {
        console.error(`Error loading patient with ID ${patientId}:`, err);
        setError('Failed to load patient data. Please try again later.');
        
        // Try to fall back to mock data
        import('@/lib/mockData').then(({ mockPatients }) => {
          const mockPatient = mockPatients.find(p => p.id === patientId);
          if (mockPatient) {
            setPatient(mockPatient);
          }
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
        </Box>
      </Box>
    </Container>
  );
} 