"""
Telegram handler for sending scheduled messages.

This module provides a handler for sending scheduled messages via Telegram.
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

class TelegramHandler:
    """Handler for sending scheduled messages via Telegram."""
    
    def __init__(self):
        """Initialize the Telegram handler."""
        self.api_token = settings.TELEGRAM_BOT_TOKEN
        self.api_base = settings.TELEGRAM_API_BASE
        self.base_url = f"{self.api_base}/bot{self.api_token}"
        
    async def _make_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the Telegram API.
        
        Args:
            method: The API method to call
            params: The parameters for the API call
            
        Returns:
            The API response
        """
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
        """
        Send a message to a Telegram chat.
        
        Args:
            chat_id: The ID of the chat
            message: The message to send
            parse_mode: The parse mode for the message (HTML, Markdown)
            
        Returns:
            The API response
        """
        params = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        
        return await self._make_request("sendMessage", params)
    
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
        
        result = await self.send_message(recipient_id, message_content)
        
        if result.get("success"):
            logger.info(f"Sent scheduled message to Telegram recipient {recipient_id}")
            return {
                "success": True,
                "message_id": result.get("result", {}).get("message_id"),
                "platform": "telegram"
            }
        else:
            logger.error(f"Failed to send Telegram message: {result.get('error')}")
            return {
                "success": False,
                "error": result.get("error"),
                "platform": "telegram"
            }
            
    async def parse_command(self, message_text: str) -> Optional[Dict[str, Any]]:
        """Parse a scheduling command from Telegram.
        
        Args:
            message_text: Raw message text from Telegram
            
        Returns:
            Dictionary with parsed command data or None if parsing fails
        """
        try:
            # Basic validation
            if not message_text or not message_text.lower().startswith("/schedule"):
                return {"success": False, "error": "Not a valid scheduling command"}
            
            # Remove the command prefix and trim
            content = message_text[9:].strip()
            if not content:
                return {"success": False, "error": "Missing schedule information"}
            
            # Check for simple time-based schedule (e.g., "/schedule tomorrow 15:00 Take your medicine")
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
            return {"success": False, "error": "Invalid format. Use '/schedule [when] [message]'"}
        except Exception as e:
            logger.error(f"Error parsing Telegram command: {e}")
            return {"success": False, "error": "Error parsing the command"} 