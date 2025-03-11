"""
Time and event-based triggers for scheduled messages.

This module provides functionality to parse and process trigger specifications
for scheduling messages at specific times or in response to events.
"""

import logging
import re
from datetime import datetime, timedelta, time
from typing import Dict, Any, Optional, Tuple, Union
import calendar

logger = logging.getLogger(__name__)

# Day of week mappings (both English and Lithuanian)
DAYS_OF_WEEK = {
    "monday": 0, "mon": 0, "pirmadienis": 0, "pr": 0,
    "tuesday": 1, "tue": 1, "antradienis": 1, "an": 1,
    "wednesday": 2, "wed": 2, "trečiadienis": 2, "tr": 2,
    "thursday": 3, "thu": 3, "ketvirtadienis": 3, "kt": 3,
    "friday": 4, "fri": 4, "penktadienis": 4, "pn": 4,
    "saturday": 5, "sat": 5, "šeštadienis": 5, "št": 5,
    "sunday": 6, "sun": 6, "sekmadienis": 6, "sk": 6
}

# Relative time mappings
RELATIVE_TIME = {
    "today": 0,
    "tomorrow": 1,
    "šiandien": 0,
    "rytoj": 1
}

def parse_time(time_str: str) -> Optional[time]:
    """
    Parse a time string (HH:MM) into a time object.
    
    Args:
        time_str: String representing time (e.g., "09:00")
        
    Returns:
        time object or None if parsing fails
    """
    patterns = [
        r'(\d{1,2}):(\d{2})',  # 9:00, 09:00
        r'(\d{1,2})(\d{2})',   # 900, 0900
        r'(\d{1,2})[.:]?(\d{2})\s*(am|pm)',  # 9:00am, 9.00pm, 900am
    ]
    
    for pattern in patterns:
        match = re.match(pattern, time_str.lower())
        if match:
            groups = match.groups()
            
            hour = int(groups[0])
            minute = int(groups[1])
            
            # Handle AM/PM if present
            if len(groups) > 2 and groups[2]:
                if groups[2].lower() == 'pm' and hour < 12:
                    hour += 12
                elif groups[2].lower() == 'am' and hour == 12:
                    hour = 0
            
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return time(hour, minute)
    
    logger.warning(f"Failed to parse time string: {time_str}")
    return None

def parse_day_of_week(day_str: str) -> Optional[int]:
    """
    Parse a day of week string into a weekday number (0=Monday, 6=Sunday).
    
    Args:
        day_str: String representing day of week (e.g., "monday")
        
    Returns:
        Weekday number or None if parsing fails
    """
    day_lower = day_str.lower()
    
    if day_lower in DAYS_OF_WEEK:
        return DAYS_OF_WEEK[day_lower]
    
    logger.warning(f"Failed to parse day of week: {day_str}")
    return None

def parse_trigger(trigger_str: str) -> Optional[datetime]:
    """
    Parse a trigger string into a datetime.
    
    Supported formats:
    - "today 10:00"
    - "tomorrow 15:30"
    - "monday 09:00"
    - "in 2 hours"
    - "in 30 minutes"
    - Specific date-time: "2023-04-15 14:00"
    
    Args:
        trigger_str: String representing when to trigger
        
    Returns:
        datetime object or None if parsing fails
    """
    trigger_lower = trigger_str.lower()
    now = datetime.now()
    
    # Try parsing as "today/tomorrow HH:MM"
    relative_day_match = re.match(r'(today|tomorrow|šiandien|rytoj)\s+(\d{1,2}[:.]?\d{2}(?:\s*[ap]m)?)', trigger_lower)
    if relative_day_match:
        day_offset = RELATIVE_TIME.get(relative_day_match.group(1), 0)
        time_obj = parse_time(relative_day_match.group(2))
        
        if time_obj:
            target_date = now.date() + timedelta(days=day_offset)
            return datetime.combine(target_date, time_obj)
    
    # Try parsing as "weekday HH:MM"
    weekday_match = re.match(r'([a-zA-ZčČęĘėĖįĮšŠųŲūŪžŽ]+)\s+(\d{1,2}[:.]?\d{2}(?:\s*[ap]m)?)', trigger_lower)
    if weekday_match:
        weekday = parse_day_of_week(weekday_match.group(1))
        time_obj = parse_time(weekday_match.group(2))
        
        if weekday is not None and time_obj:
            days_ahead = (weekday - now.weekday()) % 7
            if days_ahead == 0:
                # If today is the target day and the time has passed, schedule for next week
                if now.time() > time_obj:
                    days_ahead = 7
                    
            target_date = now.date() + timedelta(days=days_ahead)
            return datetime.combine(target_date, time_obj)
    
    # Try parsing as "in X hours/minutes"
    relative_match = re.match(r'in\s+(\d+)\s+(hour|hours|minute|minutes|min|mins)', trigger_lower)
    if relative_match:
        amount = int(relative_match.group(1))
        unit = relative_match.group(2)
        
        if unit in ['hour', 'hours']:
            return now + timedelta(hours=amount)
        elif unit in ['minute', 'minutes', 'min', 'mins']:
            return now + timedelta(minutes=amount)
    
    # Try parsing as ISO date with time
    try:
        return datetime.fromisoformat(trigger_str)
    except ValueError:
        pass
        
    # Try parsing as "YYYY-MM-DD HH:MM"
    date_time_match = re.match(r'(\d{4}-\d{2}-\d{2})\s+(\d{1,2}[:.]?\d{2}(?:\s*[ap]m)?)', trigger_lower)
    if date_time_match:
        try:
            date_obj = datetime.strptime(date_time_match.group(1), "%Y-%m-%d").date()
            time_obj = parse_time(date_time_match.group(2))
            
            if time_obj:
                return datetime.combine(date_obj, time_obj)
        except ValueError:
            pass
    
    logger.warning(f"Failed to parse trigger string: {trigger_str}")
    return None

