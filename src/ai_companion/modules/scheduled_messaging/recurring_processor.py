"""
Recurring message processor for scheduled messaging.

This module handles processing of recurring message schedules,
generating the next occurrence dates for daily, weekly, and monthly
scheduled messages.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date, time
import json

from ai_companion.modules.scheduled_messaging.storage import update_message_status, get_message_by_id

logger = logging.getLogger(__name__)

def process_recurring_message(message_data: Dict[str, Any]) -> Optional[datetime]:
    """
    Process a recurring message and calculate its next scheduled time.
    
    Args:
        message_data: The message data with recurrence information
        
    Returns:
        The next scheduled time or None if no recurrence is set
    """
    message_id = message_data.get("id")
    status = message_data.get("status")
    
    # Only process pending messages
    if status != "pending":
        logger.debug(f"Skipping message {message_id} with status {status}")
        return None
    
    # Get recurrence data if available
    recurrence = message_data.get("recurrence")
    if not recurrence:
        logger.debug(f"Message {message_id} has no recurrence data")
        return None
    
    # Parse recurrence data if it's a JSON string
    if isinstance(recurrence, str):
        try:
            recurrence = json.loads(recurrence)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse recurrence data for message {message_id}")
            return None
    
    # Calculate next occurrence
    now = datetime.now()
    recurrence_type = recurrence.get("type")
    
    if recurrence_type == "daily":
        next_time = calculate_next_daily(recurrence, now)
    elif recurrence_type == "weekly":
        next_time = calculate_next_weekly(recurrence, now)
    elif recurrence_type == "monthly":
        next_time = calculate_next_monthly(recurrence, now)
    else:
        logger.warning(f"Unknown recurrence type: {recurrence_type}")
        return None
    
    if next_time:
        logger.info(f"Next occurrence for message {message_id} is {next_time.isoformat()}")
        return next_time
    
    return None

def calculate_next_daily(recurrence: Dict[str, Any], now: datetime) -> Optional[datetime]:
    """
    Calculate the next occurrence for a daily recurring message.
    
    Args:
        recurrence: The recurrence configuration
        now: The current time
        
    Returns:
        The next scheduled time
    """
    time_str = recurrence.get("time", "09:00")
    hour, minute = map(int, time_str.split(":", 1))
    
    # Create datetime for today with the specified time
    target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # If the time has already passed today, use tomorrow
    if target_time <= now:
        target_time += timedelta(days=1)
    
    return target_time

def calculate_next_weekly(recurrence: Dict[str, Any], now: datetime) -> Optional[datetime]:
    """
    Calculate the next occurrence for a weekly recurring message.
    
    Args:
        recurrence: The recurrence configuration
        now: The current time
        
    Returns:
        The next scheduled time
    """
    days = recurrence.get("days", [0])  # Default to Sunday if not specified
    time_str = recurrence.get("time", "09:00")
    hour, minute = map(int, time_str.split(":", 1))
    
    # Current day of week (0 = Monday in our system)
    current_weekday = now.weekday()
    
    # Find the next day in the list
    next_day = None
    days_sorted = sorted(days)
    
    # Check if any day in the list is later this week
    for day in days_sorted:
        if day > current_weekday:
            next_day = day
            break
    
    # If not found, take the first day (for next week)
    if next_day is None and days_sorted:
        next_day = days_sorted[0]
        days_until_next = 7 - current_weekday + next_day
    else:
        days_until_next = next_day - current_weekday
    
    if next_day is not None:
        target_date = now.date() + timedelta(days=days_until_next)
        target_time = datetime.combine(target_date, time(hour=hour, minute=minute))
        
        # If the time has already passed today and it's the same day, go to next week
        if target_time <= now and days_until_next == 0:
            target_time += timedelta(days=7)
            
        return target_time
    
    return None

def calculate_next_monthly(recurrence: Dict[str, Any], now: datetime) -> Optional[datetime]:
    """
    Calculate the next occurrence for a monthly recurring message.
    
    Args:
        recurrence: The recurrence configuration
        now: The current time
        
    Returns:
        The next scheduled time
    """
    day_of_month = recurrence.get("day_of_month", now.day)
    time_str = recurrence.get("time", "09:00")
    hour, minute = map(int, time_str.split(":", 1))
    
    # Start with current month
    year, month = now.year, now.month
    
    # Try to create a date for this month
    try:
        target_date = date(year, month, day_of_month)
    except ValueError:
        # Invalid day for this month, try the last day
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
            
        # Get the last day of the current month
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)
            
        target_date = last_day
    
    target_time = datetime.combine(target_date, time(hour=hour, minute=minute))
    
    # If the target time has already passed this month, go to next month
    if target_time <= now:
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
            
        # Try to create a date for next month
        try:
            target_date = date(next_year, next_month, day_of_month)
        except ValueError:
            # Invalid day for next month, use the last day
            if next_month == 12:
                last_day = date(next_year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(next_year, next_month + 1, 1) - timedelta(days=1)
                
            target_date = last_day
            
        target_time = datetime.combine(target_date, time(hour=hour, minute=minute))
    
    return target_time

async def update_recurring_schedule(message_id: str, next_time: datetime) -> Dict[str, Any]:
    """
    Update a recurring message with its next scheduled time.
    
    Args:
        message_id: The ID of the message
        next_time: The next scheduled time
        
    Returns:
        The result of the update operation
    """
    try:
        # Clone the original message as a new scheduled message
        original_message = await get_message_by_id(message_id)
        
        if not original_message:
            logger.error(f"Failed to find message {message_id}")
            return {"success": False, "error": "Message not found"}
        
        # Update the original message status to 'processing'
        await update_message_status(message_id, "processing")
        
        # Calculate the next scheduled time
        if isinstance(next_time, datetime):
            next_scheduled_time = next_time.isoformat()
        else:
            next_scheduled_time = next_time
            
        # Insert a new scheduled message with the next time
        from ai_companion.modules.scheduled_messaging.storage import insert_scheduled_message
        
        new_message = {
            "patient_id": original_message.get("patient_id"),
            "message_content": original_message.get("message_content"),
            "scheduled_time": next_scheduled_time,
            "status": "pending",
            "platform": original_message.get("platform", "telegram"),
            "recurrence": original_message.get("recurrence")
        }
        
        result = await insert_scheduled_message(new_message)
        
        if result.get("success"):
            # Update the original message status to 'recurring-processed'
            await update_message_status(message_id, "recurring-processed", {
                "next_message_id": result.get("message_id")
            })
            logger.info(f"Updated recurring message {message_id} with next time {next_scheduled_time}")
            return {"success": True, "message_id": result.get("message_id")}
        else:
            # If insertion failed, update the original message status back to 'pending'
            await update_message_status(message_id, "pending")
            logger.error(f"Failed to create next occurrence for message {message_id}")
            return {"success": False, "error": result.get("error")}
            
    except Exception as e:
        logger.error(f"Error updating recurring schedule {message_id}: {e}")
        # Make sure the original message is reset to pending
        try:
            await update_message_status(message_id, "pending")
        except Exception as inner_e:
            logger.error(f"Failed to reset message status: {inner_e}")
            
        return {"success": False, "error": str(e)} 