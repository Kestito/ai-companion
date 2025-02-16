import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from supabase import create_client, Client
from pydantic import BaseModel, Field

from ai_companion.settings import settings

class ShortTermMemory(BaseModel):
    """Model for short-term memory entries."""
    id: str = Field(..., description="Unique identifier for the memory")
    content: str = Field(..., description="The actual memory content")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the memory was created")
    expires_at: datetime = Field(..., description="When the memory should expire")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the memory")

class ShortTermMemoryManager:
    """Manager class for handling short-term memory operations."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        self._initialize_table()

    def _initialize_table(self) -> None:
        """Initialize the short-term memories table if it doesn't exist."""
        try:
            # Create table if not exists using SQL
            self.supabase.table("short_term").select("id").limit(1).execute()
        except Exception as e:
            self.logger.error(f"Error initializing short-term table: {e}")
            raise

    async def store_memory(
        self, 
        content: str, 
        ttl_minutes: int = 60,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ShortTermMemory:
        """Store a new short-term memory with specified TTL."""
        try:
            expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
            memory = ShortTermMemory(
                id=str(uuid.uuid4()),
                content=content,
                expires_at=expires_at,
                metadata=metadata or {}
            )

            result = self.supabase.table("short_term").insert({
                "id": memory.id,
                "content": memory.content,
                "created_at": memory.created_at.isoformat(),
                "expires_at": memory.expires_at.isoformat(),
                "metadata": memory.metadata
            }).execute()

            self.logger.info(f"Stored short-term memory: {memory.id}")
            return memory
        except Exception as e:
            self.logger.error(f"Error storing short-term memory: {e}")
            raise

    async def get_memory(self, memory_id: str) -> Optional[ShortTermMemory]:
        """Retrieve a specific short-term memory by ID if not expired."""
        try:
            result = self.supabase.table("short_term").select("*").eq("id", memory_id).execute()
            
            if not result.data:
                return None

            memory_data = result.data[0]
            if datetime.fromisoformat(memory_data["expires_at"]) < datetime.utcnow():
                await self.delete_memory(memory_id)
                return None

            return ShortTermMemory(**memory_data)
        except Exception as e:
            self.logger.error(f"Error retrieving short-term memory: {e}")
            raise

    async def get_active_memories(self) -> List[ShortTermMemory]:
        """Retrieve all non-expired short-term memories."""
        try:
            current_time = datetime.utcnow().isoformat()
            result = self.supabase.table("short_term")\
                .select("*")\
                .gt("expires_at", current_time)\
                .execute()

            return [ShortTermMemory(**item) for item in result.data]
        except Exception as e:
            self.logger.error(f"Error retrieving active memories: {e}")
            raise

    async def delete_memory(self, memory_id: str) -> None:
        """Delete a specific short-term memory."""
        try:
            self.supabase.table("short_term").delete().eq("id", memory_id).execute()
            self.logger.info(f"Deleted short-term memory: {memory_id}")
        except Exception as e:
            self.logger.error(f"Error deleting short-term memory: {e}")
            raise

    async def cleanup_expired_memories(self) -> int:
        """Remove all expired memories and return the count of deleted items."""
        try:
            current_time = datetime.utcnow().isoformat()
            result = self.supabase.table("short_term")\
                .delete()\
                .lt("expires_at", current_time)\
                .execute()

            deleted_count = len(result.data)
            self.logger.info(f"Cleaned up {deleted_count} expired memories")
            return deleted_count
        except Exception as e:
            self.logger.error(f"Error cleaning up expired memories: {e}")
            raise

def get_short_term_memory_manager() -> ShortTermMemoryManager:
    """Get a ShortTermMemoryManager instance."""
    return ShortTermMemoryManager() 