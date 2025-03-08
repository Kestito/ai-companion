-- Drop existing trigger and function
drop trigger if exists users_encrypt_trigger on evelinaai.users;
drop function if exists evelinaai.encrypt_column();

-- Remove check constraints from users table
alter table evelinaai.users drop constraint if exists users_email_check;
alter table evelinaai.users drop constraint if exists users_phone_check;

-- Create new validation and encryption function
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

-- Create new trigger
create trigger users_validate_and_encrypt_trigger
before insert or update on evelinaai.users
for each row execute function evelinaai.validate_and_encrypt_user(); 