# Dashboard Real Data Integration

This document explains how to set up and use real data for the medical dashboard.

## Overview

The dashboard is designed to display real-time statistics, activity logs, and notifications from the Supabase database. To ensure the dashboard works properly with real data, we've implemented the following:

1. **Real-time Statistics**: Patient counts, activity levels, and critical metrics
2. **Activity Logs**: Recent actions taken by system users
3. **Notifications**: Important alerts and updates

## Database Setup

Before the dashboard can display real data, you need to set up the required tables in Supabase. We've provided a setup script to make this process easy.

### 1. Install Required Dependencies

First, install the required dependencies:

```bash
npm install dotenv node-fetch @supabase/supabase-js
```

### 2. Verify Environment Variables

Make sure your `.env.local` file contains the required Supabase credentials:

```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
```

The `SUPABASE_SERVICE_KEY` is required as it has permissions to create tables.

### 3. Run the Setup Script

Run the setup script to create the required tables and insert sample data:

```bash
npm run setup-db
```

This script will:
1. Check if each required table exists
2. Create missing tables
3. Insert sample data only if tables are empty
4. Log each step for easy troubleshooting

### Required Tables

The dashboard uses the following tables:

1. **patients**: Stores patient information
   - Fields: id, name, email, phone, age, gender, status, admission_date, etc.

2. **activity_logs**: Tracks user actions in the system
   - Fields: id, user_name, action, severity, details, created_at

3. **notifications**: Stores system notifications
   - Fields: id, type, message, read, created_at

4. **appointments**: Tracks scheduled appointments
   - Fields: id, patient_id, doctor, appointment_date, status, notes, created_at

5. **messages**: Stores patient-doctor communications
   - Fields: id, patient_id, sender, content, is_responded, created_at

## Troubleshooting

If you encounter any issues with the setup script:

### Connection Issues

1. **API Key Permissions**: Make sure your `SUPABASE_SERVICE_KEY` has permissions to create tables and insert data
2. **Network Errors**: Check your firewall or network settings if you're getting connection timeouts
3. **Database Errors**: Look for detailed error messages in the console output

### Table Creation Errors

1. **Cannot Create Tables**: 
   - Verify that your service key has the necessary permissions
   - Check if the tables already exist with different schemas
   - Try running SQL queries directly in the Supabase dashboard

2. **SQL Execution Errors**:
   - The script uses a RESTful approach to execute SQL; check your Supabase project settings
   - If REST SQL is not available, try using the Supabase Dashboard to create tables manually

### Sample Data Issues

1. **Foreign Key Constraints**: The script creates related data in the correct order to satisfy foreign key constraints
2. **Duplicate Data**: The script checks if tables are empty before inserting sample data
3. **Missing Data**: If some tables have data but others don't, you may see inconsistencies

## Manual Table Creation

If the automatic setup fails, you can manually create the tables using the Supabase SQL editor. Here are the SQL commands:

```sql
-- Create patients table
CREATE TABLE IF NOT EXISTS patients (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  age INTEGER,
  gender TEXT,
  status TEXT DEFAULT 'active',
  admission_date TIMESTAMP WITH TIME ZONE,
  diagnosis TEXT,
  doctor TEXT,
  room_number TEXT,
  contact_number TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create activity_logs table
CREATE TABLE IF NOT EXISTS activity_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_name TEXT,
  action TEXT NOT NULL,
  severity TEXT DEFAULT 'info',
  details JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  type TEXT DEFAULT 'info',
  message TEXT NOT NULL,
  read BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create appointments table
CREATE TABLE IF NOT EXISTS appointments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  patient_id UUID NOT NULL,
  doctor TEXT NOT NULL,
  appointment_date TIMESTAMP WITH TIME ZONE NOT NULL,
  status TEXT DEFAULT 'pending',
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  patient_id UUID NOT NULL,
  sender TEXT NOT NULL,
  content TEXT NOT NULL,
  is_responded BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Implementation Details

### Data Fetching

The dashboard fetches data from three main services:

1. **patientService.ts**: Retrieves patient statistics and demographics
2. **activityService.ts**: Fetches recent activity logs
3. **notificationService.ts**: Retrieves notifications and alerts

All services are designed to handle missing tables gracefully by providing fallback data, ensuring the dashboard always displays something meaningful even during initial setup.

### Realtime Updates

For future enhancement: The dashboard can be configured to subscribe to Supabase realtime updates for immediate data refresh when changes occur in the database.

To implement this feature:

```typescript
// Example code to be added to DashboardPage
useEffect(() => {
  const supabase = getSupabaseClient();
  
  // Subscribe to patients table changes
  const subscription = supabase
    .from('patients')
    .on('*', (payload) => {
      console.log('Patient data changed:', payload);
      loadDashboardData();
    })
    .subscribe();
  
  return () => {
    supabase.removeSubscription(subscription);
  };
}, []);
```

## Contributing

When adding new features to the dashboard:

1. Create appropriate database tables
2. Update the setup script to include the new tables
3. Create service files for data access
4. Update the UI components to display the new data 