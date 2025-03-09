'use client';

import { Box, Button, Checkbox, Container, FormControlLabel, IconButton, InputAdornment, Link, Stack, TextField, Typography, Alert } from '@mui/material';
import { Visibility, VisibilityOff, Google, Microsoft } from '@mui/icons-material';
import { useState, FormEvent, useEffect, Suspense } from 'react';
import Image from 'next/image';
import { useRouter, useSearchParams } from 'next/navigation';

const DEMO_USER = {
  email: 'demo@evelina.ai',
  password: 'demo123'
};

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [showPassword, setShowPassword] = useState(false);
  const [language, setLanguage] = useState('en');
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });

  useEffect(() => {
    // Handle URL query parameters
    const emailParam = searchParams.get('email');
    const passwordParam = searchParams.get('password');
    
    if (emailParam || passwordParam) {
      setFormData(prev => ({
        ...prev,
        email: emailParam || '',
        password: passwordParam || ''
      }));
      
      // Auto-submit if both email and password are provided
      if (emailParam === 'demo' && passwordParam === 'demo') {
        handleLogin({
          email: DEMO_USER.email,
          password: DEMO_USER.password
        });
      }
    }
  }, [searchParams]);

  const handleTogglePassword = () => setShowPassword(!showPassword);
  const handleLanguageChange = (lang: string) => setLanguage(lang);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'rememberMe' ? checked : value
    }));
  };

  const handleLogin = async (credentials: { email: string; password: string }) => {
    setError('');
    try {
      // For demo purposes, we'll check against demo credentials
      if (credentials.email === DEMO_USER.email && credentials.password === DEMO_USER.password) {
        // In a real app, you would handle authentication here
        router.push('/dashboard');
      } else {
        setError('Invalid credentials. Please use demo@evelina.ai / demo123 for demo access.');
      }
    } catch (err) {
      setError('An error occurred during login. Please try again.');
    }
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    await handleLogin(formData);
  };

  const handleDemoLogin = () => {
    setFormData({
      email: DEMO_USER.email,
      password: DEMO_USER.password,
      rememberMe: false
    });
    handleLogin(DEMO_USER);
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
                />
              }
              label="Remember me"
            />
            <Link href="#" variant="body2" underline="hover">
              Forgot Password?
            </Link>
          </Box>

          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 2 }}
          >
            SIGN IN
          </Button>

          <Button
            fullWidth
            variant="outlined"
            sx={{ mt: 2, mb: 3 }}
            onClick={handleDemoLogin}
          >
            Use Demo Account
          </Button>

          <Box sx={{ position: 'relative', my: 3 }}>
            <Box sx={{ position: 'absolute', top: '50%', width: '100%', borderBottom: '1px solid #e0e0e0' }} />
            <Typography variant="body2" align="center" sx={{ position: 'relative', bgcolor: 'background.paper', px: 2, display: 'inline-block' }}>
              or
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
            <Link href="#" variant="body2" underline="hover">
              Register
            </Link>
          </Box>

          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center', gap: 1 }}>
            <Button
              size="small"
              variant={language === 'lt' ? 'contained' : 'text'}
              disabled
            >
              LT
            </Button>
            <Button
              size="small"
              variant={language === 'en' ? 'contained' : 'text'}
              disabled
            >
              EN
            </Button>
          </Box>
        </Box>
      </Box>
    </Container>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <LoginForm />
    </Suspense>
  );
} 