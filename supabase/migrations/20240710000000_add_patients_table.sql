-- Add patients table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.patients (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    platform TEXT NOT NULL CHECK (platform IN ('telegram', 'whatsapp', 'web', 'unknown')),
    user_id TEXT,
    diagnosis TEXT,
    doctor TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_patients_platform ON public.patients(platform);
CREATE INDEX IF NOT EXISTS idx_patients_status ON public.patients(status);
CREATE INDEX IF NOT EXISTS idx_patients_user_id ON public.patients(user_id);

-- Enable Row Level Security
ALTER TABLE public.patients ENABLE ROW LEVEL SECURITY;

-- Create a policy that allows all authenticated users to read patients
CREATE POLICY "Allow authenticated users to read patients"
    ON public.patients
    FOR SELECT
    TO authenticated
    USING (true);

-- Create a policy that allows insertion of patients by public users (for messaging platforms)
CREATE POLICY "Allow public users to insert patients"
    ON public.patients
    FOR INSERT
    TO public
    WITH CHECK (true);

-- Create a function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to automatically update the updated_at column
DROP TRIGGER IF EXISTS update_patients_updated_at ON public.patients;
CREATE TRIGGER update_patients_updated_at
    BEFORE UPDATE ON public.patients
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- Grant access to the public role
GRANT ALL ON public.patients TO public; 