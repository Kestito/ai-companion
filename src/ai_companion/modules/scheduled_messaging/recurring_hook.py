"""
Recurring message hook for scheduled messaging.

This module provides hooks to process recurring messages after they've been
sent, creating the next scheduled occurrence.
"""

import logging
from typing import Dict, Any, Optional

from ai_companion.modules.scheduled_messaging.recurring_processor import (
    process_recurring_message,
    update_recurring_schedule
)

logger = logging.getLogger(__name__)

async def process_after_send(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a message after it has been sent.
    This checks for recurrence and schedules the next occurrence if needed.
    
    Args:
        message_data: The message data that was just sent
        
    Returns:
        Dict with the result of the recurring processing
    """
    message_id = message_data.get("id")
    
    # Check if this is a recurring message
    recurrence = message_data.get("recurrence")
    if not recurrence:
        logger.debug(f"Message {message_id} is not recurring, skipping")
        return {"success": True, "recurring": False}
    
    # Calculate the next occurrence
    next_time = process_recurring_message(message_data)
    if not next_time:
        logger.warning(f"Failed to calculate next occurrence for message {message_id}")
        return {"success": False, "error": "Failed to calculate next occurrence"}
    
    # Update the schedule with the next occurrence
    result = await update_recurring_schedule(message_id, next_time)
    
    if result.get("success"):
        logger.info(f"Scheduled next occurrence for message {message_id} at {next_time}")
        return {
            "success": True,
            "recurring": True,
            "next_message_id": result.get("message_id"),
            "next_time": next_time.isoformat() if hasattr(next_time, "isoformat") else next_time
        }
    else:
        logger.error(f"Failed to schedule next occurrence: {result.get('error')}")
        return {
            "success": False,
            "error": result.get("error")
        } 