def parse_recurrence(recurrence_str: str) -> Optional[Dict[str, Any]]:
    """Parse a recurrence pattern string.
    
    Args:
        recurrence_str: String representing a recurrence pattern
        
    Returns:
        Dictionary with recurrence details or None if not parseable
    """
    logger.debug(f"Parsing recurrence pattern: '{recurrence_str}'")
    
    # Standardize the string
    recurrence_str = recurrence_str.lower().strip()
    
    # Patterns for different recurrence types
    daily_pattern = r'^daily\s+at\s+(\d{1,2}):(\d{2})$'
    weekly_pattern = r'^weekly\s+on\s+(\w+)\s+at\s+(\d{1,2}):(\d{2})$'
    monthly_pattern = r'^monthly\s+on\s+(\d{1,2})\s+at\s+(\d{1,2}):(\d{2})$'
    
    # Alternative patterns that might be used
    alt_daily_pattern = r'^daily$'
    alt_weekly_pattern = r'^weekly\s+on\s+(\w+)$'
    alt_monthly_pattern = r'^monthly\s+on\s+(\d{1,2})$'
    
    # Time pattern to extract time separately
    time_pattern = r'at\s+(\d{1,2}):(\d{2})'
    
    # Log the patterns and input for debugging
    logger.debug(f"Daily pattern: {daily_pattern}")
    logger.debug(f"Weekly pattern: {weekly_pattern}")
    logger.debug(f"Monthly pattern: {monthly_pattern}")
    logger.debug(f"Input string: '{recurrence_str}'")
    
    # First try the standard patterns
    
    # Check for daily recurrence
    daily_match = re.match(daily_pattern, recurrence_str, re.IGNORECASE)
    if daily_match:
        try:
            hour = int(daily_match.group(1))
            minute = int(daily_match.group(2))
            
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                logger.debug(f"Matched daily pattern: hour={hour}, minute={minute}")
                return {
                    "type": "daily",
                    "hour": hour,
                    "minute": minute,
                    "next_date": get_next_daily_occurrence(hour, minute)
                }
        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing daily recurrence: {e}")
    
    # Check for weekly recurrence
    weekly_match = re.match(weekly_pattern, recurrence_str, re.IGNORECASE)
    if weekly_match:
        try:
            day_name = weekly_match.group(1)
            hour = int(weekly_match.group(2))
            minute = int(weekly_match.group(3))
            
            day_of_week = parse_day_of_week(day_name)
            if day_of_week is not None and 0 <= hour <= 23 and 0 <= minute <= 59:
                logger.debug(f"Matched weekly pattern: day={day_name}({day_of_week}), hour={hour}, minute={minute}")
                return {
                    "type": "weekly",
                    "day_of_week": day_of_week,
                    "hour": hour,
                    "minute": minute,
                    "next_date": get_next_weekly_occurrence(day_of_week, hour, minute)
                }
        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing weekly recurrence: {e}")
    
    # Check for monthly recurrence
    monthly_match = re.match(monthly_pattern, recurrence_str, re.IGNORECASE)
    if monthly_match:
        try:
            day_of_month = int(monthly_match.group(1))
            hour = int(monthly_match.group(2))
            minute = int(monthly_match.group(3))
            
            if 1 <= day_of_month <= 31 and 0 <= hour <= 23 and 0 <= minute <= 59:
                logger.debug(f"Matched monthly pattern: day={day_of_month}, hour={hour}, minute={minute}")
                return {
                    "type": "monthly",
                    "day_of_month": day_of_month,
                    "hour": hour,
                    "minute": minute,
                    "next_date": get_next_monthly_occurrence(day_of_month, hour, minute)
                }
        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing monthly recurrence: {e}")
    
    # If standard patterns don't match, try alternative approaches
    
    # Try more flexible patterns
    flexible_daily_pattern = r'daily\s+at\s+(\d{1,2}):(\d{2})'
    flexible_weekly_pattern = r'weekly\s+on\s+(\w+)\s+at\s+(\d{1,2}):(\d{2})'
    flexible_monthly_pattern = r'monthly\s+on\s+(\d{1,2})\s+at\s+(\d{1,2}):(\d{2})'
    
    # Check for flexible daily recurrence
    daily_match = re.search(flexible_daily_pattern, recurrence_str, re.IGNORECASE)
    if daily_match:
        try:
            hour = int(daily_match.group(1))
            minute = int(daily_match.group(2))
            
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                logger.debug(f"Matched flexible daily pattern: hour={hour}, minute={minute}")
                return {
                    "type": "daily",
                    "hour": hour,
                    "minute": minute,
                    "next_date": get_next_daily_occurrence(hour, minute)
                }
        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing flexible daily recurrence: {e}")
    
    # Check for flexible weekly recurrence
    weekly_match = re.search(flexible_weekly_pattern, recurrence_str, re.IGNORECASE)
    if weekly_match:
        try:
            day_name = weekly_match.group(1)
            hour = int(weekly_match.group(2))
            minute = int(weekly_match.group(3))
            
            day_of_week = parse_day_of_week(day_name)
            if day_of_week is not None and 0 <= hour <= 23 and 0 <= minute <= 59:
                logger.debug(f"Matched flexible weekly pattern: day={day_name}({day_of_week}), hour={hour}, minute={minute}")
                return {
                    "type": "weekly",
                    "day_of_week": day_of_week,
                    "hour": hour,
                    "minute": minute,
                    "next_date": get_next_weekly_occurrence(day_of_week, hour, minute)
                }
        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing flexible weekly recurrence: {e}")
    
    # Check for flexible monthly recurrence
    monthly_match = re.search(flexible_monthly_pattern, recurrence_str, re.IGNORECASE)
    if monthly_match:
        try:
            day_of_month = int(monthly_match.group(1))
            hour = int(monthly_match.group(2))
            minute = int(monthly_match.group(3))
            
            if 1 <= day_of_month <= 31 and 0 <= hour <= 23 and 0 <= minute <= 59:
                logger.debug(f"Matched flexible monthly pattern: day={day_of_month}, hour={hour}, minute={minute}")
                return {
                    "type": "monthly",
                    "day_of_month": day_of_month,
                    "hour": hour,
                    "minute": minute,
                    "next_date": get_next_monthly_occurrence(day_of_month, hour, minute)
                }
        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing flexible monthly recurrence: {e}")
    
    # Extract time if present anywhere in the string
    time_match = re.search(time_pattern, recurrence_str)
    hour = None
    minute = None
    
    if time_match:
        try:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            logger.debug(f"Extracted time from string: hour={hour}, minute={minute}")
        except (ValueError, IndexError) as e:
            logger.warning(f"Error extracting time: {e}")
    
    # If we have a valid time, check for recurrence type
    if hour is not None and minute is not None and 0 <= hour <= 23 and 0 <= minute <= 59:
        # Check for daily recurrence
        if 'daily' in recurrence_str:
            logger.debug(f"Matched alternative daily pattern: hour={hour}, minute={minute}")
            return {
                "type": "daily",
                "hour": hour,
                "minute": minute,
                "next_date": get_next_daily_occurrence(hour, minute)
            }
        
        # Check for weekly recurrence
        weekly_day_match = re.search(r'weekly\s+on\s+(\w+)', recurrence_str, re.IGNORECASE)
        if weekly_day_match:
            day_name = weekly_day_match.group(1)
            day_of_week = parse_day_of_week(day_name)
            
            if day_of_week is not None:
                logger.debug(f"Matched alternative weekly pattern: day={day_name}({day_of_week}), hour={hour}, minute={minute}")
                return {
                    "type": "weekly",
                    "day_of_week": day_of_week,
                    "hour": hour,
                    "minute": minute,
                    "next_date": get_next_weekly_occurrence(day_of_week, hour, minute)
                }
        
        # Check for monthly recurrence
        monthly_day_match = re.search(r'monthly\s+on\s+(\d{1,2})', recurrence_str, re.IGNORECASE)
        if monthly_day_match:
            try:
                day_of_month = int(monthly_day_match.group(1))
                
                if 1 <= day_of_month <= 31:
                    logger.debug(f"Matched alternative monthly pattern: day={day_of_month}, hour={hour}, minute={minute}")
                    return {
                        "type": "monthly",
                        "day_of_month": day_of_month,
                        "hour": hour,
                        "minute": minute,
                        "next_date": get_next_monthly_occurrence(day_of_month, hour, minute)
                    }
            except (ValueError, IndexError) as e:
                logger.warning(f"Error parsing alternative monthly pattern: {e}")
    
    # If we still don't have a match, try to be even more flexible
    if 'daily' in recurrence_str:
        # Default to noon if no time specified
        hour = hour if hour is not None else 12
        minute = minute if minute is not None else 0
        
        logger.debug(f"Fallback daily pattern match: hour={hour}, minute={minute}")
        return {
            "type": "daily",
            "hour": hour,
            "minute": minute,
            "next_date": get_next_daily_occurrence(hour, minute)
        }
    
    logger.warning(f"Failed to parse recurrence pattern: {recurrence_str}")
    return None

