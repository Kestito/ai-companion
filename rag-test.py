"""
RAG System Test Script

This script tests each component of the RAG system to identify
where failures may be occurring.
"""

import os
import asyncio
import sys
import time
import traceback
from typing import Dict, Any, List, Optional

# Add color output functions
def print_green(text: str) -> None:
    print(f"\033[92m{text}\033[0m")

def print_yellow(text: str) -> None:
    print(f"\033[93m{text}\033[0m")

def print_red(text: str) -> None:
    print(f"\033[91m{text}\033[0m")

def print_cyan(text: str) -> None:
    print(f"\033[96m{text}\033[0m")

def print_header(text: str) -> None:
    print("\n" + "=" * 50)
    print_cyan(text)
    print("=" * 50)

async def test_query_processor() -> bool:
    """Test the query processor component."""
    print_header("TESTING QUERY PROCESSOR")
    
    try:
        from ai_companion.modules.rag.core.query_preprocessor import LithuanianQueryPreprocessor
        
        processor = LithuanianQueryPreprocessor(
            model_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT"),
            model_name=os.environ.get("LLM_MODEL")
        )
        
        # Test with English query
        print_yellow("Processing English test query...")
        start_time = time.time()
        result = await processor.process_query("What is the capital of Lithuania?")
        duration = time.time() - start_time
        
        print_green(f"English query processing succeeded in {duration:.2f}s")
        print_yellow("Query variations:")
        for variation in result.get("variations", []):
            print(f"  - {variation}")
        
        # Test with Lithuanian query
        print_yellow("\nProcessing Lithuanian test query: 'Kaip gauti pola kortele'...")
        start_time = time.time()
        result_lt = await processor.process_query("Kaip gauti pola kortele")
        duration = time.time() - start_time
        
        print_green(f"Lithuanian query processing succeeded in {duration:.2f}s")
        print_yellow("Query variations:")
        for variation in result_lt.get("variations", []):
            print(f"  - {variation}")
            
        return True
        
    except Exception as e:
        print_red(f"Query processor test failed: {str(e)}")
        print_red(traceback.format_exc())
        return False

async def test_vector_store() -> bool:
    """Test the vector store connection and retrieval."""
    print_header("TESTING VECTOR STORE")
    
    try:
        from ai_companion.modules.rag.core.vector_store import VectorStoreRetriever
        
        print_yellow("Initializing vector store...")
        store = VectorStoreRetriever(
            collection_name="Information",
            embedding_deployment=os.environ.get("AZURE_EMBEDDING_DEPLOYMENT"),
            embedding_model=os.environ.get("EMBEDDING_MODEL")
        )
        
        # Test English query
        print_yellow("Testing vector similarity search with English query...")
        start_time = time.time()
        results = await store.similarity_search(
            query="What is the capital of Lithuania?",
            k=3
        )
        duration = time.time() - start_time
        
        if results:
            print_green(f"English vector search succeeded in {duration:.2f}s, found {len(results)} results")
            print_yellow("First result content preview:")
            print(f"  {results[0][0].page_content[:100]}...")
        else:
            print_yellow(f"English vector search completed in {duration:.2f}s but found no results")
        
        # Test Lithuanian query
        print_yellow("\nTesting vector similarity search with Lithuanian query: 'Kaip gauti pola kortele'...")
        start_time = time.time()
        results_lt = await store.similarity_search(
            query="Kaip gauti pola kortele",
            k=3
        )
        duration = time.time() - start_time
        
        if results_lt:
            print_green(f"Lithuanian vector search succeeded in {duration:.2f}s, found {len(results_lt)} results")
            print_yellow("First result content preview:")
            print(f"  {results_lt[0][0].page_content[:100]}...")
        else:
            print_yellow(f"Lithuanian vector search completed in {duration:.2f}s but found no results")
            
        return True
            
    except Exception as e:
        print_red(f"Vector store test failed: {str(e)}")
        print_red(traceback.format_exc())
        return False

async def test_rag_chain() -> bool:
    """Test the full RAG chain."""
    print_header("TESTING FULL RAG CHAIN")
    
    try:
        from ai_companion.modules.rag.core.rag_chain import get_rag_chain
        
        print_yellow("Initializing RAG chain...")
        rag_chain = get_rag_chain()
        
        # Test English query
        print_yellow("Running English test query through RAG chain...")
        start_time = time.time()
        response, docs = await rag_chain.query(
            query="What is the capital of Lithuania?",
            min_confidence=0.5
        )
        duration = time.time() - start_time
        
        print_green(f"English query RAG chain succeeded in {duration:.2f}s")
        print_yellow(f"Response: {response[:100]}...")
        print_yellow(f"Retrieved {len(docs)} documents")
        
        # Test Lithuanian query
        print_yellow("\nRunning Lithuanian test query through RAG chain: 'Kaip gauti pola kortele'...")
        start_time = time.time()
        response_lt, docs_lt = await rag_chain.query(
            query="Kaip gauti pola kortele",
            min_confidence=0.5
        )
        duration = time.time() - start_time
        
        print_green(f"Lithuanian query RAG chain succeeded in {duration:.2f}s")
        print_yellow(f"Response: {response_lt[:100]}...")
        print_yellow(f"Retrieved {len(docs_lt)} documents")
        
        return True
    
    except Exception as e:
        print_red(f"RAG chain test failed: {str(e)}")
        print_red(traceback.format_exc())
        return False

