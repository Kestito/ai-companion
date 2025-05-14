#!/usr/bin/env python
"""
Test script to verify memory retrieval functionality.
This script checks if the get_relevant_memories fixes are working correctly.
"""

import asyncio
import logging
from ai_companion.modules.memory.short_term.memory_manager import (
    get_short_term_memory_manager,
)

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Use DEBUG level to see more detailed logs
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Test patient ID from the screenshot/logs
TEST_PATIENT_ID = "38592401-8cc1-4559-9a14-ef146e1aa4ea"
TEST_QUERY = "test query"


async def test_memory_retrieval():
    """Test memory retrieval functionality."""
    logger.info("=" * 50)
    logger.info("TESTING MEMORY RETRIEVAL")
    logger.info("=" * 50)

    # Get memory manager
    memory_manager = get_short_term_memory_manager()
    await memory_manager.start()

    try:
        logger.info(f"Testing memory retrieval for patient_id: {TEST_PATIENT_ID}")

        # Retrieve memories to verify storage
        memories = memory_manager.get_relevant_memories(TEST_QUERY, TEST_PATIENT_ID)

        logger.info(f"Retrieved {len(memories)} memories for patient {TEST_PATIENT_ID}")

        if memories:
            logger.info("Memory retrieval successful!")
            # Display retrieved memories
            for i, memory in enumerate(memories):
                content = memory.get("content", "No content")
                metadata = memory.get("metadata", {})

                # Safely truncate content for display
                if isinstance(content, str) and len(content) > 100:
                    content_display = content[:100] + "..."
                else:
                    content_display = str(content)

                logger.info(f"Memory #{i+1}:")
                logger.info(f"  ID: {memory.get('id', 'No ID')}")
                logger.info(f"  Content: {content_display}")
                logger.info(f"  Metadata: {metadata}")

            # Test formatting
            formatted_memories = memory_manager.format_memories_for_prompt(memories)
            logger.info("Formatted memories:")
            logger.info(formatted_memories)

            return True
        else:
            logger.warning("No memories found. Retrieval may not be working correctly.")
            return False

    except Exception as e:
        logger.error(f"Error testing memory retrieval: {e}", exc_info=True)
        return False
    finally:
        # Clean up
        await memory_manager.stop()


if __name__ == "__main__":
    success = asyncio.run(test_memory_retrieval())
    if success:
        logger.info("✅ Memory retrieval test completed!")
    else:
        logger.error("❌ Memory retrieval test failed!")
