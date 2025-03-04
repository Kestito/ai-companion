import { Database } from '@/lib/supabase/types'

declare global {
  type User = Database['public']['Tables']['users']['Row']
  type Conversation = Database['public']['Tables']['conversations']['Row']
} 