"""
WhatsApp handler for sending scheduled messages.

This module provides a handler for sending scheduled messages via WhatsApp.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
import json
import re
from datetime import datetime

from ai_companion.settings import settings
import aiohttp

logger = logging.getLogger(__name__)

class WhatsAppHandler:
    """Handler for sending scheduled messages via WhatsApp."""
    
    def __init__(self):
        """Initialize the WhatsApp handler."""
        self.token = settings.WHATSAPP_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.api_base = "https://graph.facebook.com/v22.0"
        
    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the WhatsApp API.
        
        Args:
            endpoint: The API endpoint
            data: The data for the API call
            
        Returns:
            The API response
        """
        url = f"{self.api_base}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"WhatsApp API error: {response.status} - {error_text}")
                        return {"success": False, "error": f"API error: {response.status}"}
                    
                    result = await response.json()
                    return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Error making WhatsApp API request: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_message(self, 
                         recipient_phone: str, 
                         message: str) -> Dict[str, Any]:
        """
        Send a message to a WhatsApp recipient.
        
        Args:
            recipient_phone: The recipient's phone number
            message: The message to send
            
        Returns:
            The API response
        """
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message
            }
        }
        
        endpoint = f"{self.phone_number_id}/messages"
        return await self._make_request(endpoint, data)
    
    async def send_scheduled_message(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a scheduled message.
        
        Args:
            schedule_data: Details of the scheduled message
            
        Returns:
            Dict with the result of the operation
        """
        recipient_id = schedule_data.get("recipient_id")
        message_content = schedule_data.get("message_content", "")
        
        if not recipient_id:
            return {
                "success": False,
                "error": "Missing recipient ID"
            }
        
        # For WhatsApp, ensure the recipient ID is in the correct format
        # If it's not a properly formatted phone number with country code,
        # the request will fail
        if not recipient_id.startswith("+"):
            # Check if it's already in E.164 format
            if recipient_id.isdigit() and len(recipient_id) > 10:
                # Assuming it has country code but missing +
                recipient_id = "+" + recipient_id
            else:
                return {
                    "success": False,
                    "error": "Invalid WhatsApp recipient ID format. Must be E.164 format with country code."
                }
        
        result = await self.send_message(recipient_id, message_content)
        
        if result.get("success"):
            logger.info(f"Sent scheduled message to WhatsApp recipient {recipient_id}")
            return {
                "success": True,
                "message_id": result.get("result", {}).get("messages", [{}])[0].get("id"),
                "platform": "whatsapp"
            }
        else:
            logger.error(f"Failed to send WhatsApp message: {result.get('error')}")
            return {
                "success": False,
                "error": result.get("error"),
                "platform": "whatsapp"
            }
            
    async def parse_command(self, message_text: str) -> Optional[Dict[str, Any]]:
        """Parse a scheduling command from WhatsApp.
        
        Args:
            message_text: Raw message text from WhatsApp
            
        Returns:
            Dictionary with parsed command data or None if parsing fails
        """
        try:
            # Basic validation
            if not message_text or not message_text.lower().startswith("schedule "):
                return {"success": False, "error": "Not a valid scheduling command"}
            
            # Remove the command prefix and trim
            content = message_text[9:].strip()
            if not content:
                return {"success": False, "error": "Missing schedule information"}
            
            # Check for simple time-based schedule (e.g., "schedule tomorrow 15:00 Take your medicine")
            # Pattern: [time specification] [message]
            time_pattern = r'^(tomorrow|today|in \d+ (hours|minutes)|next \w+|\d{4}-\d{2}-\d{2}|\w+ \d{1,2}(st|nd|rd|th)?)\s+(\d{1,2}:\d{2})\s+(.+)$'
            recurring_pattern = r'^(daily|weekly on \w+|monthly on \d{1,2})\s+at\s+(\d{1,2}:\d{2})\s+(.+)$'
            
            # Try single occurrence format
            single_match = re.match(time_pattern, content, re.IGNORECASE)
            if single_match:
                date_spec = single_match.group(1)
                time_spec = single_match.group(4)
                message = single_match.group(5).strip()
                
                # Parse the date and time
                from ai_companion.modules.scheduled_messaging.triggers import parse_trigger
                scheduled_time = parse_trigger(f"{date_spec} {time_spec}")
                
                if scheduled_time:
                    return {
                        "success": True,
                        "type": "single",
                        "time": scheduled_time.isoformat(),
                        "message": message
                    }
                else:
                    return {"success": False, "error": "Could not parse the scheduled time"}
            
            # Try recurring format
            recurring_match = re.match(recurring_pattern, content, re.IGNORECASE)
            if recurring_match:
                recurrence_spec = recurring_match.group(1)
                time_spec = recurring_match.group(2)
                message = recurring_match.group(3).strip()
                
                # Parse the recurrence pattern
                from ai_companion.modules.scheduled_messaging.triggers import parse_recurrence
                recurrence = parse_recurrence(f"{recurrence_spec} at {time_spec}")
                
                if recurrence:
                    return {
                        "success": True,
                        "type": "recurring",
                        "recurrence": recurrence,
                        "time": recurrence["next_date"].isoformat() if "next_date" in recurrence else datetime.now().isoformat(),
                        "message": message
                    }
                else:
                    return {"success": False, "error": "Could not parse the recurrence pattern"}
            
            # If neither pattern matches
            return {"success": False, "error": "Invalid format. Use 'schedule [when] [message]'"}
        except Exception as e:
            logger.error(f"Error parsing WhatsApp command: {e}")
            return {"success": False, "error": "Error parsing the command"} 