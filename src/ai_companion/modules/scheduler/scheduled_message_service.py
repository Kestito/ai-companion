import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from ai_companion.utils.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class ScheduledMessageService:
    """Service for managing scheduled messages."""

    def __init__(self):
        """Initialize the scheduled message service."""
        self.supabase = get_supabase_client()
        self.table_name = "scheduled_messages"
        logger.info("Initialized ScheduledMessageService")

    def create_scheduled_message(
        self,
        chat_id: int,
        message_content: str,
        scheduled_time: datetime,
        platform: str = "telegram",
        patient_id: Optional[str] = None,
        priority: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new scheduled message.

        Args:
            chat_id: The chat ID to send to
            message_content: The message text
            scheduled_time: When to send the message
            platform: The platform (telegram, etc.)
            patient_id: Optional patient ID
            priority: Priority (1-5, 1 is highest)
            metadata: Additional metadata

        Returns:
            The ID of the created message
        """
        if metadata is None:
            metadata = {}

        # Add platform-specific data to metadata
        if "platform_data" not in metadata:
            metadata["platform_data"] = {}

        metadata["platform_data"]["chat_id"] = chat_id

        # Generate a UUID for the message ID
        message_id = str(uuid.uuid4())

        # Create the message record
        message_data = {
            "id": message_id,
            "message_content": message_content,
            "scheduled_time": scheduled_time.isoformat(),
            "platform": platform,
            "status": "pending",
            "priority": priority,
            "patient_id": patient_id,
            "metadata": metadata,
            "attempts": 0,
        }

        # Insert into Supabase
        try:
            result = self.supabase.table(self.table_name).insert(message_data).execute()
            logger.info(f"Created scheduled message: {message_id}")
            return message_id
        except Exception as e:
            logger.error(f"Error creating scheduled message: {e}")
            # Log more detailed information for debugging
            logger.error(f"Message data: {message_data}")
            logger.error(f"Exception details: {str(e)}", exc_info=True)
            # Check if Supabase client is properly initialized
            if not self.supabase:
                logger.error("Supabase client is not initialized")
            raise

    def get_message_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a scheduled message by ID.

        Args:
            message_id: The message ID

        Returns:
            The message record or None if not found
        """
        try:
            result = (
                self.supabase.table(self.table_name)
                .select("*")
                .eq("id", message_id)
                .execute()
            )

            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting scheduled message {message_id}: {e}")
            return None

    def get_due_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get scheduled messages that are due for sending.

        Args:
            limit: Maximum number of messages to retrieve

        Returns:
            List of message records
        """
        now = datetime.utcnow().isoformat()

        try:
            # Get pending messages that are due
            result = (
                self.supabase.table(self.table_name)
                .select("*")
                .eq("status", "pending")
                .lte("scheduled_time", now)
                .order("priority")
                .order("scheduled_time")
                .limit(limit)
                .execute()
            )

            if result.data:
                logger.info(f"Found {len(result.data)} due messages")
                return result.data

            return []
        except Exception as e:
            logger.error(f"Error getting due messages: {e}")
            return []

    def get_messages_by_chat_id(
        self, chat_id: int, status: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get scheduled messages for a specific chat.

        Args:
            chat_id: The chat ID
            status: Optional status filter
            limit: Maximum number of messages to retrieve

        Returns:
            List of message records
        """
        try:
            # Base query
            query = self.supabase.table(self.table_name).select("*")

            # Apply filtering based on chat_id in metadata
            # Use raw SQL filtering for JSON data
            query = query.filter("metadata->platform_data->chat_id", "eq", chat_id)

            # Add status filter if provided
            if status:
                query = query.eq("status", status)

            # Execute query
            result = (
                query.order("scheduled_time", options={"ascending": False})
                .limit(limit)
                .execute()
            )

            if result.data:
                return result.data
            return []
        except Exception as e:
            logger.error(
                f"Database connection error when getting messages for chat {chat_id}: {e}",
                exc_info=True,
            )
            # Include connection error information in the returned data instead of empty list
            return [
                {
                    "error": True,
                    "message": f"Database connection error: {str(e)}",
                    "status": "error",
                }
            ]

    def update_message_status(
        self,
        message_id: str,
        status: str,
        next_scheduled_time: Optional[datetime] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Update the status of a scheduled message.

        Args:
            message_id: The message ID
            status: New status (pending, sent, failed, cancelled)
            next_scheduled_time: Optional next scheduled time (for recurring)
            error_message: Optional error message

        Returns:
            True if update succeeded
        """
        try:
            # Prepare update data
            update_data = {"status": status}

            # Update attempts count for non-sent status
            if status != "sent" and status != "cancelled":
                # Get current message first to increment attempts
                current = self.get_message_by_id(message_id)
                if current:
                    current_attempts = current.get("attempts", 0)
                    update_data["attempts"] = current_attempts + 1

            # Add next scheduled time if provided
            if next_scheduled_time:
                update_data["scheduled_time"] = next_scheduled_time.isoformat()

            # Add error message to metadata if provided
            if error_message:
                # Get current metadata first
                current = self.get_message_by_id(message_id)
                if current:
                    metadata = current.get("metadata", {})

                    if not metadata:
                        metadata = {}

                    # Add or update error information
                    metadata["last_error"] = {
                        "message": error_message,
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                    update_data["metadata"] = metadata

            # Update the record
            result = (
                self.supabase.table(self.table_name)
                .update(update_data)
                .eq("id", message_id)
                .execute()
            )

            if result.data and len(result.data) > 0:
                logger.info(f"Updated message {message_id} status to {status}")
                return True

            logger.warning(f"No rows updated for message {message_id}")
            return False
        except Exception as e:
            logger.error(f"Error updating message {message_id}: {e}")
            return False

    def cancel_message(self, message_id: str) -> bool:
        """
        Cancel a scheduled message.

        Args:
            message_id: The message ID

        Returns:
            True if cancellation succeeded
        """
        return self.update_message_status(message_id, "cancelled")

    def reschedule_message(self, message_id: str, new_scheduled_time: datetime) -> bool:
        """
        Reschedule a message to a new time.

        Args:
            message_id: The message ID
            new_scheduled_time: New scheduled time

        Returns:
            True if rescheduling succeeded
        """
        try:
            # Update scheduled time and reset status to pending
            result = (
                self.supabase.table(self.table_name)
                .update(
                    {
                        "scheduled_time": new_scheduled_time.isoformat(),
                        "status": "pending",
                    }
                )
                .eq("id", message_id)
                .execute()
            )

            if result.data and len(result.data) > 0:
                logger.info(f"Rescheduled message {message_id} to {new_scheduled_time}")
                return True

            logger.warning(f"No rows updated for message {message_id}")
            return False
        except Exception as e:
            logger.error(f"Error rescheduling message {message_id}: {e}")
            return False

    def calculate_next_execution_time(self, message_id: str) -> Optional[datetime]:
        """
        Calculate the next execution time for a recurring message.

        Args:
            message_id: The message ID

        Returns:
            The next scheduled time or None if not recurring or invalid
        """
        try:
            # Get the message record
            message = self.get_message_by_id(message_id)

            if not message:
                logger.warning(f"Message {message_id} not found")
                return None

            # Check if message has recurrence pattern
            metadata = message.get("metadata", {})
            recurrence = metadata.get("recurrence")

            if not recurrence:
                # Not a recurring message
                return None

            # Get current scheduled time
            scheduled_time = message.get("scheduled_time")
            if not scheduled_time:
                logger.warning(f"Message {message_id} has no scheduled_time")
                return None

            # Parse the scheduled time
            if isinstance(scheduled_time, str):
                base_time = datetime.fromisoformat(
                    scheduled_time.replace("Z", "+00:00")
                )
            else:
                base_time = scheduled_time

            # Get current time
            now = datetime.utcnow()

            # Calculate next time based on recurrence pattern
            recurrence_type = recurrence.get("type")

            if recurrence_type == "daily":
                # Daily recurrence - add one day
                interval = recurrence.get("interval", 1)
                next_time = base_time + timedelta(days=interval)

                # If next time is in the past, adjust to today
                if next_time < now:
                    days_ahead = (now - next_time).days + 1
                    next_time = next_time + timedelta(days=days_ahead)

                return next_time

            elif recurrence_type == "weekly":
                # Weekly recurrence on specific days
                days = recurrence.get("days", [])
                if not days:
                    return None

                # Convert to integers if they are strings
                days = [int(d) if isinstance(d, str) else d for d in days]

                interval = recurrence.get("interval", 1)
                current_day = base_time.weekday()

                # Find the next day in the list
                days_sorted = sorted(days)
                next_day = None

                for day in days_sorted:
                    if day > current_day:
                        next_day = day
                        break

                if next_day is not None:
                    # Found a day later this week
                    days_diff = next_day - current_day
                else:
                    # Wrap to next week
                    days_diff = 7 + days_sorted[0] - current_day

                # Create next schedule time
                next_time = base_time + timedelta(days=days_diff)

                # If next time is in the past, adjust forward
                if next_time < now:
                    # Add weeks until we're in the future
                    weeks_ahead = interval
                    while next_time < now:
                        next_time = next_time + timedelta(days=7 * weeks_ahead)

                return next_time

            elif recurrence_type == "monthly":
                # Monthly recurrence on a specific day
                day = recurrence.get("day")
                if not day:
                    return None

                interval = recurrence.get("interval", 1)

                # Calculate next month
                month = base_time.month + interval
                year = base_time.year

                # Handle year rollover
                if month > 12:
                    year += (month - 1) // 12
                    month = ((month - 1) % 12) + 1

                # Handle month length issues
                import calendar

                _, last_day = calendar.monthrange(year, month)
                if day > last_day:
                    day = last_day

                # Create next time
                next_time = datetime(
                    year=year,
                    month=month,
                    day=day,
                    hour=base_time.hour,
                    minute=base_time.minute,
                    second=base_time.second,
                )

                # If next time is in the past, adjust forward
                if next_time < now:
                    # Go to next interval
                    month = next_time.month + interval
                    year = next_time.year

                    if month > 12:
                        year += (month - 1) // 12
                        month = ((month - 1) % 12) + 1

                    # Handle month length issues again
                    _, last_day = calendar.monthrange(year, month)
                    if day > last_day:
                        day = last_day

                    next_time = datetime(
                        year=year,
                        month=month,
                        day=day,
                        hour=next_time.hour,
                        minute=next_time.minute,
                        second=next_time.second,
                    )

                return next_time

            elif recurrence_type == "custom":
                # Custom interval in minutes
                minutes = recurrence.get("minutes")
                if not minutes:
                    return None

                next_time = base_time + timedelta(minutes=minutes)

                # If next time is in the past, adjust forward
                if next_time < now:
                    # Calculate how many intervals we need to add
                    elapsed_minutes = (now - base_time).total_seconds() / 60
                    intervals_needed = (elapsed_minutes // minutes) + 1

                    next_time = base_time + timedelta(
                        minutes=minutes * intervals_needed
                    )

                return next_time

            # Unknown recurrence type
            logger.warning(f"Unknown recurrence type: {recurrence_type}")
            return None

        except Exception as e:
            logger.error(
                f"Error calculating next execution time for {message_id}: {e}",
                exc_info=True,
            )
            return None


# Singleton instance
_service_instance = None


def get_scheduled_message_service() -> ScheduledMessageService:
    """Get the singleton instance of the scheduled message service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ScheduledMessageService()
    return _service_instance
