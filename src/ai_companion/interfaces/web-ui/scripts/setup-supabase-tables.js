/**
 * This script sets up the necessary Supabase tables for the dashboard
 * Run with: node scripts/setup-supabase-tables.js
 */

require('dotenv').config({ path: '.env.local' });
const { createClient } = require('@supabase/supabase-js');
// Use node-fetch with CommonJS
const fetch = (...args) => import('node-fetch').then(({ default: fetch }) => fetch(...args));

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing Supabase credentials. Please check your .env.local file.');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function setupTables() {
  console.log('Setting up Supabase tables...');

  try {
    console.log(`Connecting to Supabase at: ${supabaseUrl}`);
    
    // First check if we can connect to the database
    const { data: connectionTest, error: connectionError } = await supabase.from('_tables').select('*').limit(1);
    
    if (connectionError) {
      console.log('Testing connection to Supabase...');
      // Alternative way to check connection
      const { data: connectionData, error: connectionErr } = await supabase.auth.getSession();
      
      if (connectionErr) {
        console.error('Failed to connect to Supabase:', connectionErr.message);
        process.exit(1);
      } else {
        console.log('Connected to Supabase successfully!');
      }
    } else {
      console.log('Connected to Supabase successfully!');
    }

    // Check if patients table exists by trying to query it
    const { data: patientsExists, error: patientsError } = await supabase
      .from('patients')
      .select('id')
      .limit(1);

    if (patientsError) {
      console.log('Checking if patients table exists...');
      if (patientsError.code === '42P01') {
        console.log('Patients table does not exist. Creating...');
        
        // Using raw SQL via the REST API endpoint
        const res = await fetch(`${supabaseUrl}/rest/v1/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${supabaseKey}`,
            'apikey': `${supabaseKey}`,
            'Prefer': 'return=minimal'
          },
          body: JSON.stringify({
            query: `
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
            `
          })
        });

        if (res.ok) {
          console.log('Patients table created successfully');
          await insertSamplePatientData();
        } else {
          const errorData = await res.json();
          console.error('Error creating patients table:', errorData);
        }
      } else {
        console.error('Error checking patients table:', patientsError);
      }
    } else {
      console.log('Patients table already exists');
    }

    // Check if activity_logs table exists
    const { data: activityExists, error: activityError } = await supabase
      .from('activity_logs')
      .select('id')
      .limit(1);

    if (activityError) {
      console.log('Checking if activity_logs table exists...');
      if (activityError.code === '42P01') {
        console.log('Activity logs table does not exist. Creating...');
        
        const res = await fetch(`${supabaseUrl}/rest/v1/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${supabaseKey}`,
            'apikey': `${supabaseKey}`,
            'Prefer': 'return=minimal'
          },
          body: JSON.stringify({
            query: `
              CREATE TABLE IF NOT EXISTS activity_logs (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_name TEXT,
                action TEXT NOT NULL,
                severity TEXT DEFAULT 'info',
                details JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
              );
            `
          })
        });

        if (res.ok) {
          console.log('Activity logs table created successfully');
          await insertSampleActivityData();
        } else {
          const errorData = await res.json();
          console.error('Error creating activity_logs table:', errorData);
        }
      } else {
        console.error('Error checking activity_logs table:', activityError);
      }
    } else {
      console.log('Activity logs table already exists');
    }

    // Check if notifications table exists
    const { data: notificationsExists, error: notificationsError } = await supabase
      .from('notifications')
      .select('id')
      .limit(1);

    if (notificationsError) {
      console.log('Checking if notifications table exists...');
      if (notificationsError.code === '42P01') {
        console.log('Notifications table does not exist. Creating...');
        
        const res = await fetch(`${supabaseUrl}/rest/v1/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${supabaseKey}`,
            'apikey': `${supabaseKey}`,
            'Prefer': 'return=minimal'
          },
          body: JSON.stringify({
            query: `
              CREATE TABLE IF NOT EXISTS notifications (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                type TEXT DEFAULT 'info',
                message TEXT NOT NULL,
                read BOOLEAN DEFAULT false,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
              );
            `
          })
        });

        if (res.ok) {
          console.log('Notifications table created successfully');
          await insertSampleNotificationData();
        } else {
          const errorData = await res.json();
          console.error('Error creating notifications table:', errorData);
        }
      } else {
        console.error('Error checking notifications table:', notificationsError);
      }
    } else {
      console.log('Notifications table already exists');
    }

    // Check if appointments table exists
    const { data: appointmentsExists, error: appointmentsError } = await supabase
      .from('appointments')
      .select('id')
      .limit(1);

    if (appointmentsError) {
      console.log('Checking if appointments table exists...');
      if (appointmentsError.code === '42P01') {
        console.log('Appointments table does not exist. Creating...');
        
        const res = await fetch(`${supabaseUrl}/rest/v1/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${supabaseKey}`,
            'apikey': `${supabaseKey}`,
            'Prefer': 'return=minimal'
          },
          body: JSON.stringify({
            query: `
              CREATE TABLE IF NOT EXISTS appointments (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                patient_id UUID NOT NULL,
                doctor TEXT NOT NULL,
                appointment_date TIMESTAMP WITH TIME ZONE NOT NULL,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
              );
            `
          })
        });

        if (res.ok) {
          console.log('Appointments table created successfully');
          await insertSampleAppointmentData();
        } else {
          const errorData = await res.json();
          console.error('Error creating appointments table:', errorData);
        }
      } else {
        console.error('Error checking appointments table:', appointmentsError);
      }
    } else {
      console.log('Appointments table already exists');
    }

    // Check if messages table exists
    const { data: messagesExists, error: messagesError } = await supabase
      .from('messages')
      .select('id')
      .limit(1);

    if (messagesError) {
      console.log('Checking if messages table exists...');
      if (messagesError.code === '42P01') {
        console.log('Messages table does not exist. Creating...');
        
        const res = await fetch(`${supabaseUrl}/rest/v1/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${supabaseKey}`,
            'apikey': `${supabaseKey}`,
            'Prefer': 'return=minimal'
          },
          body: JSON.stringify({
            query: `
              CREATE TABLE IF NOT EXISTS messages (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                patient_id UUID NOT NULL,
                sender TEXT NOT NULL,
                content TEXT NOT NULL,
                is_responded BOOLEAN DEFAULT false,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
              );
            `
          })
        });

        if (res.ok) {
          console.log('Messages table created successfully');
          await insertSampleMessageData();
        } else {
          const errorData = await res.json();
          console.error('Error creating messages table:', errorData);
        }
      } else {
        console.error('Error checking messages table:', messagesError);
      }
    } else {
      console.log('Messages table already exists');
    }

    console.log('Setup completed successfully');
  } catch (error) {
    console.error('Error setting up tables:', error);
  }
}

