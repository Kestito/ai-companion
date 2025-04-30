#!/usr/bin/env python
"""
Script to identify and fix invalid Telegram chat IDs in scheduled messages
"""

import asyncio
import os
import sys
import httpx
from datetime import datetime
from pathlib import Path

# Add project root to the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Set required environment variables
os.environ["TELEGRAM_BOT_TOKEN"] = "7764956576:AAE2C57S9jzihsYvoA2R7fjvLPjoopFbNxU"
os.environ["TELEGRAM_API_BASE"] = "https://api.telegram.org"
os.environ["ENVIRONMENT"] = "development"


async def check_chat_exists(chat_id):
    """Check if a Telegram chat exists by attempting to get chat info"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    api_base = os.environ.get("TELEGRAM_API_BASE", "https://api.telegram.org")
    url = f"{api_base}/bot{token}/getChat"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={"chat_id": chat_id}, timeout=10.0)
            return response.status_code == 200
    except Exception as e:
        print(f"Error checking chat {chat_id}: {str(e)}")
        return False


async def main():
    try:
        # Import here to avoid module not found errors
        from src.ai_companion.integrations.supabase_client import create_supabase_client

        print("Connecting to Supabase...")
        supabase = create_supabase_client()

        # Get all scheduled messages
        print("Fetching scheduled messages...")
        response = supabase.table("scheduled_messages").select("*").execute()
        messages = response.data

        print(f"Found {len(messages)} scheduled messages")

        invalid_count = 0
        valid_count = 0

        for message in messages:
            message_id = message.get("id")
            chat_id = message.get("chat_id")
            status = message.get("status")

            if chat_id:
                print(f"Checking chat ID: {chat_id}")
                exists = await check_chat_exists(chat_id)

                if not exists:
                    print(f"Invalid chat ID: {chat_id} for message {message_id}")
                    invalid_count += 1

                    # Mark as failed if currently pending
                    if status == "pending":
                        supabase.table("scheduled_messages").update(
                            {
                                "status": "failed",
                                "error_message": "Chat ID not found or invalid",
                                "updated_at": datetime.utcnow().isoformat(),
                            }
                        ).eq("id", message_id).execute()
                        print(f"Marked message {message_id} as failed")
                else:
                    valid_count += 1
                    print(f"Valid chat ID: {chat_id} for message {message_id}")

        print(
            f"Completed cleanup: {invalid_count} invalid chats, {valid_count} valid chats"
        )

    except Exception as e:
        print(f"Error during cleanup: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
