import pytest
import os
import json
from datetime import datetime, timezone, timedelta
from crawl_for_docs import URLTracker

@pytest.fixture
def temp_json_file(tmp_path):
    """Create a temporary JSON file for testing."""
    json_file = tmp_path / "test_processed_urls.json"
    return str(json_file)

@pytest.fixture
def url_tracker(temp_json_file):
    """Create a URLTracker instance with a temporary file."""
    tracker = URLTracker(storage_file=temp_json_file)
    return tracker

@pytest.mark.asyncio
async def test_mark_url_processed(url_tracker, temp_json_file):
    """Test marking a URL as processed."""
    test_url = "https://test.com/page"
    metadata = {"test_key": "test_value"}
    
    await url_tracker.mark_url_processed(test_url, "success", metadata)
    
    # Verify in-memory state
    assert url_tracker.is_url_processed(test_url)
    status = url_tracker.get_url_status(test_url)
    assert status["status"] == "success"
    assert status["metadata"] == metadata
    
    # Verify persisted state
    with open(temp_json_file, 'r') as f:
        saved_data = json.load(f)
    assert test_url.strip('/') in saved_data
    assert saved_data[test_url.strip('/')]["status"] == "success"
    assert saved_data[test_url.strip('/')]["metadata"] == metadata

@pytest.mark.asyncio
async def test_mark_url_failed(url_tracker):
    """Test marking a URL as failed."""
    test_url = "https://test.com/failed"
    error_msg = "Test error message"
    
    await url_tracker.mark_url_failed(test_url, error_msg)
    
    status = url_tracker.get_url_status(test_url)
    assert status["status"] == "failed"
    assert status["metadata"]["error"] == error_msg

def test_is_url_processed(url_tracker):
    """Test checking if URL is processed."""
    test_url = "https://test.com/check"
    assert not url_tracker.is_url_processed(test_url)
    assert not url_tracker.is_url_processed(test_url + "/")  # Test with trailing slash

def test_get_unprocessed_urls(url_tracker):
    """Test filtering unprocessed URLs."""
    urls = [
        "https://test.com/page1",
        "https://test.com/page2",
        "https://test.com/page3"
    ]
    
    # Mark one URL as processed
    url_tracker.processed_urls[urls[0].strip('/')] = {
        "status": "success",
        "last_processed": datetime.now(timezone.utc).isoformat(),
        "metadata": {}
    }
    
    unprocessed = url_tracker.get_unprocessed_urls(urls)
    assert len(unprocessed) == 2
    assert urls[0] not in unprocessed
    assert urls[1] in unprocessed
    assert urls[2] in unprocessed

@pytest.mark.asyncio
async def test_cleanup_old_entries(url_tracker):
    """Test cleaning up old entries."""
    # Add some test entries
    old_date = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
    recent_date = datetime.now(timezone.utc).isoformat()
    
    url_tracker.processed_urls = {
        "old_url": {
            "status": "success",
            "last_processed": old_date,
            "metadata": {}
        },
        "recent_url": {
            "status": "success",
            "last_processed": recent_date,
            "metadata": {}
        }
    }
    
    await url_tracker.cleanup_old_entries(days=30)
    
    assert "old_url" not in url_tracker.processed_urls
    assert "recent_url" in url_tracker.processed_urls

def test_load_processed_urls(temp_json_file):
    """Test loading URLs from file."""
    # Create test data
    test_data = {
        "test_url": {
            "status": "success",
            "last_processed": datetime.now(timezone.utc).isoformat(),
            "metadata": {"test": "data"}
        }
    }
    
    # Write test data to file
    with open(temp_json_file, 'w') as f:
        json.dump(test_data, f)
    
    # Create new tracker instance to load data
    tracker = URLTracker(storage_file=temp_json_file)
    
    assert "test_url" in tracker.processed_urls
    assert tracker.processed_urls["test_url"]["metadata"]["test"] == "data"

def test_normalize_urls(url_tracker):
    """Test URL normalization handling."""
    test_urls = [
        "https://test.com/page",
        "https://test.com/page/",
        "https://test.com/page//////"
    ]
    
    # Mark first URL format as processed
    url_tracker.processed_urls[test_urls[0].strip('/')] = {
        "status": "success",
        "last_processed": datetime.now(timezone.utc).isoformat(),
        "metadata": {}
    }
    
    # All formats should be considered processed
    for url in test_urls:
        assert url_tracker.is_url_processed(url)

@pytest.mark.asyncio
async def test_url_tracker_initialization(temp_json_file):
    """Test URLTracker initialization and file creation."""
    # Test with non-existent file
    if os.path.exists(temp_json_file):
        os.remove(temp_json_file)
    
    tracker = URLTracker(storage_file=temp_json_file)
    
    # Check if file was created
    assert os.path.exists(temp_json_file)
    
    # Check if file contains valid JSON
    with open(temp_json_file, 'r') as f:
        data = json.load(f)
        assert isinstance(data, dict)
    
    # Test with existing file
    test_data = {
        "test_url": {
            "status": "success",
            "last_processed": datetime.now(timezone.utc).isoformat(),
            "metadata": {}
        }
    }
    
    with open(temp_json_file, 'w') as f:
        json.dump(test_data, f)
    
    tracker = URLTracker(storage_file=temp_json_file)
    assert tracker.processed_urls == test_data

@pytest.mark.asyncio
async def test_url_tracker_file_permissions(temp_json_file):
    """Test URLTracker handles file permission issues gracefully."""
    # Create directory with same name to simulate permission error
    os.makedirs(temp_json_file, exist_ok=True)
    
    tracker = URLTracker(storage_file=temp_json_file)
    assert tracker.processed_urls == {}
    
    # Cleanup
    os.rmdir(temp_json_file)

if __name__ == "__main__":
    pytest.main([__file__]) 