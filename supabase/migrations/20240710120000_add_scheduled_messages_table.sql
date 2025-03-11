-- Add scheduled_messages table to public schema
CREATE TABLE IF NOT EXISTS public.scheduled_messages (
    id UUID PRIMARY KEY,
    patient_id UUID REFERENCES public.patients(id),
    recipient_id TEXT NOT NULL,
    platform TEXT NOT NULL CHECK (platform IN ('telegram', 'whatsapp')),
    message_content TEXT NOT NULL,
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    template_key TEXT,
    parameters JSONB,
    recurrence_pattern JSONB,
    status TEXT NOT NULL CHECK (status IN ('pending', 'sent', 'failed', 'cancelled')),
    error_message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_status_time ON public.scheduled_messages(status, scheduled_time);
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_patient ON public.scheduled_messages(patient_id);

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION public.update_scheduled_messages_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_scheduled_messages_updated_at ON public.scheduled_messages;

CREATE TRIGGER set_scheduled_messages_updated_at
BEFORE UPDATE ON public.scheduled_messages
FOR EACH ROW
EXECUTE FUNCTION public.update_scheduled_messages_updated_at();

-- Enable Row Level Security
ALTER TABLE public.scheduled_messages ENABLE ROW LEVEL SECURITY;

-- Create a policy that allows all authenticated users to read scheduled messages
CREATE POLICY "Allow authenticated users to read scheduled messages"
    ON public.scheduled_messages
    FOR SELECT
    TO authenticated
    USING (true);

-- Create a policy that allows service role to manage scheduled messages
CREATE POLICY "Allow service role to manage scheduled messages"
    ON public.scheduled_messages
    USING (true)
    WITH CHECK (true);

-- Grant access to the public role
GRANT ALL ON public.scheduled_messages TO public; 