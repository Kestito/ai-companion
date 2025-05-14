import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import our modified vector store
from ai_companion.modules.memory.long_term.vector_store import get_initialized_vector_store

async def main():
    """Test the async initialization of the vector store"""
    logging.info("Starting vector store initialization test")
    
    try:
        # Get an initialized vector store
        vector_store = await get_initialized_vector_store()
        logging.info("Vector store initialized successfully")
        
        # Test collection existence
        collection_name = "test_collection"
        result = await vector_store.ensure_collection(collection_name)
        logging.info(f"Collection {collection_name} ensured: {result}")
        
        # Test a simple search
        if result:
            memories = await vector_store.search_memories(
                "Test query",
                k=3,
                filter_conditions={"test_field": "test_value"}
            )
            logging.info(f"Search returned {len(memories)} results")
        
        logging.info("All tests completed successfully")
        return True
    except Exception as e:
        logging.error(f"Test failed with error: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    asyncio.run(main()) 