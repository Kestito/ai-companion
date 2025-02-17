import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain.schema import Document, BaseRetriever
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

from ai_companion.modules.rag.core.rag_chain import RAGChain
from ai_companion.modules.rag.core.vector_store import VectorStoreManager

class MockRetriever(BaseRetriever):
    """Mock retriever for testing."""
    def get_relevant_documents(self, query):
        return []
    
    async def aget_relevant_documents(self, query):
        return []

@pytest.fixture
def mock_azure_chat():
    with patch("langchain_openai.AzureChatOpenAI") as mock:
        chat = MagicMock()
        mock.return_value = chat
        # Mock necessary methods to make it Runnable
        chat.invoke = Mock()
        chat.stream = Mock()
        chat.batch = Mock()
        chat.abatch = Mock()
        chat.ainvoke = Mock()
        chat.astream = Mock()
        yield chat

@pytest.fixture
def mock_vector_store():
    mock = Mock(spec=VectorStoreManager)
    mock.vector_store = Mock()
    retriever = MockRetriever()
    mock.vector_store.as_retriever.return_value = retriever
    return mock

@pytest.fixture
def mock_qa_chain():
    with patch("langchain.chains.RetrievalQA.from_chain_type") as mock_factory:
        chain = MagicMock(spec=RetrievalQA)
        chain.return_value = {
            "result": "Test answer",
            "source_documents": []
        }
        mock_factory.return_value = chain
        yield chain

@pytest.fixture
def rag_chain(mock_azure_chat, mock_vector_store, mock_qa_chain):
    return RAGChain(vector_store=mock_vector_store)

@pytest.fixture
def sample_documents():
    return [
        Document(page_content="Test document 1", metadata={"source": "test1"}),
        Document(page_content="Test document 2", metadata={"source": "test2"})
    ]

def test_init(rag_chain):
    """Test initialization of RAG chain."""
    assert rag_chain.vector_store is not None
    assert rag_chain.llm is not None
    assert rag_chain.prompt is not None
    assert rag_chain.chain is not None

def test_query(rag_chain, sample_documents):
    """Test querying the RAG chain."""
    mock_response = {
        "result": "This is the answer",
        "source_documents": sample_documents
    }
    rag_chain.chain.return_value = mock_response
    
    answer, sources = rag_chain.query("What is the test about?")
    
    assert answer == "This is the answer"
    assert sources == sample_documents
    rag_chain.chain.assert_called_once_with({"query": "What is the test about?"})

def test_update_prompt(rag_chain, mock_qa_chain):
    """Test updating the prompt template."""
    new_template = "New test template with {context} and {question}"
    
    rag_chain.update_prompt(new_template)
    
    assert rag_chain.prompt.template == new_template
    # Verify that a new chain was created with the updated prompt
    RetrievalQA.from_chain_type.assert_called_with(
        llm=rag_chain.llm,
        chain_type="stuff",
        retriever=rag_chain.vector_store.vector_store.as_retriever(),
        return_source_documents=True,
        chain_type_kwargs={"prompt": rag_chain.prompt}
    )

def test_custom_prompt_initialization(mock_azure_chat, mock_vector_store, mock_qa_chain):
    """Test initialization with custom prompt."""
    custom_prompt = "Custom template with {context} and {question}"
    chain = RAGChain(
        vector_store=mock_vector_store,
        prompt_template=custom_prompt
    )
    
    assert chain.prompt.template == custom_prompt

def test_query_with_filter(rag_chain, sample_documents):
    """Test querying with filters."""
    mock_response = {
        "result": "Filtered answer",
        "source_documents": sample_documents
    }
    rag_chain.chain.return_value = mock_response
    
    filter_condition = {"metadata_field": "test_value"}
    answer, sources = rag_chain.query(
        "What is the test about?",
        filter=filter_condition
    )
    
    assert answer == "Filtered answer"
    assert sources == sample_documents 