import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain.schema import Document
from qdrant_client import QdrantClient, models
from qdrant_client.models import CollectionInfo, CollectionStatus, OptimizersStatusOneOf, CollectionConfig, CollectionParams, VectorParams, Distance
import os
import httpx

from ai_companion.modules.rag.core.vector_store import VectorStoreManager

@pytest.fixture(autouse=True)
def mock_env_vars():
    with patch.dict(os.environ, {
        "AZURE_EMBEDDING_DEPLOYMENT": "test-embedding",
        "EMBEDDING_MODEL": "test-model",
        "AZURE_EMBEDDING_API_VERSION": "2023-05-15",
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
        "AZURE_OPENAI_API_KEY": "test-key",
        "QDRANT_URL": "https://b88198bc-6212-4390-bbac-b1930f543812.europe-west3-0.gcp.cloud.qdrant.io",
        "QDRANT_API_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwiZXhwIjoxNzQ3MDY5MzcyfQ.plLwDbnIi7ggn_d98e-OsxpF60lcNq9nzZ0EzwFAnQw",
        "EMBEDDING_DIM": "1536"
    }):
        yield

@pytest.fixture
def mock_httpx_client():
    with patch("httpx.Client") as mock:
        client = MagicMock()
        mock.return_value = client
        
        # Mock response for collection creation
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": True, "status": "ok"}
        client.send.return_value = mock_response
        client.build_request.return_value = httpx.Request("GET", "http://test")
        
        yield client

@pytest.fixture
def mock_qdrant_client():
    client = MagicMock(spec=QdrantClient)
    
    # Create mock HTTP client
    http_client = MagicMock()
    collections_api = MagicMock()
    api_client = MagicMock()
    
    # Set up the mock chain
    http_client.collections_api = collections_api
    http_client.api_client = api_client
    client._client = http_client
    
    # Mock successful responses
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": True, "status": "ok"}
    api_client.request.return_value = mock_response
    api_client.send.return_value = mock_response
    
    return client

@pytest.fixture
def mock_embeddings():
    with patch("langchain_openai.AzureOpenAIEmbeddings") as mock:
        embeddings = MagicMock()
        mock.return_value = embeddings
        # Mock necessary methods
        embeddings.embed_documents = MagicMock(return_value=[[0.1] * 1536])
        embeddings.embed_query = MagicMock(return_value=[0.1] * 1536)
        yield embeddings

@pytest.fixture
def mock_vector_store():
    with patch("langchain_qdrant.Qdrant") as mock:
        instance = MagicMock()
        mock.return_value = instance
        # Mock necessary methods
        instance.add_documents = MagicMock()
        instance.similarity_search = MagicMock()
        instance.as_retriever = MagicMock()
        yield instance

@pytest.fixture
def mock_collection_info():
    return CollectionInfo(
        status=CollectionStatus.GREEN,
        optimizer_status=OptimizersStatusOneOf.OK,
        vectors_count=100,
        indexed_vectors_count=100,
        points_count=100,
        segments_count=1,
        payload_schema={},  # Simplified payload schema since we don't need complex schema for tests
        config=CollectionConfig(
            params=CollectionParams(
                vectors=VectorParams(
                    size=1536,
                    distance=Distance.COSINE
                )
            ),
            hnsw_config=models.HnswConfig(
                m=16,
                ef_construct=100,
                full_scan_threshold=10000,
                max_indexing_threads=0,
                on_disk=False,
                payload_m=None
            ),
            optimizer_config=models.OptimizersConfig(
                deleted_threshold=0.2,
                vacuum_min_vector_number=1000,
                default_segment_number=0,
                max_segment_size=None,
                memmap_threshold=None,
                indexing_threshold=20000,
                flush_interval_sec=5,
                max_optimization_threads=1
            ),
            wal_config=models.WalConfig(
                wal_capacity_mb=32,
                wal_segments_ahead=0
            ),
            quantization_config=None
        )
    )

@pytest.fixture
def vector_store_manager(mock_embeddings, mock_vector_store):
    """Create a real vector store manager with actual Qdrant client."""
    with patch("langchain_openai.AzureOpenAIEmbeddings", return_value=mock_embeddings), \
         patch("langchain_qdrant.Qdrant", return_value=mock_vector_store):
        manager = VectorStoreManager(collection_name="test_collection")
        yield manager
        # Cleanup: Delete test collection after tests
        try:
            manager.delete_collection()
        except Exception:
            pass

