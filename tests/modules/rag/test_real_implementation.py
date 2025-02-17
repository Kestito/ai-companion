import pytest
from pathlib import Path
import tempfile
import os
from typing import Generator
import time

from ai_companion.modules.rag.core.document_processor import DocumentProcessor
from ai_companion.modules.rag.core.vector_store import VectorStoreManager
from ai_companion.modules.rag.core.rag_chain import RAGChain

POLA_CONTENT = """
Pagalbos onkologiniams ligoniams asociacija (POLA)
Kas? – Kortelę gali gauti bet kuris fizinis asmuo, kuriam yra diagnozuota onkologinė liga, susipažinęs su kortelės taisyklėmis ir užpildęs kortelės paraišką.
Kiek? Pirmą kartą POLA kortelė išduodama nemokamai. Reikia susimokėti tik už siuntimo paslaugas.
Nuo 2021 m. sausio 1 d. – su POLA kortele 80% nuolaida viešajam transportui visoje Lietuvoje!
Kiekvienais metais Lietuvoje vėžiu suserga daugiau nei 18 000 žmonių. Lietuvoje gyvena apie 110 000 žmonių, kurie šiuo metu gauna aktyvų gydymą.
POLA kortelės projekto tikslas – pagerinti onkologinių pacientų gyvenimo kokybę: sumažinti finansinę naštą, suteikti gerų emocijų ir pozityvumo.
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
    file_path = Path(temp_dir) / "pola_info.txt"
    file_path.write_text(POLA_CONTENT, encoding='utf-8')
    return str(file_path)

@pytest.fixture(scope="module")
def vector_store() -> Generator[VectorStoreManager, None, None]:
    collection_name = f"test_pola_content_{int(time.time())}"
    manager = VectorStoreManager(collection_name=collection_name)
    yield manager
    # Cleanup
    try:
        manager.delete_collection()
    except Exception:
        pass

@pytest.fixture(scope="module")
def rag_chain(vector_store: VectorStoreManager) -> RAGChain:
    return RAGChain(
        vector_store=vector_store,
        prompt_template="""Based on the following context about POLA organization, answer the question directly and precisely. 
        If numbers or specific details are mentioned in the context, include them in your answer.
        If you don't know the answer, just say that you don't know.
        
        Context: {context}
        
        Question: {question}
        Answer in Lithuanian: """
    )

def test_document_processing(document_processor: DocumentProcessor, test_file: str):
    """Test processing POLA content into chunks."""
    chunks = document_processor.process_file(test_file)
    
    assert len(chunks) > 0
    assert all(len(chunk.page_content) <= 500 for chunk in chunks)
    assert any("POLA" in chunk.page_content for chunk in chunks)
    assert any("onkologiniams" in chunk.page_content for chunk in chunks)

def test_vector_storage(vector_store: VectorStoreManager, document_processor: DocumentProcessor, test_file: str):
    """Test storing and retrieving POLA content vectors."""
    # Process and store documents
    documents = document_processor.process_file(test_file)
    print(f"\nProcessed {len(documents)} documents:")
    for i, doc in enumerate(documents):
        print(f"Document {i + 1}: {doc.page_content[:100]}...")
    
    vector_store.add_documents(documents)
    
    # Wait a bit for indexing
    time.sleep(2)
    
    # Test retrieval with multiple queries
    test_queries = [
        "Kas gali gauti POLA kortelę?",
        "POLA kortelės gavimas",
        "Kortelės gavimo sąlygos"
    ]
    
    for query in test_queries:
        print(f"\nTesting query: {query}")
        results = vector_store.similarity_search(query, k=3)
        
        print(f"Got {len(results)} results:")
        for i, doc in enumerate(results):
            print(f"Result {i + 1}: {doc.page_content[:100]}...")
        
        # Check if any result contains relevant information
        relevant_keywords = ["kortelę", "gauti", "POLA", "fizinis asmuo", "onkologinė"]
        found_keywords = []
        
        for doc in results:
            doc_lower = doc.page_content.lower()
            found_keywords.extend([kw for kw in relevant_keywords if kw.lower() in doc_lower])
        
        assert found_keywords, f"Expected to find at least one of {relevant_keywords} in results for query: {query}"
        print(f"Found keywords: {found_keywords}")

def test_rag_chain_queries(rag_chain: RAGChain, vector_store: VectorStoreManager, document_processor: DocumentProcessor, test_file: str):
    """Test RAG chain with real queries about POLA."""
    # Process and store documents if not already done
    documents = document_processor.process_file(test_file)
    print(f"\nProcessed {len(documents)} documents:")
    for doc in documents:
        print(f"Document content: {doc.page_content[:200]}...")
    
    vector_store.add_documents(documents)
    
    # Wait a bit for indexing
    time.sleep(2)
    
    # Test various queries
    queries = [
        ("Kiek kainuoja POLA kortelė pirmą kartą?", ["nemokamai", "siuntimo"]),
        ("Kokia nuolaida suteikiama viešajam transportui?", ["80%", "viešajam transportui"]),
        ("Kiek žmonių Lietuvoje serga vėžiu?", ["18 000", "110 000", "suserga", "gyvena"]),
        ("Koks yra POLA kortelės tikslas?", ["kokybę", "naštą", "emocijų", "pozityvumo"])
    ]
    
    for query, expected_keywords in queries:
        print(f"\nTesting query: {query}")
        answer, sources = rag_chain.query(query)
        print(f"Answer: {answer}")
        print("Sources:")
        for source in sources:
            print(f"- {source.page_content[:200]}...")
        
        assert answer, f"No answer received for query: {query}"
        assert sources, f"No sources found for query: {query}"
        assert len(sources) > 0, f"No source documents returned for query: {query}"
        
        # Verify answer relevance by checking for expected keywords
        answer_lower = answer.lower()
        found_keywords = [keyword for keyword in expected_keywords if keyword.lower() in answer_lower]
        assert found_keywords, f"Expected to find at least one of {expected_keywords} in answer: {answer}"
        print(f"Found keywords: {found_keywords}")

def test_collection_info(vector_store: VectorStoreManager):
    """Test retrieving collection information."""
    info = vector_store.get_collection_info()
    
    assert info is not None
    assert hasattr(info, "status") or isinstance(info, dict) 