import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json

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
        self.table_name = "short_term_memory"  # Define the table name as a class attribute
        self.memory_store = {}  # Always initialize in-memory store as fallback
        
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
            self.logger.warning("Using in-memory fallback for memory management")

    def _initialize_table(self) -> None:
        """Initialize the short-term memories table if it doesn't exist."""
        if not self.supabase:
            self.logger.warning("Skipping table initialization - using in-memory store")
            return
            
        try:
            # Create table if not exists using SQL
            self.supabase.table(self.table_name).select("id").limit(1).execute()
            self.logger.info(f"Successfully verified access to {self.table_name} table")
        except Exception as e:
            self.logger.error(f"Error initializing {self.table_name} table: {e}")
            # Don't raise, just log and continue with in-memory store
            self.supabase = None
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

            # Check if we have necessary data for database storage
            patient_id = metadata.get("patient_id") if metadata else None
            conversation_id = metadata.get("conversation_id") if metadata else None
            
            # Only use database if we have Supabase client
            if self.supabase:
                try:
                    # Create context object with content and metadata
                    context = {
                        "content": content,
                        "metadata": metadata or {},
                        "created_at": datetime.utcnow().isoformat()
                    }
                    
                    # Prepare record for db insert with correct schema
                    record = {
                        "id": memory.id,
                        "context": context,
                        "expires_at": memory.expires_at.isoformat()
                    }
                    
                    # Add patient_id and conversation_id if available
                    if patient_id:
                        record["patient_id"] = patient_id
                    
                    if conversation_id:
                        record["conversation_id"] = conversation_id
                    
                    # Insert into database
                    result = self.supabase.table(self.table_name).insert(record).execute()
                    self.logger.info(f"Memory stored in database with ID: {memory.id}")
                except Exception as e:
                    self.logger.error(f"Error storing memory in database: {e}")
                    # Fall back to in-memory storage
                    self.memory_store[memory.id] = memory
                    self.logger.info(f"Memory stored in-memory (fallback) with ID: {memory.id}")
            else:
                # Store in local memory
                self.memory_store[memory.id] = memory
                self.logger.info(f"Memory stored in-memory with ID: {memory.id}")

            return memory
        except Exception as e:
            self.logger.error(f"Error storing short-term memory: {e}")
            # Still return the memory object even if storage failed
            return memory

    async def get_memory(self, memory_id: str) -> Optional[ShortTermMemory]:
        """Retrieve a specific short-term memory by ID if not expired."""
        try:
            # First check in-memory store
            if memory_id in self.memory_store:
                memory = self.memory_store[memory_id]
                if memory.expires_at < datetime.utcnow():
                    del self.memory_store[memory_id]
                    return None
                return memory
                
            # Then check database if available
            if self.supabase:
                result = self.supabase.table(self.table_name).select("*").eq("id", memory_id).execute()
                
                if not result.data:
                    return None

                memory_data = result.data[0]
                if datetime.fromisoformat(memory_data["expires_at"]) < datetime.utcnow():
                    await self.delete_memory(memory_id)
                    return None

                # Extract content and metadata from context
                context = memory_data.get("context", {})
                content = context.get("content", "")
                metadata = context.get("metadata", {})
                created_at_str = context.get("created_at")
                
                # Parse created_at or use current time
                if created_at_str:
                    try:
                        created_at = datetime.fromisoformat(created_at_str)
                    except (ValueError, TypeError):
                        created_at = datetime.utcnow()
                else:
                    created_at = datetime.utcnow()
                
                # Create a memory object with the extracted data
                return ShortTermMemory(
                    id=memory_data["id"],
                    content=content,
                    created_at=created_at,
                    expires_at=datetime.fromisoformat(memory_data["expires_at"]),
                    metadata=metadata
                )
                
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving short-term memory: {e}")
            return None

    async def get_active_memories(self) -> List[ShortTermMemory]:
        """Retrieve all non-expired short-term memories."""
        memories = []
        
        try:
            # First get memories from in-memory store
            current_time = datetime.utcnow()
            in_memory_memories = [mem for mem in self.memory_store.values() if mem.expires_at > current_time]
            memories.extend(in_memory_memories)
            
            # Then get from database if available
            if self.supabase:
                try:
                    current_time_str = datetime.utcnow().isoformat()
                    result = self.supabase.table(self.table_name)\
                        .select("*")\
                        .gt("expires_at", current_time_str)\
                        .execute()

                    for item in result.data:
                        try:
                            # Extract content and metadata from context
                            context = item.get("context", {})
                            content = context.get("content", "")
                            metadata = context.get("metadata", {})
                            created_at_str = context.get("created_at")
                            
                            # Parse created_at or use current time
                            if created_at_str:
                                try:
                                    created_at = datetime.fromisoformat(created_at_str)
                                except (ValueError, TypeError):
                                    created_at = datetime.utcnow()
                            else:
                                created_at = datetime.utcnow()
                            
                            memory = ShortTermMemory(
                                id=item["id"],
                                content=content,
                                created_at=created_at,
                                expires_at=datetime.fromisoformat(item["expires_at"]),
                                metadata=metadata
                            )
                            
                            # Only add if not already in memories (by ID)
                            if not any(mem.id == memory.id for mem in memories):
                                memories.append(memory)
                        except Exception as e:
                            self.logger.error(f"Error parsing memory from database: {e}")
                except Exception as e:
                    self.logger.error(f"Error retrieving memories from database: {e}")
            
            return memories
        except Exception as e:
            self.logger.error(f"Error retrieving active memories: {e}")
            return []

    async def delete_memory(self, memory_id: str) -> None:
        """Delete a specific short-term memory."""
        try:
            # Delete from in-memory store if present
            if memory_id in self.memory_store:
                del self.memory_store[memory_id]
                
            # Delete from database if available
            if self.supabase:
                try:
                    self.supabase.table(self.table_name).delete().eq("id", memory_id).execute()
                except Exception as e:
                    self.logger.error(f"Error deleting memory from database: {e}")
                    
            self.logger.info(f"Deleted short-term memory: {memory_id}")
        except Exception as e:
            self.logger.error(f"Error deleting short-term memory: {e}")

    async def cleanup_expired_memories(self) -> int:
        """Remove all expired memories and return the count of deleted items."""
        try:
            deleted_count = 0
            
            # Clean up in-memory store
            current_time = datetime.utcnow()
            expired_keys = [k for k, v in self.memory_store.items() if v.expires_at < current_time]
            for key in expired_keys:
                del self.memory_store[key]
            deleted_count += len(expired_keys)
            
            # Clean up database if available
            if self.supabase:
                try:
                    current_time_str = datetime.utcnow().isoformat()
                    result = self.supabase.table(self.table_name)\
                        .delete()\
                        .lt("expires_at", current_time_str)\
                        .execute()

                    deleted_count += len(result.data)
                except Exception as e:
                    self.logger.error(f"Error cleaning up expired memories from database: {e}")
                
            self.logger.info(f"Cleaned up {deleted_count} expired memories")
            return deleted_count
        except Exception as e:
            self.logger.error(f"Error cleaning up expired memories: {e}")
            return 0

def get_short_term_memory_manager() -> ShortTermMemoryManager:
    """Get a ShortTermMemoryManager instance."""
    return ShortTermMemoryManager() 