@pytest.fixture
def sample_documents():
    return [
        Document(page_content="Test document 1", metadata={"source": "test1"}),
        Document(page_content="Test document 2", metadata={"source": "test2"}),
        Document(page_content="Test document 3", metadata={"source": "test3"})
    ]

def test_init(vector_store_manager):
    """Test initialization of vector store manager."""
    assert vector_store_manager.collection_name == "test_collection"
    assert vector_store_manager.vector_store is not None
    
    # Verify collection exists
    collection_info = vector_store_manager.get_collection_info()
    assert collection_info is not None
    assert isinstance(collection_info, (dict, CollectionInfo))

def test_init_creates_collection():
    """Test collection creation when it doesn't exist."""
    manager = None
    try:
        with patch("langchain_openai.AzureOpenAIEmbeddings") as mock_embeddings, \
             patch("langchain_qdrant.Qdrant") as mock_qdrant:
            # Setup mock embeddings
            embeddings = MagicMock()
            embeddings.embed_documents = MagicMock(return_value=[[0.1] * 1536])
            embeddings.embed_query = MagicMock(return_value=[0.1] * 1536)
            mock_embeddings.return_value = embeddings
            
            # Setup mock Qdrant
            instance = MagicMock()
            instance.add_documents = MagicMock()
            instance.similarity_search = MagicMock()
            instance.as_retriever = MagicMock()
            mock_qdrant.return_value = instance
            
            # Create manager with unique collection name
            manager = VectorStoreManager(collection_name="test_collection_create")
            
            # Verify collection exists
            collection_info = manager.get_collection_info()
            assert collection_info is not None
            assert isinstance(collection_info, (dict, CollectionInfo))
    finally:
        # Cleanup
        if manager:
            manager.delete_collection()

def test_add_documents(vector_store_manager, mock_vector_store, sample_documents):
    """Test adding documents to vector store."""
    # Mock the embeddings at the class level
    with patch("langchain_openai.embeddings.base.AzureOpenAIEmbeddings._get_len_safe_embeddings", 
              return_value=[[0.1] * 1536] * len(sample_documents)):
        vector_store_manager.add_documents(sample_documents)
        mock_vector_store.add_documents.assert_called_once_with(sample_documents)

def test_similarity_search(vector_store_manager, mock_vector_store):
    """Test similarity search."""
    query = "test query"
    k = 5
    filter_dict = {"metadata_field": "value"}
    
    # Mock the embeddings at the class level
    with patch("langchain_openai.embeddings.base.AzureOpenAIEmbeddings._get_len_safe_embeddings", 
              return_value=[[0.1] * 1536]):
        vector_store_manager.similarity_search(query, k=k, filter=filter_dict)
        mock_vector_store.similarity_search.assert_called_once_with(
            query, k=k, filter=filter_dict
        )

def test_delete_collection():
    """Test collection deletion."""
    manager = None
    try:
        with patch("langchain_openai.AzureOpenAIEmbeddings") as mock_embeddings, \
             patch("langchain_qdrant.Qdrant") as mock_qdrant:
            # Setup mock embeddings
            embeddings = MagicMock()
            embeddings.embed_documents = MagicMock(return_value=[[0.1] * 1536])
            embeddings.embed_query = MagicMock(return_value=[0.1] * 1536)
            mock_embeddings.return_value = embeddings
            
            # Setup mock Qdrant
            instance = MagicMock()
            instance.add_documents = MagicMock()
            instance.similarity_search = MagicMock()
            instance.as_retriever = MagicMock()
            mock_qdrant.return_value = instance
            
            # Create and then delete collection
            manager = VectorStoreManager(collection_name="test_collection_delete")
            
            # Verify collection exists
            collection_info = manager.get_collection_info()
            assert collection_info is not None
            
            # Delete collection
            manager.delete_collection()
            
            # Verify collection no longer exists
            with pytest.raises(Exception):
                manager.get_collection_info()
    finally:
        # Cleanup in case test fails
        if manager:
            try:
                manager.delete_collection()
            except Exception:
                pass 