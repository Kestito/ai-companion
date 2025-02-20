import pytest
import os
import json
from datetime import datetime, timezone
from crawl_for_docs import SitemapProcessor

@pytest.fixture
def temp_json_file(tmp_path):
    """Create a temporary JSON file for testing."""
    json_file = tmp_path / "test_sitemap_state.json"
    return str(json_file)

@pytest.fixture
def sitemap_processor(temp_json_file):
    """Create a SitemapProcessor instance with test sitemaps."""
    test_sitemaps = [
        "https://test.com/sitemap1.xml",
        "https://test.com/sitemap2.xml"
    ]
    return SitemapProcessor(test_sitemaps, storage_file=temp_json_file)

def test_initialization(temp_json_file):
    """Test SitemapProcessor initialization and file creation."""
    test_sitemaps = ["https://test.com/sitemap.xml"]
    processor = SitemapProcessor(test_sitemaps, storage_file=temp_json_file)
    
    # Check if file was created
    assert os.path.exists(temp_json_file)
    
    # Check if file contains valid JSON with correct structure
    with open(temp_json_file, 'r') as f:
        state = json.load(f)
        assert "sitemaps" in state
        assert "last_run" in state
        assert "stats" in state
        assert all(key in state["stats"] for key in ["total_urls_found", "successful_crawls", "failed_crawls"])

def test_update_sitemap_state(sitemap_processor):
    """Test updating sitemap processing state."""
    test_url = "https://test.com/sitemap1.xml"
    urls_found = 10
    
    # Test successful update
    sitemap_processor.update_sitemap_state(test_url, urls_found, True)
    state = sitemap_processor.get_sitemap_state(test_url)
    
    assert state["status"] == "success"
    assert state["urls_found"] == urls_found
    assert "last_processed" in state
    
    # Test failed update
    sitemap_processor.update_sitemap_state(test_url, 0, False)
    state = sitemap_processor.get_sitemap_state(test_url)
    
    assert state["status"] == "failed"
    assert state["urls_found"] == 0

def test_get_processing_stats(sitemap_processor):
    """Test getting processing statistics."""
    # Add some test data
    sitemap_processor.update_sitemap_state("https://test.com/sitemap1.xml", 10, True)
    sitemap_processor.update_sitemap_state("https://test.com/sitemap2.xml", 0, False)
    
    stats = sitemap_processor.get_processing_stats()
    assert stats["total_urls_found"] == 10
    assert stats["successful_crawls"] == 1
    assert stats["failed_crawls"] == 1

def test_state_persistence(temp_json_file):
    """Test if state persists between instances."""
    test_sitemaps = ["https://test.com/sitemap.xml"]
    
    # Create first instance and update state
    processor1 = SitemapProcessor(test_sitemaps, storage_file=temp_json_file)
    processor1.update_sitemap_state(test_sitemaps[0], 5, True)
    
    # Create second instance and verify state
    processor2 = SitemapProcessor(test_sitemaps, storage_file=temp_json_file)
    state = processor2.get_sitemap_state(test_sitemaps[0])
    
    assert state["status"] == "success"
    assert state["urls_found"] == 5

def test_error_handling(temp_json_file):
    """Test error handling in state management."""
    test_sitemaps = ["https://test.com/sitemap.xml"]
    
    # Create directory instead of file to simulate error
    os.makedirs(temp_json_file, exist_ok=True)
    
    processor = SitemapProcessor(test_sitemaps, storage_file=temp_json_file)
    assert processor.state == processor._create_default_state()
    
    # Cleanup
    os.rmdir(temp_json_file)

if __name__ == "__main__":
    pytest.main([__file__]) 