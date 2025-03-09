-- Create patients table in the evelinaai schema
CREATE TABLE IF NOT EXISTS evelinaai.patients (
  id VARCHAR(20) PRIMARY KEY, -- Format like P10001
  name VARCHAR(255) NOT NULL,
  age INT NOT NULL CHECK (age > 0 AND age < 120),
  gender VARCHAR(10) NOT NULL CHECK (gender IN ('male', 'female', 'other')),
  status VARCHAR(20) NOT NULL CHECK (status IN ('stable', 'critical', 'moderate', 'recovering', 'discharged', 'scheduled')),
  admission_date DATE NOT NULL,
  diagnosis VARCHAR(255) NOT NULL,
  doctor VARCHAR(255) NOT NULL,
  room_number VARCHAR(10),
  contact_number VARCHAR(20),
  email VARCHAR(255),
  medical_history JSONB,
  current_medications JSONB,
  allergies JSONB,
  vital_signs JSONB,
  last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add index for faster querying by status
CREATE INDEX idx_patients_status ON evelinaai.patients(status);

-- Function to transform columns to match the Patient interface
CREATE OR REPLACE FUNCTION evelinaai.transform_patient_model() RETURNS TRIGGER AS $$
BEGIN
  -- Convert from snake_case to camelCase for frontend compatibility
  NEW.admissionDate := NEW.admission_date;
  NEW.roomNumber := NEW.room_number;
  NEW.contactNumber := NEW.contact_number;
  NEW.medicalHistory := NEW.medical_history;
  NEW.currentMedications := NEW.current_medications;
  NEW.vitalSigns := NEW.vital_signs;
  NEW.lastUpdated := NEW.last_updated;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to transform patient data before sending to client
CREATE TRIGGER transform_patient_before_select
BEFORE SELECT ON evelinaai.patients
FOR EACH ROW
EXECUTE FUNCTION evelinaai.transform_patient_model();

-- Insert some example patients for testing
INSERT INTO evelinaai.patients (
  id, name, age, gender, status, admission_date, diagnosis, doctor, 
  room_number, contact_number, email, medical_history, current_medications, last_updated
)
VALUES
  (
    'P10001', 
    'William Wilson', 
    30, 
    'male', 
    'discharged', 
    '2024-02-10', 
    'Hypertension', 
    'Dr. Elizabeth Taylor', 
    NULL,
    '(555) 123-4567', 
    'william.wilson@example.com', 
    '["Asthma", "Seasonal Allergies"]', 
    '["Lisinopril 10mg", "Amlodipine 5mg"]', 
    NOW()
  ),
  (
    'P10002', 
    'Sophia Lewis', 
    76, 
    'female', 
    'critical', 
    '2024-03-15', 
    'Sinusitis', 
    'Dr. Michael Chen', 
    '545',
    '(555) 234-5678', 
    'sophia.lewis@example.com', 
    NULL,
    '["Amoxicillin 500mg", "Pseudoephedrine 30mg"]', 
    NOW()
  ),
  (
    'P10003', 
    'Emma Walker', 
    69, 
    'female', 
    'critical', 
    '2024-04-20', 
    'Migraine', 
    'Dr. Amanda Martinez', 
    '549',
    '(555) 345-6789', 
    'emma.walker@example.com', 
    '["Chronic Migraine", "Hypertension"]', 
    '["Sumatriptan 50mg", "Propranolol 20mg"]', 
    NOW()
  ),
  (
    'P10004', 
    'Harper Johnson', 
    63, 
    'male', 
    'moderate', 
    '2024-05-01', 
    'Sinusitis', 
    'Dr. Elizabeth Taylor', 
    '474',
    '(555) 456-7890', 
    'harper.johnson@example.com', 
    NULL, 
    '["Amoxicillin 500mg", "Fluticasone nasal spray"]', 
    NOW()
  );

-- Add row level security policies
ALTER TABLE evelinaai.patients ENABLE ROW LEVEL SECURITY;

-- RLS policy - In production, you would limit this to authenticated users only
CREATE POLICY "Allow full access to patients table for authenticated users"
  ON evelinaai.patients
  USING (true);  -- Allowing access to all rows for demo purposes

-- Grant permissions
GRANT ALL ON evelinaai.patients TO public; 