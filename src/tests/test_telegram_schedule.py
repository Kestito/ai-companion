"""
Test script for scheduling a one-time weather joke message via Telegram.

This will schedule a message to be sent 1 minute from now.
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
logger = logging.getLogger("test_telegram_schedule")

# Patient ID - we'll use the one we created in the test
PATIENT_ID = "37af7f21-193a-40e2-b68f-0a83e5ba52e4"
TELEGRAM_USER_ID = "telegram_user_789"  # from the test script

async def test_schedule_weather_joke():
    """Test scheduling a weather joke to be sent in 1 minute."""
    logger.info("Testing scheduling a weather joke...")
    
    # Current time + 1 minute
    scheduled_time = datetime.now() + timedelta(minutes=1)
    formatted_time = scheduled_time.strftime("%Y-%m-%d %H:%M")
    
    # Create a weather joke
    weather_joke = "Why did the meteorologist go to therapy? Because they had too many clouded judgments!"
    
    # Create a scheduling command
    schedule_command = f"/schedule today {formatted_time.split(' ')[1]} {weather_joke}"
    
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
            return True
        else:
            logger.error(f"Failed to schedule message: {result.get('error')}")
            return False
    except Exception as e:
        logger.error(f"Error in schedule_message_node: {e}", exc_info=True)
        return False

async def main():
    """Run the test."""
    print("Starting telegram schedule test script...")
    print("Running schedule test...")
    success = await test_schedule_weather_joke()
    print(f"Schedule test completed: {'✅ PASSED' if success else '❌ FAILED'}")
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"Test script complete with result: {'SUCCESS' if result else 'FAILURE'}") 