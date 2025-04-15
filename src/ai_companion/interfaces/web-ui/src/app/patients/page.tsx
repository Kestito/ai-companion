'use client';

import { useEffect, useState } from 'react';
import { getSupabaseClient } from '@/lib/supabase/client';
import { 
  Typography, 
  Box, 
  Paper, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Button, 
  Chip, 
  CircularProgress, 
  Alert, 
  Container,
  Link as MuiLink,
  Grid
} from '@mui/material';
import Link from 'next/link';
import PersonIcon from '@mui/icons-material/Person';
import InfoIcon from '@mui/icons-material/Info';
import CodeIcon from '@mui/icons-material/Code';
import HomeIcon from '@mui/icons-material/Home';

interface Patient {
  id: string;
  email: string;
  phone?: string;
  created_at: string;
  preferred_language?: string;
  support_status?: string;
  name?: string;
  platform?: string;
  risk?: string;
  first_name?: string;
  last_name?: string;
  [key: string]: any;
}

export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        setLoading(true);
        const supabase = getSupabaseClient();
        
        // Try direct table access (in public schema)
        let data, error;
        
        try {
          // Direct table access - tables should be in public schema
          const result = await supabase
            .from('patients')
            .select('*');
              
          data = result.data;
          error = result.error;
        } catch (directAccessError) {
          console.error('Direct access failed:', directAccessError);
          throw directAccessError;
        }
        
        if (error) throw error;
        
        setPatients(data || []);
      } catch (err: any) {
        console.error('Error fetching patients:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPatients();
  }, []);

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
            <Typography color="text.primary">Patients</Typography>
          </Box>
          
          <Typography variant="h4" component="h1" sx={{ mt: 3, mb: 2 }}>
            Patients
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
            <Typography color="text.primary">Patients</Typography>
          </Box>
          
          <Typography variant="h4" component="h1" sx={{ mt: 3, mb: 2 }}>
            Patients
          </Typography>
        </Box>
        
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="subtitle1" fontWeight="bold">Error loading patients</Typography>
          <Typography variant="body2">{error}</Typography>
          <Typography variant="body2" sx={{ mt: 2 }}>Make sure the patients table exists in your Supabase database.</Typography>
          
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2">Troubleshooting steps:</Typography>
            <Box component="ul" sx={{ pl: 2, mt: 1 }}>
              <Box component="li" sx={{ mb: 0.5 }}>Verify that the 'patients' table exists in the 'public' schema</Box>
              <Box component="li" sx={{ mb: 0.5 }}>Ensure your Supabase client has permissions to access this table</Box>
              <Box component="li" sx={{ mb: 0.5 }}>
                Try running this SQL in Supabase SQL Editor:
                <Box 
                  component="code" 
                  sx={{ 
                    display: 'block', 
                    p: 1, 
                    mt: 1, 
                    bgcolor: 'grey.100', 
                    borderRadius: 1,
                    fontFamily: 'monospace'
                  }}
                >
                  SELECT * FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'patients';
                </Box>
              </Box>
              <Box component="li">
                Visit <MuiLink component={Link} href="/test-schema">Schema Test Page</MuiLink> to diagnose schema access methods
              </Box>
            </Box>
          </Box>
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
          <Typography color="text.primary">Patients</Typography>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 3 }}>
          <Typography variant="h4" component="h1" sx={{ mb: 2 }}>
            Patients
          </Typography>
          
          <Button 
            variant="contained" 
            color="primary" 
            startIcon={<PersonIcon />}
            component={Link}
            href="/patients/add"
          >
            Add New Patient
          </Button>
        </Box>
        <Typography variant="body1" color="text.secondary" paragraph sx={{ mb: 4 }}>
          Manage patient records and information.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          {patients.length === 0 ? (
            <Paper sx={{ textAlign: 'center', py: 5, px: 2 }}>
              <Typography color="text.secondary" sx={{ mb: 2 }}>
                No patients found in the database.
              </Typography>
              <Typography variant="body2">
                Visit <MuiLink component={Link} href="/test-schema">Schema Test Page</MuiLink> to diagnose schema access
              </Typography>
            </Paper>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>Email</TableCell>
                    <TableCell>Channel</TableCell>
                    <TableCell>Risk</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {patients.map((patient) => (
                    <TableRow key={patient.id} hover>
                      <TableCell>
                        {patient.id && patient.id.substring(0, 8)}...
                      </TableCell>
                      <TableCell>
                        {(patient.first_name || patient.last_name) 
                          ? `${patient.first_name || ''} ${patient.last_name || ''}`.trim() 
                          : (patient.name || 'N/A')}
                      </TableCell>
                      <TableCell>
                        {patient.email && typeof patient.email === 'string' && !patient.email.startsWith('\\x') 
                          ? patient.email 
                          : '[Encrypted]'}
                      </TableCell>
                      <TableCell>
                        {patient.channel || patient.platform || 'N/A'}
                      </TableCell>
                      <TableCell>
                        {patient.risk || 'Low'}
                      </TableCell>
                      <TableCell>
                        {patient.created_at && new Date(patient.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={patient.support_status || 'Unknown'} 
                          color={patient.support_status === 'active' ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="text"
                          color="primary"
                          component={Link}
                          href={`/patients/${patient.id}`}
                          size="small"
                        >
                          View
                        </Button>
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