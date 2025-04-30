'use client';

import { Box, Button, Checkbox, Container, FormControlLabel, IconButton, InputAdornment, Link, Stack, TextField, Typography, Alert, CircularProgress } from '@mui/material';
import { Visibility, VisibilityOff, Google, Microsoft, PersonAdd } from '@mui/icons-material';
import { useState, FormEvent, useEffect } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';
import Cookies from 'js-cookie';

// Demo user credentials
const DEMO_USER = {
  email: 'demo@evelina.ai',
  password: 'demo123'
};

// Hardcoded version as fallback
const DEFAULT_VERSION = '1.0.128';

function LoginForm() {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });

  // Create Supabase client
  const supabase = createClientComponentClient();

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
    setError(null);
    setLoading(true);
    console.log('==================== START PATIENT CREATION JOURNEY ====================');
    
    try {
      // Generate random data for the test patient
      const patientId = `test-${Date.now()}`;
      const now = new Date().toISOString();
      
      // Random name generation for test patient
      const getRandomName = () => {
        const firstNames = ['John', 'Jane', 'Emma', 'David', 'Sarah', 'Michael', 'Lisa', 'James'];
        const lastNames = ['Smith', 'Johnson', 'Brown', 'Wilson', 'Taylor', 'Lee', 'Wright', 'Davis'];
        return {
          first: firstNames[Math.floor(Math.random() * firstNames.length)],
          last: lastNames[Math.floor(Math.random() * lastNames.length)]
        };
      };
      
      const name = getRandomName();
      const firstName = name.first;
      const lastName = name.last;
      const fullName = `${firstName} ${lastName}`;
      
      console.log(`[1] Generated random name: ${fullName}`);
      console.log(`[2] Generated random patient ID: ${patientId}`);
      
      // Check database connection before attempting to create patient
      let isDbConnected = false;
      let dbConnectionError = null;
      
      console.log('[3] Checking database connection...');
      try {
        const { data: healthCheck, error: healthError } = await supabase.from('patients').select('count(*)', { count: 'exact', head: true });
        
        if (healthError) {
          console.error('[4] Database connection check failed:', healthError);
          dbConnectionError = healthError;
          isDbConnected = false;
        } else {
          console.log('[4] Database connection successful!');
          isDbConnected = true;
        }
      } catch (dbCheckError) {
        console.error('[4] Error checking database connection:', dbCheckError);
        dbConnectionError = dbCheckError;
        isDbConnected = false;
      }
      
      // If database is not connected, use a fallback approach
      if (!isDbConnected) {
        console.warn('[5] Unable to connect to database, using local storage only mode');
        
        // Store the patient info directly in localStorage without attempting DB operations
        const localStorageData = {
          id: patientId,
          patientId: patientId,
          first_name: firstName,
          last_name: lastName,
          name: fullName,
          role: 'patient',
          isTestMode: true,
          createdAt: now,
          dbError: dbConnectionError ? String(dbConnectionError) : 'Unknown database error'
        };
        
        localStorage.setItem('test_patient', JSON.stringify(localStorageData));
        console.log('[6] Patient data saved to localStorage (fallback mode):', JSON.stringify(localStorageData, null, 2));
        
        // Set cookie for patient test session
        Cookies.set('patient_test_mode', 'true', { expires: 1 });
        console.log('[7] Set patient_test_mode cookie');
        
        // Redirect to patient chat interface after a brief delay
        console.log('[8] Preparing to redirect to patient chat...');
        setTimeout(() => {
          console.log('[9] Redirecting to patient chat interface (fallback mode)');
          router.push('/patient-chat');
        }, 800);
        
        return;
      }
      
      // If database is connected, attempt to create the patient record
      console.log('[5] Checking if patients table exists and is valid...');
      
      try {
        const { data: tableData, error: tableError } = await supabase
          .from('patients')
          .select('id')
          .limit(1);
        
        if (tableError) {
          console.error('[6] Error checking patients table:', tableError);
          throw tableError;
        }
        
        if (tableData === null) {
          console.error('[7] Patients table returned null data');
          throw new Error('Patients table returned null data');
        }
        
        // Continue with existing creation logic for the patient record if table is valid
        console.log('[9] Patients table is valid');
      } catch (tableCheckError) {
        console.error('[8] Error checking patients table:', tableCheckError);
        throw tableCheckError;
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
        subsidy_eligible: true,
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
          position: 'relative',
          pb: 5 // Add padding at bottom to make room for version
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
  const [version, setVersion] = useState(DEFAULT_VERSION);
  
  useEffect(() => {
    // Fetch version on client-side
    const fetchVersion = async () => {
      try {
        const response = await fetch('/api/systeminfo');
        if (response.ok) {
          const data = await response.json();
          setVersion(data.version || DEFAULT_VERSION);
        }
      } catch (err) {
        console.error('Failed to fetch version:', err);
        // Keep default version
      }
    };
    
    fetchVersion();
  }, []);
  
  return (
    <>
      <LoginForm />
      <Box 
        sx={{ 
          position: 'fixed', 
          bottom: 12, 
          right: 12, 
          zIndex: 1000,
          backgroundColor: 'rgba(255,255,255,0.7)',
          padding: '2px 8px',
          borderRadius: 8
        }}
      >
        <Typography variant="caption" sx={{ opacity: 0.8, fontSize: '0.7rem' }}>
          v{version}
        </Typography>
      </Box>
    </>
  );
} 