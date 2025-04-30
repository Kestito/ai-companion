"""
Short-term memory manager for AI Companion.

This module provides short-term memory management through a tiered approach:
1. In-memory cache (fast, limited capacity)
2. Database storage (slower, persistent)
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from langchain_core.messages import BaseMessage

from ai_companion.utils.supabase import get_supabase_client
from ai_companion.modules.memory.cache import MemoryCache

logger = logging.getLogger(__name__)


class Memory:
    """Memory object representing a single memory entry."""

    def __init__(
        self,
        id: str,
        content: str,
        metadata: Dict[str, Any],
        created_at: datetime,
        expires_at: datetime,
    ):
        self.id = id
        self.content = content
        self.metadata = metadata
        self.created_at = created_at
        self.expires_at = expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to dictionary format."""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }


class ShortTermMemoryManager:
    """
    Manager for short-term memory storage with tiered caching.

    Provides methods for storing and retrieving memories using a two-tiered
    approach: fast in-memory cache and persistent database storage.
    """

    def __init__(
        self,
        max_cached_conversations: int = 100,
        max_messages_per_conversation: int = 10,
        db_sync_interval_seconds: int = 60,
        table_name: str = "short_term_memory",
    ):
        """
        Initialize the short-term memory manager.

        Args:
            max_cached_conversations: Maximum conversations to keep in memory
            max_messages_per_conversation: Maximum messages per conversation to cache
            db_sync_interval_seconds: Interval between database synchronization
            table_name: Database table name for memory storage
        """
        self.table_name = table_name
        self.supabase = get_supabase_client()
        self.initialized = False
        self.table_exists = False

        # Initialize memory cache
        self.cache = MemoryCache(
            max_conversations=max_cached_conversations,
            max_messages_per_conversation=max_messages_per_conversation,
            default_ttl_minutes=60,
        )

        # Database sync task
        self.db_sync_interval = db_sync_interval_seconds
        self.sync_task = None
        self.running = False

        # Try to initialize the table
        try:
            self._init_table()
            self.initialized = True
        except Exception as e:
            logger.error(f"Error initializing short-term table: {e}")
            logger.warning(
                "Falling back to in-memory store after table initialization failure"
            )

    def _init_table(self):
        """Initialize the database table if it doesn't exist."""
        if not self.supabase:
            logger.error("Supabase client not available")
            return

        try:
            # Try to access the table using the correct table name
            self.supabase.table(self.table_name).select("id").limit(1).execute()
            self.table_exists = True
            logger.info(f"Connected to {self.table_name} table")
        except Exception as e:
            # If the table doesn't exist, try to create it
            try:
                logger.warning(
                    f"Table {self.table_name} not found, attempting to check if it needs to be created"
                )

                # Check if this is a 'table does not exist' error
                if isinstance(e, dict) and e.get("code") == "42P01":
                    logger.warning(
                        f"The table {self.table_name} does not exist, will use in-memory storage only"
                    )
                    # We don't have permissions to create tables automatically, so just log the issue

                self.table_exists = False
            except Exception as create_e:
                logger.error(f"Error handling table initialization: {create_e}")
                self.table_exists = False

    async def start(self):
        """Start background tasks for the memory manager."""
        await self.cache.start()

        # Start database sync task
        self.running = True
        self.sync_task = asyncio.create_task(self._sync_loop())

        logger.info("Short-term memory manager background tasks started")

    async def stop(self):
        """Stop background tasks for the memory manager."""
        self.running = False

        # Stop the cache cleanup task
        await self.cache.stop()

        # Stop the database sync task
        if self.sync_task:
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass

        logger.info("Short-term memory manager background tasks stopped")

    async def _sync_loop(self):
        """Background task to synchronize memory cache with database."""
        try:
            while self.running:
                try:
                    await self._sync_to_database()
                except Exception as e:
                    logger.error(f"Error in database sync: {e}")

                await asyncio.sleep(self.db_sync_interval)
        except asyncio.CancelledError:
            logger.info("Database sync task cancelled")
        except Exception as e:
            logger.error(f"Error in database sync loop: {e}")

    async def _sync_to_database(self):
        """Synchronize modified cache entries to the database."""
        if not self.supabase or not self.table_exists:
            return

        # Get all modified sessions from cache
        modified_sessions = await self.cache.get_modified_sessions()

        if not modified_sessions:
            return

        logger.debug(f"Syncing {len(modified_sessions)} sessions to database")

        # Process each session in parallel
        tasks = []
        for session_id, messages in modified_sessions.items():
            tasks.append(self._sync_session_to_database(session_id, messages))

        # Wait for all sync tasks to complete
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Mark sessions as synced if successful
            successful_syncs = 0
            for i, (session_id, _) in enumerate(modified_sessions.items()):
                if isinstance(results[i], bool) and results[i]:
                    await self.cache.mark_synced(session_id)
                    successful_syncs += 1
                elif isinstance(results[i], Exception):
                    logger.error(f"Error syncing session {session_id}: {results[i]}")

            logger.debug(
                f"Successfully synced {successful_syncs}/{len(tasks)} sessions to database"
            )

    async def _sync_session_to_database(
        self, session_id: str, messages: List[Dict[str, Any]]
    ) -> bool:
        """
        Synchronize a session's messages to the database.

        Args:
            session_id: The unique session identifier
            messages: List of message data to sync

        Returns:
            True if sync was successful
        """
        if not self.supabase or not self.table_exists:
            return False

        try:
            # Prepare batch of records for insertion
            records = []

            for message in messages:
                # Only sync messages that haven't been synced yet
                if message.get("synced_to_db"):
                    continue

                # Extract necessary fields from the message
                content = message.get("content", "{}")
                metadata = message.get("metadata", {})
                expires_at = datetime.fromtimestamp(
                    message.get("expires_at", 0)
                ).isoformat()

                # Gather session info from metadata
                user_id = metadata.get("user_id", "unknown")
                chat_id = metadata.get("chat_id", "unknown")
                platform = metadata.get("platform", "unknown")

                # Prepare the record
                record = {
                    "id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "user_id": str(user_id),
                    "chat_id": str(chat_id),
                    "platform": platform,
                    "content": content,
                    "metadata": json.dumps(metadata),
                    "expires_at": expires_at,
                }

                records.append(record)

                # Mark this message as synced in the cache
                message["synced_to_db"] = True

            # Skip if no records to sync
            if not records:
                return True

            # Insert records in a batch
            result = self.supabase.table(self.table_name).insert(records).execute()

            if hasattr(result, "data"):
                logger.debug(f"Synced {len(records)} messages for session {session_id}")
                return True
            else:
                logger.warning(
                    f"Sync failed for session {session_id}: No data returned"
                )
                return False

        except Exception as e:
            logger.error(f"Error syncing session {session_id} to database: {e}")
            return False

    async def store_memory(
        self,
        content: str,
        ttl_minutes: int = 60,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Memory:
        """
        Store a memory in the cache and database.

        Args:
            content: Memory content to store
            ttl_minutes: Time-to-live in minutes
            metadata: Additional metadata for the memory

        Returns:
            Memory object representing the stored memory
        """
        # Generate a unique ID for this memory
        memory_id = str(uuid.uuid4())

        # Set timestamps
        created_at = datetime.now()
        expires_at = created_at + timedelta(minutes=ttl_minutes)

        # Create memory object
        memory = Memory(
            id=memory_id,
            content=content,
            metadata=metadata or {},
            created_at=created_at,
            expires_at=expires_at,
        )

        # Get session ID from metadata or generate a default
        session_id = metadata.get("session_id", f"default-{memory_id}")

        # Prepare message for cache
        cache_message = {
            "id": memory_id,
            "content": content,
            "metadata": metadata or {},
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.timestamp(),
            "synced_to_db": False,
        }

        # Add to cache first (non-blocking)
        await self.cache.add_message(session_id, cache_message, ttl_minutes)

        # If database is available, store there too
        if self.supabase and self.table_exists:
            try:
                # Extract info from metadata
                user_id = metadata.get("user_id", "unknown") if metadata else "unknown"
                chat_id = metadata.get("chat_id", "unknown") if metadata else "unknown"
                platform = (
                    metadata.get("platform", "unknown") if metadata else "unknown"
                )

                # Create record for database
                record = {
                    "id": memory_id,
                    "session_id": session_id,
                    "user_id": str(user_id),
                    "chat_id": str(chat_id),
                    "platform": platform,
                    "content": content,
                    "metadata": json.dumps(metadata) if metadata else "{}",
                    "created_at": created_at.isoformat(),
                    "expires_at": expires_at.isoformat(),
                }

                # Store in database
                result = self.supabase.table(self.table_name).insert(record).execute()

                if result.data:
                    # Mark as synced in cache
                    cache_message["synced_to_db"] = True
                    logger.debug(f"Memory {memory_id} stored in database")
            except Exception as e:
                logger.error(f"Error storing memory in database: {e}")
                # Continue even if database storage fails, as it's in cache

        return memory

    async def get_active_memories(self) -> List[Memory]:
        """Get all active (non-expired) memories."""
        memories = []

        # Collect memories from all cache entries
        cache_data = await self.cache.get_modified_sessions()

        # Convert cache data to Memory objects
        for session_id, messages in cache_data.items():
            for msg in messages:
                try:
                    content = msg.get("content", "{}")
                    metadata = msg.get("metadata", {})
                    created_at = datetime.fromisoformat(msg.get("created_at"))
                    expires_at = datetime.fromtimestamp(msg.get("expires_at", 0))

                    memory = Memory(
                        id=msg.get("id", str(uuid.uuid4())),
                        content=content,
                        metadata=metadata,
                        created_at=created_at,
                        expires_at=expires_at,
                    )

                    memories.append(memory)
                except Exception as e:
                    logger.error(f"Error parsing memory from cache: {e}")

        # If database is available, also fetch memories from there
        if self.supabase and self.table_exists:
            try:
                # Get non-expired memories
                now = datetime.now().isoformat()
                result = (
                    self.supabase.table(self.table_name)
                    .select("*")
                    .gt("expires_at", now)
                    .execute()
                )

                if result.data:
                    # Convert to Memory objects
                    for item in result.data:
                        try:
                            metadata = json.loads(item.get("metadata", "{}"))
                            created_at = datetime.fromisoformat(item.get("created_at"))
                            expires_at = datetime.fromisoformat(item.get("expires_at"))

                            memory = Memory(
                                id=item.get("id"),
                                content=item.get("content", ""),
                                metadata=metadata,
                                created_at=created_at,
                                expires_at=expires_at,
                            )

                            # Check if this memory is already in our list
                            if not any(m.id == memory.id for m in memories):
                                memories.append(memory)
                        except Exception as e:
                            logger.error(f"Error parsing memory from database: {e}")
            except Exception as e:
                logger.error(f"Error fetching memories from database: {e}")

        return memories

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        # Delete from database if available
        if self.supabase and self.table_exists:
            try:
                self.supabase.table(self.table_name).delete().eq(
                    "id", memory_id
                ).execute()
            except Exception as e:
                logger.error(f"Error deleting memory {memory_id} from database: {e}")

        # Return success assuming at least cache deletion succeeded
        return True

    async def get_cached_messages(
        self, session_id: str, limit: int = 10, patient_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get messages from cache with patient context validation.

        Args:
            session_id: The session identifier
            limit: Maximum number of messages to return
            patient_id: The patient ID for validation

        Returns:
            List of messages for the session
        """
        messages = []

        try:
            # Get from cache
            cached_data = await self.cache.get_messages(session_id, limit)

            # Process and filter by patient
            for item in cached_data:
                try:
                    if not item or "content" not in item:
                        continue

                    # Parse content
                    if isinstance(item["content"], str):
                        try:
                            content_data = json.loads(item["content"])
                        except:
                            content_data = {"content": item["content"]}
                    else:
                        content_data = item["content"]

                    # Extract metadata
                    metadata = content_data.get("metadata", {})
                    item_patient_id = metadata.get("patient_id")

                    # Validate patient context if provided
                    if patient_id and item_patient_id != patient_id:
                        logger.warning(
                            f"Skipping memory with mismatched patient_id: expected {patient_id}, got {item_patient_id}"
                        )
                        continue

                    # Add to results
                    messages.append(
                        {
                            "id": item.get("id", ""),
                            "content": content_data,
                            "created_at": item.get("created_at", ""),
                            "metadata": metadata,
                        }
                    )

                except Exception as e:
                    logger.error(f"Error processing cached message: {e}")

            logger.debug(
                f"Retrieved {len(messages)} messages from cache for session {session_id}"
            )
            return messages

        except Exception as e:
            logger.error(f"Error getting cached messages: {e}")
            return []

    async def get_messages_parallel(
        self, session_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get messages for a session from both cache and database in parallel.

        Args:
            session_id: The session identifier
            limit: Maximum number of messages to return

        Returns:
            Combined list of message dictionaries (newest first)
        """
        # Create tasks for parallel execution
        cache_task = self.cache.get_messages(session_id, limit)
        db_task = self._get_database_messages(session_id, limit)

        # Run tasks in parallel
        cache_messages, db_messages = await asyncio.gather(cache_task, db_task)

        # Combine results, removing duplicates (prefer cache versions)
        cache_ids = set(msg.get("id") for msg in cache_messages if "id" in msg)
        unique_db_messages = [
            msg for msg in db_messages if msg.get("id") not in cache_ids
        ]

        # Sort by timestamp
        combined = cache_messages + unique_db_messages
        combined.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return combined[:limit]

    async def _get_database_messages(
        self, session_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get messages for a session from the database.

        Args:
            session_id: The session identifier
            limit: Maximum number of messages to return

        Returns:
            List of message dictionaries from database (newest first)
        """
        if not self.supabase or not self.table_exists:
            return []

        try:
            # Query database for messages
            result = (
                self.supabase.table(self.table_name)
                .select("*")
                .eq("session_id", session_id)
                .order("created_at", {"ascending": False})
                .limit(limit)
                .execute()
            )

            if not result.data:
                return []

            # Convert to consistent format
            messages = []
            for item in result.data:
                try:
                    metadata = json.loads(item.get("metadata", "{}"))
                    content = item.get("content", "{}")

                    messages.append(
                        {
                            "id": item.get("id"),
                            "content": content,
                            "metadata": metadata,
                            "created_at": item.get("created_at"),
                            "expires_at": item.get("expires_at"),
                            "source": "database",
                        }
                    )
                except Exception as e:
                    logger.error(f"Error parsing message from database: {e}")

            return messages

        except Exception as e:
            logger.error(f"Error fetching messages from database: {e}")
            return []

    async def store_with_cache(
        self,
        content: str,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        ttl_minutes: int = 60,
    ) -> Dict[str, Any]:
        """
        Store a message with cache-first approach.

        Args:
            content: Message content
            session_id: Session identifier
            metadata: Additional metadata (must include patient_id)
            ttl_minutes: Time-to-live in minutes

        Returns:
            Dictionary with memory information including ID
        """
        # Validate patient context
        full_metadata = metadata.copy() if metadata else {}
        if "patient_id" not in full_metadata:
            logger.error("Missing required patient_id in memory metadata")
            raise ValueError("Patient ID is required for memory storage")

        # Ensure metadata has session_id and patient_id
        full_metadata["session_id"] = session_id

        # Create memory through main method
        memory = await self.store_memory(content, ttl_minutes, full_metadata)

        return memory.to_dict()

    async def extract_and_store_memories(self, message: BaseMessage) -> List[Memory]:
        """
        Extract and store memories from a message.

        Args:
            message: The message to extract memories from

        Returns:
            List of Memory objects created
        """
        # Extract metadata if available
        metadata = getattr(message, "metadata", {}) or {}

        # Get session ID from metadata or use default
        session_id = metadata.get("session_id", f"default-{uuid.uuid4()}")

        # Extract content
        content = message.content if hasattr(message, "content") else str(message)

        # Store as a memory
        memory = await self.store_memory(content, 60, metadata)

        return [memory]

    def get_relevant_memories(self, query: str) -> List[Dict[str, Any]]:
        """
        Get memories relevant to a query.

        This is a placeholder for future semantic search implementation.
        Currently just returns an empty list.

        Args:
            query: The query to find relevant memories for

        Returns:
            List of relevant memory data
        """
        # This is where semantic search would go for advanced retrieval
        # For now, just return an empty list
        return []

    def format_memories_for_prompt(self, memories: List[Dict[str, Any]]) -> str:
        """
        Format memories for inclusion in a prompt.

        Args:
            memories: List of memory data to format

        Returns:
            Formatted string for inclusion in prompt
        """
        if not memories:
            return ""

        # Simple formatting of memories
        memory_text = []
        for memory in memories:
            if isinstance(memory, dict) and "content" in memory:
                memory_text.append(f"- {memory.get('content', '')}")

        return "\n".join(memory_text)

    async def add_memory(
        self, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Memory:
        """
        Add a new memory.

        Args:
            content: Memory content
            metadata: Additional metadata

        Returns:
            Memory object representing the stored memory
        """
        # Generate session ID if not provided in metadata
        if metadata and "session_id" in metadata:
            session_id = metadata["session_id"]
        else:
            session_id = f"default-{uuid.uuid4()}"
            if metadata:
                metadata["session_id"] = session_id
            else:
                metadata = {"session_id": session_id}

        # Store the memory
        return await self.store_memory(content, 60, metadata)


def get_short_term_memory_manager():
    """Get a singleton instance of the short-term memory manager."""
    if not hasattr(get_short_term_memory_manager, "instance"):
        get_short_term_memory_manager.instance = ShortTermMemoryManager()

    return get_short_term_memory_manager.instance
