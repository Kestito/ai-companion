-- Script to migrate data from evelinaai schema to public schema
-- Run this after creating the tables in public schema

-- Step 1: First check if evelinaai schema exists
DO $$
DECLARE
    schema_exists BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1 FROM information_schema.schemata WHERE schema_name = 'evelinaai'
    ) INTO schema_exists;

    IF NOT schema_exists THEN
        RAISE NOTICE 'evelinaai schema does not exist. Nothing to migrate.';
        RETURN;
    END IF;
    
    -- Step 2: Check if the tables exist in evelinaai schema
    PERFORM 1 FROM information_schema.tables 
    WHERE table_schema = 'evelinaai' AND table_name = 'patients'
    LIMIT 1;
    
    IF NOT FOUND THEN
        RAISE NOTICE 'No tables found in evelinaai schema. Nothing to migrate.';
        RETURN;
    END IF;
    
    -- Step 3: Begin migration
    RAISE NOTICE 'Starting migration from evelinaai schema to public schema...';
    
    -- No need to disable triggers as we don't have encryption triggers anymore
    
    -- Migrate patients table
    INSERT INTO public.patients 
    SELECT * FROM evelinaai.patients
    ON CONFLICT (id) DO NOTHING;
    RAISE NOTICE 'Migrated patients table';
    
    -- Migrate conversations table
    INSERT INTO public.conversations 
    SELECT * FROM evelinaai.conversations
    ON CONFLICT (id) DO NOTHING;
    RAISE NOTICE 'Migrated conversations table';
    
    -- Migrate conversation_details table
    INSERT INTO public.conversation_details 
    SELECT * FROM evelinaai.conversation_details
    ON CONFLICT (id) DO NOTHING;
    RAISE NOTICE 'Migrated conversation_details table';
    
    -- Migrate short_term_memory table
    INSERT INTO public.short_term_memory 
    SELECT * FROM evelinaai.short_term_memory
    ON CONFLICT (id) DO NOTHING;
    RAISE NOTICE 'Migrated short_term_memory table';
    
    -- Migrate long_term_memory table
    INSERT INTO public.long_term_memory 
    SELECT * FROM evelinaai.long_term_memory
    ON CONFLICT (id) DO NOTHING;
    RAISE NOTICE 'Migrated long_term_memory table';
    
    -- Migrate scheduled_appointments table
    INSERT INTO public.scheduled_appointments 
    SELECT * FROM evelinaai.scheduled_appointments
    ON CONFLICT (id) DO NOTHING;
    RAISE NOTICE 'Migrated scheduled_appointments table';
    
    -- Migrate risk_assessments table
    INSERT INTO public.risk_assessments 
    SELECT * FROM evelinaai.risk_assessments
    ON CONFLICT (id) DO NOTHING;
    RAISE NOTICE 'Migrated risk_assessments table';
    
    -- Migrate reports table
    INSERT INTO public.reports 
    SELECT * FROM evelinaai.reports
    ON CONFLICT (id) DO NOTHING;
    RAISE NOTICE 'Migrated reports table';
    
    RAISE NOTICE 'Migration completed successfully!';
    RAISE NOTICE 'To verify the migration, run: SELECT COUNT(*) FROM public.patients; SELECT COUNT(*) FROM evelinaai.patients;';
END $$; 