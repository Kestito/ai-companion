#!/usr/bin/env python
"""
Test script to validate memory storage and retrieval with patient_id.
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime

from ai_companion.modules.memory.short_term.memory_manager import ShortTermMemoryManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Use a real patient ID from the database
TEST_PATIENT_ID = "38592401-8cc1-4559-9a14-ef146e1aa4ea"  # Verified ID from get_patient_id_from_platform_id
TEST_PLATFORM = "telegram"
TEST_USER_ID = "6519374243"


async def test_memory_storage_and_retrieval():
    """Test memory storage and retrieval with patient_id."""
    logger.info(
        f"Testing memory storage and retrieval with patient_id: {TEST_PATIENT_ID}"
    )

    # Initialize memory manager
    memory_manager = ShortTermMemoryManager()
    await memory_manager.start()

    try:
        # Create test memory content
        memory_content = json.dumps(
            {
                "user_message": "Hello, how are you?",
                "assistant_response": "I'm doing well, thank you for asking!",
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Create metadata with patient_id
        metadata = {
            "user_id": TEST_USER_ID,
            "platform": TEST_PLATFORM,
            "session_id": f"test-session-{uuid.uuid4()}",
            "patient_id": TEST_PATIENT_ID,
            "context": {
                "conversation_id": str(uuid.uuid4()),
            },
        }

        # Store memory
        memory = await memory_manager.store_memory(
            content=memory_content, ttl_minutes=60, metadata=metadata
        )

        logger.info(f"Stored memory with ID: {memory.id}")

        # Wait a moment for async storage to complete
        await asyncio.sleep(1)

        # Retrieve memories using patient_id
        logger.info(f"Retrieving memories for patient {TEST_PATIENT_ID}")
        memories = memory_manager.get_relevant_memories("test query", TEST_PATIENT_ID)

        # Check if memories were found
        if memories:
            logger.info(
                f"Found {len(memories)} memories for patient_id: {TEST_PATIENT_ID}"
            )
            logger.info(f"Memory content: {memories[0].get('content', '')[:100]}...")
        else:
            logger.error(f"No memories found for patient_id: {TEST_PATIENT_ID}")

        # Try with a non-existent patient ID
        non_existent_id = str(uuid.uuid4())
        logger.info(
            f"Testing retrieval with non-existent patient_id: {non_existent_id}"
        )
        empty_memories = memory_manager.get_relevant_memories(
            "test query", non_existent_id
        )
        logger.info(f"Found {len(empty_memories)} memories for non-existent patient_id")

        # Add a second memory to test multiple retrievals
        second_content = json.dumps(
            {
                "user_message": "What's the weather like today?",
                "assistant_response": "It's sunny and warm!",
                "timestamp": datetime.now().isoformat(),
            }
        )

        second_memory = await memory_manager.store_memory(
            content=second_content, ttl_minutes=60, metadata=metadata
        )

        logger.info(f"Stored second memory with ID: {second_memory.id}")

        # Wait a moment for async storage to complete
        await asyncio.sleep(1)

        # Retrieve memories again
        updated_memories = memory_manager.get_relevant_memories(
            "test query", TEST_PATIENT_ID
        )
        logger.info(
            f"Found {len(updated_memories)} memories after adding second memory"
        )

        return True

    except Exception as e:
        logger.error(f"Error in test: {e}", exc_info=True)
        return False
    finally:
        # Clean up
        await memory_manager.stop()


if __name__ == "__main__":
    asyncio.run(test_memory_storage_and_retrieval())
