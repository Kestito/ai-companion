import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
import json

from supabase import create_client, Client
from pydantic import BaseModel, Field

from ai_companion.settings import settings


class ShortTermMemoryItem(BaseModel):
    """Data model for a short-term memory item."""

    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    patient_id: Optional[str] = None
    conversation_id: Optional[str] = None


class ShortTermMemory:
    """Manages short-term conversational memory using an in-memory store and Supabase persistence."""

    def __init__(
        self,
        supabase_url: str = settings.SUPABASE_URL,
        supabase_key: str = settings.SUPABASE_KEY,
        table_name: str = "short_term_memory",
    ):
        self.logger = logging.getLogger(__name__)
        self.table_name = table_name
        self.memory_store = {}  # Always initialize in-memory store as fallback
        self.table_exists = False  # Initialize table_exists flag

        try:
            # Use correct setting name: settings.SUPABASE_KEY
            self.supabase: Client = create_client(supabase_url, supabase_key)
            self.logger.info(f"Connected to Supabase at {supabase_url}")
            # We need to await the initialization
            # asyncio.run(self._initialize_table()) # This might block, call it elsewhere or make __init__ async
            self.table_exists = True  # Assume connection implies existence for now, _initialize_table needs proper async handling
            # TODO: Properly handle async table initialization
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
            self.logger.warning(
                "Falling back to in-memory store after table initialization failure"
            )

    async def add_memory(
        self,
        session_id: str,
        content: Dict,
        metadata: Dict,
        patient_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ):
        """Adds a memory item to the store and persists it to Supabase."""
        if not session_id:
            self.logger.error("Session ID is required to add memory.")
            return

        created_at = datetime.utcnow()

        memory = ShortTermMemoryItem(
            session_id=session_id,
            created_at=created_at,
            content=content,
            metadata=metadata,
            patient_id=patient_id,
            conversation_id=conversation_id,
        )

        # Add to in-memory store
        key = f"{session_id}::{created_at.isoformat()}"  # Use timestamp for uniqueness
        self.memory_store[key] = memory
        self.logger.debug(f"Added memory item to in-memory store: {key}")

        # Persist to Supabase
        await self._persist_memory(memory)

    async def _persist_memory(self, memory: ShortTermMemoryItem):
        """Persists a single memory item to Supabase."""
        if not self.supabase or not self.table_exists:
            self.logger.warning(
                "Supabase not initialized or table doesn't exist. Cannot persist memory."
            )
            return

        try:
            # Simplify for database schema - only use fields that exist in the table
            # Looking at the logs, only these fields are recognized
            record = {
                "context": {
                    "metadata": {
                        **memory.metadata,
                        "session_id": memory.session_id,  # Include session_id in metadata
                    },
                    "content": memory.content,
                    "created_at": memory.created_at.isoformat(),
                }
            }

            # Add patient_id only if it looks like a valid UUID (36 chars with hyphens in right places)
            if (
                memory.patient_id
                and isinstance(memory.patient_id, str)
                and len(memory.patient_id) == 36
                and memory.patient_id.count("-") == 4
            ):
                record["patient_id"] = memory.patient_id
            else:
                # If not a valid UUID format, include it in the metadata only
                record["context"]["metadata"]["patient_id"] = memory.patient_id

            if memory.conversation_id:
                # Only add if it looks like a valid UUID
                if (
                    isinstance(memory.conversation_id, str)
                    and len(memory.conversation_id) == 36
                    and memory.conversation_id.count("-") == 4
                ):
                    record["conversation_id"] = memory.conversation_id
                else:
                    # Store in metadata instead
                    record["context"]["metadata"]["conversation_id"] = (
                        memory.conversation_id
                    )

            response = self.supabase.table(self.table_name).insert(record).execute()
            if response.data:
                self.logger.debug(
                    f"Successfully persisted memory item to Supabase for session {memory.session_id}"
                )
            else:
                self.logger.error(
                    f"Failed to persist memory item to Supabase for session {memory.session_id}. Response: {response}"
                )
        except Exception as e:
            self.logger.error(
                f"Error persisting memory item to Supabase: {e}", exc_info=True
            )

    async def get_memories(
        self, session_id: str, limit: int = 10, patient_id: Optional[str] = None
    ) -> List[ShortTermMemoryItem]:
        """Retrieves memory items for a session, optionally filtered by patient_id."""
        if not session_id and not patient_id:
            self.logger.error(
                "Either session_id or patient_id is required to get memories."
            )
            return []

        # 1. Get from in-memory store (filter by session/patient)
        in_memory_memories = []
        for mem in self.memory_store.values():
            match = False
            if patient_id and mem.patient_id == patient_id:
                match = True
            elif session_id and mem.session_id == session_id:
                # Match if patient_id filter wasn't active or didn't match
                if not patient_id or mem.patient_id != patient_id:
                    match = True

            if match:
                in_memory_memories.append(mem)

        # Sort in-memory by creation time (most recent first)
        in_memory_memories.sort(key=lambda x: x.created_at, reverse=True)

        # 2. If not enough in memory, query Supabase
        if len(in_memory_memories) < limit:
            needed = limit - len(in_memory_memories)
            db_memories = await self._query_supabase(session_id, needed, patient_id)

            # Combine and deduplicate (prefer in-memory versions)
            combined_memories = list(in_memory_memories)  # Make a copy
            in_memory_keys = set(
                f"{m.session_id}::{m.created_at.isoformat()}"
                for m in in_memory_memories
            )

            for db_mem in db_memories:
                db_key = f"{db_mem.session_id}::{db_mem.created_at.isoformat()}"
                if db_key not in in_memory_keys:
                    combined_memories.append(db_mem)

            # Sort final list by creation time (most recent first)
            combined_memories.sort(key=lambda x: x.created_at, reverse=True)
            return combined_memories[:limit]
        else:
            return in_memory_memories[:limit]

    async def _query_supabase(
        self, session_id: str, limit: int, patient_id: Optional[str] = None
    ) -> List[ShortTermMemoryItem]:
        """Queries Supabase for memory items."""
        if not self.supabase or not self.table_exists:
            return []

        memories = []
        try:
            query = self.supabase.table(self.table_name).select("*")

            if patient_id:
                query = query.eq("patient_id", patient_id)
            elif session_id:
                query = query.eq("session_id", session_id)
            else:
                return []  # Should not happen based on caller check

            query = query.order("created_at", desc=True).limit(limit)

            response = query.execute()

            if response.data:
                for item in response.data:
                    try:
                        content_data = json.loads(item.get("content", "{}"))
                        metadata_data = json.loads(item.get("metadata", "{}"))
                        memories.append(
                            ShortTermMemoryItem(
                                session_id=item["session_id"],
                                created_at=datetime.fromisoformat(item["created_at"]),
                                content=content_data,
                                metadata=metadata_data,
                                patient_id=item.get("patient_id"),
                                conversation_id=item.get("conversation_id"),
                            )
                        )
                    except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
                        self.logger.error(
                            f"Error parsing memory item from Supabase (ID: {item.get('id')}): {e}"
                        )
            return memories
        except Exception as e:
            self.logger.error(
                f"Error querying Supabase for memories: {e}", exc_info=True
            )
            return []

    async def prune_expired_memories(self):
        """Removes expired memories from the in-memory store and Supabase."""
        # This entire method is now obsolete as there's no expires_at
        self.logger.info("Pruning based on expires_at is disabled.")
        pass

    # ... (keep other methods like clear_session, clear_all)


def get_short_term_memory_manager() -> ShortTermMemory:
    """Get a ShortTermMemoryManager instance."""
    return ShortTermMemory()
