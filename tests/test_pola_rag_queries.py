import pytest
from pathlib import Path
import tempfile
from typing import Generator, AsyncGenerator
import time
import asyncio
import logging
import json
from datetime import datetime
from asyncio import TimeoutError

from ai_companion.modules.rag.core.document_processor import DocumentProcessor
from ai_companion.modules.rag.core.vector_store import VectorStoreManager
from ai_companion.modules.rag.core.rag_chain import RAGChain

# Configure logging with both file and console output
log_dir = Path("tests/logs")
log_dir.mkdir(exist_ok=True)
log_filename = log_dir / "pola_test_results.log"

# Remove any existing handlers
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# POLA-specific content
POLA_CONTENT = """
Pagalbos onkologiniams ligoniams asociacija (POLA)

POLA kortelė - tai speciali kortelė onkologiniams pacientams:

Gavimas:
- Kortelę gali gauti bet kuris fizinis asmuo su onkologine diagnoze
- Pirmą kartą išduodama nemokamai
- Reikia tik susimokėti už siuntimo paslaugas
- Būtina užpildyti kortelės paraišką

Nuolaidos ir privilegijos:
- 80% nuolaida viešajam transportui visoje Lietuvoje (nuo 2021 m.)
- Nuolaidos vaistinėse
- Specialios kainos medicinos paslaugoms
- Psichologinė pagalba

Statistika:
- Kasmet Lietuvoje vėžiu suserga virš 18 000 žmonių
- Apie 110 000 žmonių gauna aktyvų gydymą
- POLA turi virš 50 000 kortelių turėtojų

Tikslai:
- Pagerinti onkologinių pacientų gyvenimo kokybę
- Sumažinti finansinę naštą
- Suteikti emocinę paramą
- Užtikrinti informacijos prieinamumą

Papildomos paslaugos:
- Nemokamos konsultacijos
- Pagalba gaunant kompensacijas
- Informacija apie gydymo galimybes
- Bendruomenės palaikymas
"""

@pytest.fixture(scope="module")
def temp_dir() -> Generator[str, None, None]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir

@pytest.fixture(scope="module")
async def setup_rag_environment(temp_dir) -> AsyncGenerator:
    """Setup RAG environment with timeout protection"""
    try:
        async with asyncio.timeout(30):  # 30 seconds timeout for setup
            document_processor = DocumentProcessor(
                chunk_size=500,
                chunk_overlap=50,
                base_dir=temp_dir
            )
            
            # Create and process test file
            file_path = Path(temp_dir) / "pola_info.txt"
            file_path.write_text(POLA_CONTENT, encoding='utf-8')
            
            # Setup vector store
            collection_name = f"test_pola_queries_{int(time.time())}"
            vector_store = VectorStoreManager(collection_name=collection_name)
            
            # Process and store documents
            documents = document_processor.process_file(str(file_path))
            vector_store.add_documents(documents)
            
            # Create RAG chain
            rag_chain = RAGChain(
                vector_store=vector_store,
                prompt_template="""Based on the following context about POLA organization, answer the question directly and precisely in Lithuanian. 
                If numbers or specific details are mentioned in the context, include them in your answer.
                If you don't know the answer based on the context, just say that you don't know.
                
                Context: {context}
                
                Question: {question}
                Answer: """
            )
            
            await asyncio.sleep(2)  # Wait for indexing
            
            yield (document_processor, vector_store, rag_chain, str(file_path))
            
            # Cleanup
            try:
                vector_store.delete_collection()
            except Exception as e:
                logging.error(f"Error during cleanup: {e}")
    except TimeoutError:
        logging.error("Setup timed out after 30 seconds")
        raise
    except Exception as e:
        logging.error(f"Error during setup: {e}")
        raise

async def execute_query_with_timeout(rag_chain, query: str, timeout: int = 10):
    """Execute a single query with timeout"""
    try:
        print(f"Executing query (timeout: {timeout}s): {query}")
        async with asyncio.timeout(timeout):
            return await rag_chain.query(query)
    except TimeoutError:
        print(f"Query timed out after {timeout} seconds")
        logger.error(f"Query timed out after {timeout} seconds: {query}")
        return f"Query timed out after {timeout} seconds", []
    except Exception as e:
        print(f"Error executing query: {e}")
        logger.error(f"Error executing query: {e}")
        return str(e), []

