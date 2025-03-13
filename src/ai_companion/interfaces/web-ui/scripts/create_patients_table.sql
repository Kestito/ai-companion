-- Create patients table with no data hiding
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

-- Add indexes for performance
create index if not exists idx_patients_email on public.patients(email);

-- Sample data insert (optional)
insert into public.patients (email, first_name, last_name, preferred_language)
values 
  ('patient1@example.com', 'John', 'Doe', 'en'),
  ('patient2@example.com', 'Jane', 'Smith', 'lt')
on conflict (email) do nothing; 