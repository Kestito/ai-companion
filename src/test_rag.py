import asyncio
import logging
from ai_companion.modules.rag.core.rag_chain import get_rag_chain

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rag():
    # Initialize RAG chain
    rag_chain = get_rag_chain()
    print(f"RAG chain initialized with collection: {rag_chain.store.collection_name}")
    
    # Test queries - RAG questions and non-RAG questions
    test_queries = [
        # RAG questions
        {"query": "kaip gauti pola kortele", "description": "RAG question about getting POLA card"},
        {"query": "Kas gydomas smegenu vezys", "description": "RAG question about brain cancer treatment"},
        {"query": "kaip gauti kompensacija vilniuje", "description": "RAG question about compensation in Vilnius"},
        {"query": "kokios ismokos prklauso segant veziu vln", "description": "RAG question about benefits for cancer patients in Vilnius"},
        {"query": "as iekau pagalbus", "description": "RAG question about seeking help"},
        {"query": "kaip gydomas kruties vezys", "description": "RAG question about breast cancer treatment"},
        
        # Non-RAG questions
        {"query": "koks dabar orgas", "description": "Non-RAG question about current weather"},
        {"query": "koks tavo vardas", "description": "Non-RAG question about assistant's name"},
        {"query": "koks dabar horoskopas", "description": "Non-RAG question about horoscope"},
        {"query": "kaip tu jauties", "description": "Non-RAG question about assistant's feelings"}
    ]
    
    min_confidence = 0.5
    
    for test_case in test_queries:
        query = test_case["query"]
        description = test_case["description"]
        
        print("\n" + "="*80)
        print(f"TESTING: {description}")
        print(f"QUERY: {query}")
        print("="*80)
        
        try:
            print(f"Querying with min_confidence={min_confidence}")
            response, docs = await rag_chain.query(query, min_confidence=min_confidence)
            
            print(f"\nRESPONSE:")
            print("-"*40)
            print(response)
            print("-"*40)
            
            print(f"\nFound {len(docs)} documents")
            
            # Print document snippets
            if docs:
                print("\nTOP DOCUMENTS:")
                for i, doc in enumerate(docs[:3]):  # Show top 3 docs max
                    print(f"\nDocument {i+1}: {doc.page_content[:150]}...")
                    if hasattr(doc, 'metadata') and doc.metadata:
                        print(f"Score: {doc.metadata.get('score', 'N/A')}")
                        print(f"Title: {doc.metadata.get('title', 'N/A')}")
            else:
                print("\nNo documents retrieved.")
                
            print(f"\nTEST RESULT: {'SUCCESS' if response else 'FAILURE'}")
        
        except Exception as e:
            print(f"\nERROR during RAG query: {e}")
            print(f"TEST RESULT: FAILURE")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rag()) 