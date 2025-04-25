import pytest
import asyncio
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestSchedulerRunner:
    """Test class for running and debugging the scheduler system."""

    @pytest.mark.asyncio
    async def test_run_scheduler(self):
        """
        Start the scheduler worker and keep it running.
        This is not a standard test - it's meant to be run directly to process scheduled messages.
        """
        try:
            # Import the necessary components
            from ai_companion.interfaces.telegram.telegram_bot import TelegramBot
            from ai_companion.modules.scheduler.scheduler_worker import (
                get_scheduler_worker,
            )
            from ai_companion.modules.scheduler.scheduled_message_service import (
                get_scheduled_message_service,
            )

            # Log startup
            logger.info("=== SCHEDULER RUNNER STARTED ===")
            logger.info(f"Current time: {datetime.now()}")

            # Initialize the Telegram bot
            bot = TelegramBot()
            logger.info(
                f"Telegram bot initialized with token ending in: ...{bot.token[-4:]}"
            )

            # Get scheduler service
            service = get_scheduled_message_service()
            logger.info(
                f"Scheduler service initialized with Supabase URL: {service.supabase.url}"
            )

            # Check for pending messages
            pending_messages = service.get_due_messages(limit=100)
            logger.info(
                f"Found {len(pending_messages)} pending messages due for processing"
            )

            for i, msg in enumerate(pending_messages):
                msg_id = msg.get("id", "unknown")
                content = msg.get("message_content", "no content")[:30] + (
                    "..." if len(msg.get("message_content", "")) > 30 else ""
                )
                scheduled_time = msg.get("scheduled_time", "no time")
                status = msg.get("status", "unknown")

                # Get chat ID from metadata
                metadata = msg.get("metadata", {})
                platform_data = metadata.get("platform_data", {})
                chat_id = platform_data.get("chat_id", "unknown")

                logger.info(
                    f"Pending message {i+1}: ID={msg_id}, Chat={chat_id}, Time={scheduled_time}, Content='{content}'"
                )

            # Initialize and start the scheduler worker
            worker = get_scheduler_worker(bot)
            await worker.start(bot)
            logger.info("Scheduler worker started successfully!")

            # Create a test message for immediate delivery (10 seconds from now)
            test_time = datetime.now() + timedelta(seconds=10)
            test_msg_id = service.create_scheduled_message(
                chat_id=6519374243,  # Your Telegram ID
                message_content=f"Test message from scheduler runner at {datetime.now().strftime('%H:%M:%S')}",
                scheduled_time=test_time,
                platform="telegram",
            )
            logger.info(
                f"Created test message ID: {test_msg_id}, scheduled for: {test_time}"
            )

            # Keep the worker running for a limited time in test mode
            # In a real environment, this would run indefinitely
            runtime_seconds = 300  # Run for 5 minutes by default

            logger.info(
                f"Scheduler will run for {runtime_seconds} seconds. Press Ctrl+C to stop early."
            )
            logger.info("=== SCHEDULER PROCESSING STARTED ===")

            # Main processing loop
            start_time = datetime.now()
            while (datetime.now() - start_time).total_seconds() < runtime_seconds:
                # Check for due messages every 10 seconds
                await asyncio.sleep(10)
                due_messages = service.get_due_messages(limit=10)

                if due_messages:
                    logger.info(f"Found {len(due_messages)} messages due for sending")
                    for msg in due_messages:
                        msg_id = msg.get("id", "unknown")
                        scheduled_time = msg.get("scheduled_time", "unknown")
                        logger.info(f"Due message: ID={msg_id}, Time={scheduled_time}")

                # Log time remaining
                elapsed = (datetime.now() - start_time).total_seconds()
                remaining = runtime_seconds - elapsed
                logger.info(f"Scheduler running... {int(remaining)}s remaining")

            logger.info("=== SCHEDULER RUN COMPLETED ===")

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt. Shutting down...")
        except Exception as e:
            logger.error(f"Error in scheduler runner: {e}", exc_info=True)
            assert False, f"Scheduler runner error: {str(e)}"
        finally:
            # Stop the worker if it was started
            if "worker" in locals():
                worker.stop()
                logger.info("Scheduler worker stopped")

    @pytest.mark.asyncio
    async def test_check_scheduled_messages(self):
        """
        Check scheduled messages in the database without running the worker.
        This is useful for debugging purposes.
        """
        try:
            # Import the service
            from ai_companion.modules.scheduler.scheduled_message_service import (
                get_scheduled_message_service,
            )

            # Get the service
            service = get_scheduled_message_service()

            # Check for all messages
            logger.info("=== CHECKING ALL SCHEDULED MESSAGES ===")
            all_messages = (
                service.supabase.table("scheduled_messages").select("*").execute()
            )

            if all_messages.data:
                total = len(all_messages.data)
                logger.info(f"Found {total} total scheduled messages")

                # Group by status
                statuses = {}
                for msg in all_messages.data:
                    status = msg.get("status", "unknown")
                    if status not in statuses:
                        statuses[status] = 0
                    statuses[status] += 1

                logger.info("Status breakdown:")
                for status, count in statuses.items():
                    logger.info(
                        f"  - {status}: {count} messages ({count/total*100:.1f}%)"
                    )

                # There should be scheduled messages
                assert total > 0, "No scheduled messages found in the database"
            else:
                logger.warning("No scheduled messages found in the database")

            # This test always passes since it's just for information
            assert True

        except Exception as e:
            logger.error(f"Error checking scheduled messages: {e}")
            assert False, f"Error checking scheduled messages: {str(e)}"


if __name__ == "__main__":
    # When run directly, execute the scheduler runner
    # This allows us to run the script to process messages without pytest
    async def run_directly():
        runner = TestSchedulerRunner()
        await runner.test_run_scheduler()

    asyncio.run(run_directly())