async function insertSamplePatientData() {
  // Insert sample patient data if the table is empty
  const { count, error: countError } = await supabase
    .from('patients')
    .select('*', { count: 'exact', head: true });

  if (countError) {
    console.error('Error checking patient count:', countError);
    return;
  }

  if (count === 0) {
    console.log('Inserting sample patient data...');
    
    const samplePatients = [
      {
        name: 'John Doe',
        email: 'john.doe@example.com',
        phone: '+1234567890',
        age: 45,
        gender: 'male',
        status: 'active',
        admission_date: new Date().toISOString(),
        diagnosis: 'Hypertension',
        doctor: 'Dr. Smith',
        room_number: '101',
        contact_number: '+1987654321'
      },
      {
        name: 'Jane Smith',
        email: 'jane.smith@example.com',
        phone: '+1234567891',
        age: 32,
        gender: 'female',
        status: 'active',
        admission_date: new Date().toISOString(),
        diagnosis: 'Diabetes Type 2',
        doctor: 'Dr. Johnson',
        room_number: '102',
        contact_number: '+1987654322'
      },
      {
        name: 'Robert Johnson',
        email: 'robert.johnson@example.com',
        phone: '+1234567892',
        age: 67,
        gender: 'male',
        status: 'critical',
        admission_date: new Date().toISOString(),
        diagnosis: 'Pneumonia',
        doctor: 'Dr. Williams',
        room_number: '201',
        contact_number: '+1987654323'
      },
      {
        name: 'Maria Garcia',
        email: 'maria.garcia@example.com',
        phone: '+1234567893',
        age: 28,
        gender: 'female',
        status: 'active',
        admission_date: new Date().toISOString(),
        diagnosis: 'Pregnancy',
        doctor: 'Dr. Brown',
        room_number: '103',
        contact_number: '+1987654324'
      },
      {
        name: 'David Wilson',
        email: 'david.wilson@example.com',
        phone: '+1234567894',
        age: 55,
        gender: 'male',
        status: 'inactive',
        admission_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        diagnosis: 'Recovered',
        doctor: 'Dr. Davis',
        room_number: null,
        contact_number: '+1987654325'
      }
    ];
    
    const { error: insertError } = await supabase
      .from('patients')
      .insert(samplePatients);
    
    if (insertError) {
      console.error('Error inserting sample patient data:', insertError);
    } else {
      console.log('Sample patient data inserted successfully');
    }
  } else {
    console.log('Patient table already has data, skipping sample data insertion');
  }
}

