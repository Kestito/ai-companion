import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

from ai_companion.interfaces.whatsapp.whatsapp_response import whatsapp_router
from ai_companion.modules.memory.short_term import (
    ShortTermMemory,
    ShortTermMemoryManager,
    get_short_term_memory_manager,
)
from ai_companion.modules.memory.long_term.memory_manager import (
    MemoryManager,
    MemoryAnalysis,
)

# Test data
TEST_PHONE_NUMBER = "1234567890"
TEST_MESSAGE_TEXT = "Hello, this is a test message"
TEST_MEMORY_ID = "test-memory-id"
TEST_METADATA = {"session": TEST_PHONE_NUMBER, "message_type": "user_input"}

@pytest.fixture
def test_client():
    """Create a test client for the WhatsApp router."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(whatsapp_router)
    return TestClient(app)

@pytest.fixture
async def mock_short_term_memory():
    """Create a mock short-term memory instance."""
    memory = ShortTermMemory(
        id=TEST_MEMORY_ID,
        content=TEST_MESSAGE_TEXT,
        expires_at=datetime.utcnow() + timedelta(minutes=60),
        metadata=TEST_METADATA
    )
    return memory

@pytest.fixture
def mock_memory_manager():
    """Create a mock memory manager."""
    with patch("ai_companion.modules.memory.short_term.short_memory.ShortTermMemoryManager") as mock:
        manager = mock.return_value
        manager.store_memory = AsyncMock()
        manager.get_memory = AsyncMock()
        manager.get_active_memories = AsyncMock()
        manager.delete_memory = AsyncMock()
        manager.cleanup_expired_memories = AsyncMock()
        yield manager

@pytest.mark.asyncio
class TestWhatsAppHandler:
    """Test suite for WhatsApp webhook handler."""

    async def test_webhook_verification(self, test_client):
        """Test webhook verification endpoint."""
        challenge = "test_challenge"
        verify_token = "test_token"
        
        with patch("os.getenv", return_value=verify_token):
            response = test_client.get(
                "/whatsapp_response",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": verify_token,
                    "hub.challenge": challenge
                }
            )
        
        assert response.status_code == 200
        assert response.text == challenge

    async def test_webhook_verification_invalid_token(self, test_client):
        """Test webhook verification with invalid token."""
        challenge = "test_challenge"
        verify_token = "test_token"
        invalid_token = "invalid_token"
        
        with patch("os.getenv", return_value=verify_token):
            response = test_client.get(
                "/whatsapp_response",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": invalid_token,
                    "hub.challenge": challenge
                }
            )
        
        assert response.status_code == 403

    @pytest.mark.parametrize("message_type", ["text", "audio", "image"])
    async def test_message_processing(self, test_client, mock_memory_manager, message_type):
        """Test processing different types of messages."""
        message_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": TEST_PHONE_NUMBER,
                            "type": message_type,
                        }]
                    }
                }]
            }]
        }

        if message_type == "text":
            message_data["entry"][0]["changes"][0]["value"]["messages"][0]["text"] = {
                "body": TEST_MESSAGE_TEXT
            }
        elif message_type == "audio":
            message_data["entry"][0]["changes"][0]["value"]["messages"][0]["audio"] = {
                "id": "test_audio_id"
            }
        elif message_type == "image":
            message_data["entry"][0]["changes"][0]["value"]["messages"][0]["image"] = {
                "id": "test_image_id",
                "caption": "Test image caption"
            }

        # Mock necessary dependencies
        with patch("ai_companion.interfaces.whatsapp.whatsapp_response.get_short_term_memory_manager", 
                  return_value=mock_memory_manager):
            with patch("ai_companion.interfaces.whatsapp.whatsapp_response.send_response", 
                      new_callable=AsyncMock) as mock_send:
                mock_send.return_value = True
                
                response = test_client.post(
                    "/whatsapp_response",
                    json=message_data
                )

        assert response.status_code == 200
        mock_memory_manager.store_memory.assert_called_once()

@pytest.mark.asyncio
class TestShortTermMemory:
    """Test suite for short-term memory functionality."""

    async def test_store_memory(self, mock_memory_manager, mock_short_term_memory):
        """Test storing a new memory."""
        mock_memory_manager.store_memory.return_value = mock_short_term_memory
        
        memory = await mock_memory_manager.store_memory(
            content=TEST_MESSAGE_TEXT,
            ttl_minutes=60,
            metadata=TEST_METADATA
        )
        
        assert isinstance(memory, ShortTermMemory)
        assert memory.content == TEST_MESSAGE_TEXT
        assert memory.metadata == TEST_METADATA

    async def test_get_memory(self, mock_memory_manager, mock_short_term_memory):
        """Test retrieving a memory by ID."""
        mock_memory_manager.get_memory.return_value = mock_short_term_memory
        
        memory = await mock_memory_manager.get_memory(TEST_MEMORY_ID)
        
        assert memory is not None
        assert memory.id == TEST_MEMORY_ID
        assert memory.content == TEST_MESSAGE_TEXT

    async def test_get_expired_memory(self, mock_memory_manager):
        """Test retrieving an expired memory."""
        mock_memory_manager.get_memory.return_value = None
        
        memory = await mock_memory_manager.get_memory(TEST_MEMORY_ID)
        
        assert memory is None

    async def test_cleanup_expired_memories(self, mock_memory_manager):
        """Test cleaning up expired memories."""
        mock_memory_manager.cleanup_expired_memories.return_value = 1
        
        deleted_count = await mock_memory_manager.cleanup_expired_memories()
        
        assert deleted_count == 1
        mock_memory_manager.cleanup_expired_memories.assert_called_once()

@pytest.mark.asyncio
class TestLongTermMemory:
    """Test suite for long-term memory functionality."""

    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock vector store."""
        with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock:
            store = mock.return_value
            store.store_memory = MagicMock()
            store.search_memories = MagicMock()
            store.find_similar_memory = MagicMock()
            yield store

    async def test_memory_analysis(self):
        """Test analyzing message importance."""
        memory_manager = MemoryManager()
        
        # Mock the LLM response
        memory_manager.llm = AsyncMock()
        memory_manager.llm.ainvoke.return_value = MemoryAnalysis(
            is_important=True,
            formatted_memory="Important test memory"
        )
        
        analysis = await memory_manager._analyze_memory(TEST_MESSAGE_TEXT)
        
        assert analysis.is_important
        assert analysis.formatted_memory == "Important test memory"

    async def test_extract_and_store_memories(self, mock_vector_store):
        """Test extracting and storing important memories."""
        from langchain_core.messages import HumanMessage
        
        memory_manager = MemoryManager()
        memory_manager.vector_store = mock_vector_store
        
        # Mock the analysis
        memory_manager._analyze_memory = AsyncMock()
        memory_manager._analyze_memory.return_value = MemoryAnalysis(
            is_important=True,
            formatted_memory="Important test memory"
        )
        
        # Mock that no similar memory exists
        mock_vector_store.find_similar_memory.return_value = None
        
        message = HumanMessage(content=TEST_MESSAGE_TEXT)
        await memory_manager.extract_and_store_memories(message)
        
        mock_vector_store.store_memory.assert_called_once()

    def test_get_relevant_memories(self, mock_vector_store):
        """Test retrieving relevant memories."""
        memory_manager = MemoryManager()
        memory_manager.vector_store = mock_vector_store
        
        # Mock search results
        mock_vector_store.search_memories.return_value = [
            MagicMock(text="Memory 1", score=0.9),
            MagicMock(text="Memory 2", score=0.8)
        ]
        
        memories = memory_manager.get_relevant_memories("test context")
        
        assert len(memories) == 2
        assert "Memory 1" in memories
        assert "Memory 2" in memories 