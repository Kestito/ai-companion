'use client';

import { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Button, 
  FormControl, 
  InputLabel, 
  MenuItem, 
  Select,
  SelectChangeEvent,
  TextField,
  CircularProgress,
  Alert,
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  Divider,
  Chip
} from '@mui/material';
import { 
  ArrowBack,
  AssessmentOutlined,
  Check,
  Chat
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';
import PageHeader from '@/components/common/PageHeader';

export default function CreateRiskAssessmentPage() {
  const router = useRouter();
  const supabase = createClientComponentClient();
  
  // State
  const [patients, setPatients] = useState<{
    id: string;
    first_name: string;
    last_name: string;
    email: string | null;
    phone: string | null;
  }[]>([]);
  const [conversations, setConversations] = useState<any[]>([]);
  const [selectedPatient, setSelectedPatient] = useState('');
  const [selectedConversations, setSelectedConversations] = useState<string[]>([]);
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [patientLoading, setPatientLoading] = useState(true);
  const [error, setError] = useState('');
  const [assessmentResult, setAssessmentResult] = useState<any>(null);
  
  // Steps in the process
  const steps = [
    'Select Patient', 
    'Select Conversations', 
    'Generate Assessment'
  ];
  
  // Load patients on initial page load
  useEffect(() => {
    const loadPatients = async () => {
      setPatientLoading(true);
      
      try {
        const { data, error } = await supabase
          .from('patients')
          .select('id, first_name, last_name, email, phone')
          .order('last_name', { ascending: true });
        
        if (error) throw error;
        setPatients(data || []);
      } catch (err) {
        console.error('Error loading patients:', err);
        setError('Failed to load patients. Please try again.');
      } finally {
        setPatientLoading(false);
      }
    };
    
    loadPatients();
  }, []);
  
  // Load patient conversations when a patient is selected
  useEffect(() => {
    const loadConversations = async () => {
      if (!selectedPatient) return;
      
      setLoading(true);
      setError('');
      
      try {
        const { data, error } = await supabase
          .from('conversations')
          .select('*')
          .eq('patient_id', selectedPatient)
          .order('start_time', { ascending: false })
          .limit(10);
        
        if (error) throw error;
        setConversations(data || []);
      } catch (err) {
        console.error('Error loading conversations:', err);
        setError('Failed to load patient conversations. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    
    loadConversations();
  }, [selectedPatient]);
  
  // Handle patient selection
  const handlePatientChange = (event: SelectChangeEvent) => {
    setSelectedPatient(event.target.value);
    setSelectedConversations([]);
  };
  
  // Handle conversation selection
  const handleConversationToggle = (conversationId: string) => {
    setSelectedConversations(prev => {
      if (prev.includes(conversationId)) {
        return prev.filter(id => id !== conversationId);
      } else {
        return [...prev, conversationId];
      }
    });
  };
  
  // Format date for display
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  // Handle next step
  const handleNext = () => {
    setActiveStep((prevStep) => prevStep + 1);
  };
  
  // Handle back step
  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };
  
  // Generate risk assessment
  const generateAssessment = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('/api/risk-assessment/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          patientId: selectedPatient,
          conversationIds: selectedConversations
        }),
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'Failed to generate assessment');
      }
      
      setAssessmentResult(result.data);
      handleNext();
    } catch (err) {
      console.error('Error generating assessment:', err);
      setError(
        err instanceof Error 
          ? err.message 
          : 'Failed to generate assessment. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };
  
  // Get color based on risk level
  const getRiskColor = (risk: string | undefined) => {
    switch (risk?.toLowerCase()) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'success';
      default:
        return 'info';
    }
  };
  
  // View assessment details
  const viewAssessment = () => {
    if (assessmentResult?.id) {
      router.push(`/risk-assessment/${assessmentResult.id}`);
    }
  };
  
  // Return to risk assessments list
  const returnToList = () => {
    router.push('/risk-assessment');
  };
  
  // Render step content
  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Box sx={{ mt: 4, maxWidth: 600 }}>
            <FormControl fullWidth sx={{ mb: 4 }}>
              <InputLabel id="patient-select-label">Select Patient</InputLabel>
              <Select
                labelId="patient-select-label"
                id="patient-select"
                value={selectedPatient}
                label="Select Patient"
                onChange={handlePatientChange}
                disabled={patientLoading}
              >
                {patients.map((patient) => (
                  <MenuItem key={patient.id} value={patient.id}>
                    {patient.first_name} {patient.last_name} ({patient.email || patient.phone})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
              <Button
                variant="contained"
                onClick={handleNext}
                disabled={!selectedPatient}
              >
                Next
              </Button>
            </Box>
          </Box>
        );
        
      case 1:
        return (
          <Box sx={{ mt: 4 }}>
            <Typography variant="h6" gutterBottom>
              Select Conversations to Analyze
            </Typography>
            
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
              </Box>
            ) : conversations.length === 0 ? (
              <Alert severity="info" sx={{ mb: 3 }}>
                No conversations found for this patient. Please select a different patient or proceed to generate an assessment based on patient profile.
              </Alert>
            ) : (
              <Box>
                <List sx={{ width: '100%', bgcolor: 'background.paper' }}>
                  {conversations.map((conversation, index) => (
                    <Box key={conversation.id}>
                      {index > 0 && <Divider />}
                      <ListItem
                        button
                        selected={selectedConversations.includes(conversation.id)}
                        onClick={() => handleConversationToggle(conversation.id)}
                        secondaryAction={
                          selectedConversations.includes(conversation.id) ? (
                            <Check color="primary" />
                          ) : null
                        }
                      >
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Chat fontSize="small" />
                              <Typography variant="body1">
                                {conversation.conversation_type} Conversation
                              </Typography>
                              <Chip 
                                label={conversation.status} 
                                size="small"
                                color={conversation.status === 'completed' ? 'success' : 'default'}
                              />
                            </Box>
                          }
                          secondary={
                            <Typography variant="body2" color="text.secondary">
                              {formatDate(conversation.start_time)}
                              {conversation.end_time && ` - ${formatDate(conversation.end_time)}`}
                            </Typography>
                          }
                        />
                      </ListItem>
                    </Box>
                  ))}
                </List>
                
                <Typography 
                  variant="body2" 
                  color="text.secondary" 
                  sx={{ mt: 2, fontStyle: 'italic' }}
                >
                  {selectedConversations.length === 0 
                    ? "No conversations selected. We'll analyze recent messages for this patient."
                    : `${selectedConversations.length} conversation(s) selected for analysis.`}
                </Typography>
              </Box>
            )}
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
              <Button onClick={handleBack}>
                Back
              </Button>
              <Button
                variant="contained"
                onClick={handleNext}
              >
                Next
              </Button>
            </Box>
          </Box>
        );
        
      case 2:
        return (
          <Box sx={{ mt: 4 }}>
            <Typography variant="h6" gutterBottom>
              Generate Risk Assessment
            </Typography>
            
            <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
              <Typography variant="body1" paragraph>
                You are about to generate a risk assessment for:
              </Typography>
              
              <Typography variant="subtitle1" fontWeight="bold">
                {patients.find(p => p.id === selectedPatient)?.first_name || ''} {patients.find(p => p.id === selectedPatient)?.last_name || ''}
              </Typography>
              
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Based on {selectedConversations.length} selected conversation(s)
              </Typography>
              
              <Typography variant="body2" sx={{ mt: 3, mb: 2, fontStyle: 'italic' }}>
                The system will analyze the conversation content to assess risk factors and provide recommendations.
              </Typography>
              
              <Button
                variant="contained"
                color="primary"
                onClick={generateAssessment}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <AssessmentOutlined />}
                fullWidth
                sx={{ mt: 2 }}
              >
                {loading ? 'Generating Assessment...' : 'Generate Assessment'}
              </Button>
            </Paper>
            
            {error && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {error}
              </Alert>
            )}
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
              <Button onClick={handleBack}>
                Back
              </Button>
            </Box>
          </Box>
        );
        
      case 3:
        return (
          <Box sx={{ mt: 4 }}>
            <Alert severity="success" sx={{ mb: 4 }}>
              Risk assessment has been generated successfully!
            </Alert>
            
            <Card elevation={3}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Assessment Results
                </Typography>
                
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Typography variant="subtitle1" sx={{ mr: 2 }}>
                    Risk Level:
                  </Typography>
                  <Chip 
                    label={assessmentResult?.risk_level?.toUpperCase() || 'UNKNOWN'} 
                    color={getRiskColor(assessmentResult?.risk_level)}
                  />
                </Box>
                
                <Typography variant="subtitle1" gutterBottom>
                  Risk Factors:
                </Typography>
                
                <List dense>
                  {assessmentResult?.risk_factors?.map((factor: string, index: number) => (
                    <ListItem key={index}>
                      <ListItemText primary={factor} />
                    </ListItem>
                  ))}
                </List>
                
                <Divider sx={{ my: 2 }} />
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
                  <Button 
                    variant="outlined"
                    onClick={returnToList}
                    startIcon={<ArrowBack />}
                  >
                    Back to List
                  </Button>
                  
                  <Button
                    variant="contained"
                    onClick={viewAssessment}
                  >
                    View Full Details
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Box>
        );
        
      default:
        return 'Unknown step';
    }
  };
  
  return (
    <Box sx={{ p: 3, maxWidth: '1000px', margin: '0 auto' }}>
      <PageHeader
        title="Create Risk Assessment"
        subtitle="Generate a new patient risk assessment based on conversation analysis"
      />
      
      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>
      
      <Paper elevation={2} sx={{ p: 3 }}>
        {getStepContent(activeStep)}
      </Paper>
    </Box>
  );
} 