"""
Message processor for scheduled messages.

This module provides a background process that handles the sending
of scheduled messages that are due.
"""

import logging
import asyncio
import time
from typing import Dict, Any, List, Optional
import sys
import json
import signal

from ai_companion.settings import settings
from ai_companion.modules.scheduled_messaging.storage import (
    get_pending_messages,
    update_message_status,
    create_scheduled_messages_table
)
from ai_companion.modules.scheduled_messaging.handlers.telegram_handler import TelegramHandler
from ai_companion.modules.scheduled_messaging.handlers.whatsapp_handler import WhatsAppHandler

logger = logging.getLogger(__name__)

# Platform handlers
HANDLERS = {
    "telegram": TelegramHandler(),
    "whatsapp": WhatsAppHandler()
}

async def process_due_messages():
    """Process all messages that are due for delivery."""
    logger.info("Processing due messages")
    
    # Get all pending messages that are due
    due_messages = await get_pending_messages()
    
    if not due_messages:
        logger.debug("No due messages to process")
        return
    
    logger.info(f"Found {len(due_messages)} messages to process")
    
    for message in due_messages:
        await process_message(message)

async def process_message(message: Dict[str, Any]):
    """
    Process a single scheduled message.
    
    Args:
        message: The scheduled message to process
    """
    schedule_id = message.get("id")
    platform = message.get("platform", "").lower()
    recipient_id = message.get("recipient_id")
    
    logger.info(f"Processing message {schedule_id} for {platform} recipient {recipient_id}")
    
    if platform not in HANDLERS:
        logger.error(f"Unsupported platform: {platform}")
        await update_message_status(schedule_id, "failed", {"error": f"Unsupported platform: {platform}"})
        return
    
    handler = HANDLERS[platform]
    
    try:
        # Send the message
        result = await handler.send_scheduled_message(message)
        
        if result.get("success"):
            logger.info(f"Successfully sent message {schedule_id}")
            await update_message_status(schedule_id, "sent")
            
            # If message has recurrence pattern, create next occurrence
            if message.get("recurrence_pattern"):
                await create_next_occurrence(message)
        else:
            logger.error(f"Failed to send message {schedule_id}: {result.get('error')}")
            await update_message_status(schedule_id, "failed", {"error": result.get("error")})
    except Exception as e:
        logger.error(f"Error processing message {schedule_id}: {e}")
        await update_message_status(schedule_id, "failed", {"error": str(e)})

async def create_next_occurrence(message: Dict[str, Any]):
    """
    Create a new scheduled message for the next occurrence.
    
    Args:
        message: The current scheduled message
    """
    from ai_companion.modules.scheduled_messaging.scheduler import ScheduleManager
    from ai_companion.modules.scheduled_messaging.triggers import parse_recurrence, get_next_occurrence
    
    # Parse the recurrence pattern
    recurrence_str = message.get("recurrence_pattern")
    if not recurrence_str:
        return
    
    try:
        # Parse JSON if it's a string
        if isinstance(recurrence_str, str):
            recurrence = json.loads(recurrence_str)
        else:
            recurrence = recurrence_str
            
        # Calculate next occurrence
        next_time = get_next_occurrence(recurrence)
        
        if next_time:
            # Create new schedule for next occurrence
            scheduler = ScheduleManager()
            await scheduler.schedule_message(
                patient_id=message.get("patient_id"),
                recipient_id=message.get("recipient_id"),
                platform=message.get("platform"),
                message_content=message.get("message_content"),
                scheduled_time=next_time,
                template_key=message.get("template_key"),
                parameters=(json.loads(message.get("parameters")) if message.get("parameters") else None),
                recurrence_pattern=recurrence
            )
            
            logger.info(f"Created next occurrence for {message.get('id')} at {next_time}")
    except Exception as e:
        logger.error(f"Failed to create next occurrence: {e}")

async def run_processor():
    """Run the message processor repeatedly."""
    # Create the scheduled_messages table if it doesn't exist
    await create_scheduled_messages_table()
    
    # Run indefinitely
    while True:
        try:
            await process_due_messages()
        except Exception as e:
            logger.error(f"Error in message processor: {e}")
        
        # Sleep for the polling interval
        await asyncio.sleep(60)  # Check every minute

def handle_signal(signum, frame):
    """Handle termination signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

def main():
    """Entry point for the processor."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    logger.info("Starting scheduled message processor")
    
    try:
        # Run the processor
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_processor())
    except KeyboardInterrupt:
        logger.info("Shutting down due to keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 