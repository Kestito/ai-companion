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
  Alert
} from '@mui/material';
import { 
  Refresh, 
  Info, 
  Download,
  Add
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
  const supabase = createClientComponentClient();
  
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
  
  return (
    <Box sx={{ p: 3, maxWidth: '1200px', margin: '0 auto' }}>
      <PageHeader
        title="Patient Risk Assessments"
        subtitle="View and manage patient risk assessments generated from conversations"
      />
      
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2, gap: 2 }}>
        <Button 
          variant="outlined" 
          startIcon={<Refresh />}
          onClick={loadAssessments}
        >
          Refresh
        </Button>
        <Button 
          variant="contained" 
          color="primary" 
          startIcon={<Add />}
          onClick={createAssessment}
        >
          Create Assessment
        </Button>
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper} elevation={2}>
          <Table sx={{ minWidth: 650 }}>
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
              {assessments.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography variant="body1" sx={{ py: 3 }}>
                      No risk assessments found. Create your first assessment to get started.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                assessments.map((assessment) => (
                  <TableRow 
                    key={assessment.id}
                    hover
                    sx={{ '&:hover': { cursor: 'pointer' } }}
                    onClick={() => viewAssessment(assessment.id)}
                  >
                    <TableCell>
                      {assessment.patients?.first_name} {assessment.patients?.last_name}
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
                      >
                        <Info fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          // Export/download functionality
                        }}
                      >
                        <Download fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
} 