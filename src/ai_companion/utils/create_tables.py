"""
Utility script to create necessary tables in Supabase.
"""

import asyncio
import logging
from ai_companion.utils.supabase import get_supabase_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_short_term_memory_table():
    """Create the short_term_memory table in Supabase if it doesn't exist."""
    
    # Get Supabase client
    supabase = get_supabase_client()
    
    if not supabase:
        logger.error("Failed to initialize Supabase client")
        return False
    
    try:
        # Check if the table exists
        response = supabase.table("short_term_memory").select("id").limit(1).execute()
        logger.info("short_term_memory table already exists")
        return True
    except Exception as e:
        # Table likely doesn't exist, create it
        logger.info(f"Creating short_term_memory table: {e}")
        
        # Create the table using Supabase SQL
        sql = """
        CREATE TABLE IF NOT EXISTS short_term_memory (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            chat_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            content JSONB NOT NULL,
            state JSONB,
            metadata JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            expires_at TIMESTAMPTZ NOT NULL,
            
            CONSTRAINT short_term_memory_session_id_idx UNIQUE (session_id, created_at)
        );
        
        -- Add indexes for faster queries
        CREATE INDEX IF NOT EXISTS short_term_memory_session_id_idx ON short_term_memory(session_id);
        CREATE INDEX IF NOT EXISTS short_term_memory_user_id_idx ON short_term_memory(user_id);
        CREATE INDEX IF NOT EXISTS short_term_memory_created_at_idx ON short_term_memory(created_at);
        CREATE INDEX IF NOT EXISTS short_term_memory_expires_at_idx ON short_term_memory(expires_at);
        
        -- Create RLS policy
        ALTER TABLE short_term_memory ENABLE ROW LEVEL SECURITY;
        
        -- Create policy for authenticated users
        CREATE POLICY "Allow full access to authenticated users" 
            ON short_term_memory 
            FOR ALL 
            TO authenticated 
            USING (true);
            
        -- Optionally, create policy for anonymous users too
        CREATE POLICY "Allow anonymous read/write access" 
            ON short_term_memory 
            FOR ALL 
            TO anon 
            USING (true);
        """
        
        try:
            # Execute the SQL directly
            supabase.rpc("admin_exec_sql", {"sql": sql}).execute()
            logger.info("Successfully created short_term_memory table")
            return True
        except Exception as e:
            logger.error(f"Error creating short_term_memory table: {e}")
            return False

def main():
    # Create the short_term_memory table
    success = create_short_term_memory_table()
    
    if success:
        logger.info("All tables created successfully")
    else:
        logger.warning("Some tables couldn't be created")

if __name__ == "__main__":
    main() 