-- Create scheduled_checks table in the public schema
CREATE TABLE IF NOT EXISTS public.scheduled_checks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title TEXT NOT NULL,
  description TEXT,
  frequency TEXT NOT NULL CHECK (frequency IN ('daily', 'weekly', 'monthly', 'once')),
  next_scheduled TIMESTAMP WITH TIME ZONE NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'cancelled', 'failed')),
  platform TEXT NOT NULL CHECK (platform IN ('whatsapp', 'telegram', 'sms', 'email')),
  patient_id UUID NOT NULL REFERENCES public.patients(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_scheduled_checks_patient_id ON public.scheduled_checks(patient_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_checks_next_scheduled ON public.scheduled_checks(next_scheduled);
CREATE INDEX IF NOT EXISTS idx_scheduled_checks_status ON public.scheduled_checks(status);

-- Create trigger to update the updated_at column
CREATE OR REPLACE FUNCTION public.update_scheduled_checks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_scheduled_checks_updated_at ON public.scheduled_checks;
CREATE TRIGGER update_scheduled_checks_updated_at
BEFORE UPDATE ON public.scheduled_checks
FOR EACH ROW
EXECUTE FUNCTION public.update_scheduled_checks_updated_at();

-- Insert some sample data
INSERT INTO public.scheduled_checks (title, description, frequency, next_scheduled, status, platform, patient_id)
SELECT 
  'Blood Pressure Check',
  'Regular monitoring of blood pressure',
  'daily',
  NOW() + INTERVAL '1 day',
  'pending',
  'telegram',
  id
FROM public.patients
LIMIT 1;

INSERT INTO public.scheduled_checks (title, description, frequency, next_scheduled, status, platform, patient_id)
SELECT 
  'Medication Reminder',
  'Reminder to take prescribed medication',
  'daily',
  NOW() + INTERVAL '12 hours',
  'pending',
  'telegram',
  id
FROM public.patients
LIMIT 1;

INSERT INTO public.scheduled_checks (title, description, frequency, next_scheduled, status, platform, patient_id)
SELECT 
  'Weekly Health Survey',
  'Survey to assess overall health status',
  'weekly',
  NOW() + INTERVAL '7 days',
  'pending',
  'whatsapp',
  id
FROM public.patients
LIMIT 1; 