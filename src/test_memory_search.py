#!/usr/bin/env python
"""
Test script for memory search functionality with Supabase.
Validates that memory retrieval works correctly for different patient records.
"""

import asyncio
import logging
import json

from ai_companion.utils.supabase import get_supabase_client
from ai_companion.modules.memory.service import get_memory_service

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_memory_search():
    """Test memory search functionality using Supabase."""
    logger.info("Starting memory search test")

    # Initialize memory service
    memory_service = get_memory_service()
    supabase = get_supabase_client()

    # Test patient IDs
    patients = [
        "38592401-8cc1-4559-9a14-ef146e1aa4ea",  # Patient with proper JSON data
        "ee0b625d-a5d7-4c6d-8179-28a9c1b548fc",  # Patient with number as context
    ]

    for patient_id in patients:
        logger.info(f"\n===== Testing memory search for patient {patient_id} =====")

        # Test direct database query
        logger.info("Testing direct database query")
        memories_db = (
            supabase.table("short_term_memory")
            .select("*")
            .eq("patient_id", patient_id)
            .order("id", desc=True)
            .limit(5)
            .execute()
        )

        records = memories_db.data
        logger.info(f"Found {len(records)} records via direct query")

        if records:
            # Show first record structure
            first_record = records[0]
            logger.info(f"Record ID: {first_record.get('id')}")
            logger.info(f"Context type: {type(first_record.get('context'))}")
            logger.info(f"Context preview: {str(first_record.get('context'))[:100]}")

            # Test context extraction
            try:
                context = first_record.get("context")
                if isinstance(context, dict):
                    logger.info("Context is already a dictionary")
                    content = context.get("content", "")
                elif isinstance(context, str):
                    logger.info("Context is a string, attempting to parse as JSON")
                    context_dict = json.loads(context)
                    content = context_dict.get("content", "")
                elif isinstance(context, (int, float)):
                    logger.info(f"Context is a {type(context).__name__}: {context}")
                    content = str(context)
                else:
                    logger.info(f"Unknown context type: {type(context)}")
                    content = str(context)

                logger.info(f"Extracted content: {content[:100]}")
            except Exception as e:
                logger.warning(f"Error extracting context: {e}")

        # Test memory service
        logger.info("\nTesting memory service get_session_memory")
        memories = await memory_service.get_session_memory(
            platform="test", user_id="test_user", patient_id=patient_id, limit=5
        )

        logger.info(f"Found {len(memories)} records via memory service")
        if memories:
            logger.info(f"Memory format: {memories[0][:100]}")

        # Test with non-existent patient
        logger.info("\nTesting with non-existent patient")
        fake_patient = "00000000-0000-0000-0000-000000000000"
        fake_memories = await memory_service.get_session_memory(
            platform="test", user_id="test_user", patient_id=fake_patient, limit=5
        )
        logger.info(f"Found {len(fake_memories)} records for non-existent patient")

    logger.info("\nMemory search test completed successfully")


if __name__ == "__main__":
    asyncio.run(test_memory_search())
