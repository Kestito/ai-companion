'use client';

import React, { useState, useEffect } from 'react';
import { 
  Button, 
  Box, 
  Typography, 
  Paper, 
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Container,
  CircularProgress,
  Alert,
  Chip,
  Grid
} from '@mui/material';
import Link from 'next/link';
import { CalendarMonth, Schedule, Add, Home as HomeIcon } from '@mui/icons-material';
import { getSupabaseClient, TABLE_NAMES } from '@/lib/supabase/client';

// Define appointment type
type Appointment = {
  id: string;
  patient_id: string;
  scheduled_time: string;
  contact_method: string;
  purpose: string;
  status: string;
};

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchAppointments() {
      try {
        setLoading(true);
        const supabase = getSupabaseClient();

        const { data, error } = await supabase
          .from(TABLE_NAMES.SCHEDULED_APPOINTMENTS)
          .select(`
            id,
            patient_id,
            scheduled_time,
            contact_method,
            purpose,
            status
          `)
          .order('scheduled_time', { ascending: true });

        if (error) {
          throw error;
        }

        // Type assertion to help TypeScript
        setAppointments(data as Appointment[] || []);
      } catch (err: any) {
        console.error('Error fetching appointments:', err);
        setError(err.message || 'Failed to load appointments');
      } finally {
        setLoading(false);
      }
    }

    fetchAppointments();
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
            <Typography color="text.primary">Appointments</Typography>
          </Box>
          
          <Typography variant="h4" component="h1" sx={{ mt: 3, mb: 2 }}>
            Scheduled Appointments
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
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
            <Typography color="text.primary">Appointments</Typography>
          </Box>
          
          <Typography variant="h4" component="h1" sx={{ mt: 3, mb: 2 }}>
            Scheduled Appointments
          </Typography>
        </Box>
        
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="subtitle1" component="div" fontWeight="bold">Error!</Typography>
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
          <Typography color="text.primary">Appointments</Typography>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 3 }}>
          <Typography variant="h4" component="h1" sx={{ mb: 2 }}>
            Scheduled Appointments
          </Typography>

          <Button 
            variant="contained" 
            color="primary" 
            startIcon={<Add />}
            component={Link}
            href="/appointments/new"
          >
            Create Appointment
          </Button>
        </Box>
        <Typography variant="body1" color="text.secondary" paragraph sx={{ mb: 4 }}>
          Manage and schedule appointments for patients.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Patient ID</TableCell>
                  <TableCell>Date & Time</TableCell>
                  <TableCell>Contact Method</TableCell>
                  <TableCell>Purpose</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {appointments.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      No appointments found
                    </TableCell>
                  </TableRow>
                ) : (
                  appointments.map((appointment) => (
                    <TableRow key={appointment.id} hover>
                      <TableCell>{appointment.patient_id}</TableCell>
                      <TableCell>{new Date(appointment.scheduled_time).toLocaleString()}</TableCell>
                      <TableCell>{appointment.contact_method}</TableCell>
                      <TableCell>{appointment.purpose}</TableCell>
                      <TableCell>
                        <Chip 
                          label={appointment.status}
                          color={
                            appointment.status === 'confirmed' ? 'success' : 
                            appointment.status === 'pending' ? 'warning' : 
                            'error'
                          }
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Button 
                            variant="text" 
                            color="primary"
                            component={Link} 
                            href={`/appointments/${appointment.id}`}
                            size="small"
                          >
                            View
                          </Button>
                          <Button 
                            variant="text" 
                            color="error"
                            size="small"
                          >
                            Cancel
                          </Button>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>
      </Grid>
    </Container>
  );
} 