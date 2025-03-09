"use client";

import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import supabase from '@/lib/supabase/client'

export const RouteGuard = ({ children }: { children: React.ReactNode }) => {
  const router = useRouter()
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
    const { data: authListener } = supabase.auth.onAuthStateChange((event) => {
      if (event === 'SIGNED_OUT') {
        router.push('/login')
      }
    })

    return () => authListener?.subscription.unsubscribe()
  }, [])

  if (!isClient) return null
  return children
} 