def get_next_daily_occurrence(hour: int, minute: int) -> datetime:
    """Get the next occurrence for a daily pattern."""
    now = datetime.now()
    target_time = datetime(now.year, now.month, now.day, hour, minute)
    
    if target_time <= now:
        # If the time has already passed today, schedule for tomorrow
        target_time += timedelta(days=1)
    
    return target_time

def get_next_weekly_occurrence(day_of_week: int, hour: int, minute: int) -> datetime:
    """Get the next occurrence for a weekly pattern."""
    now = datetime.now()
    days_ahead = day_of_week - now.weekday()
    
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    
    next_day = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_ahead)
    
    return next_day

def get_next_monthly_occurrence(day_of_month: int, hour: int, minute: int) -> datetime:
    """Get the next occurrence for a monthly pattern."""
    now = datetime.now()
    
    # Try to set the target day in the current month
    try:
        target_time = datetime(now.year, now.month, day_of_month, hour, minute)
    except ValueError:  # Day is not valid for this month (e.g., Feb 30)
        # Move to the next month and try again
        if now.month == 12:
            next_month = datetime(now.year + 1, 1, 1)
        else:
            next_month = datetime(now.year, now.month + 1, 1)
        
        # Find the valid day in the next month
        target_day = min(day_of_month, calendar.monthrange(next_month.year, next_month.month)[1])
        target_time = datetime(next_month.year, next_month.month, target_day, hour, minute)
    
    # If the target time has already passed this month, move to next month
    if target_time <= now:
        if now.month == 12:
            target_time = datetime(now.year + 1, 1, day_of_month, hour, minute)
        else:
            next_month = now.month + 1
            target_day = min(day_of_month, calendar.monthrange(now.year, next_month)[1])
            target_time = datetime(now.year, next_month, target_day, hour, minute)
    
    return target_time

