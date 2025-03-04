import { supabase } from '@/lib/supabase/client'

export const Assistant = () => {
  const handleQuery = async (query: string) => {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.SUPABASE_SERVICE_KEY}`
      },
      body: JSON.stringify({ query })
    })
    // ...
  }
} 