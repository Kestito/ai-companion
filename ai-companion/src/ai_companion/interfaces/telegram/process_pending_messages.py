#!/usr/bin/env python3

"""
Manually Process Pending Telegram Messages

This script finds and processes all pending scheduled messages at once.
Useful for manual intervention when the scheduler is not working correctly.
"""

import os
import sys
import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("manual_process.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ManualMessageProcessor")

# Import Supabase client
try:
    from supabase import create_client, Client
except ImportError:
    logger.error("Supabase client not found. Install with: pip install supabase")
    sys.exit(1)

# Try to import Telegram bot
try:
    from telegram.ext import Application
except ImportError:
    logger.error("Python-telegram-bot not found. Install with: pip install python-telegram-bot")
    sys.exit(1)

# Supabase credentials 
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://aubulhjfeszmsheonmpy.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc")

# Telegram Bot Token
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "5933996374:AAGZDvHg3tYoXnGIa1wKVAsCO-iqFnCmGMw")

async def fetch_pending_messages() -> List[Dict[str, Any]]:
    """Fetch all pending messages, including those scheduled for the future"""
    logger.info("Fetching all pending messages")
    
    try:
        # Connect to Supabase
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Get all pending messages
        response = await asyncio.to_thread(
            supabase.table("scheduled_messages")
            .select("*")
            .eq("status", "pending")
            .execute
        )
        
        pending_messages = response.data
        logger.info(f"Found {len(pending_messages)} pending messages to process")
        return pending_messages
    
    except Exception as e:
        logger.error(f"Error fetching pending messages: {e}")
        return []

async def send_telegram_message(patient_id: str, message_content: str) -> bool:
    """Send a message to a patient via Telegram"""
    logger.info(f"Attempting to send message to patient {patient_id}")
    
    try:
        # Connect to Supabase
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Initialize Telegram bot
        telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # First, get the patient's telegram_id from the patients table
        patient_response = await asyncio.to_thread(
            supabase.table("patients")
            .select("telegram_id")
            .eq("id", patient_id)
            .execute
        )
        
        if not patient_response.data:
            logger.error(f"Patient {patient_id} not found in database")
            return False
        
        telegram_id = patient_response.data[0].get("telegram_id")
        if not telegram_id:
            logger.error(f"Patient {patient_id} has no telegram_id")
            return False
        
        # Send the message using the Telegram bot
        await telegram_app.bot.send_message(
            chat_id=telegram_id,
            text=message_content
        )
        
        logger.info(f"Successfully sent message to patient {patient_id} (Telegram ID: {telegram_id})")
        return True
    
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        return False

async def update_message_status(message_id: str, status: str, error_message: str = None) -> None:
    """Update the status of a message in the database"""
    try:
        # Connect to Supabase
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Use last_attempt_time instead of processed_at
        update_data = {
            "status": status,
            "last_attempt_time": datetime.now(timezone.utc).isoformat(),
            "attempts": supabase.table("scheduled_messages").select("attempts").eq("id", message_id).execute().data[0].get("attempts", 0) + 1
        }
        
        if error_message:
            # Store error in metadata
            message_data = supabase.table("scheduled_messages").select("metadata").eq("id", message_id).execute().data[0]
            metadata = message_data.get("metadata", {}) or {}
            if isinstance(metadata, str):
                try:
                    import json
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            metadata["error_message"] = error_message
            update_data["metadata"] = metadata
        
        await asyncio.to_thread(
            supabase.table("scheduled_messages")
            .update(update_data)
            .eq("id", message_id)
            .execute
        )
        
        logger.info(f"Updated message {message_id} status to '{status}'")
    
    except Exception as e:
        logger.error(f"Error updating message status: {e}")

async def process_all_messages() -> None:
    """Process all pending messages, including future ones"""
    logger.info("=== Starting Manual Processing of All Pending Messages ===")
    
    try:
        pending_messages = await fetch_pending_messages()
        if not pending_messages:
            logger.info("No pending messages to process")
            return
        
        for message in pending_messages:
            message_id = message.get("id")
            patient_id = message.get("patient_id")
            content = message.get("message_content")
            scheduled_time = message.get("scheduled_time")
            
            logger.info(f"Processing message {message_id} for patient {patient_id} (scheduled: {scheduled_time})")
            
            # Try to send the message
            success = await send_telegram_message(patient_id, content)
            
            # Update the status based on the result
            if success:
                await update_message_status(message_id, "sent")
            else:
                error_msg = "Failed to send message via Telegram API"
                await update_message_status(message_id, "failed", error_msg)
        
        logger.info(f"Completed processing {len(pending_messages)} messages")
    
    except Exception as e:
        logger.error(f"Unhandled exception in processor: {e}")
    
    logger.info("=== Manual Processing Completed ===")

if __name__ == "__main__":
    asyncio.run(process_all_messages()) 