import pytest
from pathlib import Path
import tempfile
from typing import Generator
import time
import asyncio

from ai_companion.modules.rag.core.document_processor import DocumentProcessor
from ai_companion.modules.rag.core.vector_store import VectorStoreManager
from ai_companion.modules.rag.core.rag_chain import RAGChain

# Test content about AI and Technology
TEST_CONTENT = """
Artificial Intelligence and Machine Learning

AI (Artificial Intelligence) is the simulation of human intelligence by machines. 
Machine Learning is a subset of AI that enables systems to learn from data.
Deep Learning is a type of machine learning based on artificial neural networks.

Key AI Applications:
1. Natural Language Processing (NLP)
2. Computer Vision
3. Robotics
4. Expert Systems

Benefits of AI:
- Automation of repetitive tasks
- 24/7 availability
- Reduced human error
- Enhanced decision making
- Faster processing of large data sets

AI Ethics Considerations:
- Privacy concerns
- Bias in AI systems
- Job displacement
- Accountability
- Transparency in AI decisions
"""

@pytest.fixture(scope="module")
def temp_dir() -> Generator[str, None, None]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir

@pytest.fixture(scope="module")
def document_processor(temp_dir: str) -> DocumentProcessor:
    return DocumentProcessor(
        chunk_size=500,
        chunk_overlap=50,
        base_dir=temp_dir
    )

@pytest.fixture(scope="module")
def test_file(temp_dir: str) -> str:
    file_path = Path(temp_dir) / "ai_info.txt"
    file_path.write_text(TEST_CONTENT, encoding='utf-8')
    return str(file_path)

@pytest.fixture(scope="module")
def vector_store() -> Generator[VectorStoreManager, None, None]:
    collection_name = f"test_mixed_queries_{int(time.time())}"
    manager = VectorStoreManager(collection_name=collection_name)
    yield manager
    try:
        manager.delete_collection()
    except Exception:
        pass

@pytest.fixture(scope="module")
def rag_chain(vector_store: VectorStoreManager) -> RAGChain:
    return RAGChain(
        vector_store=vector_store,
        prompt_template="""Based on the following context about AI and technology, answer the question directly and precisely.
        If you don't know the answer based on the context, just say that you don't know.
        
        Context: {context}
        
        Question: {question}
        Answer: """
    )

@pytest.mark.asyncio
async def test_mixed_queries(rag_chain: RAGChain, vector_store: VectorStoreManager, document_processor: DocumentProcessor, test_file: str):
    """Test both RAG and non-RAG queries with various scenarios."""
    # Process and store documents
    documents = document_processor.process_file(test_file)
    vector_store.add_documents(documents)
    await asyncio.sleep(2)  # Wait for indexing

    # Test cases combining RAG and non-RAG queries
    test_cases = [
        # RAG-based queries (information present in the context)
        {
            "query": "What is AI?",
            "expected_keywords": ["simulation", "human intelligence", "machines"],
            "is_rag": True
        },
        {
            "query": "List the key AI applications mentioned.",
            "expected_keywords": ["Natural Language Processing", "Computer Vision", "Robotics", "Expert Systems"],
            "is_rag": True
        },
        {
            "query": "What are the benefits of AI?",
            "expected_keywords": ["Automation", "24/7", "human error", "decision making"],
            "is_rag": True
        },
        {
            "query": "What ethical concerns are mentioned for AI?",
            "expected_keywords": ["Privacy", "Bias", "Job displacement", "Accountability"],
            "is_rag": True
        },
        {
            "query": "What is Machine Learning's relationship to AI?",
            "expected_keywords": ["subset", "learn", "data"],
            "is_rag": True
        },
        
        # Non-RAG queries (information not in context)
        {
            "query": "What is the latest version of GPT?",
            "expected_response": "I don't know based on the provided context.",
            "is_rag": False
        },
        {
            "query": "Who invented the first computer?",
            "expected_response": "I don't know based on the provided context.",
            "is_rag": False
        },
        {
            "query": "What is the market size of AI industry in 2024?",
            "expected_response": "I don't know based on the provided context.",
            "is_rag": False
        },
        {
            "query": "How much does it cost to train a large language model?",
            "expected_response": "I don't know based on the provided context.",
            "is_rag": False
        },
        {
            "query": "What programming languages are best for AI development?",
            "expected_response": "I don't know based on the provided context.",
            "is_rag": False
        }
    ]

    results = []
    for test_case in test_cases:
        print(f"\nTesting query: {test_case['query']}")
        answer, sources = await rag_chain.query(test_case['query'])
        print(f"Answer: {answer}")
        print(f"Number of sources: {len(sources)}")

        result = {
            "query": test_case['query'],
            "answer": answer,
            "sources": len(sources),
            "passed": False
        }

        if test_case['is_rag']:
            # For RAG queries, check if expected keywords are present
            answer_lower = answer.lower()
            found_keywords = [
                keyword for keyword in test_case['expected_keywords']
                if keyword.lower() in answer_lower
            ]
            result["passed"] = len(found_keywords) > 0
            result["found_keywords"] = found_keywords
            assert len(found_keywords) > 0, f"Expected to find at least one of {test_case['expected_keywords']} in answer: {answer}"
        else:
            # For non-RAG queries, check if system acknowledges lack of context
            result["passed"] = "don't know" in answer.lower() or "context" in answer.lower()
            assert "don't know" in answer.lower() or "context" in answer.lower(), \
                f"Expected 'don't know' response for non-RAG query, got: {answer}"

        results.append(result)
        print(f"Test passed: {result['passed']}")

    # Print summary
    print("\nTest Summary:")
    print(f"Total tests: {len(results)}")
    print(f"Passed tests: {sum(1 for r in results if r['passed'])}")
    print(f"Failed tests: {sum(1 for r in results if not r['passed'])}")

    # Detailed results
    print("\nDetailed Results:")
    for result in results:
        print(f"\nQuery: {result['query']}")
        print(f"Answer: {result['answer']}")
        print(f"Sources found: {result['sources']}")
        print(f"Passed: {result['passed']}")
        if 'found_keywords' in result:
            print(f"Found keywords: {result['found_keywords']}") 