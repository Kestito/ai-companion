"""
Scheduler for managing message delivery at specified times.

This module provides the core functionality for scheduling messages
to be delivered via various platforms at specified times.
"""

import logging
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import json

from ai_companion.utils.supabase import get_supabase_client
from ai_companion.settings import settings

logger = logging.getLogger(__name__)

class ScheduleManager:
    """Manages scheduled messages for different platforms."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self.supabase = get_supabase_client()
        
    async def schedule_message(self, 
                             patient_id: str, 
                             recipient_id: str,
                             platform: str, 
                             message_content: str,
                             scheduled_time: Union[datetime, str],
                             template_key: Optional[str] = None,
                             parameters: Optional[Dict[str, Any]] = None,
                             recurrence_pattern: Optional[str] = None) -> Dict[str, Any]:
        """
        Schedule a message for delivery.
        
        Args:
            patient_id: The ID of the patient
            recipient_id: Platform-specific recipient ID
            platform: The platform to deliver to (telegram, whatsapp)
            message_content: The content of the message
            scheduled_time: When to deliver the message
            template_key: Optional template identifier
            parameters: Optional parameters for template
            recurrence_pattern: Optional recurrence pattern
            
        Returns:
            Dict containing the created schedule details
        """
        # Convert datetime to ISO string if needed
        if isinstance(scheduled_time, datetime):
            scheduled_time_str = scheduled_time.isoformat()
        else:
            scheduled_time_str = scheduled_time
            
        # Create the schedule record
        schedule_id = str(uuid.uuid4())
        schedule_data = {
            "id": schedule_id,
            "patient_id": patient_id,
            "recipient_id": recipient_id,
            "platform": platform.lower(),
            "message_content": message_content,
            "scheduled_time": scheduled_time_str,
            "template_key": template_key,
            "parameters": json.dumps(parameters) if parameters else None,
            "recurrence_pattern": recurrence_pattern,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }
        
        # Insert into Supabase
        try:
            result = self.supabase.table("scheduled_messages").insert(schedule_data).execute()
            
            logger.info(f"Scheduled message {schedule_id} for {recipient_id} via {platform} at {scheduled_time_str}")
            
            return {
                "schedule_id": schedule_id,
                "status": "scheduled",
                "scheduled_time": scheduled_time_str,
                "platform": platform
            }
        except Exception as e:
            logger.error(f"Failed to schedule message: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def cancel_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """
        Cancel a scheduled message.
        
        Args:
            schedule_id: The ID of the schedule to cancel
            
        Returns:
            Dict containing the result of the operation
        """
        try:
            self.supabase.table("scheduled_messages").update({"status": "cancelled"}).eq("id", schedule_id).execute()
            
            logger.info(f"Cancelled scheduled message {schedule_id}")
            
            return {
                "schedule_id": schedule_id,
                "status": "cancelled"
            }
        except Exception as e:
            logger.error(f"Failed to cancel schedule {schedule_id}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_due_messages(self) -> List[Dict[str, Any]]:
        """
        Get all messages that are due for delivery.
        
        Returns:
            List of scheduled messages that are due
        """
        now = datetime.now().isoformat()
        
        try:
            result = self.supabase.table("scheduled_messages") \
                .select("*") \
                .eq("status", "pending") \
                .lte("scheduled_time", now) \
                .execute()
                
            due_messages = result.data if result and hasattr(result, 'data') else []
            
            return due_messages
        except Exception as e:
            logger.error(f"Failed to fetch due messages: {e}")
            return []
    
    async def mark_as_sent(self, schedule_id: str) -> Dict[str, Any]:
        """
        Mark a scheduled message as sent.
        
        Args:
            schedule_id: The ID of the schedule
            
        Returns:
            Dict containing the result of the operation
        """
        try:
            update_data = {
                "status": "sent",
                "sent_at": datetime.now().isoformat()
            }
            
            self.supabase.table("scheduled_messages").update(update_data).eq("id", schedule_id).execute()
            
            return {
                "schedule_id": schedule_id,
                "status": "sent"
            }
        except Exception as e:
            logger.error(f"Failed to mark message {schedule_id} as sent: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def mark_as_failed(self, schedule_id: str, error_message: str) -> Dict[str, Any]:
        """
        Mark a scheduled message as failed.
        
        Args:
            schedule_id: The ID of the schedule
            error_message: The error message
            
        Returns:
            Dict containing the result of the operation
        """
        try:
            update_data = {
                "status": "failed",
                "error_message": error_message,
                "failed_at": datetime.now().isoformat()
            }
            
            self.supabase.table("scheduled_messages").update(update_data).eq("id", schedule_id).execute()
            
            return {
                "schedule_id": schedule_id,
                "status": "failed",
                "error": error_message
            }
        except Exception as e:
            logger.error(f"Failed to mark message {schedule_id} as failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            } 