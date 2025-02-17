import pytest
from pathlib import Path
import tempfile
import os

from ai_companion.modules.rag.core.document_processor import DocumentProcessor

@pytest.fixture
def document_processor():
    return DocumentProcessor(chunk_size=100, chunk_overlap=20)

@pytest.fixture
def sample_text():
    return """This is a sample text that will be used for testing the document processor.
    It needs to be long enough to create multiple chunks when processed.
    We'll add some more text to ensure we get multiple chunks.
    This should be sufficient to test the chunking functionality."""

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir

def test_process_text(document_processor, sample_text):
    """Test processing of text into chunks."""
    chunks = document_processor.process_text(sample_text)
    
    assert len(chunks) > 0
    assert all(len(chunk.page_content) <= 100 for chunk in chunks)
    assert isinstance(chunks[0].page_content, str)

def test_process_text_with_metadata(document_processor, sample_text):
    """Test processing text with metadata."""
    metadata = {"source": "test", "category": "sample"}
    chunks = document_processor.process_text(sample_text, metadata)
    
    assert len(chunks) > 0
    assert all(chunk.metadata == metadata for chunk in chunks)

def test_process_file(document_processor, temp_dir):
    """Test processing a single file."""
    # Create a test file
    file_path = Path(temp_dir) / "test.txt"
    test_content = "This is a test file content.\n" * 5
    file_path.write_text(test_content)
    
    chunks = document_processor.process_file(str(file_path))
    
    assert len(chunks) > 0
    assert all(len(chunk.page_content) <= 100 for chunk in chunks)
    assert all("test.txt" in chunk.metadata.get("source", "") for chunk in chunks)

def test_process_directory(document_processor, temp_dir):
    """Test processing all files in a directory."""
    # Create multiple test files
    for i in range(3):
        file_path = Path(temp_dir) / f"test_{i}.txt"
        test_content = f"This is test file {i} content.\n" * 5
        file_path.write_text(test_content)
    
    # Update base_dir
    document_processor.base_dir = temp_dir
    chunks = document_processor.process_directory()
    
    assert len(chunks) > 0
    assert all(len(chunk.page_content) <= 100 for chunk in chunks)
    assert len(set(chunk.metadata.get("source", "") for chunk in chunks)) == 3

def test_process_directory_nonexistent(document_processor):
    """Test processing a non-existent directory."""
    with pytest.raises(ValueError, match="Directory does not exist"):
        document_processor.process_directory("nonexistent_dir") 