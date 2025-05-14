"""
Test script to verify the async/await functionality in the AI companion's memory system.
This script tests if all async functions are properly awaited.
"""

import asyncio
import logging
import uuid
from datetime import datetime

from langchain_core.messages import HumanMessage

from ai_companion.modules.memory.long_term.memory_manager import get_memory_manager
from ai_companion.modules.rag.core.vector_store import VectorStoreRetriever


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_memory_manager():
    """Test memory manager async functions."""
    logger.info("Testing MemoryManager async functions")

    # Initialize memory manager
    memory_manager = get_memory_manager()

    # Generate a test patient ID
    test_patient_id = str(uuid.uuid4())

    # Create test metadata
    metadata = {
        "patient_id": test_patient_id,
        "platform": "test",
        "external_system_id": "12345",
        "timestamp": datetime.now().isoformat(),
    }

    # Test add_memory
    logger.info("Testing add_memory function")
    try:
        result = await memory_manager.add_memory(
            "This is a test memory for coroutine fix", metadata
        )
        logger.info(f"Memory add result: {result}")
    except Exception as e:
        logger.error(f"Error in add_memory: {e}", exc_info=True)

    # Test get_relevant_memories
    logger.info("Testing get_relevant_memories function")
    try:
        memories = await memory_manager.get_relevant_memories(
            "Test query for memory retrieval", test_patient_id
        )
        logger.info(f"Retrieved {len(memories)} memories")
    except Exception as e:
        logger.error(f"Error in get_relevant_memories: {e}", exc_info=True)

    # Test extract_and_store_memories
    logger.info("Testing extract_and_store_memories function")
    try:
        test_message = HumanMessage(
            content="This is a test message for memory extraction", metadata=metadata
        )
        await memory_manager.extract_and_store_memories(test_message)
        logger.info("extract_and_store_memories completed")
    except Exception as e:
        logger.error(f"Error in extract_and_store_memories: {e}", exc_info=True)


async def test_vector_store():
    """Test vector store async functions."""
    logger.info("Testing VectorStoreRetriever async functions")

    # Initialize vector store
    vector_store = VectorStoreRetriever()

    # Test embedding generation
    logger.info("Testing _get_embedding function")
    try:
        embedding = await vector_store._get_embedding(
            "Test text for embedding generation"
        )
        logger.info(f"Generated embedding with {len(embedding)} dimensions")
    except Exception as e:
        logger.error(f"Error in _get_embedding: {e}", exc_info=True)

    # Test similarity search
    logger.info("Testing similarity_search function")
    try:
        results = await vector_store.similarity_search(
            "Test query for similarity search"
        )
        logger.info(f"Similarity search returned {len(results)} results")
    except Exception as e:
        logger.error(f"Error in similarity_search: {e}", exc_info=True)

    # Test search memories
    logger.info("Testing search_memories function")
    try:
        memories = await vector_store.search_memories("Test query for memory search")
        logger.info(f"Memory search returned {len(memories)} results")
    except Exception as e:
        logger.error(f"Error in search_memories: {e}", exc_info=True)


async def main():
    """Run all tests."""
    logger.info("Starting coroutine fix verification tests")

    try:
        await test_memory_manager()
        await test_vector_store()
        logger.info("All tests completed")
    except Exception as e:
        logger.error(f"Error in test execution: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
