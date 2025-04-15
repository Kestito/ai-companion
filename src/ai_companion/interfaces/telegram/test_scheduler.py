#!/usr/bin/env python3

"""
Test script for the scheduled message processor.
This script will create a test scheduled message for immediate processing
and then run the processor to verify it works correctly.
"""

import os
import sys
import logging
import json
import asyncio
from datetime import datetime, timezone, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("TestScheduler")

# Import Supabase client
try:
    from supabase import create_client, Client
except ImportError:
    logger.error("Supabase client not found. Install with: pip install supabase")
    sys.exit(1)

# Supabase credentials
SUPABASE_URL = "https://aubulhjfeszmsheonmpy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzUyODc0MTIsImV4cCI6MjA1MDg2MzQxMn0.ovHMLKm5nN4o7_P_Pld1vEzPpL1uKZK1xxtWn3RMMJw"


async def create_test_message(patient_id: str) -> str:
    """Create a test scheduled message for immediate processing"""
    logger.info(f"Creating test scheduled message for patient {patient_id}")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Schedule message for 1 minute ago (should be processed immediately)
    scheduled_time = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    
    # Test data with all required fields
    message_data = {
        "patient_id": patient_id,
        "message_content": "This is a test scheduled message created by the test script.",
        "scheduled_time": scheduled_time,
        "platform": "telegram",  # Include platform as required by schema
        "status": "pending"
    }
    
    # Insert test message
    response = supabase.table("scheduled_messages").insert(message_data).execute()
    
    if "error" in response:
        logger.error(f"Error creating test message: {response['error']}")
        return None
    
    message_id = response.data[0]["id"]
    logger.info(f"Successfully created test message with ID: {message_id}")
    return message_id


async def run_processor():
    """Run the scheduled message processor"""
    logger.info("Running scheduled message processor")
    
    try:
        # Import and run the processor
        from scheduled_message_processor import main as processor_main
        await processor_main()
        logger.info("Processor completed successfully")
    except Exception as e:
        logger.error(f"Error running processor: {e}")


async def check_message_status(message_id: str):
    """Check if the test message was successfully processed"""
    logger.info(f"Checking status of message {message_id}")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Get the message
    response = supabase.table("scheduled_messages").select("*").eq("id", message_id).execute()
    
    if not response.data:
        logger.error(f"Message {message_id} not found")
        return False
    
    message = response.data[0]
    status = message.get("status")
    
    logger.info(f"Message status: {status}")
    
    # Check if the status was updated from 'pending'
    if status in ["sent", "failed"]:
        logger.info(f"Message was processed with status: {status}")
        if status == "failed" and "error_message" in message:
            logger.warning(f"Error message: {message['error_message']}")
        return True
    else:
        logger.warning(f"Message was not processed. Status is still: {status}")
        return False


async def main():
    """Test the scheduled message processor"""
    logger.info("=== Starting Scheduler Test ===")
    
    # Prompt for patient ID
    patient_id = input("Enter patient ID to test with: ").strip()
    if not patient_id:
        logger.error("No patient ID provided")
        return
    
    # Create a test message
    message_id = await create_test_message(patient_id)
    if not message_id:
        logger.error("Failed to create test message")
        return
    
    # Wait a moment to ensure the message is stored
    logger.info("Waiting for message to be stored in database...")
    await asyncio.sleep(2)
    
    # Run the processor
    await run_processor()
    
    # Wait a moment for processing to complete
    logger.info("Waiting for processing to complete...")
    await asyncio.sleep(2)
    
    # Check the status
    processed = await check_message_status(message_id)
    
    if processed:
        logger.info("✅ Test successful: Message was processed correctly")
    else:
        logger.error("❌ Test failed: Message was not processed")
    
    logger.info("=== Scheduler Test Completed ===")


if __name__ == "__main__":
    asyncio.run(main()) 