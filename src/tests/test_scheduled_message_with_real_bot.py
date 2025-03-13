"""
Test scheduling and sending a real message using the test Telegram bot.

This script will:
1. Create a scheduled message in the database
2. Run the message processor to send it
3. Verify it was sent successfully
"""

import asyncio
import logging
import sys
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any
import aiohttp
import signal
import subprocess

from test_config import TEST_TELEGRAM_BOT_TOKEN, YOUR_TELEGRAM_USER_ID, TEST_PATIENT_ID
from ai_companion.utils.supabase import get_supabase_client
from ai_companion.modules.scheduled_messaging.storage import create_scheduled_messages_table
from ai_companion.modules.scheduled_messaging.scheduler import ScheduleManager

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_scheduled_message")

# Create a custom version of the Telegram handler that uses the test token
class TestTelegramHandler:
    """Custom Telegram handler for test bot."""
    
    def __init__(self):
        """Initialize the Telegram handler with test token."""
        self.api_token = TEST_TELEGRAM_BOT_TOKEN
        self.api_base = "https://api.telegram.org"
        self.base_url = f"{self.api_base}/bot{self.api_token}"
    
    async def _make_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to the Telegram API."""
        url = f"{self.base_url}/{method}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=params) as response:
                    result = await response.json()
                    
                    if not result.get("ok", False):
                        logger.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
                        return {"success": False, "error": result.get("description", "Unknown error")}
                    
                    return {"success": True, "result": result.get("result")}
        except Exception as e:
            logger.error(f"Error making Telegram API request: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_message(self, 
                         chat_id: str, 
                         message: str, 
                         parse_mode: str = "HTML") -> Dict[str, Any]:
        """Send a message to a Telegram chat."""
        params = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        
        return await self._make_request("sendMessage", params)
    
    async def send_scheduled_message(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a scheduled message using the test bot."""
        recipient_id = schedule_data.get("recipient_id")
        message_content = schedule_data.get("message_content", "")
        
        if not recipient_id:
            return {
                "success": False,
                "error": "Missing recipient ID"
            }
        
        # Make sure to use YOUR_TELEGRAM_USER_ID instead of the test ID
        actual_recipient_id = YOUR_TELEGRAM_USER_ID
        
        result = await self.send_message(actual_recipient_id, message_content)
        
        if result.get("success"):
            logger.info(f"✅ Sent scheduled message to Telegram recipient {actual_recipient_id}")
            return {
                "success": True,
                "platform": "telegram"
            }
        else:
            logger.error(f"❌ Failed to send Telegram message: {result.get('error')}")
            return {
                "success": False,
                "error": result.get("error"),
                "platform": "telegram"
            }

async def schedule_test_message():
    """Schedule a test message to be sent in 1 minute."""
    # Check if YOUR_TELEGRAM_USER_ID is properly set
    if YOUR_TELEGRAM_USER_ID == "YOUR_ACTUAL_USER_ID":
        logger.error("Please set YOUR_TELEGRAM_USER_ID in test_config.py to your actual Telegram user ID")
        logger.error("You can get this by messaging @userinfobot on Telegram")
        return None
        
    # Ensure the scheduled_messages table exists
    await create_scheduled_messages_table()
    
    # Schedule a message for 30 seconds in the future
    scheduled_time = datetime.now() + timedelta(seconds=30)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create a weather joke message
    message_content = f"""🌤️ Scheduled Weather Joke 🌤️

Why did the meteorologist go to therapy? 
Because they had too many clouded judgments!

This message was scheduled at {current_time} and delivered via the message processor.
Your user ID: {YOUR_TELEGRAM_USER_ID}
Test patient ID: {TEST_PATIENT_ID}"""
    
    # Create schedule manager
    scheduler = ScheduleManager()
    
    # Schedule the message
    logger.info(f"Scheduling message to be sent at {scheduled_time}")
    result = await scheduler.schedule_message(
        patient_id=TEST_PATIENT_ID,
        recipient_id=YOUR_TELEGRAM_USER_ID,  # This will be replaced with the actual ID in the handler
        platform="telegram",
        message_content=message_content,
        scheduled_time=scheduled_time.isoformat(),
    )
    
    if result.get("status") == "scheduled":
        schedule_id = result.get("schedule_id")
        logger.info(f"✅ Successfully scheduled message with ID: {schedule_id}")
        return schedule_id
    else:
        logger.error(f"❌ Failed to schedule message: {result.get('error')}")
        return None

