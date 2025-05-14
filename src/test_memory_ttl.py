#!/usr/bin/env python
"""
Test script to verify the new TTL settings for memories.
This script confirms that memories are stored with a long TTL to prevent expiration.
"""

import asyncio
import json
import logging
from datetime import datetime
from ai_companion.modules.memory.short_term.memory_manager import (
    get_short_term_memory_manager,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Test patient ID from the screenshot/logs
TEST_PATIENT_ID = "38592401-8cc1-4559-9a14-ef146e1aa4ea"
TEST_MESSAGE = "This is a test memory to verify long TTL"


async def test_memory_ttl():
    """Test that memories are stored with long TTL."""
    logger.info("=" * 50)
    logger.info("TESTING MEMORY TTL SETTINGS")
    logger.info("=" * 50)

    # Get memory manager
    memory_manager = get_short_term_memory_manager()
    await memory_manager.start()

    try:
        logger.info(f"Testing memory storage for patient_id: {TEST_PATIENT_ID}")

        # Create memory data structure
        memory_data = {
            "user_message": "Test TTL message",
            "assistant_response": "Testing long-term memory storage",
            "timestamp": datetime.now().isoformat(),
        }

        # Create metadata with patient_id
        memory_metadata = {
            "patient_id": TEST_PATIENT_ID,
            "platform": "test",
            "external_system_id": "ttl_test",
            "timestamp": datetime.now().isoformat(),
        }

        # Store memory
        memory = await memory_manager.store_memory(
            json.dumps(memory_data), metadata=memory_metadata
        )

        # Check TTL - should be far in the future
        now = datetime.now()
        ttl_days = (memory.expires_at - now).days

        logger.info(f"Memory created at: {memory.created_at}")
        logger.info(f"Memory expires at: {memory.expires_at}")
        logger.info(f"Memory TTL in days: {ttl_days}")

        # Verify TTL is long enough (should be close to 365 days)
        if ttl_days > 350:
            logger.info(f"✅ Memory has correct long-term TTL: {ttl_days} days")
            return True
        else:
            logger.error(f"❌ Memory TTL too short: {ttl_days} days")
            return False

    except Exception as e:
        logger.error(f"Error testing memory TTL: {e}", exc_info=True)
        return False
    finally:
        # Clean up
        await memory_manager.stop()


if __name__ == "__main__":
    success = asyncio.run(test_memory_ttl())
    if success:
        logger.info("✅ Memory TTL test passed!")
    else:
        logger.error("❌ Memory TTL test failed!")