async def test_qdrant_connection() -> bool:
    """Test direct connection to Qdrant."""
    print_header("TESTING QDRANT CONNECTION")
    
    try:
        import qdrant_client
        from qdrant_client.http import models
        
        qdrant_url = os.environ.get("QDRANT_URL")
        qdrant_api_key = os.environ.get("QDRANT_API_KEY")
        
        if not qdrant_url:
            print_red("QDRANT_URL environment variable not set")
            return False
            
        print_yellow(f"Connecting to Qdrant at {qdrant_url}")
        client = qdrant_client.QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key
        )
        
        print_yellow("Listing collections...")
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        print_green(f"Successfully connected to Qdrant")
        print_yellow(f"Available collections: {', '.join(collection_names)}")
        
        if "Information" in collection_names:
            print_green("Found 'Information' collection")
            
            print_yellow("Checking collection info...")
            collection_info = client.get_collection("Information")
            print_yellow(f"Collection size: {collection_info.vectors_count} vectors")
            
            if collection_info.vectors_count == 0:
                print_red("WARNING: 'Information' collection is empty!")
            else:
                print_green(f"'Information' collection contains {collection_info.vectors_count} documents")
        else:
            print_red("WARNING: 'Information' collection not found!")
            
        return True
        
    except Exception as e:
        print_red(f"Qdrant connection test failed: {str(e)}")
        print_red(traceback.format_exc())
        return False

async def test_embedding_generation() -> bool:
    """Test embedding generation."""
    print_header("TESTING EMBEDDING GENERATION")
    
    try:
        from openai import AzureOpenAI
        
        azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15")
        deployment = os.environ.get("AZURE_EMBEDDING_DEPLOYMENT")
        
        if not azure_endpoint:
            print_red("AZURE_OPENAI_ENDPOINT environment variable not set")
            return False
            
        if not api_key:
            print_red("AZURE_OPENAI_API_KEY environment variable not set")
            return False
            
        if not deployment:
            print_red("AZURE_EMBEDDING_DEPLOYMENT environment variable not set")
            return False
        
        print_yellow(f"Connecting to Azure OpenAI at {azure_endpoint}")
        client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            api_version=api_version
        )
        
        print_yellow(f"Generating embedding using deployment: {deployment}")
        start_time = time.time()
        response = client.embeddings.create(
            input=["This is a test to check if embeddings are working"],
            model=deployment
        )
        duration = time.time() - start_time
        
        embedding = response.data[0].embedding
        
        if len(embedding) > 0:
            print_green(f"Successfully generated embedding with {len(embedding)} dimensions in {duration:.2f}s")
            return True
        else:
            print_red("Empty embedding returned")
            return False
            
    except Exception as e:
        print_red(f"Embedding generation test failed: {str(e)}")
        print_red(traceback.format_exc())
        return False

async def main() -> None:
    """Run all tests and show a summary."""
    print_cyan("\nRAG SYSTEM DIAGNOSTIC TESTS\n")
    
    results = {}
    
    # Test embedding generation first as it's needed for other components
    results["Embedding Generation"] = await test_embedding_generation()
    
    # Test Qdrant connection
    results["Qdrant Connection"] = await test_qdrant_connection()
    
    # Test components
    results["Query Processor"] = await test_query_processor()
    results["Vector Store"] = await test_vector_store()
    results["Full RAG Chain"] = await test_rag_chain()
    
    # Print summary
    print_header("TEST SUMMARY")
    
    all_passed = True
    for test, passed in results.items():
        if passed:
            print_green(f"✓ {test}: PASSED")
        else:
            print_red(f"✗ {test}: FAILED")
            all_passed = False
    
    print("\n")
    if all_passed:
        print_green("All tests passed successfully!")
        print_green("If you're still seeing errors in the application, check the following:")
        print_yellow("1. Are there enough documents in your vector store?")
        print_yellow("2. Do the documents contain relevant information?")
        print_yellow("3. Are there any permission issues or rate limits?")
    else:
        print_red("Some tests failed. Here are recommendations to fix the issues:")
        
        if not results.get("Embedding Generation", True):
            print_yellow("- Check your Azure OpenAI API credentials and embedding model deployment")
            print_yellow("- Verify that the AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, and AZURE_EMBEDDING_DEPLOYMENT environment variables are set correctly")
        
        if not results.get("Qdrant Connection", True):
            print_yellow("- Verify that the QDRANT_URL and QDRANT_API_KEY environment variables are set correctly")
            print_yellow("- Check if your Qdrant instance is running and accessible")
            print_yellow("- Ensure that the 'Information' collection exists")
        
        if not results.get("Query Processor", True):
            print_yellow("- Check if the query processor can connect to the LLM model")
            print_yellow("- Verify that AZURE_OPENAI_DEPLOYMENT and LLM_MODEL environment variables are set correctly")
        
        if not results.get("Vector Store", True):
            print_yellow("- Check if the vector store can access the embeddings model")
            print_yellow("- Verify that EMBEDDING_MODEL environment variable is set correctly")
        
        if not results.get("Full RAG Chain", True):
            print_yellow("- Review error messages from the previous tests to identify component failures")
            print_yellow("- Check if all components are properly initialized and connected")

if __name__ == "__main__":
    asyncio.run(main()) 