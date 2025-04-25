import asyncio
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def check_scheduled_messages():
    """Check and debug scheduled messages in the database."""
    try:
        # Import the service
        from ai_companion.modules.scheduler.scheduled_message_service import (
            get_scheduled_message_service,
        )

        # Get the service
        service = get_scheduled_message_service()

        # Check for all messages
        print("\n=== CHECKING ALL SCHEDULED MESSAGES ===")
        all_pending = service.supabase.table("scheduled_messages").select("*").execute()

        if all_pending.data:
            print(f"Found {len(all_pending.data)} total scheduled messages")

            # Group by status
            statuses = {}
            for msg in all_pending.data:
                status = msg.get("status", "unknown")
                if status not in statuses:
                    statuses[status] = 0
                statuses[status] += 1

            print("Status breakdown:")
            for status, count in statuses.items():
                print(f"  - {status}: {count} messages")

            # Check due messages
            print("\n=== CHECKING DUE MESSAGES ===")
            due_messages = service.get_due_messages(limit=100)
            print(f"Found {len(due_messages)} messages due for sending")

            for i, msg in enumerate(due_messages):
                # Print message details
                msg_id = msg.get("id", "unknown")
                content = msg.get("message_content", "no content")
                scheduled_time = msg.get("scheduled_time", "no time")
                status = msg.get("status", "unknown")
                attempts = msg.get("attempts", 0)

                # Get chat ID from metadata
                metadata = msg.get("metadata", {})
                platform_data = metadata.get("platform_data", {})
                chat_id = platform_data.get("chat_id", "unknown")

                # Check if recurring
                recurrence = metadata.get("recurrence", {})
                recurring_type = (
                    recurrence.get("type", "non-recurring")
                    if recurrence
                    else "non-recurring"
                )

                print(f"\nMessage {i+1}:")
                print(f"  ID: {msg_id}")
                print(f"  Content: {content}")
                print(f"  Chat ID: {chat_id}")
                print(f"  Scheduled Time: {scheduled_time}")
                print(f"  Status: {status}")
                print(f"  Attempts: {attempts}")
                print(f"  Type: {recurring_type}")

                # If recurring, check next execution time
                if recurrence:
                    next_time = service.calculate_next_execution_time(msg_id)
                    print(f"  Next Execution: {next_time}")

            # Test creating a test message with immediate scheduling
            print("\n=== CREATING TEST MESSAGE ===")
            now = datetime.now() + timedelta(
                seconds=10
            )  # Schedule for 10 seconds from now
            test_message_id = service.create_scheduled_message(
                chat_id=6519374243,  # Replace with your chat ID
                message_content=f"Test message created at {datetime.now().strftime('%H:%M:%S')}",
                scheduled_time=now,
                platform="telegram",
            )
            print(f"Created test message with ID: {test_message_id}")
            print(f"Scheduled for: {now}")
        else:
            print("No scheduled messages found in the database")

    except Exception as e:
        print(f"Error checking scheduled messages: {e}")


if __name__ == "__main__":
    asyncio.run(check_scheduled_messages())
