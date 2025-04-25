import pytest
import asyncio
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Update the fixture to address the deprecation warning
# Instead of redefining event_loop, we'll use the pytest-asyncio event_loop_policy fixture
@pytest.fixture(scope="session")
def event_loop_policy():
    """Configure the event loop policy for tests."""
    policy = asyncio.get_event_loop_policy()
    return policy


# The pytest.ini config should set the default fixture loop scope
# Add pytest config to set asyncio_default_fixture_loop_scope
def pytest_configure(config):
    """Configure pytest settings programmatically."""
    config.option.asyncio_default_fixture_loop_scope = "session"


# Mock environment variables
@pytest.fixture(scope="session", autouse=True)
def mock_env_vars():
    """Set up environment variables for testing."""
    # Save original environment variables
    original_vars = {}
    for key in ["SUPABASE_URL", "SUPABASE_KEY", "TELEGRAM_BOT_TOKEN"]:
        original_vars[key] = os.environ.get(key)

    # Set test environment variables
    os.environ["SUPABASE_URL"] = "https://test-supabase-url.co"
    os.environ["SUPABASE_KEY"] = "test-supabase-key"
    os.environ["TELEGRAM_BOT_TOKEN"] = "7764956576:AAE2C57S9jzihsYvoA2R7fjvLPjoopFbNxU"

    yield

    # Restore original environment variables
    for key, value in original_vars.items():
        if value is not None:
            os.environ[key] = value
        else:
            os.environ.pop(key, None)
