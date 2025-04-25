#!/usr/bin/env python
"""
Script to fix data issues in scheduled messages.
"""

import asyncio
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main():
    """Fix data issues in scheduled messages."""
    try:
        # Import the service
        from ai_companion.modules.scheduler.scheduled_message_service import (
            get_scheduled_message_service,
        )

        # User's Telegram chat ID
        YOUR_CHAT_ID = (
            6519374243  # This will be used to fix messages with missing chat_id
        )

        print("\n" + "=" * 80)
        print("SCHEDULED MESSAGES DATA FIX UTILITY")
        print("=" * 80 + "\n")

        # Get the service
        service = get_scheduled_message_service()

        # Fetch all messages
        print("Retrieving all scheduled messages...")
        all_messages = (
            service.supabase.table("scheduled_messages").select("*").execute()
        )

        if not all_messages.data:
            print("No scheduled messages found in the database.")
            return

        total = len(all_messages.data)
        print(f"Found {total} total scheduled messages\n")

        # Count and identify messages with issues
        missing_metadata = []
        missing_chat_id = []

        for msg in all_messages.data:
            # Check for missing metadata
            if msg.get("metadata") is None:
                missing_metadata.append(msg["id"])
                continue

            # Check for missing chat_id
            metadata = msg.get("metadata", {})
            if isinstance(metadata, dict):
                platform_data = metadata.get("platform_data", {})
                if not platform_data or not platform_data.get("chat_id"):
                    missing_chat_id.append(msg["id"])

        # Report on issues
        print(f"Messages with missing metadata: {len(missing_metadata)}")
        print(f"Messages with missing chat_id: {len(missing_chat_id)}")

        # Fix missing metadata
        if missing_metadata:
            print("\n--- FIXING MISSING METADATA ---")
            print(f"Fixing {len(missing_metadata)} messages with NULL metadata...")

            for msg_id in missing_metadata:
                try:
                    # Create proper metadata with chat_id
                    new_metadata = {"platform_data": {"chat_id": YOUR_CHAT_ID}}

                    # Update the message
                    result = (
                        service.supabase.table("scheduled_messages")
                        .update({"metadata": new_metadata})
                        .eq("id", msg_id)
                        .execute()
                    )

                    if result.data and len(result.data) > 0:
                        print(f"✅ Fixed metadata for message {msg_id}")
                    else:
                        print(f"❌ Failed to fix metadata for message {msg_id}")
                except Exception as e:
                    print(f"❌ Error fixing metadata for message {msg_id}: {e}")

        # Fix missing chat_id
        if missing_chat_id:
            print("\n--- FIXING MISSING CHAT_ID ---")
            print(f"Fixing {len(missing_chat_id)} messages with missing chat_id...")

            for msg_id in missing_chat_id:
                try:
                    # First get the current message to preserve other metadata
                    msg = service.get_message_by_id(msg_id)
                    if not msg:
                        print(f"❌ Message {msg_id} not found")
                        continue

                    # Get current metadata and ensure it's a dict
                    metadata = msg.get("metadata", {})
                    if not isinstance(metadata, dict):
                        metadata = {}

                    # Ensure platform_data exists
                    if "platform_data" not in metadata:
                        metadata["platform_data"] = {}

                    # Add chat_id
                    metadata["platform_data"]["chat_id"] = YOUR_CHAT_ID

                    # Update the message
                    result = (
                        service.supabase.table("scheduled_messages")
                        .update({"metadata": metadata})
                        .eq("id", msg_id)
                        .execute()
                    )

                    if result.data and len(result.data) > 0:
                        print(f"✅ Fixed chat_id for message {msg_id}")
                    else:
                        print(f"❌ Failed to fix chat_id for message {msg_id}")
                except Exception as e:
                    print(f"❌ Error fixing chat_id for message {msg_id}: {e}")

        # Fix statuses - reset failed messages if they were due to missing metadata
        failed_messages = []
        if service:
            try:
                # Get failed messages
                failed_result = (
                    service.supabase.table("scheduled_messages")
                    .select("*")
                    .eq("status", "failed")
                    .execute()
                )
                if failed_result.data:
                    failed_messages = failed_result.data
            except Exception as e:
                print(f"Error getting failed messages: {e}")

        if failed_messages:
            print("\n--- RESETTING FAILED MESSAGES ---")
            print(
                f"Found {len(failed_messages)} failed messages. Would you like to reset them to 'pending'?"
            )
            choice = input("Type 'y' to reset or any other key to skip: ")

            if choice.lower() == "y":
                reset_count = 0
                for msg in failed_messages:
                    try:
                        # Ensure message has proper metadata now
                        metadata = msg.get("metadata", {})
                        if isinstance(metadata, dict) and metadata.get(
                            "platform_data", {}
                        ).get("chat_id"):
                            # Reset to pending
                            result = (
                                service.supabase.table("scheduled_messages")
                                .update({"status": "pending", "attempts": 0})
                                .eq("id", msg["id"])
                                .execute()
                            )

                            if result.data and len(result.data) > 0:
                                reset_count += 1
                                print(f"✅ Reset message {msg['id']} to pending")
                    except Exception as e:
                        print(f"❌ Error resetting message {msg['id']}: {e}")

                print(f"\nSuccessfully reset {reset_count} messages to pending status")
            else:
                print("Skipping reset of failed messages")

        print("\n" + "=" * 80)
        print("FIX OPERATION COMPLETE")
        print("=" * 80 + "\n")

        # Provide next steps
        print("To verify the fixes, run:")
        print("python check_scheduled_messages.py")
        print("\nTo process the messages, run:")
        print("python run_scheduler.py")
        print()

    except Exception as e:
        print(f"Error fixing scheduled messages: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
