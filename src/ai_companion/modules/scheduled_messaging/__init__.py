"""
Scheduled Messaging Module.

This module provides functionality for scheduling and sending messages
on a specified schedule or recurring pattern.
"""

# Try both import approaches to be compatible with different environments
try:
    from src.ai_companion.modules.scheduled_messaging.scheduler import ScheduleManager
except ImportError:
    try:
        from ai_companion.modules.scheduled_messaging.scheduler import ScheduleManager
    except ImportError:
        # For documentation or import time reference only
        ScheduleManager = None

__all__ = ["ScheduleManager"] 