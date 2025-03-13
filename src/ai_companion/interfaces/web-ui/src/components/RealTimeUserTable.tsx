'use client';

import { useEffect, useState } from 'react';
import { getSupabaseClient } from '@/lib/supabase/client';

interface User {
  id: string;
  email?: string;
  created_at?: string;
  last_sign_in_at?: string;
  role?: string;
  [key: string]: any; // Allow for additional fields
}

interface RealTimeUserTableProps {
  tableName: string;
}

export default function RealTimeUserTable({ tableName }: RealTimeUserTableProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const fetchUsers = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const supabase = getSupabaseClient();
        const { data, error } = await supabase
          .from(tableName)
          .select('*');
        
        if (error) {
          throw error;
        }
        
        setUsers(data || []);
      } catch (err: any) {
        console.error('Error fetching users:', err);
        setError(err.message || 'Failed to fetch users');
      } finally {
        setLoading(false);
      }
    };
    
    fetchUsers();
    
    // Set up real-time subscription
    const supabase = getSupabaseClient();
    const subscription = supabase
      .channel('users-channel')
      .on('postgres_changes', {
        event: '*',
        schema: tableName.split('.')[0],
        table: tableName.split('.')[1] || tableName,
      }, (payload) => {
        console.log('Change received:', payload);
        
        // Handle different change types
        if (payload.eventType === 'INSERT') {
          setUsers(prev => [...prev, payload.new as User]);
        } else if (payload.eventType === 'UPDATE') {
          setUsers(prev => 
            prev.map(user => user.id === payload.new.id ? { ...user, ...payload.new } : user)
          );
        } else if (payload.eventType === 'DELETE') {
          setUsers(prev => prev.filter(user => user.id !== payload.old.id));
        }
      })
      .subscribe();
    
    return () => {
      supabase.removeChannel(subscription);
    };
  }, [tableName]);
  
  if (loading) {
    return <div className="text-center py-4">Loading users...</div>;
  }
  
  if (error) {
    return <div className="text-red-500 py-4">Error: {error}</div>;
  }
  
  if (users.length === 0) {
    return <div className="text-center py-4">No users found</div>;
  }
  
  // Determine columns dynamically based on the first user
  const columns = users.length > 0 
    ? Object.keys(users[0]).filter(key => 
        !key.startsWith('raw_') && 
        key !== 'encrypted_password' &&
        typeof users[0][key] !== 'object' || users[0][key] === null
      )
    : [];
  
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map(column => (
              <th 
                key={column}
                scope="col" 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                {column.replace(/_/g, ' ')}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {users.map((user) => (
            <tr key={user.id} className="hover:bg-gray-50">
              {columns.map(column => (
                <td key={`${user.id}-${column}`} className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {typeof user[column] === 'boolean' 
                    ? user[column] ? 'Yes' : 'No'
                    : user[column] instanceof Date
                    ? new Date(user[column]).toLocaleString()
                    : user[column] === null
                    ? '-'
                    : String(user[column])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
} 