async function insertSampleActivityData() {
  // Insert sample activity data
  const { count, error: countError } = await supabase
    .from('activity_logs')
    .select('*', { count: 'exact', head: true });

  if (countError) {
    console.error('Error checking activity_logs count:', countError);
    return;
  }

  if (count === 0) {
    console.log('Inserting sample activity data...');
    
    const sampleActivity = [
      {
        user_name: 'Dr. J. Smith',
        action: 'Updated patient medication',
        severity: 'info',
        details: { patientId: 'sample-1', medication: 'Aspirin' }
      },
      {
        user_name: 'Dr. A. Jonaitis',
        action: 'Completed consultation',
        severity: 'success',
        details: { patientId: 'sample-2', notes: 'Follow-up in 2 weeks' }
      },
      {
        user_name: 'Dr. L. Petrauskas',
        action: 'Flagged critical condition',
        severity: 'error',
        details: { patientId: 'sample-3', condition: 'Respiratory distress' }
      },
      {
        user_name: 'Nurse Wilson',
        action: 'Recorded vital signs',
        severity: 'info',
        details: { patientId: 'sample-4', bp: '120/80', pulse: 72 }
      },
      {
        user_name: 'System',
        action: 'Daily health reports generated',
        severity: 'info',
        details: { reportCount: 15 }
      }
    ];
    
    const { error: insertError } = await supabase
      .from('activity_logs')
      .insert(sampleActivity);
    
    if (insertError) {
      console.error('Error inserting sample activity data:', insertError);
    } else {
      console.log('Sample activity data inserted successfully');
    }
  } else {
    console.log('Activity logs table already has data, skipping sample data insertion');
  }
}

async function insertSampleNotificationData() {
  // Insert sample notification data
  const { count, error: countError } = await supabase
    .from('notifications')
    .select('*', { count: 'exact', head: true });

  if (countError) {
    console.error('Error checking notifications count:', countError);
    return;
  }

  if (count === 0) {
    console.log('Inserting sample notification data...');
    
    const sampleNotifications = [
      {
        type: 'error',
        message: '3 patients require immediate attention',
        read: false
      },
      {
        type: 'warning',
        message: '5 upcoming appointments in next hour',
        read: false
      },
      {
        type: 'info',
        message: 'New treatment protocol available',
        read: false
      },
      {
        type: 'success',
        message: 'System backup completed successfully',
        read: true
      }
    ];
    
    const { error: insertError } = await supabase
      .from('notifications')
      .insert(sampleNotifications);
    
    if (insertError) {
      console.error('Error inserting sample notification data:', insertError);
    } else {
      console.log('Sample notification data inserted successfully');
    }
  } else {
    console.log('Notifications table already has data, skipping sample data insertion');
  }
}

async function insertSampleAppointmentData() {
  // Get patient IDs
  const { data: patients, error: patientsError } = await supabase
    .from('patients')
    .select('id');
  
  if (patientsError) {
    console.error('Error fetching patient IDs:', patientsError);
    return;
  }

  if (patients && patients.length > 0) {
    console.log('Inserting sample appointment data...');
    
    const sampleAppointments = patients.slice(0, 3).map((patient, index) => ({
      patient_id: patient.id,
      doctor: ['Dr. Smith', 'Dr. Johnson', 'Dr. Williams'][index],
      appointment_date: new Date(Date.now() + (index + 1) * 24 * 60 * 60 * 1000).toISOString(),
      status: ['pending', 'confirmed', 'pending'][index],
      notes: `Follow-up appointment ${index + 1}`
    }));
    
    const { error: insertError } = await supabase
      .from('appointments')
      .insert(sampleAppointments);
    
    if (insertError) {
      console.error('Error inserting sample appointment data:', insertError);
    } else {
      console.log('Sample appointment data inserted successfully');
    }
  } else {
    console.log('No patients found, skipping appointment data insertion');
  }
}

async function insertSampleMessageData() {
  // Get patient IDs
  const { data: patients, error: patientsError } = await supabase
    .from('patients')
    .select('id');
  
  if (patientsError) {
    console.error('Error fetching patient IDs:', patientsError);
    return;
  }

  if (patients && patients.length > 0) {
    console.log('Inserting sample message data...');
    
    const sampleMessages = [];
    
    // Create multiple messages for each patient
    patients.forEach((patient, patientIndex) => {
      const responseStatus = [true, true, false];
      
      for (let i = 0; i < 3; i++) {
        sampleMessages.push({
          patient_id: patient.id,
          sender: i % 2 === 0 ? 'Doctor' : 'Patient',
          content: `Sample message ${i + 1} for patient ${patientIndex + 1}`,
          is_responded: responseStatus[i],
          created_at: new Date(Date.now() - (3 - i) * 60 * 60 * 1000).toISOString()
        });
      }
    });
    
    const { error: insertError } = await supabase
      .from('messages')
      .insert(sampleMessages);
    
    if (insertError) {
      console.error('Error inserting sample message data:', insertError);
    } else {
      console.log('Sample message data inserted successfully');
    }
  } else {
    console.log('No patients found, skipping message data insertion');
  }
}

// Run the setup
setupTables()
  .then(() => {
    console.log('Setup script completed');
    process.exit(0);
  })
  .catch(error => {
    console.error('Script failed:', error);
    process.exit(1);
  }); 