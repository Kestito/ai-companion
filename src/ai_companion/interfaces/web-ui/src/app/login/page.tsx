'use client';

import { Box, Button, Checkbox, Container, FormControlLabel, IconButton, InputAdornment, Link, Stack, TextField, Typography, Alert } from '@mui/material';
import { Visibility, VisibilityOff, Google, Microsoft, PersonAdd } from '@mui/icons-material';
import { useState, FormEvent } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { getSupabaseClient } from '@/lib/supabase/client';
import Cookies from 'js-cookie';

// Demo user credentials
const DEMO_USER = {
  email: 'demo@evelina.ai',
  password: 'demo123'
};

function LoginForm() {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });

  const handleTogglePassword = () => setShowPassword(!showPassword);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'rememberMe' ? checked : value
    }));
  };

  const handleLogin = async (credentials: { email: string; password: string }) => {
    setError('');
    setLoading(true);
    
    try {
      const supabase = getSupabaseClient();
      const { error } = await supabase.auth.signInWithPassword({
        email: credentials.email,
        password: credentials.password,
      });

      if (error) {
        throw error;
      }

      // Successful login will be handled by middleware redirecting to dashboard
    } catch (err: any) {
      setError(err.message || 'An error occurred during login. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    await handleLogin(formData);
  };

  const handleDemoLogin = () => {
    // For demo purposes, we'll use a fake login without actually authenticating
    setLoading(true);
    
    // Set a cookie for demo mode (will be checked by middleware)
    Cookies.set('demo_mode', 'true', { expires: 1 }); // Expires in 1 day
    
    // Store demo user info in localStorage for client-side access
    localStorage.setItem('demo_user', JSON.stringify({
      id: 'demo-user-123',
      email: DEMO_USER.email,
      name: 'Demo User',
      role: 'user'
    }));
    
    // Simulate authentication delay
    setTimeout(() => {
      // Redirect to dashboard
      router.push('/dashboard');
    }, 800);
  };

  const handleGoogleLogin = async () => {
    try {
      const supabase = getSupabaseClient();
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth/callback`
        }
      });

      if (error) {
        throw error;
      }
    } catch (err: any) {
      setError(err.message || 'Failed to sign in with Google');
    }
  };

  const handleMicrosoftLogin = async () => {
    try {
      const supabase = getSupabaseClient();
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'azure',
        options: {
          redirectTo: `${window.location.origin}/auth/callback`
        }
      });

      if (error) {
        throw error;
      }
    } catch (err: any) {
      setError(err.message || 'Failed to sign in with Microsoft');
    }
  };

  const handleTryAsPatient = async () => {
    console.log('==================== PATIENT CREATION JOURNEY ====================');
    console.log('[1] Starting patient creation process');
    setLoading(true);
    setError('');
    
    try {
      // Generate a unique ID for this patient session
      const patientId = `patient-${Date.now()}-${Math.random().toString(36).substring(2, 10)}`;
      console.log(`[2] Generated patient ID: ${patientId}`);
      
      // Get the Supabase client
      console.log('[3] Getting Supabase client');
      const supabase = getSupabaseClient();
      
      // Generate random name for testing
      const firstNames = ['Test', 'Demo', 'Sample', 'Trial'];
      const lastNames = ['Patient', 'User', 'Visitor', 'Tester'];
      const firstName = firstNames[Math.floor(Math.random() * firstNames.length)];
      const lastName = lastNames[Math.floor(Math.random() * lastNames.length)];
      const fullName = `${firstName} ${lastName}`;
      console.log(`[4] Generated random name: ${fullName}`);
      
      // Create timestamp for registration
      const now = new Date().toISOString();
      console.log(`[5] Timestamp for registration: ${now}`);
      
      // Check if patients table is valid by trying to query the schema
      console.log('[6] Checking if patients table is valid...');
      let patientsTableValid = true;
      
      try {
        // Try to get a sample row to determine schema
        console.log('[7] Querying patients table to verify schema');
        const { data, error } = await supabase
          .from('patients')
          .select('id, first_name, last_name, email, phone')
          .limit(1);
        
        if (error) {
          console.warn('[8] Patients table validation ERROR:', error);
          patientsTableValid = false;
        } else {
          console.log('[8] Patients table validated successfully');
          if (data && data.length > 0) {
            console.log('[9] Sample patient data:', JSON.stringify(data[0], null, 2).substring(0, 100) + '...');
          } else {
            console.log('[9] No patient records found, but table exists');
          }
        }
      } catch (e) {
        console.warn('[8] Error checking patients table:', e);
        patientsTableValid = false;
      }
      
      // If table isn't valid, store patient info only locally
      if (!patientsTableValid) {
        console.log('[10] Patients table is NOT valid. Using local storage ONLY');
        
        localStorage.setItem('test_patient', JSON.stringify({
          id: patientId,
          patientId: patientId,
          name: fullName,
          role: 'patient',
          isTestMode: true,
          createdAt: now
        }));
        console.log('[11] Patient data saved to localStorage');
        
        // Set cookies to identify this as a patient test session
        Cookies.set('patient_test_mode', 'true', { expires: 1 });
        console.log('[12] Set patient_test_mode cookie');
        
        // Redirect to patient chat interface after a brief delay
        console.log('[13] Preparing to redirect to patient chat...');
        setTimeout(() => {
          console.log('[14] Redirecting to patient chat interface');
          router.push('/patient-chat');
        }, 800);
        
        return;
      }
      
      // Create metadata for the patient
      console.log('[10] Patients table is valid, preparing to create new patient record');
      const metadataObj = {
        platform: "web-ui",
        user_id: patientId,
        username: fullName,
        is_test_patient: true
      };
      
      // Prepare patient data according to the schema we observed
      const patientData = {
        // Fields from the supabase schema diagram
        first_name: firstName,
        last_name: lastName,
        email: JSON.stringify(metadataObj),
        phone: `web:${patientId}`,
        created_at: now,
        last_active: now,
        preferred_language: "en",
        support_status: "active",
        subility_eligible: true,
        legal_consents: JSON.stringify({
          privacy_policy: true,
          terms_of_service: true,
          data_processing: true
        })
      };
      
      console.log('[11] Patient data prepared:', JSON.stringify(patientData, null, 2));
      
      // Insert the new patient into the patients table
      let dbPatientId = null;
      
      try {
        console.log('[12] Attempting to insert patient record into database...');
        const { data, error: insertError } = await supabase
          .from('patients')
          .insert(patientData)
          .select('id')
          .single();
        
        if (insertError) {
          console.error('[13] ERROR inserting patient:', insertError);
          throw insertError;
        }
        
        dbPatientId = data?.id;
        console.log(`[13] SUCCESS! Created patient with database ID: ${dbPatientId}`);
      } catch (dbError) {
        console.error('[13] Database error creating patient:', dbError);
        
        // If we can't create a patient record, use a temporary ID
        dbPatientId = `temp-${patientId}`;
        console.log(`[14] Using temporary patient ID instead: ${dbPatientId}`);
      }
      
      // Store patient info in localStorage
      const localStorageData = {
        id: dbPatientId || patientId,
        patientId: patientId,
        name: fullName,
        role: 'patient',
        isTestMode: true,
        createdAt: now
      };
      localStorage.setItem('test_patient', JSON.stringify(localStorageData));
      console.log('[15] Patient data saved to localStorage:', JSON.stringify(localStorageData, null, 2));
      
      // Set cookie for patient test session
      Cookies.set('patient_test_mode', 'true', { expires: 1 });
      console.log('[16] Set patient_test_mode cookie');
      
      // Redirect to patient chat interface
      console.log('[17] Preparing to redirect to patient chat...');
      setTimeout(() => {
        console.log('[18] Redirecting to patient chat interface');
        router.push('/patient-chat');
      }, 800);
    } catch (err: any) {
      console.error('[ERROR] Error in patient test mode:', err);
      setError('Error creating test patient: ' + (err.message || 'Unknown error'));
      setLoading(false);
    }
    console.log('==================== END PATIENT CREATION JOURNEY ====================');
  };

  return (
    <Container component="main" maxWidth="sm">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 3,
        }}
      >
        <Image
          src="/evelinalogo.png"
          alt="Evelina AI Logo"
          width={180}
          height={180}
          priority
        />

        <Typography variant="subtitle1" align="center" color="text.secondary" gutterBottom>
          Interactive patient care information system
        </Typography>

        {error && (
          <Alert severity="error" sx={{ width: '100%' }}>
            {error}
          </Alert>
        )}

        <Box component="form" noValidate sx={{ mt: 1, width: '100%' }} onSubmit={handleSubmit}>
          <TextField
            margin="normal"
            required
            fullWidth
            id="email"
            label="Email"
            name="email"
            autoComplete="email"
            autoFocus
            value={formData.email}
            onChange={handleInputChange}
            disabled={loading}
          />

          <TextField
            margin="normal"
            required
            fullWidth
            name="password"
            label="Password"
            type={showPassword ? 'text' : 'password'}
            id="password"
            autoComplete="current-password"
            value={formData.password}
            onChange={handleInputChange}
            disabled={loading}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    aria-label="toggle password visibility"
                    onClick={handleTogglePassword}
                    edge="end"
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', my: 2 }}>
            <FormControlLabel
              control={
                <Checkbox 
                  name="rememberMe"
                  checked={formData.rememberMe}
                  onChange={handleInputChange}
                  color="primary"
                  disabled={loading}
                />
              }
              label="Remember me"
            />
            <Link href="/reset-password" variant="body2" underline="hover">
              Forgot Password?
            </Link>
          </Box>

          <Button
            type="submit"
            fullWidth
            variant="contained"
            disabled={loading}
            sx={{ mt: 2 }}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </Button>

          <Button
            fullWidth
            variant="outlined"
            onClick={handleDemoLogin}
            disabled={loading}
            sx={{ mt: 2 }}
            color="success"
          >
            Use Demo Account
          </Button>

          <Button
            fullWidth
            variant="outlined"
            onClick={handleTryAsPatient}
            disabled={loading}
            sx={{ mt: 2, mb: 2 }}
            color="info"
            startIcon={<PersonAdd />}
          >
            Try as a Patient
          </Button>

          <Box sx={{ position: 'relative', my: 3 }}>
            <Box sx={{ position: 'absolute', top: '50%', width: '100%', borderBottom: '1px solid #e0e0e0' }} />
            <Typography variant="body2" align="center" sx={{ position: 'relative', bgcolor: 'background.paper', px: 2, display: 'inline-block' }}>
              or continue with
            </Typography>
          </Box>

          <Stack spacing={2}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<Google />}
              disabled
            >
              Google Sign In
            </Button>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<Microsoft />}
              disabled
            >
              Microsoft Sign In
            </Button>
          </Stack>

          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body2" display="inline">
              Don't have an account?{' '}
            </Typography>
            <Link href="/signup" variant="body2" underline="hover">
              Sign up
            </Link>
          </Box>
        </Box>
      </Box>
    </Container>
  );
}

export default function LoginPage() {
  return (
    <LoginForm />
  );
} 