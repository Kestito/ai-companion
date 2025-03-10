import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import { getSupabaseClient } from '@/lib/supabase/client'
import { CircularProgress, Box } from '@mui/material'

export const RouteGuard = ({ children }: { children: React.ReactNode }) => {
  const router = useRouter()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const supabase = getSupabaseClient();
    const checkSession = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session && router.pathname !== '/login') {
        router.push('/login')
      } else {
        setLoading(false)
      }
    }

    checkSession()
    
    const { data: authListener } = supabase.auth.onAuthStateChange((event) => {
      if (event === 'SIGNED_OUT') {
        router.push('/login')
      }
    })

    return () => authListener?.subscription.unsubscribe()
  }, [])

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" mt={4}>
        <CircularProgress />
      </Box>
    )
  }

  return <>{children}</>
} 