import { getSupabaseClient } from '@/lib/supabase/client'
import { Button, Stack } from '@mui/material'
import GoogleIcon from '@mui/icons-material/Google'
import MicrosoftIcon from '@mui/icons-material/Microsoft'

export const SocialAuthButtons = () => {
  const handleAuth = async (provider: 'google' | 'azure') => {
    const supabase = getSupabaseClient();
    await supabase.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: `${window.location.origin}/dashboard`,
        scopes: 'email profile'
      }
    })
  }

  return (
    <Stack spacing={1} sx={{ mt: 2 }}>
      <Button 
        variant="outlined" 
        startIcon={<GoogleIcon />}
        onClick={() => handleAuth('google')}
        fullWidth
      >
        Continue with Google
      </Button>
      <Button
        variant="outlined"
        startIcon={<MicrosoftIcon />}
        onClick={() => handleAuth('azure')}
        fullWidth
      >
        Continue with Microsoft
      </Button>
    </Stack>
  )
}