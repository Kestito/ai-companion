#!/usr/bin/env python3

"""
Custom test script for Telegram bot responses with Lithuanian questions.
This script tests the Telegram bot's responses to specific Lithuanian language questions.

Usage: python test_custom_responses.py
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
logger = logging.getLogger("TestCustomResponses")

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

class TestCustomResponses(unittest.TestCase):
    """Test case for Telegram bot responses to Lithuanian questions."""
    
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
    
    async def test_pola_card_question(self):
        """Test response to question about obtaining a POLA card."""
        logger.info("Testing response to: 'Kaip galima gauti pola kortele'")
        
        # Create a test message
        test_message = {
            "message_id": 12345,
            "from": {
                "id": 67890,
                "is_bot": False,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
                "language_code": "lt"
            },
            "chat": {
                "id": 67890,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
                "type": "private"
            },
            "date": int(datetime.now().timestamp()),
            "text": "Kaip galima gauti pola kortele"
        }
        
        # Set up the mock response from the graph
        test_response = "POLA kortelę galite gauti apsilankę artimiausiame POLA paslaugų centre arba užsisakydami internetu per POLA portalą. Užsisakant internetu, jums reikės pateikti asmens duomenis ir nuotrauką, o kortelė bus pristatyta paštu. Ar norėtumėte daugiau informacijos apie dokumentus, kurių reikia POLA kortelei gauti?"
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
        
        # Print the response for analysis
        logger.info(f"Response: {test_response}")
        
        logger.info("POLA card question test passed!")
    
    async def test_payments_in_vilnius(self):
        """Test response to question about payments in Vilnius."""
        logger.info("Testing response to: 'imokos vilniuje'")
        
        # Reset mocks before testing
        self.reset_mocks()
        
        # Create a test message
        test_message = {
            "message_id": 12346,
            "from": {
                "id": 67890,
                "is_bot": False,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
                "language_code": "lt"
            },
            "chat": {
                "id": 67890,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
                "type": "private"
            },
            "date": int(datetime.now().timestamp()),
            "text": "imokos vilniuje"
        }
        
        # Set up the mock response from the graph
        test_response = "Vilniuje įmokas galite atlikti įvairiose vietose: bankų skyriuose, \"Perlo\" terminaluose, \"Maxima\" parduotuvėse, Lietuvos pašto skyriuose, arba internetu per elektroninę bankininkystę. Jei jus domina konkretūs mokesčiai ar paslaugos (pvz., komunaliniai mokesčiai, baudos), galiu suteikti daugiau informacijos apie tai."
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
        
        # Verify send_message was called with the correct response
        self.bot._send_message.assert_called_once_with(67890, test_response)
        
        # Print the response for analysis
        logger.info(f"Response: {test_response}")
        
        logger.info("Payments in Vilnius test passed!")
    
    async def test_pola_ambassador_question(self):
        """Test response to question about POLA ambassador in Klaipeda."""
        logger.info("Testing response to: 'pola ambasadorius klaipedoje'")
        
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
                "language_code": "lt"
            },
            "chat": {
                "id": 67890,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
                "type": "private"
            },
            "date": int(datetime.now().timestamp()),
            "text": "pola ambasadorius klaipedoje"
        }
        
        # Set up the mock response from the graph
        test_response = "POLA ambasadorių Klaipėdoje galite rasti POLA paslaugų centre adresu H. Manto g. 47, Klaipėda. Darbo laikas: pirmadieniais-penktadieniais nuo 9:00 iki 17:00. Ambasadorius teikia informaciją apie POLA programą, padeda užsiregistruoti, teikia konsultacijas dėl POLA kortelės ir kitų paslaugų. Ar norėtumėte sužinoti konkretaus ambasadoriaus kontaktinę informaciją?"
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
        
        # Verify send_message was called with the correct response
        self.bot._send_message.assert_called_once_with(67890, test_response)
        
        # Print the response for analysis
        logger.info(f"Response: {test_response}")
        
        logger.info("POLA ambassador question test passed!")

async def run_tests():
    """Run the test cases."""
    logger.info("=== Starting Custom Lithuanian Question Tests ===")
    
    # Create test instance
    test_instance = TestCustomResponses()
    await test_instance.asyncSetUp()
    
    try:
        logger.info("Running test_pola_card_question")
        await test_instance.test_pola_card_question()
        
        logger.info("Running test_payments_in_vilnius")
        await test_instance.test_payments_in_vilnius()
        
        logger.info("Running test_pola_ambassador_question")
        await test_instance.test_pola_ambassador_question()
        
        logger.info("All tests passed!")
    finally:
        await test_instance.asyncTearDown()
    
    logger.info("=== Custom Lithuanian Question Tests Completed ===")

if __name__ == "__main__":
    asyncio.run(run_tests()) 