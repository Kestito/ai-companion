import asyncio
import logging
import datetime
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scheduler_worker.log"),
    ],
)
logger = logging.getLogger(__name__)

# Add the source directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))


async def main():
    try:
        # Import the necessary components
        from ai_companion.interfaces.telegram.telegram_bot import TelegramBot
        from ai_companion.modules.scheduler.scheduler_worker import get_scheduler_worker
        from ai_companion.modules.scheduler.scheduled_message_service import (
            get_scheduled_message_service,
        )

        # Log the current time
        logger.info(f"Starting scheduler worker at {datetime.datetime.now()}")

        # Initialize the Telegram bot
        bot = TelegramBot()

        # Get the scheduler service and check pending messages
        service = get_scheduled_message_service()
        pending_messages = service.get_due_messages(limit=100)
        logger.info(f"Found {len(pending_messages)} pending messages")

        for msg in pending_messages:
            logger.info(
                f"Pending message: {msg.get('id')} - {msg.get('message_content')} - {msg.get('scheduled_time')}"
            )

        # Initialize and start the scheduler worker
        worker = get_scheduler_worker(bot)
        await worker.start(bot)

        logger.info("Scheduler worker started successfully. Press Ctrl+C to stop.")

        # Keep the worker running
        while True:
            await asyncio.sleep(60)
            logger.info("Scheduler worker still running...")

            # Check for newly due messages
            due_messages = service.get_due_messages(limit=10)
            if due_messages:
                logger.info(f"Found {len(due_messages)} messages due for sending")
                for msg in due_messages:
                    logger.info(
                        f"Due message: {msg.get('id')} - {msg.get('scheduled_time')}"
                    )

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
    except Exception as e:
        logger.error(f"Error in scheduler worker: {e}", exc_info=True)
    finally:
        # Stop the worker if it was started
        if "worker" in locals():
            worker.stop()
            logger.info("Scheduler worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
