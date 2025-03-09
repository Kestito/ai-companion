'use client';

import { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  Container, 
  Paper,
  Breadcrumbs,
  Link,
  Divider
} from '@mui/material';
import { 
  Add as AddIcon,
  Home as HomeIcon, 
  Person as PersonIcon 
} from '@mui/icons-material';
import { PatientTable } from '@/components/patients/patienttable';
import { PatientFilter } from '@/components/patients/patientfilter';
import { doctors } from '@/lib/mockData';
import { Patient, PatientStatus } from '@/lib/supabase/types';
import { fetchAllPatients } from '@/lib/supabase/patientService';

/**
 * Patients Page
 * Main interface for viewing and managing patients
 */
export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [filteredPatients, setFilteredPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load patient data from Supabase
  useEffect(() => {
    async function loadPatients() {
      try {
        setLoading(true);
        const data = await fetchAllPatients();
        
        if (data.length === 0) {
          // If no data is returned from Supabase, use mock data as fallback
          // This can be removed once the Supabase database is populated
          import('@/lib/mockData').then(({ mockPatients }) => {
            setPatients(mockPatients);
            setFilteredPatients(mockPatients);
            setLoading(false);
          });
        } else {
          setPatients(data);
          setFilteredPatients(data);
          setLoading(false);
        }
      } catch (err) {
        console.error('Error loading patients:', err);
        setError('Failed to load patient data. Please try again later.');
        
        // Fall back to mock data in case of error
        import('@/lib/mockData').then(({ mockPatients }) => {
          setPatients(mockPatients);
          setFilteredPatients(mockPatients);
          setLoading(false);
        });
      }
    }

    loadPatients();
  }, []);

  // Handle filter changes
  const handleFilterChange = (filters: {
    search: string;
    status: PatientStatus | '';
    doctor: string;
    dateAdmitted: string;
  }) => {
    let result = [...patients];

    // Filter by search term
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      result = result.filter(
        (patient) =>
          patient.name.toLowerCase().includes(searchTerm) ||
          patient.id.toLowerCase().includes(searchTerm) ||
          patient.diagnosis.toLowerCase().includes(searchTerm)
      );
    }

    // Filter by status
    if (filters.status) {
      result = result.filter((patient) => patient.status === filters.status);
    }

    // Filter by doctor
    if (filters.doctor) {
      result = result.filter((patient) => patient.doctor === filters.doctor);
    }

    // Filter by admission date
    if (filters.dateAdmitted) {
      result = result.filter(
        (patient) => patient.admissionDate === filters.dateAdmitted
      );
    }

    setFilteredPatients(result);
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 4, mt: 6 }}>
        {/* Page header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, pt: 3 }}>
          <Box>
            <Breadcrumbs aria-label="breadcrumb" sx={{ mb: 1 }}>
              <Link underline="hover" color="inherit" href="/" sx={{ display: 'flex', alignItems: 'center' }}>
                <HomeIcon sx={{ mr: 0.5 }} fontSize="inherit" />
                Home
              </Link>
              <Typography color="text.primary" sx={{ display: 'flex', alignItems: 'center' }}>
                <PersonIcon sx={{ mr: 0.5 }} fontSize="inherit" />
                Patients
              </Typography>
            </Breadcrumbs>
            <Typography variant="h4" component="h1" gutterBottom fontWeight="500">
              Patient Management
            </Typography>
            <Typography variant="body1" color="text.secondary">
              View, manage, and monitor patient information
            </Typography>
          </Box>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />}
            onClick={() => {/* Navigate to add patient form */}}
          >
            Add Patient
          </Button>
        </Box>

        <Divider sx={{ mb: 4 }} />
        
        {/* Filters */}
        <PatientFilter 
          onFilterChange={handleFilterChange} 
          doctors={doctors}
        />
        
        {/* Patients table */}
        <PatientTable 
          patients={filteredPatients} 
          loading={loading}
        />
      </Box>
    </Container>
  );
} 