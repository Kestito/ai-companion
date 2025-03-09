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
import { mockPatients, doctors } from '@/lib/mockData';
import { Patient, PatientStatus } from '@/lib/supabase/types';

/**
 * Patients Page
 * Main interface for viewing and managing patients
 */
export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [filteredPatients, setFilteredPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);

  // Load patient data
  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setPatients(mockPatients);
      setFilteredPatients(mockPatients);
      setLoading(false);
    }, 500);
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