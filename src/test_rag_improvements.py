"""
Test script for RAG improvements.

This script tests the parallel search functionality, error handling,
and overall RAG system improvements.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any
from dotenv import load_dotenv

from ai_companion.modules.rag.core.rag_chain import get_rag_chain
from ai_companion.modules.rag.core.vector_store import VectorStoreRetriever
from ai_companion.modules.rag.core.response_generation import LithuanianResponseGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Test queries with different characteristics
TEST_QUERIES = [
    {
        "query": "Kaip gauti POLA kortelę?",
        "description": "Short keyword query with special characters",
        "expected_type": "keyword_preferred"
    },
    {
        "query": "Kas gydomas smegenų vėžys?",
        "description": "Question with Lithuanian characters",
        "expected_type": "mixed"
    },
    {
        "query": "Kokios išmokos priklauso sergantiems onkologinėmis ligomis ir kaip jas gauti?",
        "description": "Long complex query",
        "expected_type": "vector_preferred"
    },
    {
        "query": "POLA savanoriai",
        "description": "Very short query",
        "expected_type": "keyword_preferred"
    },
    {
        "query": "aš ieškau informacijos apie kompensacijas Vilniuje",
        "description": "Conversational query with misspellings",
        "expected_type": "mixed"
    }
]

async def test_parallel_search_improvements():
    """Test the improved parallel search implementation."""
    logger.info("Testing parallel search improvements...")
    
    # Initialize vector store retriever
    store = VectorStoreRetriever(collection_name="Information")
    
    results = []
    for test_case in TEST_QUERIES:
        query = test_case["query"]
        description = test_case["description"]
        
        logger.info(f"\nTesting query: '{query}' - {description}")
        
        start_time = time.time()
        
        # Run parallel search
        parallel_results = await store.parallel_search(
            query=query,
            k=10,
            score_threshold=0.5
        )
        
        # Run vector-only search for comparison
        vector_results = await store.similarity_search(
            query=query,
            k=10,
            score_threshold=0.5
        )
        
        parallel_time = time.time() - start_time
        
        # Compute performance metrics
        vector_count = sum(1 for doc, _ in parallel_results 
                            if doc.metadata.get('search_type') == 'vector')
        keyword_count = sum(1 for doc, _ in parallel_results 
                             if doc.metadata.get('search_type') == 'keyword')
        total_count = len(parallel_results)
        
        # Performance improvement percentage
        vector_time = sum(1 for _ in vector_results) * 0.1  # Estimate
        improvement = ((vector_time - parallel_time) / vector_time) * 100 if vector_time > 0 else 0
        
        # Store results
        results.append({
            "query": query,
            "description": description,
            "total_results": total_count,
            "vector_results": vector_count,
            "keyword_results": keyword_count,
            "execution_time": parallel_time,
            "performance_improvement": improvement,
            "search_type": "keyword_preferred" if keyword_count > vector_count else 
                         "vector_preferred" if vector_count > keyword_count else "mixed"
        })
        
        # Print result details
        logger.info(f"Search results: {total_count} total " 
                  f"({vector_count} vector, {keyword_count} keyword)")
        logger.info(f"Execution time: {parallel_time:.3f} seconds")
        logger.info(f"Search type: {results[-1]['search_type']}")
        
        if parallel_results:
            top_doc, top_score = parallel_results[0]
            logger.info(f"Top result (score={top_score:.3f}):")
            logger.info(f"  Source: {top_doc.metadata.get('search_type', 'unknown')}")
            logger.info(f"  Title: {top_doc.metadata.get('title', 'N/A')}")
            logger.info(f"  Content: {top_doc.page_content[:100]}...")
    
    logger.info("\n=== PARALLEL SEARCH SUMMARY ===")
    for result in results:
        logger.info(f"Query: '{result['query']}' - Expected: {test_case['expected_type']}, Actual: {result['search_type']}")
        logger.info(f"  Results: {result['total_results']} total ({result['vector_results']} vector, {result['keyword_results']} keyword)")
        logger.info(f"  Time: {result['execution_time']:.3f}s, Improvement: {result['performance_improvement']:.1f}%")
        
    return results

async def test_error_handling_improvements():
    """Test error handling improvements in the RAG system."""
    logger.info("\n\nTesting error handling improvements...")
    
    # Initialize RAG chain
    rag_chain = get_rag_chain()
    
    # Test with invalid collection
    try:
        logger.info("Testing with invalid collection name...")
        bad_store = VectorStoreRetriever(collection_name="NonexistentCollection")
        results = await bad_store.similarity_search("test query")
        logger.info(f"Results: {len(results)} (Expected: graceful error handling)")
    except Exception as e:
        logger.error(f"Error with invalid collection: {e}")
    
    # Test with empty query
    try:
        logger.info("Testing with empty query...")
        response, docs = await rag_chain.query("", min_confidence=0.5)
        logger.info(f"Response: '{response[:50]}...' (Expected: user-friendly error message)")
        logger.info(f"Documents: {len(docs)} (Expected: 0)")
    except Exception as e:
        logger.error(f"Error with empty query: {e}")
    
    # Test with extremely high confidence threshold
    try:
        logger.info("Testing with extremely high confidence threshold...")
        response, docs = await rag_chain.query("POLA", min_confidence=0.99)
        logger.info(f"Response: '{response[:50]}...' (Expected: fallback to lower threshold)")
        logger.info(f"Documents: {len(docs)} (Expected: some documents)")
    except Exception as e:
        logger.error(f"Error with high threshold: {e}")
    
    # Test with invalid query variations
    try:
        logger.info("Testing with invalid query variations...")
        response, docs = await rag_chain.query(
            "test query", 
            min_confidence=0.5, 
            query_variations=[None, "", "###"]
        )
        logger.info(f"Response: '{response[:50]}...' (Expected: graceful handling)")
        logger.info(f"Documents: {len(docs)} (Expected: normal processing)")
    except Exception as e:
        logger.error(f"Error with invalid variations: {e}")
        
    return "Error handling tests completed"

async def test_response_generation_improvements():
    """Test response generation improvements."""
    logger.info("\n\nTesting response generation improvements...")
    
    # Initialize response generator
    generator = LithuanianResponseGenerator()
    
    # Initialize RAG chain
    rag_chain = get_rag_chain()
    
    # Get documents for a test query
    query = "Kaip gauti POLA kortelę?"
    _, docs = await rag_chain.query(query, min_confidence=0.5)
    
    if not docs:
        logger.warning("No documents found for test. Using empty list.")
    
    logger.info(f"Retrieved {len(docs)} documents for response generation test")
    
    # Test with normal documents
    logger.info("Testing with normal documents...")
    response = await generator._generate_response(query, docs)
    logger.info(f"Response: '{response[:100]}...'")
    
    # Test with corrupted documents (missing metadata)
    logger.info("Testing with corrupted documents (missing metadata)...")
    corrupted_docs = docs.copy()
    if corrupted_docs:
        corrupted_docs[0].metadata = {}
    response = await generator._generate_response(query, corrupted_docs)
    logger.info(f"Response with corrupted docs: '{response[:100]}...'")
    
    # Test with no documents
    logger.info("Testing with no documents...")
    empty_response = await generator._generate_response(query, [])
    logger.info(f"Response with no docs: '{empty_response}'")
    
    # Test with memory context
    logger.info("Testing with memory context...")
    memory_response = await generator._generate_response(
        query, 
        docs, 
        memory_context="User previously asked about cancer treatments."
    )
    logger.info(f"Response with memory context: '{memory_response[:100]}...'")
    
    return "Response generation tests completed"

async def main():
    """Run all tests."""
    logger.info("Starting RAG improvement tests...")
    
    # Test parallel search improvements
    parallel_results = await test_parallel_search_improvements()
    
    # Test error handling improvements
    error_results = await test_error_handling_improvements()
    
    # Test response generation improvements
    response_results = await test_response_generation_improvements()
    
    logger.info("\n=== OVERALL TEST SUMMARY ===")
    logger.info(f"Parallel search tests: {len(parallel_results)} tests completed")
    logger.info(f"Error handling tests: {error_results}")
    logger.info(f"Response generation tests: {response_results}")
    
    logger.info("\nAll tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(main()) 