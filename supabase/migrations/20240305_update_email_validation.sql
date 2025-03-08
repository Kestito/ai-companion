-- First, make email nullable and drop existing constraints
alter table evelinaai.users alter column email drop not null;
alter table evelinaai.users drop constraint if exists users_email_check;
alter table evelinaai.users drop constraint if exists users_phone_check;

-- Drop existing triggers and functions
drop trigger if exists users_encrypt_trigger on evelinaai.users;
drop trigger if exists users_validate_and_encrypt_trigger on evelinaai.users;
drop function if exists evelinaai.encrypt_column();
drop function if exists evelinaai.validate_and_encrypt_user();

-- Create new validation and encryption function
create or replace function evelinaai.validate_and_encrypt_user() returns trigger as $$
declare
    email_regex text := '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';
    phone_regex text := '^\+?[0-9]{8,15}$';
begin
    -- Skip validation if email is null or already encrypted
    if new.email is not null and new.email !~ '^\\x' then
        -- Validate email format before encryption
        if new.email !~ email_regex then
            raise exception 'Invalid email format: %', new.email;
        end if;
        -- Encrypt email
        new.email = pgp_sym_encrypt(new.email, '${POSTGRES_PASSWORD}');
    end if;

    -- Skip validation if phone is null or already encrypted
    if new.phone is not null and new.phone !~ '^\\x' then
        -- Validate phone format before encryption
        if new.phone !~ phone_regex then
            raise exception 'Invalid phone format: %', new.phone;
        end if;
        -- Encrypt phone
        new.phone = pgp_sym_encrypt(new.phone, '${POSTGRES_PASSWORD}');
    end if;

    return new;
end;
$$ language plpgsql;

-- Create new trigger
create trigger users_validate_and_encrypt_trigger
    before insert or update on evelinaai.users
    for each row execute function evelinaai.validate_and_encrypt_user(); 