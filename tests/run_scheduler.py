#!/usr/bin/env python
"""
Scheduler runner script.
This script runs the scheduler worker to process scheduled messages.
"""

import asyncio
import sys
import os
import argparse

# Add the parent directory to the path so we can import relative modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main(duration=300):
    """
    Run the scheduler for the specified duration.

    Args:
        duration: Number of seconds to run the scheduler
    """
    try:
        # Import the test runner
        from integration.test_scheduler_runner import TestSchedulerRunner

        # Create and run the test
        runner = TestSchedulerRunner()

        # Patch the runtime_seconds value
        from types import MethodType

        async def patched_test_run_scheduler(self):
            # Import here to avoid circular imports
            from datetime import datetime, timedelta
            from ai_companion.interfaces.telegram.telegram_bot import TelegramBot
            from ai_companion.modules.scheduler.scheduler_worker import (
                get_scheduler_worker,
            )
            from ai_companion.modules.scheduler.scheduled_message_service import (
                get_scheduled_message_service,
            )

            print(f"\n{'='*80}")
            print(f"STARTING SCHEDULER WORKER FOR {duration} SECONDS")
            print(f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*80}\n")

            # Initialize components
            bot = TelegramBot()
            service = get_scheduled_message_service()
            worker = get_scheduler_worker(bot)

            try:
                # Check pending messages
                pending = service.get_due_messages(limit=100)
                print(f"Found {len(pending)} pending messages due for processing")

                # Start the worker
                await worker.start(bot)
                print("Scheduler worker started successfully!")

                # Create a test message
                test_time = datetime.now() + timedelta(seconds=10)
                test_msg = f"Test message from scheduler runner at {datetime.now().strftime('%H:%M:%S')}"

                test_id = service.create_scheduled_message(
                    chat_id=6519374243,  # Your Telegram ID
                    message_content=test_msg,
                    scheduled_time=test_time,
                    platform="telegram",
                )
                print(f"Created test message: {test_id}")
                print(f"Message content: {test_msg}")
                print(f"Scheduled for: {test_time.strftime('%H:%M:%S')}")

                # Run for the specified duration
                print(
                    f"\nScheduler will run for {duration} seconds. Press Ctrl+C to stop."
                )
                print("Your scheduled messages will be processed during this time.\n")

                start_time = datetime.now()
                while (datetime.now() - start_time).total_seconds() < duration:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    remaining = duration - elapsed

                    # Update status every 10 seconds
                    await asyncio.sleep(10)
                    print(f"Scheduler running... {int(remaining)}s remaining")

                    # Check for due messages
                    due = service.get_due_messages(limit=10)
                    if due:
                        print(f"Found {len(due)} new messages due for sending")
            finally:
                # Stop the worker
                if "worker" in locals():
                    worker.stop()
                    print("\nScheduler worker stopped")

                print(f"\n{'='*80}")
                print("SCHEDULER SESSION COMPLETED")
                print(f"{'='*80}\n")

        # Replace the method with our patched version
        runner.test_run_scheduler = MethodType(patched_test_run_scheduler, runner)

        # Run the test
        await runner.test_run_scheduler()

    except KeyboardInterrupt:
        print("\nScheduler stopped by user")
    except Exception as e:
        print(f"\nError running scheduler: {e}")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Run the scheduler worker to process scheduled messages"
    )
    parser.add_argument(
        "--duration",
        "-d",
        type=int,
        default=300,
        help="Duration to run the scheduler (in seconds, default: 300)",
    )
    args = parser.parse_args()

    # Run the main function
    asyncio.run(main(args.duration))
