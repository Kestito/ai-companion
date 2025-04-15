-- Add missing fields to the patients table
ALTER TABLE public.patients
ADD COLUMN IF NOT EXISTS risk TEXT NOT NULL DEFAULT 'Low' CHECK (risk IN ('Low', 'Medium', 'High'));

-- Create index for risk field for better query performance
CREATE INDEX IF NOT EXISTS idx_patients_risk ON public.patients(risk);

-- Add comment to describe the purpose of these fields
COMMENT ON COLUMN public.patients.risk IS 'Patient risk assessment level: Low, Medium, or High'; 