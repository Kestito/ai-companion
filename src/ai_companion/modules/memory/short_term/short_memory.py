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
        try:
            # Use lowercase attribute names to match how they're defined in settings.py
            self.supabase: Client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            self.logger.info(f"Connected to Supabase at {settings.supabase_url}")
            self._initialize_table()
        except Exception as e:
            self.logger.error(f"Failed to initialize Supabase client: {e}")
            # Create a fallback memory store using a dictionary
            self.supabase = None
            self.memory_store = {}
            self.logger.warning("Using in-memory fallback for memory management")

    def _initialize_table(self) -> None:
        """Initialize the short-term memories table if it doesn't exist."""
        if not self.supabase:
            self.logger.warning("Skipping table initialization - using in-memory store")
            return
            
        try:
            # Create table if not exists using SQL
            self.supabase.table("short_term").select("id").limit(1).execute()
        except Exception as e:
            self.logger.error(f"Error initializing short-term table: {e}")
            # Don't raise, just log and continue with in-memory store
            self.supabase = None
            self.memory_store = {}
            self.logger.warning("Falling back to in-memory store after table initialization failure")

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

            if self.supabase:
                # Store in Supabase
                result = self.supabase.table("short_term").insert({
                    "id": memory.id,
                    "content": memory.content,
                    "created_at": memory.created_at.isoformat(),
                    "expires_at": memory.expires_at.isoformat(),
                    "metadata": memory.metadata
                }).execute()
            else:
                # Store in local memory
                self.memory_store[memory.id] = memory

            self.logger.info(f"Stored short-term memory: {memory.id}")
            return memory
        except Exception as e:
            self.logger.error(f"Error storing short-term memory: {e}")
            # Still return the memory object even if storage failed
            return memory

    async def get_memory(self, memory_id: str) -> Optional[ShortTermMemory]:
        """Retrieve a specific short-term memory by ID if not expired."""
        try:
            if self.supabase:
                result = self.supabase.table("short_term").select("*").eq("id", memory_id).execute()
                
                if not result.data:
                    return None

                memory_data = result.data[0]
                if datetime.fromisoformat(memory_data["expires_at"]) < datetime.utcnow():
                    await self.delete_memory(memory_id)
                    return None

                return ShortTermMemory(**memory_data)
            else:
                # Get from local memory
                if memory_id not in self.memory_store:
                    return None
                    
                memory = self.memory_store[memory_id]
                if memory.expires_at < datetime.utcnow():
                    del self.memory_store[memory_id]
                    return None
                    
                return memory
        except Exception as e:
            self.logger.error(f"Error retrieving short-term memory: {e}")
            return None

    async def get_active_memories(self) -> List[ShortTermMemory]:
        """Retrieve all non-expired short-term memories."""
        try:
            if self.supabase:
                current_time = datetime.utcnow().isoformat()
                result = self.supabase.table("short_term")\
                    .select("*")\
                    .gt("expires_at", current_time)\
                    .execute()

                return [ShortTermMemory(**item) for item in result.data]
            else:
                # Filter from local memory
                current_time = datetime.utcnow()
                return [mem for mem in self.memory_store.values() if mem.expires_at > current_time]
        except Exception as e:
            self.logger.error(f"Error retrieving active memories: {e}")
            return []

    async def delete_memory(self, memory_id: str) -> None:
        """Delete a specific short-term memory."""
        try:
            if self.supabase:
                self.supabase.table("short_term").delete().eq("id", memory_id).execute()
            else:
                # Delete from local memory
                if memory_id in self.memory_store:
                    del self.memory_store[memory_id]
                    
            self.logger.info(f"Deleted short-term memory: {memory_id}")
        except Exception as e:
            self.logger.error(f"Error deleting short-term memory: {e}")

    async def cleanup_expired_memories(self) -> int:
        """Remove all expired memories and return the count of deleted items."""
        try:
            if self.supabase:
                current_time = datetime.utcnow().isoformat()
                result = self.supabase.table("short_term")\
                    .delete()\
                    .lt("expires_at", current_time)\
                    .execute()

                deleted_count = len(result.data)
            else:
                # Clean up local memory
                current_time = datetime.utcnow()
                expired_keys = [k for k, v in self.memory_store.items() if v.expires_at < current_time]
                for key in expired_keys:
                    del self.memory_store[key]
                deleted_count = len(expired_keys)
                
            self.logger.info(f"Cleaned up {deleted_count} expired memories")
            return deleted_count
        except Exception as e:
            self.logger.error(f"Error cleaning up expired memories: {e}")
            return 0

def get_short_term_memory_manager() -> ShortTermMemoryManager:
    """Get a ShortTermMemoryManager instance."""
    return ShortTermMemoryManager() 