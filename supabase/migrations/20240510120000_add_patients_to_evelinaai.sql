-- Add patients table to evelinaai schema
CREATE TABLE IF NOT EXISTS evelinaai.patients (
  id VARCHAR(20) PRIMARY KEY,
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
CREATE INDEX idx_evelinaai_patients_status ON evelinaai.patients(status);

-- Create a function to sync data from the patients.patients table to evelinaai.patients
CREATE OR REPLACE FUNCTION sync_patients_to_evelinaai() RETURNS TRIGGER AS $$
DECLARE
  age_calc INT;
  status_mapped VARCHAR(20);
  diagnosis_text VARCHAR(255);
  doctor_name VARCHAR(255);
BEGIN
  -- Calculate age from date_of_birth
  age_calc := DATE_PART('year', AGE(CURRENT_DATE, NEW.date_of_birth::DATE));
  
  -- Map status
  IF NEW.status = 'inactive' THEN
    status_mapped := 'discharged';
  ELSIF NEW.risk_level = 'high' THEN
    status_mapped := 'critical';
  ELSIF NEW.risk_level = 'medium' THEN
    status_mapped := 'moderate';
  ELSE
    status_mapped := 'stable';
  END IF;
  
  -- Default diagnosis
  diagnosis_text := COALESCE(NEW.notes, 'General checkup');
  IF LENGTH(diagnosis_text) > 255 THEN
    diagnosis_text := SUBSTRING(diagnosis_text, 1, 252) || '...';
  END IF;
  
  -- Get doctor name from specialists table
  SELECT name INTO doctor_name FROM patients.specialists 
  WHERE id = NEW.assigned_specialist;
  IF doctor_name IS NULL THEN
    doctor_name := 'Dr. Unknown';
  END IF;
  
  -- Insert or update into evelinaai.patients
  INSERT INTO evelinaai.patients (
    id, name, age, gender, status, admission_date, diagnosis, doctor, 
    email, last_updated, created_at
  ) VALUES (
    NEW.id,
    NEW.name,
    age_calc,
    NEW.gender,
    status_mapped,
    NEW.created_at::DATE,
    diagnosis_text,
    doctor_name,
    'patient@example.com', -- Placeholder email
    NEW.updated_at,
    NEW.created_at
  )
  ON CONFLICT (id) 
  DO UPDATE SET
    name = EXCLUDED.name,
    age = EXCLUDED.age,
    gender = EXCLUDED.gender,
    status = EXCLUDED.status,
    diagnosis = EXCLUDED.diagnosis,
    doctor = EXCLUDED.doctor,
    last_updated = EXCLUDED.last_updated;
    
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to sync data
CREATE TRIGGER sync_patients_trigger
AFTER INSERT OR UPDATE ON patients.patients
FOR EACH ROW
EXECUTE FUNCTION sync_patients_to_evelinaai();

-- Perform initial data sync
DO $$
DECLARE
  p RECORD;
BEGIN
  FOR p IN SELECT * FROM patients.patients LOOP
    -- Simulate trigger by using the same function for each existing record
    PERFORM sync_patients_to_evelinaai(p);
  END LOOP;
END $$;

-- Enable RLS on the new table
ALTER TABLE evelinaai.patients ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow access to all users for now
CREATE POLICY "Allow access to all users" 
ON evelinaai.patients 
FOR ALL 
USING (true);

-- Grant access
GRANT ALL ON evelinaai.patients TO public; 