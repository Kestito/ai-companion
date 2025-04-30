import asyncio
import logging
import signal
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any

from ai_companion.modules.scheduler.scheduled_message_service import (
    get_scheduled_message_service,
)
from ai_companion.graph import graph_builder
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)


class SchedulerWorker:
    """Worker for processing scheduled messages."""

    def __init__(self, telegram_bot=None):
        """
        Initialize the scheduler worker.

        Args:
            telegram_bot: Optional instance of the Telegram bot for sending messages
        """
        self.telegram_bot = telegram_bot
        self.scheduled_message_service = get_scheduled_message_service()
        self.check_interval = 30  # Check every 30 seconds by default
        self.max_batch_size = 10  # Process up to 10 messages per batch
        self.running = False
        self.task = None
        self._setup_signal_handlers()
        logger.info("Initialized SchedulerWorker")

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._handle_signal)

    def _handle_signal(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating scheduler shutdown...")
        self.stop()

    async def start(self, telegram_bot=None):
        """
        Start the scheduler worker.

        Args:
            telegram_bot: Optional instance of the Telegram bot (can be set later)
        """
        if telegram_bot:
            self.telegram_bot = telegram_bot

        if self.running:
            logger.warning("Scheduler worker is already running")
            return

        self.running = True
        logger.info("Starting scheduler worker...")

        # Create background task
        self.task = asyncio.create_task(self._run_scheduler_loop())

    def stop(self):
        """Stop the scheduler worker."""
        if not self.running:
            return

        logger.info("Stopping scheduler worker...")
        self.running = False

        if self.task:
            self.task.cancel()

    async def _run_scheduler_loop(self):
        """Main scheduler loop that checks for and processes due messages."""
        try:
            while self.running:
                try:
                    start_time = time.time()

                    # Check for due messages
                    messages = self.scheduled_message_service.get_due_messages(
                        limit=self.max_batch_size
                    )

                    if messages:
                        logger.info(
                            f"Found {len(messages)} messages due for processing"
                        )

                        # Process messages in a separate task to avoid blocking the loop
                        asyncio.create_task(self._process_messages(messages))

                    # Calculate time to next check
                    elapsed = time.time() - start_time
                    sleep_time = max(1, self.check_interval - elapsed)

                    logger.debug(
                        f"Scheduler check complete, sleeping for {sleep_time:.1f}s"
                    )
                    await asyncio.sleep(sleep_time)

                except asyncio.CancelledError:
                    logger.info("Scheduler loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                    await asyncio.sleep(10)  # Sleep longer after error

        except asyncio.CancelledError:
            logger.info("Scheduler worker stopped")
        except Exception as e:
            logger.error(f"Fatal error in scheduler worker: {e}", exc_info=True)

    async def _process_messages(self, messages: List[Dict[str, Any]]):
        """
        Process a batch of scheduled messages.

        Args:
            messages: List of scheduled message records to process
        """
        if not self.telegram_bot:
            logger.error("Cannot process messages: Telegram bot instance not set")
            return

        for message in messages:
            try:
                message_id = message.get("id")
                if not message_id:
                    logger.error("Message has no ID, skipping")
                    continue

                logger.info(f"Processing scheduled message: {message_id}")

                # Get chat_id from metadata - Add extra null check
                metadata = message.get("metadata")
                if metadata is None:
                    logger.error(
                        f"Message {message_id} has no metadata, marking as failed"
                    )
                    self.scheduled_message_service.update_message_status(
                        message_id=message_id,
                        status="failed",
                        error_message="Missing metadata",
                    )
                    continue

                platform_data = metadata.get("platform_data", {})
                if platform_data is None:
                    logger.error(
                        f"Message {message_id} has no platform_data, marking as failed"
                    )
                    self.scheduled_message_service.update_message_status(
                        message_id=message_id,
                        status="failed",
                        error_message="Missing platform_data in metadata",
                    )
                    continue

                chat_id = platform_data.get("chat_id")

                # Validate chat_id format - Telegram chat IDs should be integers or @username
                try:
                    # Try converting to integer if it's numeric
                    if isinstance(chat_id, str) and chat_id.isdigit():
                        chat_id = int(chat_id)
                    # If it's a UUID or other invalid format, log an error
                    elif (
                        isinstance(chat_id, str)
                        and not chat_id.startswith("@")
                        and "-" in chat_id
                    ):
                        logger.error(
                            f"Message {message_id} has invalid chat_id format: {chat_id}"
                        )
                        self.scheduled_message_service.update_message_status(
                            message_id=message_id,
                            status="failed",
                            error_message=f"Invalid chat_id format: {chat_id}. Must be numeric or @username.",
                        )
                        continue
                except (ValueError, TypeError) as e:
                    logger.error(
                        f"Error validating chat_id for message {message_id}: {e}"
                    )
                    self.scheduled_message_service.update_message_status(
                        message_id=message_id,
                        status="failed",
                        error_message=f"Invalid chat_id: {str(e)}",
                    )
                    continue

                if not chat_id:
                    logger.error(
                        f"Message {message_id} has no chat_id, marking as failed"
                    )
                    self.scheduled_message_service.update_message_status(
                        message_id=message_id,
                        status="failed",
                        error_message="Missing chat_id in metadata",
                    )
                    continue

                # Get message content
                message_content = message.get("message_content", "")
                if not message_content:
                    logger.error(
                        f"Message {message_id} has no content, marking as failed"
                    )
                    self.scheduled_message_service.update_message_status(
                        message_id=message_id,
                        status="failed",
                        error_message="Missing message content",
                    )
                    continue

                # Check for special tags
                is_dynamic = False
                is_daily_check = False

                # Check for [DAYLYCHECK] and [DYNAMIC_GENERATE] tags
                if (
                    "[DAYLYCHECK]" in message_content
                    or "[DAILYCHECK]" in message_content
                ):
                    is_daily_check = True
                    logger.info(f"Message {message_id} is a daily check")

                if "[DYNAMIC_GENERATE]" in message_content:
                    is_dynamic = True
                    logger.info(
                        f"Message {message_id} requires dynamic content generation"
                    )

                # Process special tags
                if is_dynamic:
                    try:
                        # Extract user_id from chat_id (in Telegram, they're often the same for 1:1 chats)
                        user_id = metadata.get("user_id", chat_id)

                        # Replace the special tags with generated content
                        dynamic_content = await self._generate_dynamic_content(
                            chat_id, user_id, message_content, is_daily_check
                        )

                        if dynamic_content:
                            # Replace tags with generated content
                            message_content = re.sub(
                                r"\[DYNAMIC_GENERATE\]", "", message_content
                            )
                            message_content = re.sub(
                                r"\[DAYLYCHECK\]|\[DAILYCHECK\]", "", message_content
                            )
                            message_content = (
                                message_content.strip() + "\n\n" + dynamic_content
                            )

                            logger.info(
                                f"Generated dynamic content for message {message_id}"
                            )
                    except Exception as e:
                        logger.error(
                            f"Error generating dynamic content for message {message_id}: {e}",
                            exc_info=True,
                        )
                        # Continue with original content as fallback
                        message_content = "I was going to ask a personalized question, but I had trouble accessing our conversation history. How are you doing today?"

                # Send the message
                try:
                    logger.info(f"Sending scheduled message to chat {chat_id}")
                    await self.telegram_bot._send_message(chat_id, message_content)

                    # Update message status to sent
                    logger.info(f"Message {message_id} sent successfully")

                    # Check if message is recurring and needs rescheduling
                    next_time = (
                        self.scheduled_message_service.calculate_next_execution_time(
                            message_id
                        )
                    )

                    if next_time:
                        # This is a recurring message - reschedule it
                        logger.info(
                            f"Rescheduling recurring message {message_id} for {next_time}"
                        )
                        self.scheduled_message_service.update_message_status(
                            message_id=message_id,
                            status="rescheduled",
                            next_scheduled_time=next_time,
                        )
                    else:
                        # One-time message - mark as sent
                        self.scheduled_message_service.update_message_status(
                            message_id=message_id, status="sent"
                        )

                except Exception as e:
                    logger.error(
                        f"Error sending message {message_id}: {e}", exc_info=True
                    )

                    # Check attempts count to determine if we should retry
                    attempts = message.get("attempts", 0)
                    max_attempts = metadata.get(
                        "max_attempts", 3
                    )  # Default 3 retry attempts

                    if attempts < max_attempts:
                        # Schedule retry after exponential backoff
                        retry_delay_minutes = 5 * (
                            2**attempts
                        )  # 5, 10, 20, 40 minutes...
                        next_attempt = datetime.utcnow() + timedelta(
                            minutes=retry_delay_minutes
                        )

                        logger.info(
                            f"Scheduling retry {attempts+1}/{max_attempts} for message {message_id} at {next_attempt}"
                        )

                        self.scheduled_message_service.update_message_status(
                            message_id=message_id,
                            status="pending",  # Keep as pending for retry
                            next_scheduled_time=next_attempt,
                            error_message=str(e),
                        )
                    else:
                        # Max retries reached, mark as failed
                        logger.warning(
                            f"Message {message_id} failed after {attempts} attempts"
                        )
                        self.scheduled_message_service.update_message_status(
                            message_id=message_id,
                            status="failed",
                            error_message=f"Max retries reached: {str(e)}",
                        )

            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                # Try to mark as failed if we can
                try:
                    if message_id:
                        self.scheduled_message_service.update_message_status(
                            message_id=message_id,
                            status="failed",
                            error_message=f"Processing error: {str(e)}",
                        )
                except Exception as e2:
                    logger.error(f"Error updating message status: {e2}")

    async def _generate_dynamic_content(
        self, chat_id: int, user_id: Any, template: str, is_daily_check: bool
    ) -> str:
        """
        Generate dynamic content for scheduled messages based on conversation history.

        Args:
            chat_id: The chat ID
            user_id: The user ID
            template: The message template
            is_daily_check: Whether this is a daily check message

        Returns:
            Dynamically generated content
        """
        if not self.telegram_bot:
            return "How are you feeling today?"

        try:
            # Get conversation history
            conversation_history = await self.telegram_bot._get_conversation_history(
                chat_id=chat_id,
                user_id=user_id,
                max_messages=10,  # Limit to recent messages
            )

            if not conversation_history:
                logger.warning(f"No conversation history found for chat {chat_id}")
                return "How are you feeling today? I'd love to catch up."

            # Create a prompt for the LLM
            prompt = ""
            if is_daily_check:
                prompt = """Based on our conversation history, please generate 1-3 personalized check-in questions 
                that follow up on topics we previously discussed. Focus on health-related topics, emotional well-being, 
                or anything significant the user mentioned before. Make the questions conversational and caring.
                
                Conversation history summary:
                """
            else:
                prompt = """Based on our conversation history, please generate a personalized message to check 
                in with the user. Keep it friendly and conversational.
                
                Conversation history summary:
                """

            # Add simple summary of conversation history
            for i, entry in enumerate(conversation_history[-6:]):  # Last 6 messages
                role = entry.get("role", "unknown")
                content = entry.get("content", "")
                if content:
                    prompt += f"\n{role}: {content[:100]}..."  # Truncate long messages

            # Use LangGraph/LLM to generate the response
            try:
                # Create a LangGraph config
                config = {
                    "configurable": {
                        "thread_id": f"scheduler-{chat_id}",
                        "detailed_response": True,
                        "conversation_history": conversation_history,
                        "interface": "telegram",
                    }
                }

                # Create graph instance with config
                graph = graph_builder.with_config(config)

                # Create the message
                message = HumanMessage(content=prompt)

                # Invoke the graph with the human message
                result = await graph.ainvoke({"messages": [message]})

                # Extract the response
                if isinstance(result, dict) and "messages" in result:
                    messages = result["messages"]
                    if messages and len(messages) > 0:
                        last_message = messages[-1]
                        if hasattr(last_message, "content"):
                            return last_message.content

                # Fallback if we couldn't extract response
                logger.warning("Could not extract response from graph")

            except Exception as e:
                logger.error(
                    f"Error using LangGraph for dynamic content: {e}", exc_info=True
                )

            # Fallback content if LangGraph fails
            if is_daily_check:
                return """How are you feeling today? 
                
                Have there been any changes in your symptoms or condition since we last spoke?
                
                Is there anything specific you'd like to discuss today?"""
            else:
                return "How are you doing today? I'm here if you need to talk."

        except Exception as e:
            logger.error(f"Error generating dynamic content: {e}", exc_info=True)
            return "How has your day been so far? I'd love to hear from you."


# Create a singleton instance
_scheduler_worker_instance = None


def get_scheduler_worker(telegram_bot=None) -> SchedulerWorker:
    """Get the singleton instance of the scheduler worker."""
    global _scheduler_worker_instance
    if _scheduler_worker_instance is None:
        _scheduler_worker_instance = SchedulerWorker(telegram_bot)
    elif telegram_bot is not None:
        _scheduler_worker_instance.telegram_bot = telegram_bot
    return _scheduler_worker_instance
