'use client';

import { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Button, 
  Card,
  CardContent,
  CardHeader,
  Grid,
  Chip,
  Divider,
  IconButton,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Tab,
  Tabs
} from '@mui/material';
import {
  KeyboardBackspace,
  Schedule,
  Person,
  Flag,
  Warning,
  Info,
  ArrowForward,
  Download,
  Edit
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';
import PageHeader from '@/components/common/PageHeader';

// Helper to get color based on risk level
const getRiskColor = (risk: string) => {
  switch (risk?.toLowerCase()) {
    case 'high':
      return 'error';
    case 'medium':
      return 'warning';
    case 'low':
      return 'success';
    default:
      return 'default';
  }
};

// Format date for display
const formatDate = (dateString: string) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};

export default function RiskAssessmentDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const supabase = createClientComponentClient();
  
  const [assessment, setAssessment] = useState<any>(null);
  const [patient, setPatient] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tabValue, setTabValue] = useState(0);
  
  // Load risk assessment
  useEffect(() => {
    const loadAssessment = async () => {
      setLoading(true);
      setError('');
      
      try {
        // Get risk assessment data
        const { data, error } = await supabase
          .from('patient_risk_reports')
          .select(`
            *,
            patients (
              id,
              first_name,
              last_name,
              email,
              phone,
              risk
            )
          `)
          .eq('id', params.id)
          .single();
        
        if (error) throw error;
        
        if (data) {
          setAssessment(data);
          setPatient(data.patients);
        } else {
          setError('Risk assessment not found');
        }
      } catch (err) {
        console.error('Error loading risk assessment:', err);
        setError('Failed to load risk assessment. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    
    loadAssessment();
  }, [params.id]);
  
  // Handle tab change
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };
  
  // Navigate back to list
  const goBack = () => {
    router.push('/risk-assessment');
  };
  
  // Handle editing
  const handleEdit = () => {
    router.push(`/risk-assessment/edit/${params.id}`);
  };
  
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }
  
  if (error) {
    return (
      <Box sx={{ p: 3, maxWidth: '800px', margin: '0 auto' }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
        <Button startIcon={<KeyboardBackspace />} onClick={goBack}>
          Back to Risk Assessments
        </Button>
      </Box>
    );
  }
  
  return (
    <Box sx={{ p: 3, maxWidth: '1000px', margin: '0 auto' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <Button startIcon={<KeyboardBackspace />} onClick={goBack} sx={{ mr: 2 }}>
          Back
        </Button>
        <PageHeader
          title="Risk Assessment Details"
          subtitle={`For patient ${patient?.first_name} ${patient?.last_name}`}
        />
      </Box>
      
      <Grid container spacing={3}>
        {/* Summary Card */}
        <Grid item xs={12}>
          <Card elevation={2}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography variant="h6" sx={{ mr: 2 }}>
                    Risk Assessment Summary
                  </Typography>
                  <Chip 
                    label={assessment?.risk_level?.toUpperCase() || 'UNKNOWN'} 
                    color={getRiskColor(assessment?.risk_level)}
                    sx={{ fontWeight: 'bold' }}
                  />
                </Box>
                <Box>
                  <IconButton size="small" onClick={handleEdit} sx={{ mr: 1 }}>
                    <Edit fontSize="small" />
                  </IconButton>
                  <IconButton size="small">
                    <Download fontSize="small" />
                  </IconButton>
                </Box>
              </Box>
              
              <Divider sx={{ mb: 2 }} />
              
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Person fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">
                      Patient
                    </Typography>
                  </Box>
                  <Typography variant="body1">
                    {patient?.first_name} {patient?.last_name}
                  </Typography>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Schedule fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">
                      Assessment Date
                    </Typography>
                  </Box>
                  <Typography variant="body1">
                    {formatDate(assessment?.assessment_date)}
                  </Typography>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Flag fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">
                      Status
                    </Typography>
                  </Box>
                  <Chip 
                    label={assessment?.status?.toUpperCase() || 'ACTIVE'} 
                    color={assessment?.status === 'active' ? 'primary' : 'default'}
                    size="small"
                  />
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <ArrowForward fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">
                      Follow-up Date
                    </Typography>
                  </Box>
                  <Typography variant="body1">
                    {formatDate(assessment?.follow_up_date)}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Detailed Info */}
        <Grid item xs={12}>
          <Paper elevation={2} sx={{ p: 0 }}>
            <Tabs
              value={tabValue}
              onChange={handleTabChange}
              variant="fullWidth"
              textColor="primary"
              indicatorColor="primary"
            >
              <Tab label="Risk Factors" />
              <Tab label="Action Items" />
              <Tab label="Assessment Details" />
            </Tabs>
            
            <Box sx={{ p: 3 }}>
              {/* Risk Factors Tab */}
              {tabValue === 0 && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Identified Risk Factors
                  </Typography>
                  
                  {assessment?.risk_factors?.length > 0 ? (
                    <List>
                      {assessment.risk_factors.map((factor: string, index: number) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <Warning color={getRiskColor(assessment.risk_level)} />
                          </ListItemIcon>
                          <ListItemText primary={factor} />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body1" color="text.secondary">
                      No risk factors identified
                    </Typography>
                  )}
                </Box>
              )}
              
              {/* Action Items Tab */}
              {tabValue === 1 && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Recommended Actions
                  </Typography>
                  
                  {assessment?.action_items?.length > 0 ? (
                    <List>
                      {assessment.action_items.map((action: any, index: number) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <Info color="primary" />
                          </ListItemIcon>
                          <ListItemText 
                            primary={action.title} 
                            secondary={action.description} 
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body1" color="text.secondary">
                      No action items recommended
                    </Typography>
                  )}
                </Box>
              )}
              
              {/* Assessment Details Tab */}
              {tabValue === 2 && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Detailed Assessment
                  </Typography>
                  
                  {assessment?.assessment_details && Object.keys(assessment.assessment_details).length > 0 ? (
                    <Box>
                      {Object.entries(assessment.assessment_details).map(([key, value]: [string, any]) => (
                        <Box key={key} sx={{ mb: 3 }}>
                          <Typography variant="subtitle1" gutterBottom sx={{ textTransform: 'capitalize' }}>
                            {key.replace(/_/g, ' ')}
                          </Typography>
                          <Typography variant="body1">
                            {typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
                          </Typography>
                        </Box>
                      ))}
                    </Box>
                  ) : (
                    <Typography variant="body1" color="text.secondary">
                      No detailed assessment information available
                    </Typography>
                  )}
                </Box>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
} 