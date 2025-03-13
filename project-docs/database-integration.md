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

## Schema Usage

When querying tables, explicitly specify the schema in one of the following ways:

```typescript
// Method 1: Using the schema parameter
const { data } = await supabase
  .from('users')
  .select('*')
  .schema('evelinaai');

// Method 2: Using the from parameter with schema prefix
const { data } = await supabase
  .from('evelinaai.users')
  .select('*');
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
  .schema('evelinaai')
  .eq('status', 'active');

// Get user with risk assessments
const { data: user } = await supabase
  .from('users')
  .select(`
    *,
    risk_assessments(*)
  `)
  .schema('evelinaai')
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
    users!scheduled_appointments_user_id_fkey(name)
  `)
  .schema('evelinaai')
  .eq('status', 'scheduled')
  .gte('scheduled_time', new Date().toISOString());
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
  .schema('evelinaai')
  .order('created_at', { ascending: false })
  .limit(10);
```

## Error Handling
```typescript
try {
  const { data, error } = await supabase
    .from('table')
    .select()
    .schema('evelinaai');
    
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

## Raw SQL Queries

For more complex queries, you can use raw SQL with the appropriate schema:

```typescript
const { data, error } = await supabase.rpc('execute_sql', {
  query: "SELECT * FROM evelinaai.users WHERE status = 'active'"
});
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
   
5. **Schema Consistency**
   - Always specify the 'evelinaai' schema in queries
   - Use the .schema() method in the query builder
   - For raw SQL, prefix table names with 'evelinaai.' 