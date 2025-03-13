-- Create all tables in public schema
-- No data hiding, no RLS policies, replaces Users with Patients

-- Patients table (replacing Users)
create table if not exists public.patients (
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
create table if not exists public.conversations (
    id uuid primary key default gen_random_uuid(),
    patient_id uuid references public.patients(id) on delete cascade,
    platform text not null check (platform in ('telegram', 'whatsapp', 'chainlit')),
    start_time timestamptz not null default current_timestamp,
    end_time timestamptz,
    conversation_type text not null check (conversation_type in ('support', 'subsidy', 'legal', 'general')),
    status text not null check (status in ('active', 'resolved')) default 'active'
);

-- Conversation details with message types
create table if not exists public.conversation_details (
    id uuid primary key default gen_random_uuid(),
    conversation_id uuid references public.conversations(id) on delete cascade,
    message_content text not null,
    message_type text not null check (message_type in ('text', 'voice', 'document')),
    sent_at timestamptz not null default current_timestamp,
    sender text not null check (sender in ('patient', 'evelina')),
    metadata jsonb
);

-- Memory tables with TTL
create table if not exists public.short_term_memory (
    id uuid primary key default gen_random_uuid(),
    patient_id uuid references public.patients(id) on delete cascade,
    conversation_id uuid references public.conversations(id) on delete cascade,
    context jsonb not null,
    expires_at timestamptz not null default (now() + interval '30 minutes')
);

create table if not exists public.long_term_memory (
    id uuid primary key default gen_random_uuid(),
    patient_id uuid references public.patients(id) on delete cascade,
    memory_type text not null check (memory_type in ('preference', 'interaction_pattern')),
    content jsonb not null,
    recorded_at timestamptz not null default current_timestamp
);

-- Proactive system tables
create table if not exists public.scheduled_appointments (
    id uuid primary key default gen_random_uuid(),
    patient_id uuid references public.patients(id) on delete cascade,
    scheduled_time timestamptz not null,
    contact_method text not null check (contact_method in ('push', 'email', 'sms')),
    purpose text not null check (purpose in ('subsidy_reminder', 'legal_update', 'support_checkin')),
    status text not null check (status in ('pending', 'completed')) default 'pending'
);

-- Risk assessment without anonymization
create table if not exists public.risk_assessments (
    id uuid primary key default gen_random_uuid(),
    patient_id uuid references public.patients(id) on delete cascade,
    risk_type text not null check (risk_type in ('support', 'subsidy', 'legal')),
    risk_level text not null check (risk_level in ('low', 'medium', 'high')),
    detected_at timestamptz not null default current_timestamp,
    trigger_criteria text not null
);

-- Reporting system
create table if not exists public.reports (
    id uuid primary key default gen_random_uuid(),
    generated_by uuid references public.patients(id) on delete set null,
    report_type text not null check (report_type in ('usage', 'interaction', 'subsidy')),
    generated_at timestamptz not null default current_timestamp,
    report_format text not null check (report_format in ('pdf', 'csv', 'json')),
    storage_path text not null,
    parameters jsonb
);

-- Scheduled messages table
create table if not exists public.scheduled_messages (
    id uuid primary key default gen_random_uuid(),
    patient_id uuid references public.patients(id) on delete cascade,
    scheduled_time timestamptz not null,
    message_content text not null,
    status text not null check (status in ('pending', 'sent', 'failed')) default 'pending',
    platform text not null check (platform in ('telegram', 'whatsapp', 'email')),
    created_at timestamptz not null default current_timestamp
);

-- Messages table
create table if not exists public.messages (
    id uuid primary key default gen_random_uuid(),
    patient_id uuid references public.patients(id) on delete cascade,
    content text not null,
    sent_at timestamptz not null default current_timestamp,
    read_at timestamptz,
    message_type text not null check (message_type in ('notification', 'alert', 'reminder')),
    priority text not null check (priority in ('low', 'medium', 'high')) default 'medium'
);

-- Indexes for performance
create index if not exists idx_conversations_patient on public.conversations(patient_id);
create index if not exists idx_memory_expiry on public.short_term_memory(expires_at);
create index if not exists idx_patients_email on public.patients(email);
create index if not exists idx_scheduled_messages_time on public.scheduled_messages(scheduled_time);
create index if not exists idx_messages_patient on public.messages(patient_id);

-- Sample data for testing (Optional - comment out if not needed)
insert into public.patients (email, first_name, last_name, preferred_language)
values 
  ('patient1@example.com', 'John', 'Doe', 'en'),
  ('patient2@example.com', 'Jane', 'Smith', 'lt')
on conflict (email) do nothing; 