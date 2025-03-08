-- Create tables with security policies
create schema if not exists evelinaai;

-- Users table with authentication integration
create table evelinaai.users (
    id uuid primary key default gen_random_uuid(),
    email text unique,
    phone text,
    created_at timestamptz not null default current_timestamp,
    last_active timestamptz,
    preferred_language text default 'lt',
    subsidy_eligible boolean default false,
    legal_consents jsonb,
    support_status text check (support_status in ('active', 'pending', 'resolved')),
    constraint valid_legal_consents check (legal_consents ?& array['privacy', 'terms'])
);

-- Conversations with platform tracking
create table evelinaai.conversations (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references evelinaai.users(id) on delete cascade,
    platform text not null check (platform in ('telegram', 'whatsapp', 'chainlit')),
    start_time timestamptz not null default current_timestamp,
    end_time timestamptz,
    conversation_type text not null check (conversation_type in ('support', 'subsidy', 'legal', 'general')),
    status text not null check (status in ('active', 'resolved')) default 'active'
);

-- Conversation details with message types
create table evelinaai.conversation_details (
    id uuid primary key default gen_random_uuid(),
    conversation_id uuid references evelinaai.conversations(id) on delete cascade,
    message_content text not null,
    message_type text not null check (message_type in ('text', 'voice', 'document')),
    sent_at timestamptz not null default current_timestamp,
    sender text not null check (sender in ('user', 'evelina')),
    metadata jsonb
);

-- Memory tables with TTL
create table evelinaai.short_term_memory (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references evelinaai.users(id) on delete cascade,
    conversation_id uuid references evelinaai.conversations(id) on delete cascade,
    context jsonb not null,
    expires_at timestamptz not null default (now() + interval '30 minutes')
);

create table evelinaai.long_term_memory (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references evelinaai.users(id) on delete cascade,
    memory_type text not null check (memory_type in ('preference', 'interaction_pattern')),
    content jsonb not null,
    recorded_at timestamptz not null default current_timestamp
);

-- Proactive system tables
create table evelinaai.scheduled_appointments (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references evelinaai.users(id) on delete cascade,
    scheduled_time timestamptz not null,
    contact_method text not null check (contact_method in ('push', 'email', 'sms')),
    purpose text not null check (purpose in ('subsidy_reminder', 'legal_update', 'support_checkin')),
    status text not null check (status in ('pending', 'completed')) default 'pending'
);

-- Risk assessment with anonymization
create table evelinaai.risk_assessments (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references evelinaai.users(id) on delete cascade,
    risk_type text not null check (risk_type in ('support', 'subsidy', 'legal')),
    risk_level text not null check (risk_level in ('low', 'medium', 'high')),
    detected_at timestamptz not null default current_timestamp,
    trigger_criteria text not null,
    anonymized_flag boolean not null default false
);

-- Reporting system
create table evelinaai.reports (
    id uuid primary key default gen_random_uuid(),
    generated_by uuid references evelinaai.users(id) on delete set null,
    report_type text not null check (report_type in ('usage', 'interaction', 'subsidy')),
    generated_at timestamptz not null default current_timestamp,
    report_format text not null check (report_format in ('pdf', 'csv', 'json')),
    storage_path text not null,
    parameters jsonb
);

-- Indexes for performance
create index idx_conversations_user on evelinaai.conversations(user_id);
create index idx_memory_expiry on evelinaai.short_term_memory(expires_at);
create index idx_risk_anonymized on evelinaai.risk_assessments(anonymized_flag);

-- RLS Policies
alter table evelinaai.users enable row level security;
alter table evelinaai.conversations enable row level security;
alter table evelinaai.conversation_details enable row level security;
alter table evelinaai.risk_assessments enable row level security;

create policy "Users can only access their own data" 
on evelinaai.users 
using (id = auth.uid());

create policy "Conversations visibility" 
on evelinaai.conversations 
using (user_id = auth.uid());

create policy "Anonymized risk data access"
on evelinaai.risk_assessments
using (anonymized_flag or user_id = auth.uid());

-- Enable API access
grant usage on schema evelinaai to public;
grant all privileges on all tables in schema evelinaai to public;
grant all privileges on all routines in schema evelinaai to public;

-- Security features
create or replace function evelinaai.validate_and_encrypt_user() returns trigger as $$
begin
  -- Validate email format before encryption
  if new.email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' then
    raise exception 'Invalid email format';
  end if;
  
  -- Validate phone format before encryption
  if new.phone is not null and new.phone !~ '^\+?[0-9]{8,15}$' then
    raise exception 'Invalid phone format';
  end if;
  
  -- Encrypt after validation
  new.email = pgp_sym_encrypt(new.email, '${POSTGRES_PASSWORD}');
  if new.phone is not null then
    new.phone = pgp_sym_encrypt(new.phone, '${POSTGRES_PASSWORD}');
  end if;
  
  return new;
end;
$$ language plpgsql;

create trigger users_validate_and_encrypt_trigger
before insert or update on evelinaai.users
for each row execute function evelinaai.validate_and_encrypt_user();

-- Enable JWT authentication
create type evelinaai.jwt_token as (
  role text,
  user_id uuid,
  exp integer
); 