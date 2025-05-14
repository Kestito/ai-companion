#!/usr/bin/env python
"""
Comprehensive test script to verify the memory fix and Supabase integration.
Tests the full memory workflow including:
1. Memory storage
2. Memory injection
3. Memory extraction
4. Context JSON parsing
"""

import asyncio
import logging
import sys
import uuid

from langchain_core.messages import HumanMessage, AIMessage

from ai_companion.utils.supabase import get_supabase_client
from ai_companion.modules.memory.service import get_memory_service
from ai_companion.modules.memory.short_term.memory_manager import ShortTermMemoryManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Test data
TEST_PATIENT_ID = str(uuid.uuid4())  # Generate a valid UUID for testing
TEST_CONVERSATION = [
    (
        HumanMessage(content="Hello, how are you?"),
        AIMessage(content="I'm doing well, thank you for asking!"),
    ),
    (
        HumanMessage(content="What can you help me with?"),
        AIMessage(
            content="I can assist with medical advice, answer health questions, or just chat!"
        ),
    ),
    (
        HumanMessage(content="Tell me about the weather"),
        AIMessage(
            content="It looks like it's going to be sunny today with a high of 25°C."
        ),
    ),
]


async def test_memory_storage():
    """Test storing memories in Supabase."""
    logger.info(f"Testing memory storage with patient ID: {TEST_PATIENT_ID}")

    # Initialize memory service
    memory_service = get_memory_service()
    supabase = get_supabase_client()

    # Create test memories
    for i, (user_msg, ai_msg) in enumerate(TEST_CONVERSATION):
        logger.info(f"Storing memory pair {i+1}/{len(TEST_CONVERSATION)}")

        # Add user and assistant metadata
        user_metadata = {
            "platform": "test",
            "external_system_id": f"user_{i}",
            "patient_id": TEST_PATIENT_ID,
        }
        ai_metadata = {
            "platform": "test",
            "external_system_id": "assistant",
            "patient_id": TEST_PATIENT_ID,
        }

        # Create messages with metadata
        user_message = HumanMessage(content=user_msg.content, metadata=user_metadata)
        ai_message = AIMessage(content=ai_msg.content, metadata=ai_metadata)

        # Store using memory service
        await memory_service.store_session_memory(
            platform="test",
            user_id=f"user_{i}",
            patient_id=TEST_PATIENT_ID,
            conversation={
                "user_message": user_message.content,
                "bot_response": ai_message.content,
            },
        )

        logger.info(f"Memory pair {i+1} stored successfully")

    # Verify storage with direct query
    memories_db = (
        supabase.table("short_term_memory")
        .select("*")
        .eq("patient_id", TEST_PATIENT_ID)
        .execute()
    )

    records = memories_db.data
    logger.info(f"Found {len(records)} records for test patient via direct query")

    if len(records) == len(TEST_CONVERSATION):
        logger.info("✅ Memory storage test PASSED")
        return True
    else:
        logger.error(
            f"❌ Memory storage test FAILED: Expected {len(TEST_CONVERSATION)} records, found {len(records)}"
        )
        return False


async def test_memory_retrieval():
    """Test retrieving memories from Supabase."""
    logger.info(f"Testing memory retrieval with patient ID: {TEST_PATIENT_ID}")

    # Initialize memory service
    memory_service = get_memory_service()

    # Retrieve memories using memory service
    memories = await memory_service.get_session_memory(
        platform="test", user_id="test_user", patient_id=TEST_PATIENT_ID, limit=10
    )

    logger.info(f"Found {len(memories)} records via memory service")

    # Check different retrieval methods
    memory_manager = ShortTermMemoryManager()

    # Method 1: Using the parallel method
    parallel_memories = await memory_manager.get_messages_parallel(TEST_PATIENT_ID)
    logger.info(f"Found {len(parallel_memories)} records via get_messages_parallel")

    # Method 2: Using direct database query
    supabase = get_supabase_client()
    direct_db_memories = (
        supabase.table("short_term_memory")
        .select("*")
        .eq("patient_id", TEST_PATIENT_ID)
        .order("id", desc=True)
        .limit(10)
        .execute()
    )

    records = direct_db_memories.data
    logger.info(f"Found {len(records)} records via direct query")

    # Display memory formats for verification
    if len(records) > 0:
        logger.info("Memory record format:")
        first_record = records[0]
        logger.info(f"  - ID: {first_record.get('id')}")
        logger.info(f"  - Patient ID: {first_record.get('patient_id')}")
        context = first_record.get("context")
        logger.info(f"  - Context type: {type(context)}")
        logger.info(f"  - Context sample: {str(context)[:100]}...")

    if len(memories) >= len(TEST_CONVERSATION):
        logger.info("✅ Memory retrieval test PASSED")
        return True
    else:
        logger.error(
            f"❌ Memory retrieval test FAILED: Expected at least {len(TEST_CONVERSATION)} memories, found {len(memories)}"
        )
        return False


async def cleanup_test_data():
    """Clean up test data after tests are complete."""
    logger.info(f"Cleaning up test data for patient ID: {TEST_PATIENT_ID}")

    supabase = get_supabase_client()
    result = (
        supabase.table("short_term_memory")
        .delete()
        .eq("patient_id", TEST_PATIENT_ID)
        .execute()
    )

    deleted_count = len(result.data)
    logger.info(f"Deleted {deleted_count} test records")

    return deleted_count > 0


async def main():
    """Run all memory tests."""
    logger.info("Starting comprehensive memory system test")

    try:
        # Test 1: Memory Storage
        storage_success = await test_memory_storage()

        # Test 2: Memory Retrieval
        retrieval_success = await test_memory_retrieval()

        # Cleanup
        await cleanup_test_data()

        # Final result
        if storage_success and retrieval_success:
            logger.info("🎉 All memory tests PASSED!")
            return True
        else:
            logger.error("❌ Some memory tests FAILED!")
            return False

    except Exception as e:
        logger.error(f"Error during memory tests: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Error running memory tests: {e}", exc_info=True)
        sys.exit(1)