@pytest.mark.asyncio
async def test_pola_queries(setup_rag_environment):
    """Test both RAG and non-RAG queries with POLA-specific scenarios."""
    print("\nStarting POLA RAG testing...")
    
    try:
        async with asyncio.timeout(15):  # 15 seconds timeout for setup
            env = await anext(setup_rag_environment)
            document_processor, vector_store, rag_chain, test_file = env
    except TimeoutError:
        print("Setup timed out after 15 seconds")
        logger.error("Setup timed out after 15 seconds")
        raise
    except Exception as e:
        print(f"Setup error: {e}")
        logger.error(f"Setup error: {e}")
        raise
    
    logger.info("RAG environment setup completed")
    print("RAG environment setup completed")

    # Test cases combining RAG and non-RAG queries
    test_cases = [
        # RAG-based queries (information present in the context)
        {
            "query": "Kas gali gauti POLA kortelę?",
            "expected_keywords": ["fizinis asmuo", "onkologine diagnoze", "nemokamai"],
            "is_rag": True
        },
        {
            "query": "Kokia nuolaida taikoma viešajam transportui su POLA kortele?",
            "expected_keywords": ["80%", "viešajam transportui", "Lietuvoje"],
            "is_rag": True
        },
        {
            "query": "Kiek žmonių Lietuvoje serga vėžiu ir gauna gydymą?",
            "expected_keywords": ["18 000", "110 000", "aktyvų gydymą"],
            "is_rag": True
        },
        {
            "query": "Kokie yra pagrindiniai POLA tikslai?",
            "expected_keywords": ["gyvenimo kokybę", "finansinę naštą", "emocinę paramą"],
            "is_rag": True
        },
        {
            "query": "Kokias papildomas paslaugas teikia POLA?",
            "expected_keywords": ["konsultacijos", "kompensacijas", "informacija", "bendruomenės"],
            "is_rag": True
        },
    
        # Generic non-RAG queries (completely unrelated to POLA)
        {
            "query": "Koks yra Vilniaus miesto gyventojų skaičius?",
            "expected_response": "Nežinau, ši informacija nėra susijusi su POLA organizacija.",
            "is_rag": False
        },
        {
            "query": "Kas laimėjo paskutines olimpines žaidynes?",
            "expected_response": "Nežinau, kontekste nėra informacijos apie olimpines žaidynes.",
            "is_rag": False
        },
        {
            "query": "Kiek kainuoja naujas iPhone?",
            "expected_response": "Nežinau, kontekste nėra informacijos apie iPhone kainas.",
            "is_rag": False
        },
        {
            "query": "Kokia šiandien oro prognozė?",
            "expected_response": "Nežinau, kontekste nėra informacijos apie oro prognozes.",
            "is_rag": False
        },
        {
            "query": "Kaip išspręsti kvadratinę lygtį?",
            "expected_response": "Nežinau, kontekste nėra informacijos apie matematikos uždavinius.",
            "is_rag": False
        }
    ]

    results = []
    for test_case in test_cases:
        print(f"\nTesting query: {test_case['query']}")
        logger.info(f"Testing query: {test_case['query']}")
        
        # Execute query with 10-second timeout
        answer, sources = await execute_query_with_timeout(rag_chain, test_case['query'])
        
        print(f"Answer: {answer}")
        print(f"Number of sources: {len(sources)}")
        logger.info(f"Answer: {answer}")
        logger.info(f"Number of sources: {len(sources)}")

        result = {
            "query": test_case['query'],
            "answer": answer,
            "sources": len(sources),
            "passed": False,
            "timestamp": datetime.now().isoformat()
        }

        if "timed out" in str(answer):
            result["passed"] = False
            result["error"] = "Query timed out"
            print(f"Error: Query timed out")
            logger.error("Query timed out")
        else:
            if test_case['is_rag']:
                answer_lower = answer.lower()
                found_keywords = [
                    keyword for keyword in test_case['expected_keywords']
                    if keyword.lower() in answer_lower
                ]
                result["passed"] = len(found_keywords) > 0
                result["found_keywords"] = found_keywords
                result["expected_keywords"] = test_case['expected_keywords']
                
                if not result["passed"]:
                    msg = f"Expected keywords not found. Expected: {test_case['expected_keywords']}"
                    print(f"Warning: {msg}")
                    logger.warning(msg)
            else:
                result["passed"] = any(phrase in answer.lower() for phrase in [
                    "nežinau",
                    "kontekste",
                    "negaliu atsakyti",
                    "neturiu informacijos",
                    "nėra informacijos"
                ])
                
                if not result["passed"]:
                    msg = f"Expected 'nežinau' response not found in answer: {answer}"
                    print(f"Warning: {msg}")
                    logger.warning(msg)

        results.append(result)
        print(f"Test passed: {result['passed']}")
        logger.info(f"Test passed: {result['passed']}")

    # Calculate summary
    passed_tests = sum(1 for r in results if r['passed'])
    failed_tests = sum(1 for r in results if not r['passed'])
    
    summary = f"""
Test Summary:
------------
Total tests: {len(results)}
Passed tests: {passed_tests}
Failed tests: {failed_tests}
    """
    
    print(summary)
    logger.info(summary)

    # Save detailed results to JSON
    results_file = log_dir / f"pola_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    msg = f"Detailed results saved to: {results_file}"
    print(msg)
    logger.info(msg)

    # Print detailed results
    print("\nDetailed Results:")
    logger.info("Detailed Results:")
    
    for result in results:
        details = f"""
Query: {result['query']}
Answer: {result['answer']}
Sources found: {result['sources']}
Passed: {result['passed']}
        """
        print(details)
        logger.info(details)
        
        if 'found_keywords' in result:
            keywords_info = f"Found keywords: {result['found_keywords']}\nExpected keywords: {result['expected_keywords']}"
            print(keywords_info)
            logger.info(keywords_info)
        if 'error' in result:
            error_info = f"Error: {result['error']}"
            print(error_info)
            logger.error(error_info)

    # Assert overall test success
    assert passed_tests > 0, f"No tests passed! {failed_tests} tests failed."
    
    return results  # Return results for potential further analysis 