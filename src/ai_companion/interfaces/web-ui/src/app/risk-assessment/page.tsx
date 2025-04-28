'use client';

import { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Button, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Chip,
  IconButton,
  CircularProgress,
  Alert,
  Container,
  Grid,
  Link as MuiLink
} from '@mui/material';
import { 
  Refresh, 
  Info, 
  Download,
  Add,
  Home as HomeIcon,
  Warning
} from '@mui/icons-material';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';

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
      return 'info';
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

export default function RiskAssessmentPage() {
  const router = useRouter();
  const supabase = createClientComponentClient({
    supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://aubulhjfeszmsheonmpy.supabase.co',
    supabaseKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc'
  });
  
  // Define the type for assessment objects
  type Assessment = {
    id: string;
    assessment_date: string;
    risk_level: string;
    follow_up_date: string;
    status: string;
    patients: {
      id: string;
      first_name: string;
      last_name: string;
    };
    [key: string]: any; // For any additional properties
  };
  
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Load risk assessments
  const loadAssessments = async () => {
    setLoading(true);
    setError('');
    
    try {
      const { data, error } = await supabase
        .from('patient_risk_reports')
        .select(`
          *,
          patients (
            id,
            first_name,
            last_name
          )
        `)
        .order('assessment_date', { ascending: false });
      
      if (error) throw error;
      setAssessments(data || []);
    } catch (err) {
      console.error('Error loading risk assessments:', err);
      setError('Failed to load risk assessments. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  // Load on initial page load
  useEffect(() => {
    loadAssessments();
  }, []);
  
  // Navigate to detailed assessment view
  const viewAssessment = (id: string) => {
    router.push(`/risk-assessment/${id}`);
  };
  
  // Navigate to create assessment page
  const createAssessment = () => {
    router.push('/risk-assessment/create');
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
            <Typography color="text.primary">Risk Assessment</Typography>
          </Box>
          
          <Typography variant="h4" component="h1" sx={{ mt: 3, mb: 2 }}>
            Patient Risk Assessments
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
            <Typography color="text.primary">Risk Assessment</Typography>
          </Box>
          
          <Typography variant="h4" component="h1" sx={{ mt: 3, mb: 2 }}>
            Patient Risk Assessments
          </Typography>
        </Box>
        
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="subtitle1" fontWeight="bold">Error loading risk assessments</Typography>
          <Typography variant="body2">{error}</Typography>
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
          <Typography color="text.primary">Risk Assessment</Typography>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 3 }}>
          <Typography variant="h4" component="h1" sx={{ mb: 2 }}>
            Patient Risk Assessments
          </Typography>
          
          <Button 
            variant="contained" 
            color="primary" 
            startIcon={<Add />}
            onClick={createAssessment}
          >
            Create Assessment
          </Button>
        </Box>
        <Typography variant="body1" color="text.secondary" paragraph sx={{ mb: 4 }}>
          View and manage patient risk assessments generated from conversations.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          {assessments.length === 0 ? (
            <Paper sx={{ textAlign: 'center', py: 5, px: 2 }}>
              <Typography color="text.secondary" sx={{ mb: 2 }}>
                No risk assessments found. Create your first assessment to get started.
              </Typography>
              <Button 
                variant="outlined" 
                color="primary" 
                startIcon={<Add />}
                onClick={createAssessment}
                sx={{ mt: 2 }}
              >
                Create Assessment
              </Button>
            </Paper>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell><Typography variant="subtitle2">Patient</Typography></TableCell>
                    <TableCell><Typography variant="subtitle2">Assessment Date</Typography></TableCell>
                    <TableCell><Typography variant="subtitle2">Risk Level</Typography></TableCell>
                    <TableCell><Typography variant="subtitle2">Follow-up Date</Typography></TableCell>
                    <TableCell><Typography variant="subtitle2">Status</Typography></TableCell>
                    <TableCell align="right"><Typography variant="subtitle2">Actions</Typography></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {assessments.map((assessment) => (
                    <TableRow 
                      key={assessment.id}
                      hover
                      sx={{ '&:hover': { cursor: 'pointer' } }}
                      onClick={() => viewAssessment(assessment.id)}
                    >
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Typography variant="body2" fontWeight="medium">
                            {assessment.patients?.first_name} {assessment.patients?.last_name}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>{formatDate(assessment.assessment_date)}</TableCell>
                      <TableCell>
                        <Chip 
                          label={assessment.risk_level.toUpperCase()}
                          color={getRiskColor(assessment.risk_level)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{formatDate(assessment.follow_up_date)}</TableCell>
                      <TableCell>
                        <Chip 
                          label={assessment.status.toUpperCase()}
                          color={assessment.status === 'active' ? 'primary' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            viewAssessment(assessment.id);
                          }}
                          aria-label="View details"
                        >
                          <Info fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            // Export/download functionality
                          }}
                          aria-label="Download report"
                        >
                          <Download fontSize="small" />
                        </IconButton>
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