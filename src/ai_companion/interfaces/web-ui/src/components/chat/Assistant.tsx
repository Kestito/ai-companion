import { useState } from 'react'
import { getSupabaseClient } from '@/lib/supabase/client'

export const Assistant = () => {
  const handleQuery = async (query: string) => {
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query })
      })
      return await response.json()
    } catch (error) {
      console.error('Error:', error)
    }
  }
  
  return (
    <div>
      {/* Chat assistant implementation */}
    </div>
  )
} 