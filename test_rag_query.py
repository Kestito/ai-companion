"""
Test script for RAG queries to verify fixed embedding functionality.
"""

import asyncio
import logging
from ai_companion.modules.rag.core.vector_store import VectorStoreRetriever
from ai_companion.settings import settings
from qdrant_client import QdrantClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_rag_query():
    """Test a real RAG query."""
    logger.info("Testing RAG query with fixed embedding functionality")

    # New API key that works
    new_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.cdTvd4mc74giwx-ypkE8t4muYvpQqLqkc5P6IXuJAOw"

    try:
        # Initialize vector store retriever
        retriever = VectorStoreRetriever(
            collection_name="Information",
            embedding_deployment=settings.AZURE_EMBEDDING_DEPLOYMENT,
            embedding_model=settings.FALLBACK_EMBEDDING_MODEL,
        )

        # Replace the Qdrant client with one using the new API key
        retriever.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=new_api_key,
            timeout=60,
            check_compatibility=False,
        )

        # Test a simple query
        query = "Kas yra POLA kortelė?"
        logger.info(f"Testing query: '{query}'")

        # Run the query using similarity search
        results = await retriever.similarity_search(
            query=query, k=3, score_threshold=0.5
        )

        # Log results
        logger.info(f"Found {len(results)} results")
        for i, (doc, score) in enumerate(results):
            logger.info(f"Result {i+1} - Score: {score:.4f}")
            logger.info(f"Content: {doc.page_content[:150]}...")
            logger.info(f"Metadata: {doc.metadata}")
            logger.info("-" * 50)

        logger.info("RAG query test completed successfully")

    except Exception as e:
        logger.error(f"Error in RAG query test: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(test_rag_query())
