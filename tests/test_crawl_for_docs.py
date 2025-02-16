import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock
from crawl_for_docs import (
    PolaURL,
    ProcessedChunk,
    chunk_text,
    get_embedding,
    insert_chunk,
    process_chunk,
)

@pytest.fixture
def sample_url():
    return PolaURL(
        url="https://test.com/page1",
        image_count=2,
        last_modified=datetime.now(timezone.utc)
    )

@pytest.fixture
def sample_chunk():
    return ProcessedChunk(
        url="https://test.com/page1",
        chunk_number=1,
        title="Test Title",
        summary="Test Summary",
        content="Test Content",
        metadata={"source": "test"},
        embedding=[0.1] * 1536,
        semantic_context="Test Context"
    )

def test_chunk_text():
    """Test text chunking functionality"""
    text = """# Header 1
    This is paragraph 1.
    
    # Header 2
    This is paragraph 2.
    
    ```python
    def test():
        pass
    ```
    
    Final paragraph."""
    
    chunks = chunk_text(text, chunk_size=50)
    assert len(chunks) > 0
    assert any("Header 1" in chunk for chunk in chunks)
    assert any("Header 2" in chunk for chunk in chunks)

@pytest.mark.asyncio
async def test_get_embedding():
    """Test embedding generation with mocked OpenAI client"""
    with patch('crawl_for_docs.embeddings_client.embeddings.create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value.data = [Mock(embedding=[0.1] * 1536)]
        
        embedding = await get_embedding("Test text")
        assert len(embedding) == 1536
        mock_create.assert_called_once()

@pytest.mark.asyncio
async def test_insert_chunk(sample_chunk):
    """Test chunk insertion into Qdrant"""
    with patch('crawl_for_docs.qdrant_client.upsert') as mock_upsert:
        mock_upsert.return_value = True
        
        result = await insert_chunk(sample_chunk)
        assert result is True
        mock_upsert.assert_called_once()

@pytest.mark.asyncio
async def test_process_chunk(sample_url):
    """Test chunk processing pipeline"""
    with patch('crawl_for_docs.get_title_and_summary', new_callable=AsyncMock) as mock_title_summary, \
         patch('crawl_for_docs.get_embedding', new_callable=AsyncMock) as mock_embedding:
        
        mock_title_summary.return_value = {
            "title": "Test Title",
            "summary": "Test Summary"
        }
        mock_embedding.return_value = [0.1] * 1536
        
        chunk = "Test content"
        result = await process_chunk(chunk, 1, sample_url)
        
        assert isinstance(result, ProcessedChunk)
        assert result.title == "Test Title"
        assert result.summary == "Test Summary"
        assert len(result.embedding) == 1536

@pytest.mark.asyncio
async def test_pola_url_from_string():
    """Test PolaURL creation from string"""
    url = "https://test.com"
    images = 2
    last_mod = "2024-03-20 12:00 +0000"
    
    pola_url = PolaURL.from_string(url, images, last_mod)
    
    assert pola_url.url == url
    assert pola_url.image_count == images
    assert isinstance(pola_url.last_modified, datetime)

if __name__ == "__main__":
    pytest.main([__file__]) 