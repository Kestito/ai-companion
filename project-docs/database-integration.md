# Database Integration Guide

## Connection Setup


### Supabase Client Configuration
```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(supabaseUrl, supabaseKey, {
  auth: {
    persistSession: false,
    autoRefreshToken: false
  },
  global: {
    headers: {
      'apikey': supabaseKey,
      'Authorization': `Bearer ${supabaseKey}`,
      'Content-Type': 'application/json',
      'Accept-Profile': 'evelinaai'
    }
  }
});
```

## Type Definitions

### Core Types
```typescript
type DbUser = {
  id: string;
  created_at: string;
  email: string;
  name: string;
  status: 'active' | 'inactive';
  type: 'patient' | 'doctor' | 'admin';
  last_active: string;
  risk_level?: 'low' | 'medium' | 'high';
};

type DbRiskAssessment = {
  id: string;
  created_at: string;
  user_id: string;
  risk_level: 'low' | 'medium' | 'high';
  assessment_details: any;
};

type DbAppointment = {
  id: string;
  created_at: string;
  user_id: string;
  doctor_id: string;
  appointment_date: string;
  status: 'scheduled' | 'completed' | 'cancelled';
  type: string;
};
```

## Common Queries

### User Management
```typescript
// Get active users
const { data: users } = await supabase
  .from('users')
  .select('id, status, name, type')
  .eq('status', 'active');

// Get user with risk assessments
const { data: user } = await supabase
  .from('users')
  .select(`
    *,
    risk_assessments(*)
  `)
  .eq('id', userId)
  .single();
```

### Appointments
```typescript
// Get upcoming appointments
const { data: appointments } = await supabase
  .from('scheduled_appointments')
  .select(`
    *,
    users!scheduled_appointments_user_id_fkey(name),
    users!scheduled_appointments_doctor_id_fkey(name)
  `)
  .eq('status', 'scheduled')
  .gte('appointment_date', new Date().toISOString());
```

### Conversations
```typescript
// Get recent conversations with details
const { data: conversations } = await supabase
  .from('conversations')
  .select(`
    *,
    conversation_details(*),
    users!conversations_user_id_fkey(name)
  `)
  .order('created_at', { ascending: false })
  .limit(10);
```

## Error Handling
```typescript
try {
  const { data, error } = await supabase.from('table').select();
  if (error) {
    console.error('Database error:', error);
    throw new Error(`Failed to fetch data: ${error.message}`);
  }
  return data;
} catch (err) {
  console.error('Error:', err);
  throw err;
}
```

## Best Practices

1. **Type Safety**
   - Always use TypeScript types for database entities
   - Validate data before insertion
   - Handle null/undefined cases

2. **Performance**
   - Use specific column selection instead of '*'
   - Implement pagination for large datasets
   - Cache frequently accessed data

3. **Security**
   - Use RLS (Row Level Security) policies
   - Never expose service role key in client
   - Validate user permissions before operations

4. **Maintenance**
   - Keep types in sync with schema
   - Document schema changes
   - Use migrations for schema updates 