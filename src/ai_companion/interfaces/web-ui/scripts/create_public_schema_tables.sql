-- Create tables in public schema with the same structure as evelinaai schema
-- This allows direct access without schema prefixing

-- Patients table with no data hiding
create table public.patients (
    id uuid primary key default gen_random_uuid(),
    email text unique,
    phone text,
    first_name text,
    last_name text,
    created_at timestamptz not null default current_timestamp,
    last_active timestamptz,
    preferred_language text default 'lt',
    subsidy_eligible boolean default false,
    legal_consents jsonb,
    support_status text check (support_status in ('active', 'pending', 'resolved'))
);

-- Conversations with platform tracking
create table public.conversations (
    id uuid primary key default gen_random_uuid(),
    patient_id uuid references public.patients(id) on delete cascade,
    platform text not null check (platform in ('telegram', 'whatsapp', 'chainlit')),
    start_time timestamptz not null default current_timestamp,
    end_time timestamptz,
    conversation_type text not null check (conversation_type in ('support', 'subsidy', 'legal', 'general')),
    status text not null check (status in ('active', 'resolved')) default 'active'
);

-- Conversation details with message types
create table public.conversation_details (
    id uuid primary key default gen_random_uuid(),
    conversation_id uuid references public.conversations(id) on delete cascade,
    message_content text not null,
    message_type text not null check (message_type in ('text', 'voice', 'document')),
    sent_at timestamptz not null default current_timestamp,
    sender text not null check (sender in ('patient', 'evelina')),
    metadata jsonb
);

-- Memory tables with TTL
create table public.short_term_memory (
    id uuid primary key default gen_random_uuid(),
    patient_id uuid references public.patients(id) on delete cascade,
    conversation_id uuid references public.conversations(id) on delete cascade,
    context jsonb not null,
    expires_at timestamptz not null default (now() + interval '30 minutes')
);

create table public.long_term_memory (
    id uuid primary key default gen_random_uuid(),
    patient_id uuid references public.patients(id) on delete cascade,
    memory_type text not null check (memory_type in ('preference', 'interaction_pattern')),
    content jsonb not null,
    recorded_at timestamptz not null default current_timestamp
);

-- Proactive system tables
create table public.scheduled_appointments (
    id uuid primary key default gen_random_uuid(),
    patient_id uuid references public.patients(id) on delete cascade,
    scheduled_time timestamptz not null,
    contact_method text not null check (contact_method in ('push', 'email', 'sms')),
    purpose text not null check (purpose in ('subsidy_reminder', 'legal_update', 'support_checkin')),
    status text not null check (status in ('pending', 'completed')) default 'pending'
);

-- Risk assessment without anonymization
create table public.risk_assessments (
    id uuid primary key default gen_random_uuid(),
    patient_id uuid references public.patients(id) on delete cascade,
    risk_type text not null check (risk_type in ('support', 'subsidy', 'legal')),
    risk_level text not null check (risk_level in ('low', 'medium', 'high')),
    detected_at timestamptz not null default current_timestamp,
    trigger_criteria text not null
);

-- Reporting system
create table public.reports (
    id uuid primary key default gen_random_uuid(),
    generated_by uuid references public.patients(id) on delete set null,
    report_type text not null check (report_type in ('usage', 'interaction', 'subsidy')),
    generated_at timestamptz not null default current_timestamp,
    report_format text not null check (report_format in ('pdf', 'csv', 'json')),
    storage_path text not null,
    parameters jsonb
);

-- Indexes for performance
create index idx_conversations_patient on public.conversations(patient_id);
create index idx_memory_expiry on public.short_term_memory(expires_at);

-- No RLS Policies as requested

-- No data encryption functions as requested

-- Optional: Create views to expose evelinaai schema tables if both schemas need to coexist
-- Uncomment these if you want to maintain both schemas

-- CREATE OR REPLACE VIEW public.evelinaai_patients AS SELECT * FROM evelinaai.patients;
-- CREATE OR REPLACE VIEW public.evelinaai_conversations AS SELECT * FROM evelinaai.conversations;
-- CREATE OR REPLACE VIEW public.evelinaai_conversation_details AS SELECT * FROM evelinaai.conversation_details;
-- CREATE OR REPLACE VIEW public.evelinaai_short_term_memory AS SELECT * FROM evelinaai.short_term_memory;
-- CREATE OR REPLACE VIEW public.evelinaai_long_term_memory AS SELECT * FROM evelinaai.long_term_memory;
-- CREATE OR REPLACE VIEW public.evelinaai_scheduled_appointments AS SELECT * FROM evelinaai.scheduled_appointments;
-- CREATE OR REPLACE VIEW public.evelinaai_risk_assessments AS SELECT * FROM evelinaai.risk_assessments;
-- CREATE OR REPLACE VIEW public.evelinaai_reports AS SELECT * FROM evelinaai.reports; 