def get_next_occurrence(recurrence: Dict[str, Any]) -> Optional[datetime]:
    """
    Calculate the next occurrence based on a recurrence pattern.
    
    Args:
        recurrence: Dict with recurrence details
        
    Returns:
        datetime of next occurrence or None if calculation fails
    """
    now = datetime.now()
    recurrence_type = recurrence.get("type")
    
    if not recurrence_type:
        return None
    
    time_str = recurrence.get("time", "00:00")
    hour, minute = map(int, time_str.split(":"))
    
    if recurrence_type == "daily":
        target_time = time(hour, minute)
        next_date = now.date()
        
        # If today's target time has passed, schedule for tomorrow
        if now.time() > target_time:
            next_date += timedelta(days=1)
            
        return datetime.combine(next_date, target_time)
        
    elif recurrence_type == "weekly":
        weekday = recurrence.get("day", 0)  # Default to Monday
        target_time = time(hour, minute)
        
        days_ahead = (weekday - now.weekday()) % 7
        if days_ahead == 0 and now.time() > target_time:
            days_ahead = 7
            
        next_date = now.date() + timedelta(days=days_ahead)
        return datetime.combine(next_date, target_time)
        
    elif recurrence_type == "monthly":
        day = recurrence.get("day", 1)  # Default to 1st day
        target_time = time(hour, minute)
        
        # Start with current month
        year, month = now.year, now.month
        
        # If today is after the target day or today is the target day but time has passed
        if now.day > day or (now.day == day and now.time() > target_time):
            # Move to next month
            if month == 12:
                year += 1
                month = 1
            else:
                month += 1
        
        # Adjust for months with fewer days
        last_day = calendar.monthrange(year, month)[1]
        if day > last_day:
            day = last_day
            
        try:
            next_date = datetime(year, month, day, hour, minute)
            return next_date
        except ValueError:
            logger.error(f"Invalid date: {year}-{month}-{day} {hour}:{minute}")
            return None
            
    return None 