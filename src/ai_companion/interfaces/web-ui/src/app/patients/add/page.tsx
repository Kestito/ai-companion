'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Box,
  Container,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Breadcrumbs,
  Link,
  Paper,
  Grid,
  SelectChangeEvent,
} from '@mui/material';
import { Home as HomeIcon, Person as PersonIcon } from '@mui/icons-material';
import { createPatient } from '@/lib/supabase/patientService';
import { PatientStatus } from '@/lib/supabase/types';
import { useLogger } from '@/hooks/useLogger';

export default function AddPatientPage() {
  const router = useRouter();
  const logger = useLogger({ component: 'AddPatientPage' });

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    age: '',
    gender: '',
    diagnosis: '',
    status: '',
  });

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    logger.debug('Form input changed', { field: name, value });
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSelectChange = (e: SelectChangeEvent<string>) => {
    const { name, value } = e.target;
    logger.debug('Select input changed', { field: name, value });
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    logger.info('Submitting new patient form', { formData });
    
    setLoading(true);
    setError(null);

    try {
      // Validate form data
      if (!formData.name || !formData.email || !formData.phone || !formData.age || !formData.gender) {
        throw new Error('Please fill in all required fields');
      }

      const patient = await createPatient({
        name: formData.name,
        email: formData.email,
        phone: formData.phone,
        age: parseInt(formData.age),
        gender: formData.gender as 'male' | 'female' | 'other',
        diagnosis: formData.diagnosis,
        status: formData.status as PatientStatus,
        admissionDate: new Date().toISOString(),
        doctor: 'Dr. System',
      });

      if (patient) {
        logger.info('Patient created successfully', { patientId: patient.id });
        router.push('/patients');
      } else {
        throw new Error('Failed to create patient');
      }
    } catch (err) {
      const error = err as Error;
      logger.error('Error creating patient', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4, mt: 6 }}>
        {/* Breadcrumbs */}
        <Breadcrumbs sx={{ mb: 4 }}>
          <Link
            underline="hover"
            color="inherit"
            href="/"
            onClick={(e) => {
              e.preventDefault();
              logger.info('Navigating to home');
              router.push('/');
            }}
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            <HomeIcon sx={{ mr: 0.5 }} fontSize="inherit" />
            Home
          </Link>
          <Link
            underline="hover"
            color="inherit"
            href="/patients"
            onClick={(e) => {
              e.preventDefault();
              logger.info('Navigating to patients list');
              router.push('/patients');
            }}
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            <PersonIcon sx={{ mr: 0.5 }} fontSize="inherit" />
            Patients
          </Link>
          <Typography color="text.primary">Add New Patient</Typography>
        </Breadcrumbs>

        <Paper sx={{ p: 4 }}>
          <Typography variant="h4" gutterBottom>
            Add New Patient
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Full Name"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Phone"
                  name="phone"
                  value={formData.phone}
                  onChange={handleInputChange}
                  required
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Age"
                  name="age"
                  type="number"
                  value={formData.age}
                  onChange={handleInputChange}
                  required
                  inputProps={{ min: 0, max: 150 }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth required>
                  <InputLabel>Gender</InputLabel>
                  <Select
                    name="gender"
                    value={formData.gender}
                    label="Gender"
                    onChange={handleSelectChange}
                  >
                    <MenuItem value="male">Male</MenuItem>
                    <MenuItem value="female">Female</MenuItem>
                    <MenuItem value="other">Other</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Status</InputLabel>
                  <Select
                    name="status"
                    value={formData.status}
                    label="Status"
                    onChange={handleSelectChange}
                  >
                    <MenuItem value="stable">Stable</MenuItem>
                    <MenuItem value="critical">Critical</MenuItem>
                    <MenuItem value="moderate">Moderate</MenuItem>
                    <MenuItem value="recovering">Recovering</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Initial Diagnosis"
                  name="diagnosis"
                  value={formData.diagnosis}
                  onChange={handleInputChange}
                  multiline
                  rows={3}
                />
              </Grid>
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                  <Button
                    variant="outlined"
                    onClick={() => {
                      logger.info('Canceling patient creation');
                      router.push('/patients');
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    variant="contained"
                    disabled={loading}
                  >
                    {loading ? 'Creating...' : 'Create Patient'}
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </form>
        </Paper>
      </Box>
    </Container>
  );
} 