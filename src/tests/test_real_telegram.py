"""
Test sending a real message with the test Telegram bot.

This script will send an actual message to your Telegram account using the test bot.
"""

import asyncio
import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any
import aiohttp
from test_config import TEST_TELEGRAM_BOT_TOKEN, YOUR_TELEGRAM_USER_ID, TEST_PATIENT_ID

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_real_telegram")

class TestTelegramBot:
    """Test Telegram bot for sending real messages."""
    
    def __init__(self):
        """Initialize the Telegram bot with test token."""
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

async def test_send_real_message():
    """Test sending a real message to your Telegram account."""
    # Check if YOUR_TELEGRAM_USER_ID is properly set
    if YOUR_TELEGRAM_USER_ID == "YOUR_ACTUAL_USER_ID":
        logger.error("Please set YOUR_TELEGRAM_USER_ID in test_config.py to your actual Telegram user ID")
        logger.error("You can get this by messaging @userinfobot on Telegram")
        return False
        
    # Create the bot instance
    bot = TestTelegramBot()
    
    # Create a test message
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"""🌤️ *Weather Joke Test Message* 🌤️

Why did the meteorologist go to therapy? 
Because they had too many clouded judgments!

This message was sent at {current_time} using the test bot token.
Your user ID: {YOUR_TELEGRAM_USER_ID}
Test patient ID: {TEST_PATIENT_ID}"""

    # Send the message
    logger.info(f"Sending test message to user ID {YOUR_TELEGRAM_USER_ID}")
    result = await bot.send_message(
        chat_id=YOUR_TELEGRAM_USER_ID,
        message=message,
        parse_mode="Markdown"
    )
    
    # Check the result
    if result.get("success"):
        logger.info("✅ Message sent successfully!")
        logger.info(f"Message ID: {result.get('result', {}).get('message_id')}")
        return True
    else:
        logger.error(f"❌ Failed to send message: {result.get('error')}")
        return False

async def main():
    """Run the test."""
    print("Starting real Telegram test script...")
    print("Testing sending a real message to your Telegram account...")
    success = await test_send_real_message()
    print(f"Test completed: {'✅ PASSED' if success else '❌ FAILED'}")
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"Test script complete with result: {'SUCCESS' if result else 'FAILURE'}")
    sys.exit(0 if result else 1) 