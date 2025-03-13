import { useEffect, useState } from 'react'
import { getSupabaseClient, getSchemaTable } from '@/lib/supabase/client'
import dynamic from 'next/dynamic'

// Table name with schema
const USERS_TABLE = getSchemaTable('users');

interface User {
  id: string;
  email?: string;
  last_active?: string;
}

const RealTimeUserTable = () => {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const supabase = getSupabaseClient();
        const { data, error } = await supabase
          .from(USERS_TABLE)
          .select('*')
        
        if (error) throw error
        setUsers(data || [])
      } catch (err) {
        setError('Failed to fetch users')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    
    fetchUsers()
    
    const supabase = getSupabaseClient();
    const channel = supabase
      .channel('users')
      .on('postgres_changes', {
        event: '*',
        schema: 'evelinaai',
        table: 'users'
      }, (payload) => {
        console.log('Change received:', payload)
        if (payload.eventType === 'DELETE') {
          setUsers(prev => prev.filter(u => u.id !== payload.old.id))
        } else {
          setUsers(prev => {
            const existing = prev.findIndex(u => u.id === payload.new.id)
            const newUser = payload.new as User
            
            if (existing >= 0) {
              return [...prev.slice(0, existing), newUser, ...prev.slice(existing + 1)]
            } else {
              return [...prev, newUser]
            }
          })
        }
      })
      .subscribe()
      
    return () => {
      channel.unsubscribe()
    }
  }, [])

  if (loading) {
    return <div>Loading users...</div>
  }

  if (error) {
    return <div className="text-red-500">{error}</div>
  }

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Active Users ({users.length})</h2>
      <table className="min-w-full bg-white">
        <thead>
          <tr>
            <th className="py-2 px-4 border-b">ID</th>
            <th className="py-2 px-4 border-b">Email</th>
            <th className="py-2 px-4 border-b">Last Active</th>
          </tr>
        </thead>
        <tbody>
          {users.map(user => (
            <tr key={user.id}>
              <td className="py-2 px-4 border-b">{user.id}</td>
              <td className="py-2 px-4 border-b">{user.email || 'N/A'}</td>
              <td className="py-2 px-4 border-b">
                {user.last_active 
                  ? new Date(user.last_active).toLocaleString() 
                  : 'Never'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const DynamicRealTimeUserTable = dynamic(
  () => Promise.resolve(RealTimeUserTable),
  { ssr: false }
)

export default DynamicRealTimeUserTable 