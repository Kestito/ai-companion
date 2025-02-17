import pytest
import pytest_asyncio
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
import time

from ai_companion.graph.nodes import rag_node
from ai_companion.graph.state import AICompanionState
from ai_companion.modules.rag import DocumentProcessor, VectorStoreManager

# Test content about POLA card
POLA_CONTENT = """
Pagalbos onkologiniams ligoniams asociacija (POLA)
Kas? – Kortelę gali gauti bet kuris fizinis asmuo, kuriam yra diagnozuota onkologinė liga, susipažinęs su kortelės taisyklėmis ir užpildęs kortelės paraišką.
Kiek? Pirmą kartą POLA kortelė išduodama nemokamai. Reikia susimokėti tik už siuntimo paslaugas.
Nuo 2021 m. sausio 1 d. – su POLA kortele 80% nuolaida viešajam transportui visoje Lietuvoje!
"""

@pytest_asyncio.fixture(scope="function")
async def setup_test_env():
    """Set up test environment with vector store and documents."""
    # Initialize components
    doc_processor = DocumentProcessor(chunk_size=500, chunk_overlap=50)
    collection_name = f"test_medical_knowledge_{int(time.time())}"
    vector_store = VectorStoreManager(collection_name=collection_name)
    
    # Process and store test content
    documents = doc_processor.process_text(POLA_CONTENT)
    vector_store.add_documents(documents)
    
    # Wait for indexing
    time.sleep(2)
    
    yield vector_store
    
    # Cleanup
    try:
        vector_store.delete_collection()
    except Exception:
        pass

@pytest.mark.asyncio
async def test_rag_node_basic_query(setup_test_env):
    """Test RAG node with a basic query about POLA card."""
    vector_store = setup_test_env
    
    # Create test state
    state = AICompanionState({
        "messages": [
            HumanMessage(content="Kiek kainuoja POLA kortelė?")
        ],
        "vector_store": vector_store
    })
    
    # Execute node
    result = await rag_node(state, RunnableConfig())
    
    # Verify response structure
    assert "rag_response" in result
    assert "medical_knowledge" in result["rag_response"]
    assert "has_relevant_info" in result["rag_response"]
    assert "sources" in result["rag_response"]
    
    # Verify content
    response = result["rag_response"]
    assert response["has_relevant_info"] is True
    assert "nemokamai" in response["medical_knowledge"].lower()
    assert len(response["sources"]) > 0

@pytest.mark.asyncio
async def test_rag_node_unknown_query(setup_test_env):
    """Test RAG node with a query that has no matching information."""
    vector_store = setup_test_env
    
    # Create test state
    state = AICompanionState({
        "messages": [
            HumanMessage(content="Kokios yra vėžio gydymo galimybės 2025 metais?")
        ],
        "vector_store": vector_store
    })
    
    # Execute node
    result = await rag_node(state, RunnableConfig())
    
    # Verify response structure
    assert "rag_response" in result
    response = result["rag_response"]
    
    # Verify uncertainty handling
    assert response["has_relevant_info"] is False
    assert any(phrase in response["medical_knowledge"].lower() for phrase in [
        "neturiu informacijos",
        "nežinau",
        "negaliu atsakyti",
        "nesu tikra"
    ])
    assert len(response["sources"]) == 0

@pytest.mark.asyncio
async def test_rag_node_transport_discount(setup_test_env):
    """Test RAG node's handling of specific POLA card benefits."""
    vector_store = setup_test_env
    
    # Create test state
    state = AICompanionState({
        "messages": [
            HumanMessage(content="Kokia nuolaida viešajam transportui su POLA kortele?")
        ],
        "vector_store": vector_store
    })
    
    # Execute node
    result = await rag_node(state, RunnableConfig())
    
    # Verify response
    response = result["rag_response"]
    assert response["has_relevant_info"] is True
    assert "80%" in response["medical_knowledge"]
    assert "viešajam transportui" in response["medical_knowledge"].lower()
    assert len(response["sources"]) > 0

@pytest.mark.asyncio
async def test_rag_node_error_handling():
    """Test RAG node's error handling with invalid state."""
    # Create test state without vector store
    state = AICompanionState({
        "messages": [
            HumanMessage(content="Kiek kainuoja POLA kortelė?")
        ]
    })
    
    # Execute node
    result = await rag_node(state, RunnableConfig())
    
    # Verify error handling
    response = result["rag_response"]
    assert response["has_relevant_info"] is False
    assert "klaida" in response["medical_knowledge"].lower()
    assert len(response["sources"]) == 0

@pytest.mark.asyncio
async def test_rag_node_conversation_context(setup_test_env):
    """Test RAG node with conversation context."""
    vector_store = setup_test_env
    
    # Create test state with conversation context
    state = AICompanionState({
        "messages": [
            HumanMessage(content="Labas, turiu klausimą apie POLA kortelę."),
            AIMessage(content="Žinoma, kuo galiu padėti?"),
            HumanMessage(content="Ar reikia mokėti už kortelę?")
        ],
        "vector_store": vector_store
    })
    
    # Execute node
    result = await rag_node(state, RunnableConfig())
    
    # Verify response
    response = result["rag_response"]
    assert response["has_relevant_info"] is True
    assert "nemokamai" in response["medical_knowledge"].lower()
    assert "pola" in response["medical_knowledge"].lower()
    assert len(response["sources"]) > 0 