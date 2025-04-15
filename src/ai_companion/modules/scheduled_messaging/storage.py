"""
Storage module for scheduled messages.

This module provides functions for storing and retrieving scheduled
messages from the database.
"""

import logging
import json
from typing import Dict, Any, List, Optional
import datetime
from uuid import UUID

# Try both import patterns for compatibility
try:
    from src.ai_companion.utils.supabase import get_supabase_client
    from src.ai_companion.settings import settings
except ImportError:
    try:
        from ai_companion.utils.supabase import get_supabase_client
        from ai_companion.settings import settings
    except ImportError:
        # For documentation purposes only
        get_supabase_client = settings = None

logger = logging.getLogger(__name__)

async def create_scheduled_messages_table():
    """
    Create the scheduled_messages table if it doesn't exist.
    """
    supabase = get_supabase_client()
    
    try:
        # Check if table exists
        tables = supabase.rpc("get_tables").execute()
        table_exists = False
        
        if hasattr(tables, "data"):
            table_names = [table.get("name") for table in tables.data]
            table_exists = "scheduled_messages" in table_names
        
        if not table_exists:
            # Create SQL query for table creation
            create_table_query = """
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
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE
            );
            
            CREATE INDEX IF NOT EXISTS idx_scheduled_messages_status_time ON public.scheduled_messages(status, scheduled_time);
            CREATE INDEX IF NOT EXISTS idx_scheduled_messages_patient ON public.scheduled_messages(patient_id);
            
            -- Trigger for updated_at
            CREATE OR REPLACE FUNCTION update_scheduled_messages_updated_at()
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
            EXECUTE FUNCTION update_scheduled_messages_updated_at();
            """
            
            # Execute the SQL query
            supabase.rpc("exec_sql", {"sql": create_table_query}).execute()
            logger.info("Created scheduled_messages table")
        else:
            logger.info("scheduled_messages table already exists")
    
    except Exception as e:
        logger.error(f"Failed to create scheduled_messages table: {e}")

async def get_pending_messages() -> List[Dict[str, Any]]:
    """
    Get all pending scheduled messages.
    
    Returns:
        List of pending messages
    """
    supabase = get_supabase_client()
    now = datetime.now().isoformat()
    
    try:
        result = supabase.table("scheduled_messages") \
            .select("*") \
            .eq("status", "pending") \
            .lte("scheduled_time", now) \
            .execute()
            
        if hasattr(result, 'data'):
            return result.data
        
        return []
    except Exception as e:
        logger.error(f"Failed to fetch pending messages: {e}")
        return []

async def update_message_status(schedule_id: str, 
                            status: str, 
                            details: Optional[Dict[str, Any]] = None) -> bool:
    """
    Update the status of a scheduled message.
    
    Args:
        schedule_id: The ID of the scheduled message
        status: The new status (sent, failed, cancelled)
        details: Optional details for the update
        
    Returns:
        True if successful, False otherwise
    """
    supabase = get_supabase_client()
    
    try:
        update_data = {"status": status}
        
        if status == "sent":
            update_data["sent_at"] = datetime.now().isoformat()
        elif status == "failed":
            update_data["failed_at"] = datetime.now().isoformat()
            
            if details and "error" in details:
                update_data["error_message"] = details["error"]
        
        supabase.table("scheduled_messages").update(update_data).eq("id", schedule_id).execute()
        return True
    except Exception as e:
        logger.error(f"Failed to update message status: {e}")
        return False

async def get_patient_scheduled_messages(patient_id: str) -> List[Dict[str, Any]]:
    """Get all scheduled messages for a specific patient.
    
    Args:
        patient_id: UUID of the patient
        
    Returns:
        List of scheduled message records for the patient
    """
    try:
        logger.debug(f"Fetching scheduled messages for patient {patient_id}")
        supabase = get_supabase_client()
        
        response = supabase.table("scheduled_messages") \
            .select("*") \
            .eq("patient_id", patient_id) \
            .order("scheduled_time", desc=False) \
            .execute()
        
        # Extract the data from the response
        if hasattr(response, 'data'):
            messages = response.data
            logger.debug(f"Found {len(messages)} scheduled messages for patient {patient_id}")
            return messages
        
        logger.warning(f"No data found in response for patient {patient_id}")
        return []
    except Exception as e:
        logger.error(f"Failed to fetch scheduled messages for patient {patient_id}: {e}")
        return []

async def get_scheduled_message(schedule_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a scheduled message by ID.
    
    Args:
        schedule_id: The ID of the scheduled message
        
    Returns:
        The scheduled message or None if not found
    """
    supabase = get_supabase_client()
    
    try:
        result = supabase.table("scheduled_messages") \
            .select("*") \
            .eq("id", schedule_id) \
            .execute()
            
        if hasattr(result, 'data') and len(result.data) > 0:
            return result.data[0]
        
        return None
    except Exception as e:
        logger.error(f"Failed to fetch scheduled message {schedule_id}: {e}")
        return None 