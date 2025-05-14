import asyncio
import logging
from typing import Dict, Optional, Union, Any, List
import signal
from datetime import datetime, timedelta
import random
import json

import httpx

# Import the message classes from langchain_core
from langchain_core.messages import HumanMessage
from ai_companion.graph import graph_builder
from ai_companion.modules.image import ImageToText
from ai_companion.modules.speech import SpeechToText, TextToSpeech
from ai_companion.settings import settings
from ai_companion.utils.supabase import get_supabase_client
from ai_companion.modules.memory.service import get_memory_service
from ai_companion.modules.scheduler import (
    get_scheduler_worker,
    get_scheduled_message_service,
)
from ai_companion.graph.nodes import get_patient_id_from_platform_id

# Define color codes for terminal output
GREEN = "\033[32m"
RESET = "\033[0m"

# Configure logging based on settings
log_level = getattr(logging, settings.LOGGING_LEVEL, logging.INFO)
logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Set HTTP client libraries to log at WARNING level to suppress debug logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Configure scheduler logger separately with custom log level
scheduler_logger = logging.getLogger("ai_companion.modules.scheduler")
scheduler_log_level = getattr(logging, settings.SCHEDULER_LOG_LEVEL, logging.ERROR)
scheduler_logger.setLevel(scheduler_log_level)

# Global module instances
speech_to_text = SpeechToText()
text_to_speech = TextToSpeech()
image_to_text = ImageToText()


# Helper function to print colored messages to terminal
def print_green(message: str):
    """Print message in green color to terminal."""
    print(f"{GREEN}{message}{RESET}")


