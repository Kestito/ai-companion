"""
Test script for scheduling an immediate message via Telegram.

This will schedule a message to be sent immediately (using the current time).
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from langchain_core.messages import HumanMessage

from ai_companion.graph.nodes import schedule_message_node
from ai_companion.graph.state import AICompanionState
from ai_companion.modules.scheduled_messaging.scheduler import ScheduleManager
from ai_companion.utils.supabase import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_immediate_schedule")

# Patient ID - we'll use the one we created in the test
PATIENT_ID = "37af7f21-193a-40e2-b68f-0a83e5ba52e4"
TELEGRAM_USER_ID = "telegram_user_789"  # from the test script

async def test_schedule_immediate_message():
    """Test scheduling a message to be sent immediately."""
    logger.info("Testing scheduling an immediate message...")
    
    # Current time
    current_time = datetime.now()
    formatted_time = current_time.strftime("%H:%M")
    
    # Create a test message
    message_content = f"This is a test message sent at {formatted_time}. The message processor should send this immediately!"
    
    # Create a scheduling command
    schedule_command = f"/schedule today {formatted_time} {message_content}"
    
    # Create a test message with this command
    state = AICompanionState(
        messages=[
            HumanMessage(
                content=schedule_command,
                metadata={
                    "platform": "telegram", 
                    "user_id": TELEGRAM_USER_ID,
                    "patient_id": PATIENT_ID
                }
            )
        ]
    )
    
    # Process with schedule_message_node
    logger.info(f"Scheduling message with command: {schedule_command}")
    try:
        result = await schedule_message_node(state, {})
        logger.info(f"Schedule result: {result}")
        
        if result.get("schedule_result") == "success":
            schedule_id = result.get("schedule_id")
            response = result.get("response")
            logger.info(f"Successfully scheduled message with ID: {schedule_id}")
            logger.info(f"Response: {response}")
            return schedule_id
        else:
            logger.error(f"Failed to schedule message: {result.get('error')}")
            return None
    except Exception as e:
        logger.error(f"Error in schedule_message_node: {e}", exc_info=True)
        return None

async def check_message_status(schedule_id):
    """Check the status of the scheduled message."""
    if not schedule_id:
        return
        
    logger.info(f"Checking status of message {schedule_id}...")
    
    # Wait a few seconds for the processor to pick up the message
    logger.info("Waiting 10 seconds for the processor to pick up the message...")
    await asyncio.sleep(10)
    
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Get the scheduled message
    result = supabase.table("scheduled_messages").select("*").eq("id", schedule_id).execute()
    
    # Check the status
    if result.data and len(result.data) > 0:
        message = result.data[0]
        status = message.get("status")
        logger.info(f"Message status: {status}")
        return status == "sent"
    else:
        logger.error(f"Message {schedule_id} not found")
        return False

async def main():
    """Run the test."""
    print("Starting immediate schedule test script...")
    print("Scheduling an immediate message...")
    schedule_id = await test_schedule_immediate_message()
    
    if schedule_id:
        print(f"Message scheduled with ID: {schedule_id}")
        print("Checking if message was sent...")
        was_sent = await check_message_status(schedule_id)
        print(f"Message sent: {'✅ YES' if was_sent else '❌ NO'}")
        print(f"Test completed: {'✅ PASSED' if was_sent else '❌ FAILED'}")
        return was_sent
    else:
        print("❌ Failed to schedule message")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"Test script complete with result: {'SUCCESS' if result else 'FAILURE'}") 