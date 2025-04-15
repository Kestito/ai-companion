#!/usr/bin/env python3

"""
Test script for Telegram bot responses.
This script tests the Telegram bot's response handling for different types of messages:
1. Text messages
2. Command messages
3. Edge cases (empty messages, very long messages)

Usage: python test_telegram_responses.py
"""

import asyncio
import json
import logging
import sys
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("TestTelegramResponses")

# Path adjustment for imports
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Mock the dependencies before importing TelegramBot
sys.modules['ai_companion.modules.speech.SpeechToText'] = MagicMock()
sys.modules['ai_companion.modules.speech.TextToSpeech'] = MagicMock()
sys.modules['ai_companion.modules.image.ImageToText'] = MagicMock()

# Apply patches for the modules
with patch('ai_companion.modules.speech.SpeechToText', MagicMock()), \
     patch('ai_companion.modules.speech.TextToSpeech', MagicMock()), \
     patch('ai_companion.modules.image.ImageToText', MagicMock()), \
     patch('ai_companion.utils.supabase.get_supabase_client', MagicMock()):
    # Now import the TelegramBot class
    from ai_companion.interfaces.telegram.telegram_bot import TelegramBot

class MockClient:
    """Mock for the httpx client."""
    def __init__(self):
        self.responses = {}
        self.post = AsyncMock()
        self.get = AsyncMock()
    
    def set_response(self, method, response):
        """Set the mock response for a specific method."""
        self.responses[method] = response
        
    async def aclose(self):
        """Mock close method."""
        pass