class TelegramBot:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.api_base = settings.TELEGRAM_API_BASE

        # Ensure api_base doesn't end with slash
        if self.api_base.endswith("/"):
            self.api_base = self.api_base[:-1]

        self.base_url = f"{self.api_base}/bot{self.token}"
        self.offset = 0
        self.client = httpx.AsyncClient(timeout=60.0)
        self.session = self.client  # Add session alias for compatibility
        self._running = True

        # Removed checkpoint directory functionality as it's not needed with Supabase

        self._setup_signal_handlers()

        # Use standard memory service exclusively for all operations
        self.memory_service = get_memory_service()

        # Initialize Supabase client directly
        try:
            self.supabase = get_supabase_client()
            logger.info("Successfully initialized Supabase client for TelegramBot")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.supabase = None

        # Initialize scheduled message service
        try:
            self.scheduled_message_service = get_scheduled_message_service()
            #  if scheduler_log_level <= logging.INFO:
            #     logger.info("Successfully initialized ScheduledMessageService")

            # Test connection to scheduled_messages table
            self.scheduled_message_service.supabase.table("scheduled_messages").select(
                "id"
            ).limit(1).execute()
            #  if scheduler_log_level <= logging.INFO:
            #    logger.info("Test connection to scheduled_messages table successful")
        except Exception as e:
            logger.error(
                f"Error initializing ScheduledMessageService: {e}", exc_info=True
            )
            self.scheduled_message_service = None

        # Initialize scheduler worker with this bot instance for sending messages
        self.scheduler_worker = get_scheduler_worker(self)

        # Skip memory cleanup initialization per user request
        logger.info("Memory cleanup scheduler initialization skipped per user request")
        self.memory_cleanup_thread = None

        #  logger.info(

    #       "Initialized Telegram bot with standardized memory service approach"
    #  )

    async def _run_initial_memory_cleanup(self):
        """Run initial memory cleanup on startup."""
        try:
            logger.info("Initial memory cleanup skipped as requested by user")
        except Exception as e:
            logger.error(f"Error in memory cleanup handling: {e}")

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._handle_signal)

    def _handle_signal(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self._running = False

    async def start(self):
        """Start the bot and begin polling for updates."""
        logger.info("Starting Telegram bot...")
        try:
            # Check bot health before starting
            await self._check_health()

            me = await self._make_request("getMe")
            logger.info(f"Bot started successfully: @{me['result']['username']}")

            # Start the scheduler worker
            await self.scheduler_worker.start(self)
            #  if scheduler_log_level <= logging.INFO:
            #    logger.info("Started scheduler worker")

            await self._poll_updates()
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise
        finally:
            # Stop the scheduler worker
            self.scheduler_worker.stop()
            await self.client.aclose()
            logger.info("Bot shutdown complete")

    async def _check_health(self):
        """Check the health of the bot and its dependencies."""
        logger.info("Performing health check...")
        try:
            # 1. Check if we can connect to Telegram API
            start_time = asyncio.get_event_loop().time()
            me = await self._make_request("getMe")
            api_time = asyncio.get_event_loop().time() - start_time

            if not me.get("ok"):
                logger.error("Health check failed: Unable to connect to Telegram API")
                raise Exception("Telegram API connection failed")

            logger.info(
                f"Telegram API connection successful ({api_time:.2f}s): @{me['result']['username']}"
            )

            # 2. Check if we can connect to Supabase for memory storage
            try:
                # Check Supabase connection via memory manager
                test_user_id = "test_health_check_user"  # Use a fixed test user ID for health checks

                # Get a real patient ID instead of using a hardcoded test value
                patient_id = get_patient_id_from_platform_id("telegram", test_user_id)

                # If no patient found, use the system ID format directly
                if not patient_id:
                    patient_id = f"telegram:{test_user_id}"
                    logger.debug(
                        f"No patient found for health check, using system_id: {patient_id}"
                    )

                test_memories = await self.memory_service.get_session_memory(
                    platform="telegram",
                    user_id=test_user_id,
                    patient_id=patient_id,
                    limit=10,
                )
                logger.info(
                    f"Supabase connection successful, found {len(test_memories)} active memories"
                )
            except Exception as e:
                logger.warning(f"Supabase memory check warning: {e}")
                # Not critical, continue with warning

            logger.info("Health check completed successfully")
            return True

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise

    async def _poll_updates(self):
        """Long polling for updates from Telegram."""
        while self._running:
            try:
                # Create params for getUpdates
                params = {
                    "offset": self.offset,
                    "timeout": 30,
                    "allowed_updates": ["message"],
                }

                # Get updates with error handling for conflict
                try:
                    updates = await self._make_request("getUpdates", params=params)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 409:
                        # Handle conflict error - reset offset and wait
                        logger.warning(
                            "Conflict detected in getUpdates, resetting offset"
                        )
                        # Get the latest updates to reset
                        reset_params = {"timeout": 1, "allowed_updates": ["message"]}
                        try:
                            reset_updates = await self._make_request(
                                "getUpdates", params=reset_params
                            )
                            if (
                                reset_updates.get("result")
                                and len(reset_updates["result"]) > 0
                            ):
                                # Update offset to the latest update_id + 1
                                latest = reset_updates["result"][-1]
                                self.offset = latest["update_id"] + 1
                                logger.info(f"Reset offset to {self.offset}")
                            else:
                                # If no updates, advance offset by 1 as a fallback
                                self.offset += 1
                                logger.info(
                                    f"No updates found, advanced offset to {self.offset}"
                                )
                        except Exception as reset_err:
                            logger.error(f"Failed to reset offset: {reset_err}")
                            self.offset += 1  # Still advance offset as last resort

                        await asyncio.sleep(2)  # Wait before retrying
                        continue
                    else:
                        # Re-raise other HTTP errors
                        raise

                # Process each update
                for update in updates.get("result", []):
                    if not self._running:
                        break
                    await self._process_update(update)
                    self.offset = update["update_id"] + 1

            except httpx.TimeoutException:
                logger.debug("Polling timeout, continuing...")
                continue
            except Exception as e:
                if isinstance(e, asyncio.CancelledError):
                    logger.info("Polling cancelled, shutting down...")
                    break
                logger.error(f"Error in polling loop: {e}")
                if self._running:
                    await asyncio.sleep(5)

    async def _process_update(self, update: Dict):
        """Process a single update from Telegram."""
        try:
            if "update_id" in update:
                # Update the offset for the next poll
                self.offset = update["update_id"] + 1

                if "message" in update:
                    message = update["message"]
                    await self._handle_message(message)
                elif "edited_message" in update:
                    # Just log edited messages for now
                    edited_message = update["edited_message"]
                    logger.info(
                        f"User edited message: {edited_message.get('text', '')}"
                    )
        except Exception as e:
            logger.error(f"Error processing update: {e}", exc_info=True)

    async def _handle_message(self, message: Dict):
        """Handle a message from Telegram."""
        try:
            # Skip empty messages
            if not message:
                return

            chat_id = message.get("chat", {}).get("id")
            user_id = message.get("from", {}).get("id")

            if not chat_id or not user_id:
                logger.warning("Missing chat_id or user_id in message")
                return

            # Get patient_id for this user
            patient_id = await self._get_patient_id(user_id)
            if patient_id:
                logger.info(
                    f"PATIENT MESSAGE | ID: {patient_id} | User ID: {user_id} | Chat ID: {chat_id}"
                )
            else:
                logger.info(
                    f"UNKNOWN USER MESSAGE | User ID: {user_id} | Chat ID: {chat_id}"
                )

            # Check if this is a command first
            if await self._handle_command(message):
                return

            # Extract message content
            content_result = await self._extract_message_content(message)
            if not content_result:
                logger.warning("Unable to extract message content")
                return

            message_type, message_content = content_result

            # Log the incoming message
            if message_type == "text":
                logger.info(
                    f"PATIENT TEXT | ID: {patient_id} | Content: {message_content}"
                )
                print(f"USER ({user_id}): {message_content}")
            elif message_type == "voice":
                logger.info(
                    f"PATIENT VOICE | ID: {patient_id} | Duration: {message.get('voice', {}).get('duration', 0)}s"
                )
                print(f"USER ({user_id}): [VOICE MESSAGE]")
            elif message_type == "photo":
                logger.info(f"PATIENT PHOTO | ID: {patient_id}")
                print(f"USER ({user_id}): [PHOTO]")

            # Show typing indicator
            await self._send_typing_action(chat_id)

            # Get the conversation history for enhanced context
            conversation_history = await self._get_conversation_history(
                chat_id, user_id, max_messages=20
            )

            # Create user metadata for graph processing
            user_metadata = {
                "platform": "telegram",
                "external_system_id": str(user_id),
                "chat_id": chat_id,
                "message_type": message_type,
            }

            # Add patient_id to metadata if available
            if patient_id:
                user_metadata["patient_id"] = patient_id
                logger.info(f"Added patient_id {patient_id} to user_metadata for graph")

            # Pass conversation history in the metadata for proper context management
            user_metadata["conversation_history"] = conversation_history
            logger.info(f"Looking up patient with system_id: telegram:{user_id}")
            patient_id = get_patient_id_from_platform_id("telegram", str(user_id))

            # Prepare for graph processing - graph_builder is already the compiled graph
            graph = graph_builder  # Don't call it as a function

            # Create thread ID with consistent format - always include patient_id if available
            thread_id = f"telegram-{chat_id}-{user_id}"
            if patient_id:
                thread_id += f"-patient-{patient_id}"

            # Create message for graph processing with metadata
            human_message = HumanMessage(
                content=message_content, metadata=user_metadata
            )

            # Set up graph config with appropriate patient_id if available
            config = {
                "configurable": {
                    "thread_id": thread_id,
                    "user_metadata": user_metadata,
                }
            }

            # Process message through graph
            result = await graph.ainvoke({"messages": [human_message]}, config)

            # Extract the response
            response_message = result["messages"][-1]
            response_text = (
                response_message.content
                if hasattr(response_message, "content")
                else str(response_message)
            )

            # Configure the workflow for further processing
            workflow = "conversation"  # default workflow
            result_data = {}  # default empty result data

            # Check if the response has a workflow attribute
            if (
                hasattr(response_message, "additional_kwargs")
                and "workflow" in response_message.additional_kwargs
            ):
                workflow = response_message.additional_kwargs["workflow"]

            # Extract result data if available
            if (
                hasattr(response_message, "additional_kwargs")
                and "result" in response_message.additional_kwargs
            ):
                result_data = response_message.additional_kwargs["result"]

            # Send the response based on workflow
            await self._send_response(
                chat_id, response_text, workflow, result_data, message_type
            )

            # Save to database for history tracking
            await self._save_to_database(
                user_metadata, message_content, response_text, patient_id
            )
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            try:
                # Try to send a simple error message as fallback
                if chat_id:
                    await self._send_message(
                        chat_id,
                        "Atsiprašau, įvyko klaida apdorojant jūsų žinutę. Prašome bandyti vėliau.",
                    )
            except Exception as inner_e:
                logger.error(f"Failed to send error message: {inner_e}")

    async def _get_conversation_history(
        self, chat_id: int, user_id: int, max_messages: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history using standardized memory service.

        Args:
            chat_id: Telegram chat ID
            user_id: Telegram user ID
            max_messages: Maximum number of messages to retrieve

        Returns:
            List of message dictionaries with content and role
        """
        try:
            # Get patient_id for this user
            patient_id = await self._get_patient_id(user_id)

            if not patient_id:
                logger.warning(
                    f"No patient_id found for telegram user {user_id}, cannot retrieve conversation history"
                )
                return []

            # Use memory service directly with standardized approach, including patient_id
            raw_memories = await self.memory_service.get_session_memory(
                platform="telegram",
                user_id=str(user_id),
                patient_id=patient_id,
                limit=max_messages * 2,
            )

            # Format the conversation history
            conversation_history = []

            for memory in raw_memories:
                try:
                    # Check for new format with both user message and bot response
                    if "response" in memory:
                        # Add user message
                        conversation_history.append(
                            {"role": "user", "content": memory.get("content", "")}
                        )
                        # Add bot response
                        conversation_history.append(
                            {"role": "assistant", "content": memory.get("response", "")}
                        )
                    else:
                        # Try to parse content - it might be a JSON string
                        content = memory.get("content", "")
                        if isinstance(content, str):
                            # Try to parse as JSON if it looks like JSON
                            if content.startswith("{") and content.endswith("}"):
                                try:
                                    content_obj = json.loads(content)
                                    if isinstance(content_obj, dict):
                                        # Extract user message and bot response if available
                                        user_msg = content_obj.get("user_message", "")
                                        bot_msg = content_obj.get("bot_response", "")
                                        if user_msg:
                                            conversation_history.append(
                                                {"role": "user", "content": user_msg}
                                            )
                                        if bot_msg:
                                            conversation_history.append(
                                                {
                                                    "role": "assistant",
                                                    "content": bot_msg,
                                                }
                                            )
                                except json.JSONDecodeError:
                                    # Not valid JSON, treat as regular content
                                    pass

                        # If not JSON or parsing failed, use the content as is
                        if (
                            not content.startswith("{")
                            or len(conversation_history) == 0
                        ):
                            # Try to determine the role based on metadata
                            metadata = memory.get("metadata", {})
                            role = (
                                "user"
                                if metadata.get("sender") == "patient"
                                else "assistant"
                            )
                            conversation_history.append(
                                {"role": role, "content": content}
                            )
                except Exception as e:
                    logger.warning(f"Error parsing conversation history entry: {e}")
                    continue

            # Limit to max_messages most recent entries, ensuring we have complete pairs
            return conversation_history[-max_messages:] if conversation_history else []

        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}", exc_info=True)
            return []

    async def _handle_command(self, message: Dict) -> bool:
        """
        Handle command messages starting with /.

        Args:
            message: The message containing the command

        Returns:
            True if the command was handled, False otherwise
        """
        chat_id = message.get("chat", {}).get("id")
        # Using _ for unused variable
        _ = message.get("from", {}).get("id")
        text = message.get("text", "")

        # Extract command and params
        parts = text.split()
        command = parts[0].lower()
        params = parts[1:] if len(parts) > 1 else []

        logger.info(f"Received command: {command} with params: {params}")

        if command == "/schedule":
            # Command format: /schedule <time> <message>
            # Example: /schedule 2023-12-31T12:00:00 Happy New Year!
            if len(params) < 2:
                await self._send_message(
                    chat_id,
                    "📝 *USAGE INSTRUCTIONS:* /schedule <time> <message>\n\n"
                    "*Examples:*\n"
                    "- One-time: `/schedule 2023-12-31T12:00:00 Happy New Year!`\n"
                    "- Daily: `/schedule daily 09:00 Good morning!`\n"
                    "- Weekly: `/schedule weekly mon,wed,fri 08:00 Weekly reminder`\n"
                    "- Monthly: `/schedule monthly 1 10:00 Monthly report`\n"
                    "- Custom: `/schedule every 30m Time for a break`\n"
                    "- Relative: `/schedule after 2m Send this message in 2 minutes`",
                )
                return True

            try:
                # Parse scheduled time based on format
                scheduled_time = None
                recurrence_pattern = None
                message_start_idx = 1

                # Check for recurrence pattern
                if params[0].lower() == "daily":
                    # Daily recurrence: /schedule daily 09:00 Message
                    if len(params) < 3:
                        await self._send_message(
                            chat_id,
                            "Please provide time and message for daily schedule",
                        )
                        return True

                    time_str = params[1]
                    message_start_idx = 2

                    # Parse time (HH:MM format)
                    hour, minute = map(int, time_str.split(":"))

                    # Use today's date with specified time for first occurrence
                    now = datetime.utcnow()
                    scheduled_time = datetime(
                        year=now.year,
                        month=now.month,
                        day=now.day,
                        hour=hour,
                        minute=minute,
                    )

                    # If time already passed today, start tomorrow
                    if scheduled_time < now:
                        scheduled_time += timedelta(days=1)

                    # Create recurrence pattern
                    recurrence_pattern = {"type": "daily", "interval": 1}

                    # Add state confirmation with emoji
                    await self._send_message(
                        chat_id, "⏳ *Processing daily schedule request...*"
                    )

                elif params[0].lower() == "weekly":
                    # Weekly recurrence: /schedule weekly mon,wed,fri 08:00 Message
                    if len(params) < 3:
                        await self._send_message(
                            chat_id,
                            "Please provide days, time and message for weekly schedule",
                        )
                        return True

                    days_str = params[1].lower()
                    time_str = params[2]
                    message_start_idx = 3

                    # Parse days (comma-separated day abbreviations)
                    day_mapping = {
                        "mon": 0,
                        "tue": 1,
                        "wed": 2,
                        "thu": 3,
                        "fri": 4,
                        "sat": 5,
                        "sun": 6,
                    }

                    days = []
                    for day_abbr in days_str.split(","):
                        if day_abbr in day_mapping:
                            days.append(day_mapping[day_abbr])

                    if not days:
                        await self._send_message(
                            chat_id,
                            "Please provide valid days (mon,tue,wed,thu,fri,sat,sun)",
                        )
                        return True

                    # Parse time (HH:MM format)
                    hour, minute = map(int, time_str.split(":"))

                    # Find the next occurrence
                    now = datetime.utcnow()
                    current_day = now.weekday()

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

                    # Create scheduled time
                    scheduled_time = datetime(
                        year=now.year,
                        month=now.month,
                        day=now.day,
                        hour=hour,
                        minute=minute,
                    ) + timedelta(days=days_diff)

                    # Create recurrence pattern
                    recurrence_pattern = {"type": "weekly", "interval": 1, "days": days}

                elif params[0].lower() == "monthly":
                    # Monthly recurrence: /schedule monthly 15 10:00 Message
                    if len(params) < 3:
                        await self._send_message(
                            chat_id,
                            "Please provide day, time and message for monthly schedule",
                        )
                        return True

                    day = int(params[1])
                    time_str = params[2]
                    message_start_idx = 3

                    if day < 1 or day > 31:
                        await self._send_message(
                            chat_id, "Please provide a valid day of month (1-31)"
                        )
                        return True

                    # Parse time (HH:MM format)
                    hour, minute = map(int, time_str.split(":"))

                    # Use current month with specified day for first occurrence
                    now = datetime.utcnow()

                    # Handle month length issues
                    import calendar

                    _, last_day = calendar.monthrange(now.year, now.month)
                    day = min(day, last_day)

                    scheduled_time = datetime(
                        year=now.year,
                        month=now.month,
                        day=day,
                        hour=hour,
                        minute=minute,
                    )

                    # If day already passed this month, move to next month
                    if scheduled_time < now:
                        month = now.month + 1
                        year = now.year

                        if month > 12:
                            month = 1
                            year += 1

                        # Validate day in next month
                        _, last_day = calendar.monthrange(year, month)
                        day = min(day, last_day)

                        scheduled_time = datetime(
                            year=year, month=month, day=day, hour=hour, minute=minute
                        )

                    # Create recurrence pattern
                    recurrence_pattern = {"type": "monthly", "interval": 1, "day": day}

                elif params[0].lower() == "every":
                    # Custom interval: /schedule every 30m Message
                    if len(params) < 2:
                        await self._send_message(
                            chat_id,
                            "Please provide interval and message for custom schedule",
                        )
                        return True

                    interval_str = params[1].lower()
                    message_start_idx = 2

                    # Parse interval (e.g., 30m, 2h, 1d)
                    if interval_str[-1] == "m":
                        minutes = int(interval_str[:-1])
                    elif interval_str[-1] == "h":
                        minutes = int(interval_str[:-1]) * 60
                    elif interval_str[-1] == "d":
                        minutes = int(interval_str[:-1]) * 60 * 24
                    else:
                        # Assume minutes if no unit specified
                        minutes = int(interval_str)

                    if minutes < 5:
                        await self._send_message(
                            chat_id, "Interval must be at least 5 minutes"
                        )
                        return True

                    # Start from current time
                    scheduled_time = datetime.utcnow() + timedelta(minutes=1)

                    # Create recurrence pattern
                    recurrence_pattern = {"type": "custom", "minutes": minutes}

                elif params[0].lower() == "after":
                    # Relative time: /schedule after 2m Message
                    if len(params) < 2:
                        await self._send_message(
                            chat_id,
                            "Please provide time interval and message for scheduling",
                        )
                        return True

                    interval_str = params[1].lower()
                    message_start_idx = 2

                    # Parse interval (e.g., 2m, 1h, 30s)
                    time_value = 0
                    try:
                        if interval_str[-1] == "m":
                            time_value = int(interval_str[:-1])
                            scheduled_time = datetime.utcnow() + timedelta(
                                minutes=time_value
                            )
                        elif interval_str[-1] == "h":
                            time_value = int(interval_str[:-1])
                            scheduled_time = datetime.utcnow() + timedelta(
                                hours=time_value
                            )
                        elif interval_str[-1] == "d":
                            time_value = int(interval_str[:-1])
                            scheduled_time = datetime.utcnow() + timedelta(
                                days=time_value
                            )
                        elif interval_str[-1] == "s":
                            time_value = int(interval_str[:-1])
                            scheduled_time = datetime.utcnow() + timedelta(
                                seconds=time_value
                            )
                        else:
                            # Assume minutes if no unit specified
                            time_value = int(interval_str)
                            scheduled_time = datetime.utcnow() + timedelta(
                                minutes=time_value
                            )

                        # Ensure the scheduled time is not in the past
                        if scheduled_time <= datetime.utcnow():
                            # Minimum 10 seconds in the future
                            scheduled_time = datetime.utcnow() + timedelta(seconds=10)
                            logger.info(
                                f"Adjusted scheduled_time to ensure it's in the future: {scheduled_time.isoformat()}"
                            )

                    except ValueError:
                        await self._send_message(
                            chat_id,
                            f"❌ *ERROR:* Invalid time format: {interval_str}\nPlease use a number followed by m (minutes), h (hours), d (days), or s (seconds)",
                        )
                        return True

                    # No recurrence pattern for "after" - it's a one-time message
                    recurrence_pattern = None

                    # Confirm the scheduling
                    unit_text = (
                        "minutes"
                        if interval_str[-1] == "m" or interval_str[-1].isdigit()
                        else "hours"
                        if interval_str[-1] == "h"
                        else "days"
                        if interval_str[-1] == "d"
                        else "seconds"
                    )
                    await self._send_message(
                        chat_id,
                        f"⏳ *Processing schedule request for {time_value} {unit_text} from now...*",
                    )

                    # Add specific debug logging for after command
                    logger.info(
                        f"Scheduling 'after' message: chat_id={chat_id}, time_value={time_value}, scheduled_time={scheduled_time.isoformat()}"
                    )

                else:
                    # One-time schedule: /schedule 2023-12-31T12:00:00 Message
                    time_str = params[0]
                    message_start_idx = 1

                    # Try different time formats
                    try:
                        # Try ISO format first
                        scheduled_time = datetime.fromisoformat(time_str)
                    except ValueError:
                        try:
                            # Try date+time format
                            scheduled_time = datetime.strptime(
                                time_str, "%Y-%m-%d %H:%M:%S"
                            )
                        except ValueError:
                            try:
                                # Try date with default time (00:00:00)
                                scheduled_time = datetime.strptime(time_str, "%Y-%m-%d")
                            except ValueError:
                                await self._send_message(
                                    chat_id,
                                    "Invalid time format. Please use YYYY-MM-DDThh:mm:ss or see examples with /schedule.",
                                )
                                return True

                # Check if scheduled time is in the past
                if scheduled_time < datetime.utcnow() and not recurrence_pattern:
                    await self._send_message(
                        chat_id, "❌ *ERROR:* Cannot schedule messages in the past"
                    )
                    return True

                # Extract message content
                message_content = " ".join(params[message_start_idx:])

                # Create scheduled message
                try:
                    # Log detailed parameters before scheduling
                    logger.info("About to create scheduled message with parameters:")
                    logger.info(f"  - chat_id: {chat_id}")
                    logger.info(f"  - scheduled_time: {scheduled_time.isoformat()}")
                    logger.info(f"  - message_content: '{message_content}'")
                    logger.info(f"  - recurrence_pattern: {recurrence_pattern}")

                    message_id = await self.create_scheduled_message(
                        chat_id=chat_id,
                        message_content=message_content,
                        scheduled_time=scheduled_time,
                        recurrence_pattern=recurrence_pattern,
                    )

                    # Verify the message was created
                    scheduled_message = (
                        await self.scheduled_message_service.get_message_by_id(
                            message_id
                        )
                    )
                    if not scheduled_message:
                        logger.error(
                            f"Message created but not found in database: {message_id}"
                        )
                        error_message = (
                            "❌ *ERROR:* Message scheduled but verification failed\n\n"
                            "🔴 Please try again or contact support if the issue persists."
                        )
                        await self._send_message(chat_id, error_message)
                        return True

                    logger.info(
                        f"Successfully verified message in database: {message_id}"
                    )

                    # Create confirmation message with status info
                    if recurrence_pattern:
                        recurrence_type = recurrence_pattern["type"]
                        if recurrence_type == "daily":
                            pattern_desc = "daily"
                        elif recurrence_type == "weekly":
                            days = recurrence_pattern["days"]
                            day_names = [
                                "Mon",
                                "Tue",
                                "Wed",
                                "Thu",
                                "Fri",
                                "Sat",
                                "Sun",
                            ]
                            day_list = [day_names[d] for d in days]
                            pattern_desc = f"weekly on {', '.join(day_list)}"
                        elif recurrence_type == "monthly":
                            day = recurrence_pattern["day"]
                            pattern_desc = f"monthly on day {day}"
                        elif recurrence_type == "custom":
                            minutes = recurrence_pattern["minutes"]
                            if minutes < 60:
                                pattern_desc = f"every {minutes} minutes"
                            elif minutes < 60 * 24:
                                hours = minutes / 60
                                pattern_desc = f"every {hours:.1f} hours"
                            else:
                                days = minutes / (60 * 24)
                                pattern_desc = f"every {days:.1f} days"
                        else:
                            pattern_desc = "on a recurring schedule"

                        confirmation = (
                            f"✅ *SUCCESS:* Message scheduled {pattern_desc}\n\n"
                            f"🕒 First occurrence: `{scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}`\n"
                            f"📝 Message: \"{message_content}\"\n\n"
                            f"🆔 ID: `{message_id}`\n\n"
                            f"ℹ️ Use `/scheduled` to see all your scheduled messages\n"
                            f"ℹ️ Use `/cancel_schedule {message_id}` to cancel"
                        )
                    else:
                        confirmation = (
                            f"✅ *SUCCESS:* Message scheduled for one-time delivery\n\n"
                            f"🕒 Scheduled time: `{scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}`\n"
                            f"📝 Message: \"{message_content}\"\n\n"
                            f"🆔 ID: `{message_id}`\n\n"
                            f"ℹ️ Use `/scheduled` to see all your scheduled messages\n"
                            f"ℹ️ Use `/cancel_schedule {message_id}` to cancel"
                        )

                    await self._send_message(chat_id, confirmation)
                except Exception as e:
                    error_message = (
                        f"❌ *ERROR:* Failed to schedule message\n\n"
                        f"🔴 Error details: `{str(e)}`\n\n"
                        f"Please try again or contact support if the issue persists."
                    )
                    await self._send_message(chat_id, error_message)
                    logger.error(f"Error scheduling message: {e}", exc_info=True)

            except Exception as e:
                error_message = (
                    f"❌ *ERROR:* Could not process scheduling command\n\n"
                    f"🔴 Error details: `{str(e)}`\n\n"
                    f"Please check the command format:\n"
                    f"`/schedule <time> <message>`\n\n"
                    f"Use `/schedule` without parameters for help."
                )
                await self._send_message(chat_id, error_message)
                logger.error(f"Error scheduling message: {e}", exc_info=True)

            return True

        elif command == "/scheduled":
            # List scheduled messages for this chat
            try:
                await self._send_message(
                    chat_id, "⏳ *Fetching your scheduled messages...*"
                )

                messages = await self.get_scheduled_messages_for_chat(chat_id)

                # Check if there was a database connection error
                if messages and len(messages) == 1 and messages[0].get("error") is True:
                    error_details = messages[0].get("message", "Unknown database error")
                    await self._send_message(
                        chat_id,
                        f"❌ *DATABASE CONNECTION ERROR*\n\n"
                        f"There was a problem connecting to the database: {error_details}\n\n"
                        f"Your scheduled messages exist, but can't be displayed right now.\n"
                        f"Please try again in a few minutes.",
                    )
                    logger.error(f"Database error shown to user: {error_details}")
                    return True

                if not messages:
                    await self._send_message(
                        chat_id,
                        "📭 *No scheduled messages found*\n\nYou don't have any pending scheduled messages.",
                    )
                    return True

                # Format message list
                response = "📋 *Your Scheduled Messages:*\n\n"

                for i, msg in enumerate(messages):
                    scheduled_time = datetime.fromisoformat(
                        msg["scheduled_time"].replace("Z", "+00:00")
                    )
                    status = msg["status"].capitalize()
                    message_preview = msg["message_content"]

                    # Add status emoji
                    status_emoji = (
                        "⏳"
                        if status == "Pending"
                        else "✅"
                        if status == "Sent"
                        else "❌"
                        if status == "Failed"
                        else "🔄"
                        if status == "Rescheduled"
                        else "⚠️"
                    )

                    # Truncate long messages
                    if len(message_preview) > 30:
                        message_preview = message_preview[:27] + "..."

                    # Check if recurring
                    metadata = msg.get("metadata", {})
                    recurrence = metadata.get("recurrence")
                    recurring = "🔄 " if recurrence else "📅 "

                    response += (
                        f"{i+1}. {recurring}{scheduled_time.strftime('%Y-%m-%d %H:%M')}"
                        f" ({status_emoji} {status}): {message_preview}\n"
                        f"   🆔 ID: `{msg['id']}`\n\n"
                    )

                response += "ℹ️ To cancel a message, use `/cancel_schedule <message_id>`"
                await self._send_message(chat_id, response)

            except Exception as e:
                error_message = (
                    f"❌ *ERROR:* Failed to retrieve scheduled messages\n\n"
                    f"🔴 Error details: `{str(e)}`\n\n"
                    f"There might be a connection issue with the Telegram API or database.\n"
                    f"Please try again later."
                )
                await self._send_message(chat_id, error_message)
                logger.error(f"Error listing scheduled messages: {e}", exc_info=True)

            return True

        elif command == "/cancel_schedule":
            # Cancel a scheduled message
            # Usage: /cancel_schedule <message_id>
            if len(params) != 1:
                await self._send_message(
                    chat_id,
                    "📝 *USAGE:* `/cancel_schedule <message_id>`\n\nUse `/scheduled` to see your message IDs.",
                )
                return True

            message_id = params[0]

            await self._send_message(
                chat_id,
                f"⏳ *Processing cancellation request for message* `{message_id}`...",
            )

            try:
                # Get message to verify ownership
                message = await self.scheduled_message_service.get_message_by_id(
                    message_id
                )

                if not message:
                    await self._send_message(
                        chat_id, f"❌ *ERROR:* Message with ID `{message_id}` not found"
                    )
                    return True

                # Verify that this message belongs to this chat
                metadata = message.get("metadata", {})
                platform_data = metadata.get("platform_data", {})
                message_chat_id = platform_data.get("chat_id")

                if message_chat_id != chat_id:
                    await self._send_message(
                        chat_id,
                        "⛔ *ACCESS DENIED:* You don't have permission to cancel this message",
                    )
                    return True

                # Get message details for confirmation
                scheduled_time = datetime.fromisoformat(
                    message.get("scheduled_time", "").replace("Z", "+00:00")
                )
                message_content = message.get("message_content", "")
                current_status = message.get("status", "unknown")

                # Cancel the message
                success = await self.cancel_scheduled_message(message_id)

                if success:
                    confirmation = (
                        f"✅ *SUCCESS:* Scheduled message cancelled\n\n"
                        f"🆔 ID: `{message_id}`\n"
                        f"📝 Message: \"{message_content}\"\n"
                        f"🕒 Was scheduled for: `{scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}`\n"
                        f"📊 Previous status: {current_status}"
                    )
                    await self._send_message(chat_id, confirmation)
                else:
                    error_message = (
                        f"❌ *ERROR:* Failed to cancel message\n\n"
                        f"This could be because the message has already been sent or has an invalid status.\n\n"
                        f"Current status: {current_status}"
                    )
                    await self._send_message(chat_id, error_message)

            except Exception as e:
                error_message = (
                    f"❌ *ERROR:* Failed to cancel scheduled message\n\n"
                    f"🔴 Error details: `{str(e)}`\n\n"
                    f"Please try again with a valid message ID."
                )
                await self._send_message(chat_id, error_message)
                logger.error(f"Error cancelling scheduled message: {e}", exc_info=True)

            return True

        # Command not recognized or handled
        return False

    async def _send_direct_response(
        self,
        chat_id: int,
        response_text: str,
        workflow: str,
        result: Union[Dict, Any],
        message_type: Optional[str] = None,
    ):
        """Send response directly from conversation_node without modifications."""
        try:
            # Ensure we have a valid response text
            if not response_text or not isinstance(response_text, str):
                logger.warning(f"Invalid response text: {response_text}")
                response_text = "Sorry, I encountered an error generating a response."

            # Try to get patient_id for enhanced logging
            patient_id = "unknown"
            user_id = None
            try:
                # Prioritize getting user_id and patient_id from the most reliable source:
                # 1. Check the user_metadata within the configurable part of the result
                if isinstance(result, dict) and "configurable" in result:
                    config = result.get("configurable", {})
                    user_metadata = config.get("user_metadata", {})
                    user_id = user_metadata.get(
                        "external_system_id"
                    )  # Use the correct key
                    patient_id_from_config = user_metadata.get("patient_id")
                    if user_id:
                        logger.debug(
                            f"Extracted user_id '{user_id}' from result['configurable']['user_metadata']"
                        )
                    if patient_id_from_config:
                        patient_id = patient_id_from_config
                        logger.debug(
                            f"Extracted patient_id '{patient_id}' from result['configurable']['user_metadata']"
                        )

                # 2. If not found in config, try the metadata of the last message in the result
                if not user_id or patient_id == "unknown":
                    if isinstance(result, dict) and "messages" in result:
                        messages = result.get("messages", [])
                        if (
                            messages
                            and hasattr(messages[-1], "metadata")
                            and messages[-1].metadata
                        ):
                            msg_metadata = messages[-1].metadata
                            if not user_id:
                                user_id = msg_metadata.get(
                                    "external_system_id"
                                )  # Use the correct key
                                if user_id:
                                    logger.debug(
                                        f"Extracted user_id '{user_id}' from last message metadata"
                                    )
                            if patient_id == "unknown":
                                patient_id_from_msg = msg_metadata.get("patient_id")
                                if patient_id_from_msg:
                                    patient_id = patient_id_from_msg
                                    logger.debug(
                                        f"Extracted patient_id '{patient_id}' from last message metadata"
                                    )

                # 3. If still no user_id, use chat_id as a fallback (less ideal)
                if not user_id:
                    user_id = str(chat_id)  # Ensure it's a string
                    logger.debug(f"Using chat_id '{user_id}' as fallback for user_id")

                # 4. If we have user_id but still no patient_id, look it up
                if user_id and patient_id == "unknown":
                    patient_id_result = await self._get_patient_id(user_id)
                    if patient_id_result:
                        patient_id = patient_id_result
                        logger.info(
                            f"Looked up patient_id '{patient_id}' for user_id '{user_id}'"
                        )
                    else:
                        logger.warning(
                            f"Could not find patient_id for user_id '{user_id}'"
                        )

            except Exception as e:
                logger.error(
                    f"Error getting patient_id/user_id for response logging: {e}",
                    exc_info=True,
                )

            # Print bot response in green to terminal
            print_green(f"BOT → {chat_id}: {response_text}")

            # Log the response with patient context
            logger.info(
                f"BOT RESPONSE | Patient: {patient_id} | Chat: {chat_id} | Workflow: {workflow} | Length: {len(response_text)} chars"
            )

            # For long responses, log a snippet
            if len(response_text) > 100:
                snippet = response_text[:97] + "..."
                logger.debug(f"Response snippet: {snippet}")

            # Handle the case where result is not a dictionary
            if not isinstance(result, dict):
                if message_type == "voice":
                    # For voice messages, also generate and send a voice response
                    try:
                        audio_data = await text_to_speech.synthesize(response_text)
                        await self._send_voice(chat_id, audio_data)
                        await self._send_message(chat_id, response_text)
                    except Exception as e:
                        logger.error(
                            f"Error generating voice response: {e}", exc_info=True
                        )
                        await self._send_message(chat_id, response_text)
                else:
                    await self._send_message(chat_id, response_text)
                return

            # Handle different workflow types with appropriate response formats
            if workflow == "audio":
                audio_buffer = result.get("audio_buffer")
                if audio_buffer:
                    await self._send_voice(chat_id, audio_buffer, response_text)
                else:
                    await self._send_message(chat_id, response_text)

            elif workflow == "image":
                image_path = result.get("image_path")
                if image_path:
                    try:
                        with open(image_path, "rb") as f:
                            image_data = f.read()
                        await self._send_photo(chat_id, image_data, response_text)
                    except FileNotFoundError:
                        logger.error(f"Image file not found: {image_path}")
                        await self._send_message(chat_id, response_text)
                else:
                    await self._send_message(chat_id, response_text)

            elif message_type == "voice":
                # For voice input messages, also generate and send a voice response
                try:
                    audio_data = await text_to_speech.synthesize(response_text)
                    await self._send_voice(chat_id, audio_data)
                    await self._send_message(chat_id, response_text)
                except Exception as e:
                    logger.error(f"Error generating voice response: {e}", exc_info=True)
                    await self._send_message(chat_id, response_text)

            else:  # Default to conversation workflow
                await self._send_message(chat_id, response_text)

            logger.info(f"Successfully sent response to chat {chat_id}")

        except Exception as e:
            logger.error(f"Error sending response: {e}", exc_info=True)
            try:
                # Try to send a simplified error message
                simple_msg = "Sorry, I encountered an error sending the response."
                await self._send_message(chat_id, simple_msg)
            except Exception as e2:
                logger.error(f"Failed to send error message: {e2}", exc_info=True)

    async def _extract_message_content(self, message: Dict) -> Optional[tuple]:
        """Extract and process different types of content from a message."""
        try:
            content_type = None
            content = None

            if "text" in message:
                content_type = "text"
                content = message["text"]
            elif "voice" in message:
                content_type = "voice"
                file_id = message["voice"]["file_id"]
                voice_data = await self._download_file(file_id)
                content = await speech_to_text.transcribe(voice_data)
            elif "photo" in message:
                content_type = "photo"
                # Get the largest photo (last in the array)
                file_id = message["photo"][-1]["file_id"]
                photo_data = await self._download_file(file_id)
                content = await image_to_text.process_image(photo_data)

            if content_type and content:
                return content_type, content

            return None
        except Exception as e:
            logger.error(f"Error extracting message content: {e}")
            return None

    def _clean_response_text(self, text: str) -> str:
        """
        Remove markdown formatting symbols from response text.

        Args:
            text: The response text to clean

        Returns:
            Cleaned text without markdown symbols
        """
        if not text:
            return text

        # Remove asterisks (used for bold formatting in markdown)
        cleaned_text = text.replace("*", "")

        # Other potential formatting to clean if needed:
        # cleaned_text = cleaned_text.replace("_", "")  # Remove underscores (italic)
        # cleaned_text = cleaned_text.replace("`", "")  # Remove backticks (code)

        return cleaned_text

    async def _send_response(
        self,
        chat_id: int,
        response_text: str,
        workflow: str,
        result: Union[Dict, Any],
        message_type: Optional[str] = None,
    ):
        """Send response based on workflow type."""
        try:
            # Ensure we have a valid response text
            if not response_text or not isinstance(response_text, str):
                logger.warning(f"Invalid response text: {response_text}")
                response_text = "Sorry, I encountered an error generating a response."

            # Check if response contains structured RAG information - don't modify these
            contains_structured_info = any(
                marker in response_text
                for marker in [
                    "**",
                    "##",
                    "1.",
                    "2.",
                    "3.",
                    "4.",
                    "5.",
                    "•",
                    "*Registracija*",
                    "*Dokument",
                    "*Patvirtinim",
                ]
            )

            # Only apply response variations if it's NOT a structured RAG response
            if not contains_structured_info:
                response_text = self._add_response_variation(response_text)
            else:
                logger.info(
                    "Detected structured RAG response - preserving original format"
                )

            # Clean response text to remove markdown formatting ONLY if it's not a RAG response
            if not contains_structured_info:
                response_text = self._clean_response_text(response_text)

            # Print bot response in green to terminal
            print_green(f"BOT → {chat_id}: {response_text}")

            logger.info(
                f"Sending response with workflow '{workflow}', length: {len(response_text)} chars"
            )

            # Handle the case where result is not a dictionary
            if not isinstance(result, dict):
                if message_type == "voice":
                    # For voice messages, also generate and send a voice response
                    try:
                        audio_data = await text_to_speech.synthesize(response_text)
                        await self._send_voice(chat_id, audio_data)
                        await self._send_message(chat_id, response_text)
                    except Exception as e:
                        logger.error(
                            f"Error generating voice response: {e}", exc_info=True
                        )
                        await self._send_message(chat_id, response_text)
                else:
                    await self._send_message(chat_id, response_text)
                return

            # Handle different workflow types with appropriate response formats
            if workflow == "audio":
                audio_buffer = result.get("audio_buffer")
                if audio_buffer:
                    await self._send_voice(chat_id, audio_buffer, response_text)
                else:
                    await self._send_message(chat_id, response_text)

            elif workflow == "image":
                image_path = result.get("image_path")
                if image_path:
                    try:
                        with open(image_path, "rb") as f:
                            image_data = f.read()
                        await self._send_photo(chat_id, image_data, response_text)
                    except FileNotFoundError:
                        logger.error(f"Image file not found: {image_path}")
                        await self._send_message(chat_id, response_text)
                else:
                    await self._send_message(chat_id, response_text)

            elif message_type == "voice":
                # For voice input messages, also generate and send a voice response
                try:
                    audio_data = await text_to_speech.synthesize(response_text)
                    await self._send_voice(chat_id, audio_data)
                    await self._send_message(chat_id, response_text)
                except Exception as e:
                    logger.error(f"Error generating voice response: {e}", exc_info=True)
                    await self._send_message(chat_id, response_text)

            else:  # Default to conversation workflow
                await self._send_message(chat_id, response_text)

            logger.info(f"Successfully sent response to chat {chat_id}")

        except Exception as e:
            logger.error(f"Error sending response: {e}", exc_info=True)
            try:
                # Try to send a simplified error message
                simple_msg = "Sorry, I encountered an error sending the response."
                await self._send_message(chat_id, simple_msg)
            except Exception as e2:
                logger.error(f"Failed to send error message: {e2}", exc_info=True)

    def _add_response_variation(self, text: str) -> str:
        """
        Detect and break repetitive patterns in responses to make them more natural.

        Args:
            text: The original response text

        Returns:
            Modified response with more variation
        """
        # Check for overused starting phrases
        common_starts = [
            "Žinoma!",
            "Žinoma, ",
            "Sveiki!",
            "Labas!",
            "Suprantu tavo klausimą",
        ]

        # Alternative starters in Lithuanian
        alt_starters = [
            "",  # Sometimes start directly without a greeting
            "Žiūrėk, ",
            "Na, ",
            "Hmm, ",
            "Nu tai, ",
            "Klausyk, ",
            "Matai, ",
            "Ai, ",
            "Tai jo, ",
            "Oj, ",
            "Na gerai, ",
            "Okay, ",
        ]

        modified_text = text

        # Replace standard openings with more varied ones
        for start in common_starts:
            if text.startswith(start):
                # 70% chance to replace with alternative
                if random.random() < 0.7:
                    replacement = random.choice(alt_starters)
                    modified_text = replacement + text[len(start) :].lstrip()
                break

        # Detect if the message follows the "I need more context" pattern
        context_phrases = [
            "reikia daugiau konteksto",
            "galėčiau tiksliai atsakyti",
            "reikėtų daugiau informacijos",
            "galėtumėte patikslinti",
            "norėčiau daugiau konteksto",
        ]

        # Check if the message is asking for clarification
        asks_for_clarification = any(
            phrase in modified_text.lower() for phrase in context_phrases
        )

        if asks_for_clarification and random.random() < 0.6:
            # Replace with more direct response 60% of the time
            simple_responses = [
                "Apie ką tiksliai nori sužinoti?",
                "Būtų šaunu jei patikslintum, kuo domiesi? 😊",
                "Tiesiog pasakyk konkrečiau, kuo galiu padėti?",
                "Nu tai kokia konkreti tema tave domina?",
                "Įdomu! O ką būtent norėtum sužinoti?",
                "Papasakok daugiau, kuo galiu padėti?",
                "Ką būtent nori išsiaiškinti?",
                "Sakyk drąsiai, kuo domiesi? Padėsiu kuo galėsiu!",
            ]
            modified_text = random.choice(simple_responses)

        # Break up long sentences - if we have more than 3 commas,
        # have a 50% chance to split into multiple sentences
        if modified_text.count(",") > 3 and random.random() < 0.5:
            parts = modified_text.split(",")
            if len(parts) > 3:
                # Convert some commas to periods
                for i in range(1, len(parts) - 1):
                    if random.random() < 0.4:  # 40% chance to convert each comma
                        parts[i] = parts[i].strip().capitalize() + "."
                modified_text = " ".join([p.strip() for p in parts])

        # Add some filler words and speech particles randomly
        filler_words = ["nu", "tai", "na", "žinai", "tipo", "mmm", "ane"]

        words = modified_text.split()
        if len(words) > 5 and random.random() < 0.3:  # 30% chance to add filler
            insert_pos = random.randint(1, min(4, len(words) - 1))
            filler = random.choice(filler_words)
            words.insert(insert_pos, filler)
            modified_text = " ".join(words)

        # Add an emoji at the end sometimes
        emojis = ["😊", "👍", "🙂", "😉", "🤔", "👌", "💪", "👏", "😁", "😄"]
        if random.random() < 0.2 and not any(
            emoji in modified_text for emoji in emojis
        ):
            modified_text += f" {random.choice(emojis)}"

        return modified_text

    async def _send_message(self, chat_id: int, text: str) -> Dict:
        """Send text message with chunking for long messages."""
        # Telegram has a 4096 character limit per message
        MAX_MESSAGE_LENGTH = 4000  # Using 4000 to be safe

        # Validate chat_id
        if not chat_id:
            logger.error("Attempted to send message with invalid chat_id")
            return {"ok": False, "description": "Invalid chat_id"}

        if not text:
            logger.warning("Attempted to send empty message")
            return {"ok": False, "description": "Empty message"}

        # Check if we need to split the message
        if len(text) <= MAX_MESSAGE_LENGTH:
            return await self._send_single_message(chat_id, text)

        # Split long messages into chunks
        chunks = []
        for i in range(0, len(text), MAX_MESSAGE_LENGTH):
            chunks.append(text[i : i + MAX_MESSAGE_LENGTH])

        logger.info(f"Splitting long message into {len(chunks)} chunks")

        # Send each chunk with progress indicator
        results = []
        for i, chunk in enumerate(chunks):
            # Add chunk indicator for multi-part messages
            if len(chunks) > 1:
                chunk_header = f"[Part {i+1}/{len(chunks)}]\n"
                chunk = chunk_header + chunk

            result = await self._send_single_message(chat_id, chunk)
            results.append(result)

            # Small delay between chunks to avoid rate limiting
            if i < len(chunks) - 1:
                await asyncio.sleep(0.5)

        # Return the last result as the overall result
        return results[-1]

    async def _send_single_message(self, chat_id: int, text: str) -> Dict:
        """Send a single text message with improved error handling."""
        try:
            # Validate chat_id format for Telegram (must be numeric or @username)
            if isinstance(chat_id, str):
                if chat_id.isdigit():
                    chat_id = int(chat_id)
                elif not chat_id.startswith("@"):
                    logger.error(f"Invalid chat_id format: {chat_id}")
                    return {"ok": False, "description": "Invalid chat_id format"}

            # Ensure text is not None
            if text is None:
                text = "No message content"

            return await self._make_request(
                "sendMessage", params={"chat_id": chat_id, "text": text}
            )
        except Exception as e:
            logger.error(f"Error in _send_single_message: {e}", exc_info=True)
            return {"ok": False, "description": str(e)}

    async def _make_request(
        self,
        method: str,
        params: Dict = None,
        files: Dict = None,
        data: Dict = None,
        retries: int = 5,  # Increased from 3 to 5
    ) -> Dict:
        """
        Make an HTTP request to the Telegram API.

        Args:
            method: API method name
            params: Request parameters
            files: Files to upload
            data: Form data
            retries: Maximum number of retry attempts

        Returns:
            The API response as a dict
        """
        if params is None:
            params = {}

        # Ensure there's no double slash in the URL
        if method.startswith("/"):
            method = method[1:]
        url = f"{self.base_url}/{method}"
        attempt = 0
        last_exception = None

        # Log detailed request information at debug level
        try:
            request_info = {}
            if method == "sendMessage":
                chat_id = params.get("chat_id", "unknown")
                text_preview = (
                    (params.get("text", "")[:30] + "...")
                    if params.get("text", "")
                    else "empty"
                )
                request_info = {"chat_id": chat_id, "text_preview": text_preview}
            logger.debug(f"Making request to {method} with params: {request_info}")
        except Exception as e:
            logger.warning(f"Could not log request_info for {method}: {e}")

        while attempt < retries:
            try:
                headers = {}
                attempt += 1

                if files:
                    # Multipart form request (file upload)
                    response = await self.client.post(
                        url, params=params, data=data, files=files
                    )
                else:
                    # Regular JSON request
                    headers["Content-Type"] = "application/json"
                    response = await self.client.post(url, headers=headers, json=params)

                # Make sure response is successful
                response.raise_for_status()

                # Use the built-in json method in httpx (which is not awaitable)
                result = response.json()

                if not result.get("ok", False):
                    error_msg = result.get("description", "Unknown error")
                    logger.error(f"Telegram API error in {method}: {error_msg}")

                    # Handle specific Telegram API errors
                    if "chat not found" in error_msg.lower():
                        logger.error(f"Chat ID not found: {params.get('chat_id')}")
                        return {
                            "ok": False,
                            "error_code": 400,
                            "description": f"Chat not found: {params.get('chat_id')}",
                        }

                    if "blocked by user" in error_msg.lower():
                        logger.error(
                            f"Bot was blocked by user: {params.get('chat_id')}"
                        )
                        return {
                            "ok": False,
                            "error_code": 403,
                            "description": f"Bot was blocked by user: {params.get('chat_id')}",
                        }

                    if "retry_after" in result:
                        retry_after = result["retry_after"]
                        logger.warning(
                            f"Rate limited, retrying after {retry_after} seconds"
                        )
                        await asyncio.sleep(retry_after)
                        continue

                    # Just return the error result, let the caller decide how to handle it
                    return result

                return result

            except httpx.HTTPStatusError as e:
                last_exception = e
                status_code = e.response.status_code

                if status_code == 429:  # Too Many Requests
                    try:
                        response_json = e.response.json()
                        retry_after = response_json.get("parameters", {}).get(
                            "retry_after", 5
                        )
                    except Exception:
                        retry_after = (
                            5  # Default retry time if we couldn't parse the response
                        )

                    logger.warning(
                        f"Rate limited (429), retrying after {retry_after} seconds"
                    )
                    await asyncio.sleep(retry_after)
                    continue
                elif status_code >= 500:
                    # Server error, retry with backoff
                    wait_time = min(2**attempt, 30)
                    logger.error(
                        f"Telegram server error ({status_code}), retrying in {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Client error that's not rate limiting
                    logger.error(f"HTTP error in Telegram API request: {e}")
                    if attempt < retries:
                        wait_time = min(2**attempt, 30)
                        await asyncio.sleep(wait_time)
                    else:
                        break
            except (httpx.NetworkError, httpx.TimeoutException) as e:
                last_exception = e
                logger.error(f"Network error in Telegram API request to {method}: {e}")
                wait_time = min(2**attempt, 30)  # Exponential backoff, max 30 seconds
                logger.info(
                    f"Retrying in {wait_time} seconds... (attempt {attempt}/{retries})"
                )
                await asyncio.sleep(wait_time)
            except Exception as e:
                last_exception = e
                logger.error(f"Error in Telegram API request to {method}: {e}")
                if attempt < retries:
                    wait_time = min(2**attempt, 30)
                    logger.info(
                        f"Retrying in {wait_time} seconds... (attempt {attempt}/{retries})"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    break

        # If we get here, all retries failed
        error_message = (
            str(last_exception) if last_exception else "Maximum retries reached"
        )
        logger.error(
            f"Telegram API connection failed after {retries} attempts: {error_message}"
        )

        # Return a formatted error response rather than raising an exception
        return {
            "ok": False,
            "description": f"Request failed after {retries} attempts: {error_message}",
        }

    async def _download_file(self, file_id: str) -> bytes:
        """Download file from Telegram servers."""
        try:
            # Get file path
            file_info = await self._make_request("getFile", params={"file_id": file_id})
            file_path = file_info["result"]["file_path"]

            # Download file
            download_url = f"{self.api_base}/file/bot{self.token}/{file_path}"
            response = await self.client.get(download_url)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            raise

    async def _send_photo(
        self, chat_id: int, photo: bytes, caption: str = None
    ) -> Dict:
        """Send photo message with proper handling of long captions."""
        files = {"photo": ("image.jpg", photo, "image/jpeg")}
        data = {"chat_id": chat_id}

        # Clean caption to remove markdown formatting
        if caption:
            caption = self._clean_response_text(caption)

        # Telegram has a 1024 character limit for photo captions
        MAX_CAPTION_LENGTH = 1000  # Using 1000 to be safe

        if not caption:
            return await self._make_request("sendPhoto", data=data, files=files)

        # If caption is short enough, send it with the photo
        if len(caption) <= MAX_CAPTION_LENGTH:
            data["caption"] = caption
            return await self._make_request("sendPhoto", data=data, files=files)

        # For long captions, send the photo first, then the caption as a separate message
        logger.info(f"Caption too long ({len(caption)} chars), sending separately")
        photo_result = await self._make_request("sendPhoto", data=data, files=files)

        # Send a shorter caption with the photo to give context
        short_caption = caption[:MAX_CAPTION_LENGTH] + "..."
        data["caption"] = short_caption
        await self._make_request("sendPhoto", data=data, files=files)

        # Send the full caption as a separate message
        await self._send_message(chat_id, caption)

        return photo_result

    async def _send_voice(
        self, chat_id: int, voice: bytes, caption: str = None
    ) -> Dict:
        """Send voice message with proper handling of captions."""
        files = {"voice": ("voice.ogg", voice, "audio/ogg")}
        data = {"chat_id": chat_id}

        # Send voice message first
        voice_result = await self._make_request("sendVoice", data=data, files=files)

        # Clean and send caption as a separate message if provided
        if caption and isinstance(caption, str) and caption.strip():
            caption = self._clean_response_text(caption)
            await self._send_message(chat_id, caption)

        return voice_result

    async def _save_to_database(
        self,
        user_metadata: Dict[str, Any],
        user_message: str,
        bot_response: str,
        patient_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Save conversation using standardized memory service.

        Args:
            user_metadata: User metadata including platform and IDs
            user_message: The user's message
            bot_response: The bot's response
            patient_id: Optional patient ID if already known

        Returns:
            The memory ID if successful, None otherwise
        """
        try:
            platform = "telegram"

            # Store through memory service using standardized approach
            conversation_data = {
                "user_message": user_message,
                "bot_response": bot_response,
            }

            # Create state with patient_id if available
            state = {}
            if patient_id:
                state["patient_id"] = patient_id

            # Get patient_id for this user
            if not patient_id:
                patient_id = await self._get_patient_id(user_metadata.get("user_id"))

            if not patient_id:
                logger.warning(
                    f"No patient_id found for {platform} user {user_metadata.get('user_id')}, cannot store memory"
                )
                return None

            # Store using memory service with patient_id
            memory_id = await self.memory_service.store_session_memory(
                platform=platform,
                user_id=str(user_metadata.get("user_id")),
                patient_id=patient_id,  # Add required patient_id
                state=state,
                conversation=conversation_data,
            )

            logger.info(
                f"Stored memory with ID: {memory_id} using standardized approach"
            )
            return memory_id

        except Exception as e:
            logger.error(f"Error saving to memory service: {e}")
            return None

    async def _get_recent_memories(
        self, chat_id: int, user_id: int, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent memories using standardized memory service.

        Args:
            chat_id: The Telegram chat ID
            user_id: The Telegram user ID
            limit: Maximum number of memories to retrieve

        Returns:
            List of memory contents as dictionaries
        """
        try:
            # Get patient_id for this user
            patient_id = await self._get_patient_id(user_id)

            if not patient_id:
                logger.warning(
                    f"No patient_id found for telegram user {user_id}, cannot retrieve memories"
                )
                return []

            # Use standard session ID format through memory service, including patient_id
            memories = await self.memory_service.get_session_memory(
                platform="telegram",
                user_id=str(user_id),
                patient_id=patient_id,
                limit=limit,
            )

            return memories
        except Exception as e:
            logger.error(f"Error retrieving recent memories: {e}", exc_info=True)
            return []

    async def _get_conversation_history(
        self, chat_id: int, user_id: int, max_messages: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history using standardized memory service.

        Args:
            chat_id: Telegram chat ID
            user_id: Telegram user ID
            max_messages: Maximum number of messages to retrieve

        Returns:
            List of message dictionaries with content and role
        """
        try:
            # Get patient_id for this user
            patient_id = await self._get_patient_id(user_id)

            if not patient_id:
                logger.warning(
                    f"No patient_id found for telegram user {user_id}, cannot retrieve conversation history"
                )
                return []

            # Use memory service directly with standardized approach, including patient_id
            raw_memories = await self.memory_service.get_session_memory(
                platform="telegram",
                user_id=str(user_id),
                patient_id=patient_id,
                limit=max_messages * 2,
            )

            # Format the conversation history
            conversation_history = []

            for memory in raw_memories:
                try:
                    # Check for new format with both user message and bot response
                    if "response" in memory:
                        # Add user message
                        conversation_history.append(
                            {"role": "user", "content": memory.get("content", "")}
                        )
                        # Add bot response
                        conversation_history.append(
                            {"role": "assistant", "content": memory.get("response", "")}
                        )
                    else:
                        # Try to parse content - it might be a JSON string
                        content = memory.get("content", "")
                        if isinstance(content, str):
                            # Try to parse as JSON if it looks like JSON
                            if content.startswith("{") and content.endswith("}"):
                                try:
                                    content_obj = json.loads(content)
                                    if isinstance(content_obj, dict):
                                        # Extract user message and bot response if available
                                        user_msg = content_obj.get("user_message", "")
                                        bot_msg = content_obj.get("bot_response", "")
                                        if user_msg:
                                            conversation_history.append(
                                                {"role": "user", "content": user_msg}
                                            )
                                        if bot_msg:
                                            conversation_history.append(
                                                {
                                                    "role": "assistant",
                                                    "content": bot_msg,
                                                }
                                            )
                                except json.JSONDecodeError:
                                    # Not valid JSON, treat as regular content
                                    pass

                        # If not JSON or parsing failed, use the content as is
                        if (
                            not content.startswith("{")
                            or len(conversation_history) == 0
                        ):
                            # Try to determine the role based on metadata
                            metadata = memory.get("metadata", {})
                            role = (
                                "user"
                                if metadata.get("sender") == "patient"
                                else "assistant"
                            )
                            conversation_history.append(
                                {"role": role, "content": content}
                            )
                except Exception as e:
                    logger.warning(f"Error parsing conversation history entry: {e}")
                    continue

            # Limit to max_messages most recent entries, ensuring we have complete pairs
            return conversation_history[-max_messages:] if conversation_history else []

        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}", exc_info=True)
            return []

    async def _log_memory_contents(self, chat_id: int, user_id: int):
        """
        Log the contents of short-term memory for debugging.

        Args:
            chat_id: Telegram chat ID
            user_id: Telegram user ID
        """
        logger.info(f"=== MEMORY CONTENTS FOR CHAT {chat_id}, USER {user_id} ===")
        print_green(f"=== MEMORY CONTENTS FOR CHAT {chat_id}, USER {user_id} ===")

        # Log short-term memory contents from Supabase
        try:
            # Query and log data from Supabase
            if self.supabase:
                result = (
                    self.supabase.table("short_term_memory")
                    .select("*")
                    .order("id", desc=True)  # Order by id instead of expires_at
                    .limit(10)
                    .execute()
                )

                if result.data:
                    logger.info(
                        f"SUPABASE SHORT-TERM MEMORY: Found {len(result.data)} records"
                    )
                    print_green(
                        f"SUPABASE SHORT-TERM MEMORY: Found {len(result.data)} records"
                    )

                    session_id = f"telegram-{chat_id}-{user_id}"
                    for i, record in enumerate(result.data):
                        try:
                            context = record.get("context", {})
                            metadata = context.get("metadata", {})
                            session = metadata.get("session_id", "unknown")

                            if session == session_id:
                                logger.info(f"  Record {i+1} (matching session):")
                                print_green(f"  Record {i+1} (matching session):")
                            else:
                                logger.info(
                                    f"  Record {i+1} (different session: {session}):"
                                )
                                print_green(
                                    f"  Record {i+1} (different session: {session}):"
                                )

                            logger.info(f"    ID: {record.get('id', 'N/A')}")
                            logger.info(
                                f"    Created: {context.get('created_at', 'N/A')}"
                            )
                            # REMOVED: logger.info(f"    Expires: {record.get('expires_at', 'N/A')}")

                            # Print conversation data if available
                            conversation = context.get("conversation", {})
                            if conversation:
                                logger.info(
                                    f"    User message: {conversation.get('user_message', 'N/A')}"
                                )
                                logger.info(
                                    f"    Bot response: {conversation.get('bot_response', 'N/A')}"
                                )
                                print_green(
                                    f"    User message: {conversation.get('user_message', 'N/A')}"
                                )
                                print_green(
                                    f"    Bot response: {conversation.get('bot_response', 'N/A')}"
                                )
                        except Exception as e:
                            logger.warning(f"Failed to parse record {i+1}: {e}")
                else:
                    logger.info("SUPABASE SHORT-TERM MEMORY: No records found")
                    print_green("SUPABASE SHORT-TERM MEMORY: No records found")
        except Exception as e:
            logger.error(f"Error logging short-term memory: {e}")

        logger.info("=== END MEMORY CONTENTS ===")
        print_green("=== END MEMORY CONTENTS ===")

    async def _send_typing_action(self, chat_id: int):
        """Send typing action to indicate the bot is processing the message."""
        try:
            await self._make_request(
                "sendChatAction", params={"chat_id": chat_id, "action": "typing"}
            )
        except Exception as e:
            logger.warning(f"Failed to send typing action: {e}")

    async def _generate_memory_summary(
        self, chat_id: int, user_id: int, conversation_history: List[Dict]
    ) -> str:
        """
        Generate a summary of key topics and information from memory to enhance context.

        Args:
            chat_id: Telegram chat ID
            user_id: Telegram user ID
            conversation_history: Recent conversation history

        Returns:
            A concise summary of important information from memory
        """
        try:
            # Get all memory sources for comprehensive context
            # Use standardized session ID format
            _session_id = f"telegram-{chat_id}-{user_id}"

            # Track important entities and topics mentioned
            important_topics = set()
            # Using _ for unused variable
            _ = {}
            key_facts = []

            # Extract topics from conversation history
            for entry in conversation_history:
                user_msg = entry.get("user_message", "").lower()
                bot_msg = entry.get("bot_response", "").lower()

                # Look for key entities (names, places, conditions, topics)
                for msg in [user_msg, bot_msg]:
                    # Simple keyword extraction
                    words = msg.split()
                    for word in words:
                        if (
                            len(word) > 5 and word.isalpha()
                        ):  # Focus on longer words as potential topics
                            important_topics.add(word)

                # Extract potential preferences or factual statements
                if "prefer" in user_msg or "like" in user_msg or "want" in user_msg:
                    key_facts.append(f"User preference: {user_msg}")
                if (
                    "my name is" in user_msg
                    or "i am" in user_msg
                    or "i have" in user_msg
                ):
                    key_facts.append(f"User info: {user_msg}")

            # Get patient information if available
            patient_info = {}
            if self.supabase:
                try:
                    platform_query = f'%"platform_id": "{user_id}"%'
                    result = (
                        self.supabase.table("patients")
                        .select("*")
                        .like("email", platform_query)
                        .execute()
                    )

                    if result.data and len(result.data) > 0:
                        patient_info = result.data[0]
                        # Extract relevant patient fields
                        for field in [
                            "first_name",
                            "last_name",
                            "risk",
                            "preferred_language",
                            "support_status",
                        ]:
                            if field in patient_info and patient_info[field]:
                                key_facts.append(
                                    f"Patient {field}: {patient_info[field]}"
                                )
                except Exception as e:
                    logger.warning(f"Failed to retrieve patient info: {e}")

            # Build the summary
            summary = []

            if key_facts:
                summary.append("Key user information:")
                for fact in key_facts[:5]:  # Limit to most important facts
                    summary.append(f"- {fact}")

            if important_topics:
                summary.append("\nFrequently discussed topics:")
                topic_list = list(important_topics)
                topic_summary = ", ".join(topic_list[:10])  # Limit to top topics
                summary.append(f"- {topic_summary}")

            if patient_info:
                summary.append("\nUser is a registered patient.")

            # Add interaction history summary
            summary.append(
                f"\nConversation history: {len(conversation_history)} recent interactions."
            )

            # Combine into one string
            return "\n".join(summary)

        except Exception as e:
            logger.error(f"Error generating memory summary: {e}")
            return "No memory summary available."

    async def _generate_personality_variation(self) -> Dict[str, Any]:
        """
        Generate slightly varied personality traits to make responses feel more human and diverse.

        Returns:
            Dictionary of personality instructions with slight variations each time
        """
        # Base personality elements
        empathy_levels = ["high", "very high", "warm", "compassionate"]
        tones = [
            "warm and friendly",
            "caring and personal",
            "casual and approachable",
            "warm and understanding",
        ]
        speaking_styles = [
            "conversational",
            "friendly chat",
            "relaxed and informal",
            "personal and direct",
        ]

        # Lithuanian-specific expressions to randomly include
        lt_expressions = [
            "Tai va",
            "Na žinai",
            "Nu gerai",
            "Žiūrėk",
            "Klausyk",
            "Supranti",
            "Matai kaip",
            "Tai štai",
            "Įsivaizduok",
            "Na tipo",
            "Nu jo",
        ]

        # Select random expressions to highlight (3-5 of them)
        highlighted_expressions = random.sample(lt_expressions, random.randint(3, 5))
        expressions_text = ", ".join([f"'{exp}'" for exp in highlighted_expressions])

        # Randomly vary emoji usage
        emoji_chance = random.choice([True, True, False])  # 2/3 chance of using emojis

        # Create randomly varied personality with Lithuanian traits
        personality = {
            "tone": random.choice(tones),
            "speaking_style": random.choice(speaking_styles),
            "empathy_level": random.choice(empathy_levels),
            "use_emoji": emoji_chance,
            "human_qualities": [
                "uses casual language",
                "shows genuine care",
                "uses everyday expressions",
                "speaks with emotion",
                "uses contractions and informal language",
            ],
            "lithuanian_traits": [
                "uses Lithuanian colloquialisms and slang",
                f"uses phrases like {expressions_text}",
                "occasionally shortens words like Lithuanians do in casual conversation",
                "uses friendly diminutives in appropriate contexts",
            ],
            "avoid": [
                "robotic language",
                "overly formal tone",
                "perfect grammar",
                "lengthy explanations without breaks",
                "AI-like phrases",
                "repetitive sentence structures",
                "overly clinical language",
                "too formal Lithuanian expressions typical in documentation",
            ],
        }

        # Randomly decide if the bot should include a small joke (30% chance)
        if random.random() < 0.3:
            personality["human_qualities"].append(
                "makes a light-hearted comment or gentle joke"
            )

        # Randomly decide if the bot should ask a follow-up question (60% chance)
        if random.random() < 0.6:
            personality["human_qualities"].append(
                "asks a thoughtful follow-up question"
            )

        return personality

    async def create_scheduled_message(
        self,
        chat_id: int,
        message_content: str,
        scheduled_time: datetime,
        patient_id: Optional[str] = None,
        recurrence_pattern: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        priority: int = 1,
    ) -> str:
        """
        Create a new scheduled message.

        Args:
            chat_id: The Telegram chat ID to send to
            message_content: The message text to send
            scheduled_time: When to send the message
            patient_id: Optional patient ID
            recurrence_pattern: Optional recurrence pattern dict
            metadata: Additional metadata for the message
            priority: Message priority (1=highest)

        Returns:
            The created message ID
        """
        # Validate chat_id format for Telegram
        if isinstance(chat_id, str):
            if chat_id.isdigit():
                chat_id = int(chat_id)
            elif not chat_id.startswith("@"):
                logger.warning(
                    f"Invalid chat_id format: {chat_id}. Must be numeric or @username."
                )
                raise ValueError(
                    "Invalid chat_id format. Must be numeric or @username."
                )

        # Ensure we have valid message content
        if not message_content or not isinstance(message_content, str):
            raise ValueError("Message content cannot be empty")

        # Ensure scheduled_time is in the future
        now = datetime.utcnow()
        if scheduled_time < now:
            logger.warning(f"Scheduled time {scheduled_time} is in the past")
            raise ValueError("Scheduled time must be in the future")

        # Prepare metadata with required platform data
        if metadata is None:
            metadata = {}

        # Ensure metadata is a dictionary
        if not isinstance(metadata, dict):
            metadata = {}

        # Add platform_data for Telegram integration
        metadata["platform_data"] = {
            "chat_id": chat_id,
            "platform": "telegram",
        }

        # Add patient_id to metadata if provided
        if patient_id:
            metadata["patient_id"] = patient_id

        # Add recurrence pattern to metadata if provided
        if recurrence_pattern:
            metadata["recurrence"] = recurrence_pattern

        # Store user_id in metadata for dynamic content generation with [DYNAMIC_GENERATE] tag
        # For Telegram personal chats, user_id is typically the same as chat_id
        if "user_id" not in metadata:
            metadata["user_id"] = chat_id

        logger.info(
            f"Creating scheduled message for chat_id: {chat_id}, time: {scheduled_time.isoformat()}"
        )

        try:
            # Ensure the scheduled_message_service is initialized
            if not self.scheduled_message_service:
                logger.error("scheduled_message_service is not initialized")
                raise ValueError("Scheduled message service not initialized")

            # Create the message
            message_id = await self.scheduled_message_service.create_scheduled_message(
                chat_id=chat_id,
                message_content=message_content,
                scheduled_time=scheduled_time,
                platform="telegram",
                patient_id=patient_id,
                priority=priority,
                metadata=metadata,
            )

            logger.info(f"Successfully created scheduled message with ID: {message_id}")
            return message_id

        except Exception as e:
            logger.error(f"Failed to create scheduled message: {e}", exc_info=True)
            logger.error(
                f"Parameters: chat_id={chat_id}, time={scheduled_time.isoformat()}, content='{message_content}'"
            )
            # Re-raise the exception
            raise

    async def cancel_scheduled_message(self, message_id: str) -> bool:
        """
        Cancel a scheduled message.

        Args:
            message_id: The ID of the message to cancel

        Returns:
            True if cancellation was successful
        """
        return await self.scheduled_message_service.cancel_message(message_id)

    async def get_scheduled_messages_for_chat(
        self, chat_id: int, status: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get scheduled messages for a chat.

        Args:
            chat_id: The Telegram chat ID
            status: Optional status filter
            limit: Maximum number of messages

        Returns:
            List of scheduled message records
        """
        return await self.scheduled_message_service.get_messages_by_chat_id(
            chat_id=chat_id, status=status, limit=limit
        )

    async def _get_patient_id(self, telegram_id: Union[int, str]) -> Optional[str]:
        """
        Get or create a patient ID for a Telegram user ID.

        Args:
            telegram_id: The Telegram user ID

        Returns:
            The patient ID or None if retrieval fails
        """
        try:
            # Convert ID to string if it's an integer
            telegram_id_str = str(telegram_id)

            # Generate the system_id format
            system_id = f"telegram:{telegram_id_str}"

            # Log the lookup attempt
            logger.info(f"Looking up patient with system_id: {system_id}")

            # Use the utility function from nodes.py to get the patient_id directly
            # This is not an async function, so we don't use await
            patient_id = get_patient_id_from_platform_id("telegram", telegram_id_str)

            if patient_id:
                logger.debug(f"Found patient_id {patient_id} for system_id {system_id}")
                return patient_id
            else:
                logger.warning(
                    f"Could not retrieve or create patient_id for system_id {system_id}"
                )

                # Try creating directly with Supabase as a fallback
                try:
                    if self.supabase:
                        # Create a JSON structure for email field since we're using it for platform data storage
                        email_data = {
                            "platform": "telegram",
                            "telegram_id": telegram_id_str,
                            "system_id": system_id,
                            "created_via": "telegram_bot",
                            "first_message_time": datetime.now().isoformat(),
                        }

                        # Prepare data for new patient record
                        patient_data = {
                            "system_id": system_id,
                            "channel": "telegram",
                            "risk": "Low",
                            "email": json.dumps(email_data),
                        }

                        # Insert directly
                        result = (
                            self.supabase.table("patients")
                            .insert(patient_data)
                            .execute()
                        )
                        if result.data and len(result.data) > 0:
                            new_patient_id = result.data[0].get("id")
                            logger.info(
                                f"Created new patient with ID {new_patient_id} for {system_id}"
                            )
                            return new_patient_id
                except Exception as e:
                    logger.error(f"Failed to create patient as fallback: {e}")

                return None
        except Exception as e:
            logger.error(
                f"Error in _get_patient_id for {telegram_id}: {e}", exc_info=True
            )

            # In development mode only, return a fallback ID
            if settings.ENVIRONMENT == "development":
                logger.warning("Using development fallback ID")
                return f"telegram-dev-{telegram_id}"
            return None


async def run_telegram_bot():
    """Run the Telegram bot with proper shutdown handling."""
    bot = TelegramBot()

    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Bot encountered an error: {e}", exc_info=True)
        raise
    finally:
        bot._running = False


if __name__ == "__main__":
    try:
        asyncio.run(run_telegram_bot())
    except KeyboardInterrupt:
        logger.info("Application shutdown requested by user (KeyboardInterrupt).")
    except Exception as e:
        logging.critical(
            f"CRITICAL ERROR in telegram_bot.py __main__: {e}", exc_info=True
        )
        # Optionally, re-raise or exit with error code
        # raise
        import sys

        sys.exit(1)  # Ensure a non-zero exit code on critical failure
