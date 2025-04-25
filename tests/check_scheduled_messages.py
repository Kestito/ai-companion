#!/usr/bin/env python
"""
Script to check the status of scheduled messages in the database.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main():
    """Check and report on all scheduled messages in the database."""
    try:
        # Import the service and settings
        from ai_companion.modules.scheduler.scheduled_message_service import (
            get_scheduled_message_service,
        )
        from ai_companion.settings import settings

        print("\n" + "=" * 80)
        print("SCHEDULED MESSAGES STATUS REPORT")
        print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80 + "\n")

        # Get the service
        service = get_scheduled_message_service()
        print(f"Connected to Supabase at: {settings.supabase_url}")

        # Fetch all messages
        print("\nRetrieving all scheduled messages...")
        all_messages = (
            service.supabase.table("scheduled_messages").select("*").execute()
        )

        if not all_messages.data:
            print("\nNo scheduled messages found in the database.")
            return

        total = len(all_messages.data)
        print(f"\nFound {total} total scheduled messages")

        # Count messages with missing metadata or chat_id
        missing_metadata = 0
        missing_chat_id = 0

        # Group by status
        statuses = {}
        for msg in all_messages.data:
            # Check for missing metadata
            if msg.get("metadata") is None:
                missing_metadata += 1

            # Check for missing chat_id
            metadata = msg.get("metadata", {})
            if isinstance(metadata, dict):
                platform_data = metadata.get("platform_data", {})
                if not platform_data or not platform_data.get("chat_id"):
                    missing_chat_id += 1

            # Group by status
            status = msg.get("status", "unknown")
            if status not in statuses:
                statuses[status] = []
            statuses[status].append(msg)

        print("\n--- STATUS BREAKDOWN ---")
        for status, messages in statuses.items():
            count = len(messages)
            print(f"{status}: {count} messages ({count/total*100:.1f}%)")

        # Report on data issues
        print("\n--- DATA QUALITY ISSUES ---")
        print(f"Messages with missing metadata: {missing_metadata}")
        print(f"Messages with missing chat_id: {missing_chat_id}")

        # Show recent pending messages
        if "pending" in statuses:
            pending = statuses["pending"]
            print(f"\n--- PENDING MESSAGES ({len(pending)}) ---")

            # Sort by scheduled time
            pending.sort(key=lambda m: m.get("scheduled_time", ""))

            for i, msg in enumerate(pending[:10]):  # Show first 10
                msg_id = msg.get("id", "unknown")
                content = msg.get("message_content", "no content")
                if len(content) > 40:
                    content = content[:37] + "..."

                scheduled_time = msg.get("scheduled_time", "unknown")
                try:
                    scheduled_dt = datetime.fromisoformat(
                        scheduled_time.replace("Z", "+00:00")
                    )
                    now = datetime.now().astimezone()
                    time_diff = scheduled_dt - now

                    if time_diff.total_seconds() < 0:
                        time_status = f"OVERDUE by {abs(time_diff)}"
                    else:
                        time_status = f"Due in {time_diff}"
                except:
                    time_status = "Unknown"

                # Get chat ID (handle missing metadata safely)
                metadata = msg.get("metadata", {})
                chat_id = "unknown"
                if isinstance(metadata, dict):
                    platform_data = metadata.get("platform_data", {})
                    if isinstance(platform_data, dict):
                        chat_id = platform_data.get("chat_id", "missing")

                # Check if recurring (handle missing metadata safely)
                recurring_type = ""
                if isinstance(metadata, dict):
                    recurrence = metadata.get("recurrence", {})
                    if isinstance(recurrence, dict) and recurrence:
                        recurring_type = f"[{recurrence.get('type', '')}]"

                print(f"{i+1}. ID: {msg_id}")
                print(f"   Chat: {chat_id}")
                print(f"   Content: {content}")
                print(f"   Scheduled: {scheduled_time} {recurring_type}")
                print(f"   Status: {time_status}")

                # Warn about problems
                if chat_id == "missing" or chat_id == "unknown":
                    print("   ⚠️ WARNING: Missing chat_id - this message will fail!")
                if metadata is None or not isinstance(metadata, dict):
                    print("   ⚠️ WARNING: Invalid metadata - this message will fail!")

                print()

            if len(pending) > 10:
                print(f"... and {len(pending) - 10} more pending messages\n")

        # Check for due messages
        print("\n--- DUE MESSAGES ---")
        due_messages = service.get_due_messages(limit=10)

        if not due_messages:
            print("No messages currently due for processing")
        else:
            print(f"Found {len(due_messages)} messages due for immediate processing:")

            for i, msg in enumerate(due_messages):
                msg_id = msg.get("id", "unknown")
                content = msg.get("message_content", "no content")
                if len(content) > 40:
                    content = content[:37] + "..."
                scheduled_time = msg.get("scheduled_time", "unknown")

                # Get chat ID (safely)
                metadata = msg.get("metadata", {})
                chat_id = "unknown"
                if isinstance(metadata, dict):
                    platform_data = metadata.get("platform_data", {})
                    if isinstance(platform_data, dict):
                        chat_id = platform_data.get("chat_id", "missing")

                print(f"{i+1}. ID: {msg_id}")
                print(f"   Chat: {chat_id}")
                print(f"   Content: {content}")
                print(f"   Scheduled: {scheduled_time}")

                # Warn about problems
                if chat_id == "missing" or chat_id == "unknown":
                    print("   ⚠️ WARNING: Missing chat_id - this message will fail!")
                if metadata is None or not isinstance(metadata, dict):
                    print("   ⚠️ WARNING: Invalid metadata - this message will fail!")

                print()

        # Provide fix instructions if needed
        if missing_metadata > 0 or missing_chat_id > 0:
            print("\n--- SUGGESTED FIXES ---")
            print("Some messages have missing or invalid metadata. To fix them:")
            print("1. For messages missing chat_id:")
            print("   - Run this SQL in Supabase: UPDATE scheduled_messages")
            print(
                "     SET metadata = jsonb_set(metadata, '{platform_data,chat_id}', '6519374243')"
            )
            print("     WHERE metadata->'platform_data'->>'chat_id' IS NULL;")
            print("2. For messages with NULL metadata:")
            print("   - Run this SQL: UPDATE scheduled_messages")
            print('     SET metadata = \'{"platform_data":{"chat_id":6519374243}}\'')
            print("     WHERE metadata IS NULL;")

        print("\n" + "=" * 80)
        print("REPORT COMPLETE")
        print("=" * 80 + "\n")

        # Provide instructions
        print("To process these messages, run:")
        print("cd tests && python run_scheduler.py")
        print("\n")

    except Exception as e:
        print(f"Error checking scheduled messages: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
