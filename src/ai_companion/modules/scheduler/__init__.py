# Scheduler module for managing scheduled messages
import logging

logger = logging.getLogger(__name__)

try:
    from ai_companion.modules.scheduler.scheduled_message_service import (
        get_scheduled_message_service,
    )

    logger.info("Successfully imported scheduled_message_service")
except Exception as e:
    logger.error(f"Error importing scheduled_message_service: {e}")

    def get_scheduled_message_service():
        logger.error("Using fallback scheduled_message_service function")
        return None


try:
    from ai_companion.modules.scheduler.scheduler_worker import get_scheduler_worker

    logger.info("Successfully imported scheduler_worker")
except Exception as e:
    logger.error(f"Error importing scheduler_worker: {e}")

    def get_scheduler_worker(telegram_bot=None):
        logger.error("Using fallback scheduler_worker function")
        return None


__all__ = ["get_scheduled_message_service", "get_scheduler_worker"]
