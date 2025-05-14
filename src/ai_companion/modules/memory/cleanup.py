"""
Memory cleanup script for removing expired entries from short-term memory.

This module provides functionality to periodically clean up expired memory entries
to prevent database bloat and ensure optimal performance.
"""

import asyncio
import logging
import time
import schedule
import threading


logger = logging.getLogger(__name__)


async def cleanup_expired_memories():
    """
    Log memory cleanup call but don't actually delete anything.
    Based on user request to ignore expires_at date and time.
    """
    try:
        logger.info("Memory cleanup called - ignoring per user request")
        logger.info("Skipping actual cleanup as requested")
        return 0
    except Exception as e:
        logger.error(f"Error during memory cleanup: {e}")
        return 0


def run_cleanup_schedule():
    """Run cleanup on a schedule."""
    asyncio.run(cleanup_expired_memories())


def start_cleanup_scheduler(schedule_interval=3600):
    """
    Start a background scheduler to cleanup expired memories.

    Args:
        schedule_interval: Interval in seconds between cleanup runs (default: 1 hour)
    """
    # Schedule cleanup to run periodically
    schedule.every(schedule_interval).seconds.do(run_cleanup_schedule)

    # Run in a separate thread to not block the main application
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1)

    # Start the scheduler thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    logger.info(
        f"Memory cleanup scheduler started (interval: {schedule_interval} seconds)"
    )
    return scheduler_thread


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run cleanup once when script is executed directly
    asyncio.run(cleanup_expired_memories())
