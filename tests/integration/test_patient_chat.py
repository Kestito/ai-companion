import pytest

# Import the necessary modules
from ai_companion.api.web_handler import process_message, MessageRequest
from ai_companion.graph.utils.helpers import load_memory_to_graph
from ai_companion.modules.memory.service import MemoryService
from langchain_core.messages import HumanMessage

# Test constants
TEST_USER_ID = "test-user-123"
TEST_SESSION_ID = f"web-{TEST_USER_ID}"
TEST_USER_INFO = {
    "id": TEST_USER_ID,
    "first_name": "Test",
    "last_name": "User",
    "email": "testuser@example.com",
    "preferred_language": "en",
    "last_visit": "2023-01-01T00:00:00",
    "support_status": "active",
}


class MockSupabase:
    """Mock Supabase client for testing"""

    def __init__(self):
        self.data = {}

    def table(self, table_name):
        self.current_table = table_name
        return self

    def select(self, *fields):
        return self

    def like(self, field, value):
        return self

    def order(self, field, desc=False):
        return self

    def limit(self, limit_val):
        return self

    def execute(self):
        # Return empty result as default
        return type("obj", (object,), {"data": []})

    def insert(self, record):
        if self.current_table not in self.data:
            self.data[self.current_table] = []
        self.data[self.current_table].append(record)
        return self


@pytest.fixture
def mock_memory_service(monkeypatch):
    """Create a mock memory service for testing"""
    # Create a real memory service instance
    memory_service = MemoryService()

    # Replace Supabase client with mock
    memory_service.supabase = MockSupabase()

    # Monkey patch the get_memory_service function to return our instance
    monkeypatch.setattr(
        "ai_companion.modules.memory.service.get_memory_service", lambda: memory_service
    )

    return memory_service


@pytest.mark.asyncio
async def test_load_memory_to_graph():
    """Test that load_memory_to_graph correctly awaits async function calls"""

    # Create a dummy graph
    class MockGraph:
        async def invoke(self, state, config):
            return {"messages": [], "output_message": "Test response"}

        async def aget_state(self, config):
            return {"messages": [], "state": "test"}

    # Create test messages
    messages = [HumanMessage(content="Hello")]

    # Call the function we fixed
    result = await load_memory_to_graph(MockGraph(), messages, TEST_SESSION_ID)

    # Verify we got a proper result, not a coroutine
    assert isinstance(result, dict)
    assert "output_message" in result


@pytest.mark.asyncio
async def test_memory_service_load_memory_to_graph():
    """Test that MemoryService.load_memory_to_graph correctly awaits the graph.invoke call"""
    # Create a memory service
    memory_service = MemoryService()
    memory_service.supabase = MockSupabase()

    # Create a test graph
    class MockGraph:
        async def invoke(self, state, config):
            return {"messages": [], "output_message": "Test response"}

        async def aget_state(self, config):
            return {"messages": [], "state": "test"}

    # Create test config
    config = {
        "messages": [HumanMessage(content="Hello")],
        "configurable": {"session_id": TEST_SESSION_ID},
    }

    # Call the function we fixed
    result = await memory_service.load_memory_to_graph(
        MockGraph(), config, TEST_SESSION_ID
    )

    # Verify we got a proper result, not a coroutine
    assert isinstance(result, dict)
    assert "output_message" in result


@pytest.mark.asyncio
async def test_process_message_endpoint(mock_memory_service):
    """Test the complete API endpoint to ensure it handles requests without the coroutine error"""
    # Create a test request
    request = MessageRequest(
        session_id=TEST_SESSION_ID,
        user_id=TEST_USER_ID,
        message="Hello, how are you?",
        user_info=TEST_USER_INFO,
    )

    # Process the message
    response = await process_message(request)

    # Verify response
    assert response is not None
    assert hasattr(response, "session_id")
    assert hasattr(response, "response")
    assert response.session_id == TEST_SESSION_ID
    assert response.response != ""
    assert response.error is None


@pytest.mark.asyncio
async def test_memory_chain(mock_memory_service):
    """Test the full memory chain to ensure all async functions are properly awaited"""
    # First message
    request1 = MessageRequest(
        session_id=None,  # Start with no session
        user_id=TEST_USER_ID,
        message="Hello, my name is Test User",
        user_info=TEST_USER_INFO,
    )

    # Send first message
    response1 = await process_message(request1)
    assert response1.error is None

    # Get the session ID from the response
    session_id = response1.session_id

    # Send a follow-up message using the session ID (this will test memory retrieval)
    request2 = MessageRequest(
        session_id=session_id,
        user_id=TEST_USER_ID,
        message="What's my name?",
        user_info=TEST_USER_INFO,
    )

    # Send second message
    response2 = await process_message(request2)

    # Verify second response
    assert response2.error is None
    assert response2.session_id == session_id
    assert response2.response != ""

    # The actual content would depend on the AI, so we just check
    # that we got a response without errors


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
