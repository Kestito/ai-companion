'use client';

import { Box, Button, Checkbox, Container, FormControlLabel, IconButton, InputAdornment, Link, Stack, TextField, Typography, Alert } from '@mui/material';
import { Visibility, VisibilityOff, Google, Microsoft } from '@mui/icons-material';
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
            sx={{ mt: 2, mb: 2 }}
            color="success"
          >
            Use Demo Account
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