async def process_scheduled_messages(handler):
    """Process scheduled messages with the custom handler."""
    from ai_companion.modules.scheduled_messaging.storage import get_pending_messages, update_message_status
    
    logger.info("Processing due messages with custom handler")
    
    # Get all pending messages that are due
    due_messages = await get_pending_messages()
    
    if not due_messages:
        logger.debug("No due messages to process")
        return False
    
    logger.info(f"Found {len(due_messages)} messages to process")
    success = False
    
    for message in due_messages:
        schedule_id = message.get("id")
        platform = message.get("platform", "").lower()
        recipient_id = message.get("recipient_id")
        
        if platform != "telegram":
            logger.warning(f"Skipping non-Telegram message: {schedule_id}")
            continue
        
        logger.info(f"Processing message {schedule_id} for {platform} recipient {recipient_id}")
        
        try:
            # Send the message with custom handler
            result = await handler.send_scheduled_message(message)
            
            if result.get("success"):
                logger.info(f"✅ Successfully sent message {schedule_id}")
                await update_message_status(schedule_id, "sent")
                success = True
            else:
                logger.error(f"❌ Failed to send message {schedule_id}: {result.get('error')}")
                await update_message_status(schedule_id, "failed", {"error": result.get("error")})
        except Exception as e:
            logger.error(f"Error processing message {schedule_id}: {e}")
            await update_message_status(schedule_id, "failed", {"error": str(e)})
    
    return success

async def check_message_status(schedule_id):
    """Check if a scheduled message was sent successfully."""
    if not schedule_id:
        return False
        
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Get the scheduled message
    result = supabase.table("scheduled_messages").select("*").eq("id", schedule_id).execute()
    
    # Check if we got results
    if result.data and len(result.data) > 0:
        message = result.data[0]
        status = message.get("status")
        logger.info(f"Message status: {status}")
        return status == "sent"
    else:
        logger.error(f"Message {schedule_id} not found")
        return False

async def main():
    """Run the complete test."""
    print("Starting scheduled message test with real Telegram bot...")
    
    # 1. Schedule a test message
    print("Scheduling a test message...")
    schedule_id = await schedule_test_message()
    
    if not schedule_id:
        print("❌ Failed to schedule the test message. Check the logs for details.")
        return False
    
    print(f"✅ Message scheduled with ID: {schedule_id}")
    
    # 2. Wait a moment for the database to update
    print("Waiting for scheduled time (30 seconds)...")
    await asyncio.sleep(5)
    
    # 3. Process scheduled messages with custom handler
    print("Processing scheduled messages...")
    handler = TestTelegramHandler()
    success = await process_scheduled_messages(handler)
    
    if not success:
        print("❌ No messages were processed or they failed to send. Check the logs for details.")
    
    # 4. Check if the message was sent
    print("Checking message status...")
    was_sent = await check_message_status(schedule_id)
    
    print(f"Message sent: {'✅ YES' if was_sent else '❌ NO'}")
    print(f"Test completed: {'✅ PASSED' if was_sent else '❌ FAILED'}")
    
    if was_sent:
        print("\n✨ SUCCESS! The message should have been sent to your Telegram account.")
        print("Check your Telegram messages from the test bot: @cancerinformation_bot")
    
    return was_sent

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"Test script complete with result: {'SUCCESS' if result else 'FAILURE'}")
    sys.exit(0 if result else 1) 