import { useEffect, useState } from 'react'
import { supabase } from '../../lib/supabase/client'
// OR with the path alias (once configured):
// import { supabase } from '@/lib/supabase/client'
import dynamic from 'next/dynamic'

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
        const { data, error } = await supabase
          .from('users')
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
    
    const channel = supabase
      .channel('users')
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
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

  return (
    <div>
      {loading ? (
        <p>Loading users...</p>
      ) : error ? (
        <p>Error: {error}</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Email</th>
              <th>Last Active</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr key={user.id}>
                <td>{user.id}</td>
                <td>{user.email}</td>
                <td>{user.last_active ? new Date(user.last_active).toLocaleString() : 'Never'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

const DynamicRealTimeUserTable = dynamic(
  () => Promise.resolve(RealTimeUserTable),
  { ssr: false }
)

export default DynamicRealTimeUserTable 