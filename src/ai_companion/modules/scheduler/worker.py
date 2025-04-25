import asyncio
import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional

from ai_companion.modules.scheduler.service import ScheduledMessageService

logger = logging.getLogger(__name__)


class SchedulerWorker:
    def __init__(self, service: ScheduledMessageService):
        self.service = service
        self._running = False
        self._bot_instance = None
        self._internal_bot = None

    async def start(self, bot_instance=None):
        """Start the scheduler worker process."""
        self._running = True
        self._bot_instance = bot_instance

        # If we're running in integrated mode, we don't have a direct bot instance
        # Instead, we'll need to import and create one when needed
        if not self._bot_instance:
            logger.info(
                "Starting scheduler worker in integrated mode (no direct bot instance)"
            )
        else:
            logger.info("Starting scheduler worker with provided bot instance")

        # Run worker in background task
        asyncio.create_task(self._process_scheduled_messages())

    def stop(self):
        """Stop the scheduler worker process."""
        self._running = False

    async def _get_bot_instance(self):
        """Get or create a bot instance for sending messages."""
        if self._bot_instance:
            return self._bot_instance

        # If we don't have a bot instance, create one internally
        if not self._internal_bot:
            try:
                # Import here to avoid circular imports
                from ai_companion.interfaces.telegram.telegram_bot import TelegramBot

                self._internal_bot = TelegramBot()
                logger.info("Created internal Telegram bot instance")
                # Don't start full bot polling, we just need it for sending messages
            except Exception as e:
                logger.error(f"Failed to create internal Telegram bot: {e}")
                return None

        return self._internal_bot

    async def _process_scheduled_messages(self):
        """Process scheduled messages that are due."""
        logger.info("Starting scheduled message processor")

        while self._running:
            try:
                # Get due messages
                due_messages = await self.service.get_due_messages()

                if due_messages:
                    logger.info(f"Processing {len(due_messages)} due messages")
                    for message in due_messages:
                        await self._process_message(message)

                # Wait for a short time before next check
                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in scheduled message processor: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(60)  # Wait longer after error

    async def _process_message(self, message: Dict[str, Any]):
        """Process a single scheduled message."""
        message_id = message.get("id")
        platform = message.get("platform")
        message_content = message.get("message_content")
        metadata = message.get("metadata", {})

        logger.info(
            f"Processing scheduled message {message_id} for platform {platform}"
        )

        try:
            # Mark message as in progress
            await self.service.update_message_status(message_id, "in_progress")

            # Handle different platform types
            if platform == "telegram":
                await self._process_telegram_message(message)
            else:
                logger.warning(f"Unsupported platform: {platform}")
                await self.service.update_message_status(
                    message_id, "failed", error=f"Unsupported platform: {platform}"
                )

        except Exception as e:
            logger.error(f"Error processing message {message_id}: {e}")
            logger.error(traceback.format_exc())

            # Mark as failed
            await self.service.update_message_status(message_id, "failed", error=str(e))

    async def _process_telegram_message(self, message: Dict[str, Any]):
        """Process a Telegram scheduled message."""
        message_id = message.get("id")
        message_content = message.get("message_content")
        metadata = message.get("metadata", {})
        platform_data = metadata.get("platform_data", {})
        chat_id = platform_data.get("chat_id")

        if not chat_id:
            logger.error(f"Missing chat_id for Telegram message {message_id}")
            await self.service.update_message_status(
                message_id, "failed", error="Missing chat_id in platform_data"
            )
            return

        try:
            # Get bot instance (either the provided one or create an internal one)
            bot = await self._get_bot_instance()

            if not bot:
                logger.error(
                    f"No bot instance available for sending message {message_id}"
                )
                await self.service.update_message_status(
                    message_id, "failed", error="No bot instance available"
                )
                return

            # Send the message
            logger.info(f"Sending scheduled message {message_id} to chat {chat_id}")
            result = await bot._send_message(chat_id, message_content)

            if not result.get("ok", False):
                error_desc = result.get("description", "Unknown error")
                logger.error(f"Failed to send message {message_id}: {error_desc}")
                await self.service.update_message_status(
                    message_id, "failed", error=f"Telegram API error: {error_desc}"
                )
                return

            # Message sent successfully
            logger.info(f"Successfully sent message {message_id}")

            # Check if this is a recurring message
            recurrence = metadata.get("recurrence")
            if recurrence:
                # Calculate next occurrence time
                next_time = await self._calculate_next_occurrence(message)

                if next_time:
                    # Create a new scheduled message for the next occurrence
                    logger.info(
                        f"Creating next occurrence of recurring message {message_id} at {next_time}"
                    )
                    await self.service.reschedule_message(message_id, next_time)
                else:
                    # If no valid next time (e.g., for expired recurrences), mark as completed
                    await self.service.update_message_status(message_id, "completed")
            else:
                # One-time message, mark as completed
                await self.service.update_message_status(message_id, "completed")

        except Exception as e:
            logger.error(f"Error processing Telegram message {message_id}: {e}")
            logger.error(traceback.format_exc())
            await self.service.update_message_status(message_id, "failed", error=str(e))

    async def _calculate_next_occurrence(
        self, message: Dict[str, Any]
    ) -> Optional[datetime]:
        """Calculate the next occurrence time for a recurring message."""
        try:
            metadata = message.get("metadata", {})
            recurrence = metadata.get("recurrence")

            if not recurrence:
                return None

            from datetime import datetime, timedelta
            import calendar

            recurrence_type = recurrence.get("type")

            # Start from the current scheduled time
            base_time = datetime.fromisoformat(
                message["scheduled_time"].replace("Z", "+00:00")
            )
            now = datetime.utcnow()

            if recurrence_type == "daily":
                # Daily recurrence - just add one day
                interval = recurrence.get("interval", 1)
                return base_time + timedelta(days=interval)

            elif recurrence_type == "weekly":
                # Weekly recurrence on specific days
                days = recurrence.get("days", [])
                if not days:
                    return None

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
                    days_diff = 7 - current_day + days_sorted[0]

                # Add the interval weeks for intervals > 1
                if (
                    interval > 1 and next_day is None
                ):  # Only add interval when wrapping to next week
                    days_diff += (interval - 1) * 7

                return base_time + timedelta(days=days_diff)

            elif recurrence_type == "monthly":
                # Monthly recurrence on a specific day
                day = recurrence.get("day")
                if not day:
                    return None

                interval = recurrence.get("interval", 1)

                # Move to next month
                year = base_time.year
                month = base_time.month + interval

                # Handle year rollover
                while month > 12:
                    month -= 12
                    year += 1

                # Handle month length issues
                _, last_day = calendar.monthrange(year, month)
                day = min(day, last_day)  # Ensure the day is valid for the month

                # Create the next occurrence time
                return datetime(
                    year=year,
                    month=month,
                    day=day,
                    hour=base_time.hour,
                    minute=base_time.minute,
                    second=base_time.second,
                )

            elif recurrence_type == "custom":
                # Custom interval in minutes
                minutes = recurrence.get("minutes")
                if not minutes:
                    return None

                return base_time + timedelta(minutes=minutes)

            return None  # Unknown recurrence type

        except Exception as e:
            logger.error(f"Error calculating next occurrence: {e}")
            return None
