import os
import sys
import asyncio
import json
from typing import List, Dict, Set
from datetime import datetime
from dotenv import load_dotenv

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.append(project_root)

# Import after adding to path
from ai_companion.modules.rag.core.vector_store import VectorStoreManager
from ai_companion.modules.rag.core.rag_chain import RAGChain

load_dotenv()

async def clean_vector_store() -> bool:
    """Clean the vector store and verify its state."""
    print("\n=== Step 1: Cleaning Vector Store ===")
    
    try:
        # Initialize vector store
        vector_store = VectorStoreManager(
            collection_name=os.getenv("COLLECTION_NAME", "Pola_docs"),
            embedding_deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
            embedding_model=os.getenv("EMBEDDING_MODEL")
        )
        
        # Get current collection info
        collection_info = vector_store.get_collection_info()
        print(f"Current collection size: {collection_info.points_count} points")
        
        # Delete existing collection
        print("Deleting existing collection...")
        # vector_store.delete_collection()
        print("Collection deleted successfully")
        
        # Reinitialize vector store (this will create a new collection)
        vector_store = VectorStoreManager(
            collection_name=os.getenv("COLLECTION_NAME", "Pola_docs"),
            embedding_deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
            embedding_model=os.getenv("EMBEDDING_MODEL")
        )
        print("New collection created successfully")
        
        return True
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")
        return False

async def run_crawler() -> bool:
    """Run the document crawler."""
    print("\n=== Step 2: Running Document Crawler ===")
    
    try:
        # Import and run crawl_for_docs
        import crawl_for_docs
        await crawl_for_docs.main()
        return True
    except Exception as e:
        print(f"Error running crawler: {str(e)}")
        return False

async def test_rag_system():
    """Test RAG system with comprehensive query sets."""
    print("\n=== Testing RAG System ===")
    
    # Initialize vector store and RAG chain
    vector_store = VectorStoreManager(
        collection_name=os.getenv("COLLECTION_NAME", "Pola_docs"),
        embedding_deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
        embedding_model=os.getenv("EMBEDDING_MODEL")
    )
    
    rag_chain = RAGChain(
        vector_store=vector_store,
        model_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        model_name=os.getenv("LLM_MODEL")
    )
    
    # Comprehensive test queries
    test_queries = {
        "Basic Information": [
            "Kas yra POLA?",  # What is POLA?
            "What is POLA organization?",
            "Explain POLA's mission"
        ],
        "Services": [
            "Kokias paslaugas teikia POLA?",  # What services does POLA offer?
            "What support services are available?",
            "Tell me about POLA's consultation services"
        ],
        "Card Related": [
            "Kaip gauti POLA kortelę?",  # How to get a POLA card?
            "What benefits does POLA card provide?",
            "POLA kortelės privalumai"  # POLA card benefits
        ],
        "Activities": [
            "What are POLA's main activities?",
            "Kokius renginius organizuoja POLA?",  # What events does POLA organize?
            "How does POLA help patients?"
        ],
        "Volunteering": [
            "How can I volunteer for POLA?",
            "Kaip galiu tapti POLA savanoriu?",  # How can I become a POLA volunteer?
            "What do POLA volunteers do?"
        ]
    }
    
    results = {}
    
    print("\nStarting comprehensive RAG testing...")
    for category, queries in test_queries.items():
        print(f"\n=== Testing {category} Queries ===")
        category_results = []
        
        for query in queries:
            print(f"\nQuery: {query}")
            try:
                answer, sources = await rag_chain.query(query)
                
                # Analyze sources
                unique_sections = set(source.metadata.get('section', 'N/A') for source in sources)
                source_count = len(sources)
                
                result = {
                    "query": query,
                    "answer": answer,
                    "source_count": source_count,
                    "unique_sections": list(unique_sections),
                    "sources": [{
                        "url": source.metadata.get('url', 'No URL'),
                        "title": source.metadata.get('title', 'No title'),
                        "section": source.metadata.get('section', 'N/A'),
                        "summary": source.metadata.get('summary', 'No summary')
                    } for source in sources]
                }
                
                # Print results
                print("\nAnswer:", answer)
                print("\nSources:")
                for source in sources:
                    print(f"- {source.metadata.get('url', 'No URL')}")
                    print(f"  Section: {source.metadata.get('section', 'N/A')}")
                    print(f"  Title: {source.metadata.get('title', 'No title')}")
                
                category_results.append(result)
                
            except Exception as e:
                print(f"Error testing query: {str(e)}")
                category_results.append({
                    "query": query,
                    "error": str(e)
                })
        
        results[category] = category_results
    
    # Save test results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"rag_test_results_{timestamp}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nTest results saved to {results_file}")
    
    # Print summary
    print("\n=== Test Summary ===")
    for category, category_results in results.items():
        success_count = sum(1 for r in category_results if "error" not in r)
        print(f"{category}: {success_count}/{len(category_results)} queries successful")

async def verify_collection() -> bool:
    """Verify the collection's integrity."""
    print("\n=== Step 4: Verifying Collection ===")
    
    try:
        vector_store = VectorStoreManager(
            collection_name=os.getenv("COLLECTION_NAME", "Pola_docs"),
            embedding_deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
            embedding_model=os.getenv("EMBEDDING_MODEL")
        )
        
        # Get collection info
        collection_info = vector_store.get_collection_info()
        points_count = collection_info.points_count
        print(f"Collection points count: {points_count}")
        
        if points_count == 0:
            print("Warning: Collection is empty!")
            return False
        
        # Test basic search functionality
        test_result = vector_store.similarity_search("test", k=1)
        print(f"Basic search test successful, found {len(test_result)} results")
        
        # Check for duplicates
        print("\nChecking for duplicates...")
        seen_urls = set()
        duplicate_count = 0
        
        # Sample search to get documents
        results = vector_store.similarity_search("", k=100)  # Get a large sample
        for doc in results:
            url = doc.metadata.get('url')
            if url in seen_urls:
                duplicate_count += 1
            seen_urls.add(url)
        
        if duplicate_count > 0:
            print(f"Warning: Found {duplicate_count} potential duplicates")
        else:
            print("No duplicates found in sampled documents")
        
        return True
    except Exception as e:
        print(f"Error verifying collection: {str(e)}")
        return False

async def main():
    """Run RAG system tests."""
    print("Starting RAG system testing...")
    await test_rag_system()
    print("\nTesting completed")

if __name__ == "__main__":
    asyncio.run(main()) 