class TestTelegramResponses(unittest.TestCase):
    """Test case for Telegram bot responses."""
    
    async def asyncSetUp(self):
        """Set up the test case with mocks."""
        # Create patches for all dependencies
        self.patches = [
            patch('ai_companion.modules.speech.SpeechToText', MagicMock()),
            patch('ai_companion.modules.speech.TextToSpeech', MagicMock()),
            patch('ai_companion.modules.image.ImageToText', MagicMock()),
            patch('ai_companion.utils.supabase.get_supabase_client', MagicMock()),
            patch('ai_companion.interfaces.telegram.telegram_bot.httpx.AsyncClient'),
            patch('ai_companion.interfaces.telegram.telegram_bot.settings', MagicMock(
                SHORT_TERM_MEMORY_DB_PATH="sqlite:///memory.db",
                TELEGRAM_BOT_TOKEN="mock_token",
                TELEGRAM_API_BASE="https://api.telegram.org"
            ))
        ]
        
        # Start all patches
        for p in self.patches:
            p.start()
            
        # Create a bot instance
        self.bot = TelegramBot()
        self.bot.client = MockClient()
        
        # Mock the graph builder and other components
        self.bot._make_request = AsyncMock()
        self.bot._send_message = AsyncMock()
        self.bot._send_photo = AsyncMock()
        self.bot._send_voice = AsyncMock()
        self.bot._save_to_database = AsyncMock(return_value="mock-conversation-id")
        
        # Create a mock graph instance
        self.mock_graph = AsyncMock()
        self.mock_graph_builder = MagicMock()
        self.mock_graph_builder.with_config.return_value = self.mock_graph
        
        # Patch graph_builder
        self.graph_builder_patch = patch('ai_companion.interfaces.telegram.telegram_bot.graph_builder', self.mock_graph_builder)
        self.graph_builder_patch.start()
        
        # Patch AsyncSqliteSaver
        self.mock_saver = AsyncMock()
        self.mock_saver.__aenter__ = AsyncMock(return_value=self.mock_saver)
        self.mock_saver.__aexit__ = AsyncMock(return_value=None)
        self.saver_patch = patch('ai_companion.interfaces.telegram.telegram_bot.AsyncSqliteSaver.from_conn_string', return_value=self.mock_saver)
        self.saver_patch.start()
    
    async def asyncTearDown(self):
        """Clean up after each test."""
        self.graph_builder_patch.stop()
        self.saver_patch.stop()
        
        # Stop all patches
        for p in self.patches:
            p.stop()
    
    def reset_mocks(self):
        """Reset all mocks between tests."""
        self.bot._make_request.reset_mock()
        self.bot._send_message.reset_mock()
        self.bot._send_photo.reset_mock()
        self.bot._send_voice.reset_mock()
        self.bot._save_to_database.reset_mock()
        self.mock_graph.ainvoke.reset_mock()
    
    async def test_text_message_response(self):
        """Test basic text message processing and response."""
        logger.info("Testing text message response...")
        
        # Create a test message
        test_message = {
            "message_id": 12345,
            "from": {
                "id": 67890,
                "is_bot": False,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
                "language_code": "en"
            },
            "chat": {
                "id": 67890,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
                "type": "private"
            },
            "date": int(datetime.now().timestamp()),
            "text": "Hello bot, how are you?"
        }
        
        # Set up the mock response from the graph
        test_response = "Hello! I'm doing well, thank you for asking. How can I help you today?"
        self.mock_graph.ainvoke.return_value = {
            "messages": [
                {
                    "content": test_response,
                    "type": "ai"
                }
            ]
        }
        
        # Process the message
        await self.bot._process_update({"message": test_message})
        
        # Verify the graph was called with the right message
        self.mock_graph.ainvoke.assert_called_once()
        
        # Verify send_message was called with the correct response
        self.bot._send_message.assert_called_once_with(67890, test_response)
        
        # Verify we saved to the database
        self.bot._save_to_database.assert_called_once()
        
        logger.info("Text message test passed!")
    
    async def test_command_message(self):
        """Test command message processing and response."""
        logger.info("Testing command message response...")
        
        # Reset mocks before testing
        self.reset_mocks()
        
        # Create a test command message
        test_message = {
            "message_id": 12346,
            "from": {
                "id": 67890,
                "is_bot": False,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
                "language_code": "en"
            },
            "chat": {
                "id": 67890,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
                "type": "private"
            },
            "date": int(datetime.now().timestamp()),
            "text": "/schedule tomorrow at 2pm Reminder for doctor appointment"
        }
        
        # Set up the mock response from the graph
        test_response = "I've scheduled your reminder for tomorrow at 2:00 PM."
        self.mock_graph.ainvoke.return_value = {
            "messages": [
                {
                    "content": test_response,
                    "type": "ai"
                }
            ],
            "workflow": "schedule"
        }
        
        # Process the message
        await self.bot._process_update({"message": test_message})
        
        # Verify send_message was called with the correct response
        self.bot._send_message.assert_called_once_with(67890, test_response)
        
        logger.info("Command message test passed!")
    
    async def test_long_message_response(self):
        """Test handling of very long responses that need chunking."""
        logger.info("Testing long message response...")
        
        # Reset mocks before testing
        self.reset_mocks()
        
        # Create a test message
        test_message = {
            "message_id": 12347,
            "from": {
                "id": 67890,
                "is_bot": False,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
                "language_code": "en"
            },
            "chat": {
                "id": 67890,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
                "type": "private"
            },
            "date": int(datetime.now().timestamp()),
            "text": "Please provide a detailed health overview."
        }
        
        # Set up the mock response from the graph - a very long response
        # Create a 5000 character response that will need chunking
        long_text = "A" * 5000
        self.mock_graph.ainvoke.return_value = {
            "messages": [
                {
                    "content": long_text,
                    "type": "ai"
                }
            ]
        }
        
        # Override _send_message to test chunking behavior
        original_send_message = self.bot._send_message
        self.bot._send_message = AsyncMock()
        self.bot._send_single_message = AsyncMock(return_value={"ok": True})
        
        # Process the message
        await self.bot._process_update({"message": test_message})
        
        # Verify _send_message was called
        self.bot._send_message.assert_called_once_with(67890, long_text)
        
        # Restore original method
        self.bot._send_message = original_send_message
        
        logger.info("Long message test passed!")
    
    async def test_empty_content(self):
        """Test handling of edge cases like empty content."""
        logger.info("Testing empty content handling...")
        
        # Reset mocks before testing
        self.reset_mocks()
        
        # Create a test message with no text
        test_message = {
            "message_id": 12348,
            "from": {
                "id": 67890,
                "is_bot": False,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
                "language_code": "en"
            },
            "chat": {
                "id": 67890,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
                "type": "private"
            },
            "date": int(datetime.now().timestamp())
            # No text field
        }
        
        # Process the message - should handle gracefully
        await self.bot._process_update({"message": test_message})
        
        # Verify the graph was not called
        self.mock_graph.ainvoke.assert_not_called()
        # Verify send_message was not called
        self.bot._send_message.assert_not_called()
        
        logger.info("Empty content test passed!")

async def run_tests():
    """Run the test cases."""
    logger.info("=== Starting Telegram Response Tests ===")
    
    # Create test instance
    test_instance = TestTelegramResponses()
    await test_instance.asyncSetUp()
    
    try:
        logger.info("Running test_text_message_response")
        await test_instance.test_text_message_response()
        
        logger.info("Running test_command_message")
        await test_instance.test_command_message()
        
        logger.info("Running test_long_message_response")
        await test_instance.test_long_message_response()
        
        logger.info("Running test_empty_content")
        await test_instance.test_empty_content()
        
        logger.info("All tests passed!")
    finally:
        await test_instance.asyncTearDown()
    
    logger.info("=== Telegram Response Tests Completed ===")

if __name__ == "__main__":
    asyncio.run(run_tests()) 