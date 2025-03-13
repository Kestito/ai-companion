"""
Test script for parallel search functionality.

This script tests the parallel search feature that combines vector search from 
Qdrant with keyword search from Supabase.
"""

import os
import asyncio
import time
import logging
from dotenv import load_dotenv

from ai_companion.modules.rag.core.rag_chain import LithuanianRAGChain
from ai_companion.modules.rag.core.vector_store import VectorStoreRetriever

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def test_parallel_search():
    """Test the parallel search functionality."""
    # Initialize the RAG chain
    logger.info("Initializing RAG chain...")
    rag_chain = LithuanianRAGChain(
        collection_name="Information",
        model_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        model_name=os.getenv("LLM_MODEL"),
        embedding_deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
        embedding_model=os.getenv("EMBEDDING_MODEL"),
        temperature=0.3,
        cache_size=100
    )
    
    logger.info("RAG chain initialized successfully")
    
    # Test queries
    test_queries = [
        {
            "query": "Kaip gauti POLA kortelę?",
            "description": "RAG query about obtaining a POLA card"
        },
        {
            "query": "Kas gydomas smegenų vėžys?",
            "description": "RAG query about brain cancer treatment"
        },
        {
            "query": "kaip gauti kompensacija vilniuje",
            "description": "RAG query about compensation in Vilnius"
        },
        {
            "query": "kokios išmokos priklauso sergant vėžiu",
            "description": "RAG query about benefits for cancer patients"
        },
        {
            "query": "kaip kreiptis pagalbos",
            "description": "RAG query about seeking help"
        },
        {
            "query": "krūties vėžio gydymas",
            "description": "RAG query about breast cancer treatment"
        },
        {
            "query": "Koks šiandien oras?",
            "description": "Non-RAG query about current weather"
        },
        {
            "query": "koks tavo vardas",
            "description": "Non-RAG query about the assistant's name"
        }
    ]
    
    # Test direct parallel search
    logger.info("Testing direct parallel search using VectorStoreRetriever...")
    
    # Initialize the vector store retriever
    store = VectorStoreRetriever(
        collection_name="Information",
        embedding_deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
        embedding_model=os.getenv("EMBEDDING_MODEL")
    )
    
    for test_query in test_queries[:2]:  # Test only two queries directly
        query = test_query["query"]
        description = test_query["description"]
        
        logger.info(f"\n\nTesting direct parallel search for: '{query}' - {description}")
        
        # Time the parallel search
        start_time = time.time()
        results = await store.parallel_search(query, k=10, score_threshold=0.5)
        parallel_time = time.time() - start_time
        
        # Time the regular vector search
        start_time = time.time()
        vector_results = await store.similarity_search(query, k=10, score_threshold=0.5)
        vector_time = time.time() - start_time
        
        # Count search types
        vector_sources = sum(1 for doc, _ in results if doc.metadata.get('search_type') == 'vector')
        keyword_sources = sum(1 for doc, _ in results if doc.metadata.get('search_type') == 'keyword')
        
        logger.info(f"Parallel search found {len(results)} documents:")
        logger.info(f"- Vector sources: {vector_sources}")
        logger.info(f"- Keyword sources: {keyword_sources}")
        logger.info(f"- Parallel search time: {parallel_time:.2f} seconds")
        logger.info(f"- Vector-only search time: {vector_time:.2f} seconds")
        logger.info(f"- Performance difference: {(vector_time - parallel_time) * 100 / vector_time:.2f}%")
        
        if len(results) > 0:
            # Show some details of the first result
            first_doc, score = results[0]
            logger.info(f"\nTop result (score: {score:.4f}, source: {first_doc.metadata.get('search_type', 'unknown')}):")
            logger.info(f"Title: {first_doc.metadata.get('title', 'No title')}")
            logger.info(f"Content preview: {first_doc.page_content[:150]}...")
    
    # Test through RAG chain
    logger.info("\n\nTesting RAG chain with parallel search...")
    
    # Process each query
    for test_query in test_queries:
        query = test_query["query"]
        description = test_query["description"]
        
        logger.info(f"\n\nProcessing: '{query}' - {description}")
        
        # Time the query processing
        start_time = time.time()
        
        # Process the query with the RAG chain
        response, docs = await rag_chain.query(
            query=query,
            min_confidence=0.5,
            memory_context=None
        )
        
        query_time = time.time() - start_time
        
        # Count search types
        vector_sources = sum(1 for doc in docs if doc.metadata.get('search_type') == 'vector')
        keyword_sources = sum(1 for doc in docs if doc.metadata.get('search_type') == 'keyword')
        
        logger.info(f"Response generated in {query_time:.2f} seconds")
        logger.info(f"Found {len(docs)} documents:")
        logger.info(f"- Vector sources: {vector_sources}")
        logger.info(f"- Keyword sources: {keyword_sources}")
        
        # Print the response
        logger.info("\nResponse:")
        logger.info(response)
        
        # Small delay between queries to avoid rate limits
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(test_parallel_search()) 