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
from dataclasses import dataclass

from langchain_core.messages import BaseMessage

from ai_companion.utils.supabase import get_supabase_client
from ai_companion.modules.memory.cache import MemoryCache
from ai_companion.modules.memory.types import Memory

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """Represents an item in memory."""

    session_id: str
    created_at: datetime
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    patient_id: Optional[str] = None  # Added patient_id
    conversation_id: Optional[str] = None

    def __init__(
        self,
        session_id,
        created_at,
        content,
        metadata,
        patient_id=None,
        conversation_id=None,
    ):
        self.session_id = session_id
        self.created_at = created_at
        self.content = content
        self.metadata = metadata
        self.patient_id = patient_id
        self.conversation_id = conversation_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert MemoryItem to dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "content": self.content,
            "metadata": self.metadata,
            "patient_id": self.patient_id,
            "conversation_id": self.conversation_id,
        }


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
            default_ttl_minutes=525600,  # 1 year - memories should not expire
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
                user_id = metadata.get("user_id", "unknown") if metadata else "unknown"
                chat_id = metadata.get("chat_id", "unknown") if metadata else "unknown"
                platform = (
                    metadata.get("platform", "unknown") if metadata else "unknown"
                )
                patient_id = metadata.get("patient_id") if metadata else None
                conversation_id = (
                    metadata.get("conversation_id")
                    if metadata and "conversation_id" in metadata
                    else None
                )

                # Prepare the record
                record = {
                    "id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "user_id": str(user_id),
                    "chat_id": str(chat_id),
                    "platform": platform,
                    "patient_id": patient_id,
                    "conversation_id": conversation_id,
                    "content": content,
                    "context": json.dumps(
                        {
                            "metadata": metadata,
                            "content": content,
                            "platform": platform,
                            "user_id": user_id,
                            "created_at": datetime.now().isoformat(),
                        }
                    ),
                    "created_at": expires_at,
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
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Memory:
        """
        Store a memory in the cache and database.

        Args:
            content: Memory content to store
            ttl_minutes: Time-to-live in minutes (default: 1 year, memories should not expire)
            metadata: Additional metadata for the memory

        Returns:
            Memory object representing the stored memory
        """
        # Generate a unique ID for this memory
        memory_id = str(uuid.uuid4())

        # Set timestamps
        created_at = datetime.now()
        # Set expires_at to a year from now (we don't use expiration)
        expires_at = created_at + timedelta(days=365)

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
        await self.cache.add_message(session_id, cache_message)

        # If database is available, store there too
        if self.supabase and self.table_exists:
            try:
                # Extract info from metadata
                user_id = metadata.get("user_id", "unknown") if metadata else "unknown"
                platform = (
                    metadata.get("platform", "unknown") if metadata else "unknown"
                )

                # Explicitly extract patient_id from metadata
                patient_id = None
                if metadata:
                    # Try to get patient_id directly from metadata
                    patient_id = metadata.get("patient_id")

                    # If not found, look in nested structures
                    if not patient_id and "context" in metadata:
                        context = metadata.get("context", {})
                        if isinstance(context, dict):
                            patient_id = context.get("patient_id")

                conversation_id = (
                    metadata.get("conversation_id")
                    if metadata and "conversation_id" in metadata
                    else None
                )

                # Create record for database using only columns that exist in the schema
                record = {
                    "id": memory_id,
                    "patient_id": patient_id,  # Store patient_id in dedicated column
                    "conversation_id": conversation_id,
                    "context": json.dumps(
                        {
                            "metadata": metadata,
                            "content": content,
                            "platform": platform,
                            "user_id": user_id,
                            "created_at": datetime.now().isoformat(),
                        }
                    ),
                }

                # Log the patient_id being stored
                if patient_id:
                    logger.info(
                        f"Storing memory {memory_id} with patient_id: {patient_id}"
                    )
                else:
                    logger.warning(f"Storing memory {memory_id} without patient_id")

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
                # Get all memories from the database with a limit
                result = (
                    self.supabase.table(self.table_name)
                    .select("*")
                    .order("id", desc=True)  # Order by ID
                    .limit(10)  # Add a limit to prevent fetching too many records
                    .execute()
                )

                if result.data:
                    # Convert to Memory objects
                    for item in result.data:
                        try:
                            metadata = {}
                            if "context" in item:
                                context = item.get("context", "{}")
                                if isinstance(context, str):
                                    context_data = json.loads(context)
                                    metadata = context_data.get("metadata", {})
                                elif isinstance(context, dict):
                                    metadata = context.get("metadata", {})

                            created_at = datetime.now()  # Default to now
                            if "created_at" in item:
                                created_at = datetime.fromisoformat(
                                    item.get("created_at")
                                )
                            elif "context" in item and isinstance(
                                item["context"], dict
                            ):
                                context_created = item["context"].get("created_at")
                                if context_created:
                                    created_at = datetime.fromisoformat(context_created)

                            # Just use created_at plus a year for expires_at since that column is gone
                            expires_at = created_at + timedelta(days=365)

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
        Get cached messages for a session.

        This is a compatibility method that simply calls get_messages_parallel.

        Args:
            session_id: The session identifier
            limit: Maximum number of messages to retrieve
            patient_id: Optional patient ID

        Returns:
            List of message dictionaries
        """
        try:
            logger.info(
                f"get_cached_messages called with session_id={session_id}, patient_id={patient_id}"
            )
            return await self.get_messages_parallel(session_id, limit, patient_id)
        except Exception as e:
            logger.error(f"Error in get_cached_messages: {e}", exc_info=True)
            return []

    async def get_messages_parallel(
        self, session_id: str, limit: int = 20, patient_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get messages for a session from both cache and database in parallel.

        Args:
            session_id: The session identifier
            limit: Maximum number of messages to return
            patient_id: Optional patient ID

        Returns:
            Combined list of message dictionaries (newest first)
        """
        logger.debug(
            f"Getting messages for session: {session_id}, patient: {patient_id}, limit: {limit}"
        )
        now = datetime.utcnow().isoformat()

        try:
            # Construct the query
            query = self.supabase.table(self.table_name).select(
                "id, context, patient_id, conversation_id"
            )

            # Add patient_id filter if provided
            if patient_id:
                query = query.eq("patient_id", patient_id)
                logger.debug(f"Filtering messages by patient_id: {patient_id}")
            else:
                # If no patient_id, filter by session_id as fallback (less ideal but necessary for some cases)
                query = query.eq("session_id", session_id)
                logger.debug(
                    f"Filtering messages by session_id: {session_id} (no patient_id provided)"
                )

            # Order by 'id' assuming it reflects insertion order.
            # If a reliable 'created_at' exists at the top level, use that.
            query = query.order("id", desc=True)

            result = query.limit(limit).execute()

            if result.data:
                messages = []
                for item in result.data:
                    context = item.get("context", {})
                    # Try to get conversation data directly
                    conversation_data = context.get("conversation")
                    if conversation_data:
                        messages.append(conversation_data)
                    # Fallback: Check if state contains messages (older format?)
                    elif "state" in context and "messages" in context["state"]:
                        state_messages = context["state"]["messages"]
                        if isinstance(state_messages, list) and state_messages:
                            # Add messages from state, trying to format consistently
                            for msg in reversed(
                                state_messages
                            ):  # Add most recent first from state
                                role = "unknown"
                                content = ""
                                if isinstance(msg, dict):
                                    content = msg.get("content", "")
                                    if msg.get("type") == "human":
                                        role = "user"
                                    elif msg.get("type") == "ai":
                                        role = "assistant"
                                elif hasattr(msg, "content"):
                                    content = msg.content
                                    if hasattr(msg, "type"):
                                        if msg.type == "human":
                                            role = "user"
                                        elif msg.type == "ai":
                                            role = "assistant"
                                if role != "unknown" and content:
                                    messages.append({"role": role, "content": content})

                logger.info(
                    f"Retrieved {len(messages)} messages for session {session_id} / patient {patient_id}"
                )
                return messages  # Return in chronological order (oldest first)
            else:
                logger.info(
                    f"No messages found for session {session_id} / patient {patient_id}"
                )
                return []

        except Exception as e:
            logger.error(
                f"Error retrieving messages for session {session_id}: {e}",
                exc_info=True,
            )
            return []

    async def store_with_cache(
        self,
        content: str,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Store a message with cache-first approach.

        Args:
            content: Message content
            session_id: Session identifier
            metadata: Additional metadata (must include patient_id)
            ttl_minutes: Time-to-live in minutes (default: 1 year, memories should not expire)

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
        memory = await self.store_memory(content, full_metadata)

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
        memory = await self.store_memory(content, metadata)

        return [memory]

    def get_relevant_memories(
        self, query: str, patient_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get memories relevant to a query for a specific patient.

        Args:
            query: The query to find relevant memories for
            patient_id: The patient ID to filter memories by

        Returns:
            List of relevant memory data
        """
        if not patient_id:
            logger.warning("No patient_id provided for get_relevant_memories")
            return []

        # If database is not available, return empty list
        if not self.supabase or not self.table_exists:
            logger.warning("Database not available for get_relevant_memories")
            return []

        try:
            # Log the query being made
            logger.info(
                f"Querying memories for patient_id={patient_id} with query: {query[:50]}..."
            )

            # For now, use a simple approach: fetch recent memories for this patient
            # Directly query the patient_id column in the database
            result = (
                self.supabase.table(self.table_name)
                .select("*")
                .eq("patient_id", patient_id)  # Query by dedicated patient_id column
                .order("id", desc=True)  # Order by id as a proxy for recency
                .limit(10)
                .execute()
            )

            # Log raw results for debugging
            logger.info(
                f"Raw DB query returned {len(result.data)} records for patient {patient_id}"
            )
            if result.data and len(result.data) > 0:
                logger.debug(f"First record sample: {str(result.data[0])[:200]}...")

            # Format the data
            memories = []
            for item in result.data:
                try:
                    # Extract full item data for debugging
                    if logger.level <= logging.DEBUG:
                        item_keys = list(item.keys() if hasattr(item, "keys") else {})
                        logger.debug(f"Memory item keys: {item_keys}")

                    # Try to parse context as JSON
                    context_data = {}
                    if item.get("context"):
                        try:
                            context_str = item.get("context")
                            context_data = (
                                json.loads(context_str)
                                if isinstance(context_str, str)
                                else context_str
                            )
                        except json.JSONDecodeError:
                            logger.warning(
                                f"Failed to parse context as JSON: {item.get('context')[:50]}..."
                            )

                    # Initialize metadata dict
                    metadata = {}

                    # Try to get metadata from context
                    if isinstance(context_data, dict):
                        metadata = context_data.get("metadata", {})

                    # If metadata exists directly in item, use it as fallback
                    if not metadata and item.get("metadata"):
                        try:
                            metadata_str = item.get("metadata")
                            metadata = (
                                json.loads(metadata_str)
                                if isinstance(metadata_str, str)
                                else metadata_str
                            )
                        except (json.JSONDecodeError, TypeError):
                            logger.warning(
                                f"Failed to parse metadata: {item.get('metadata')[:50]}..."
                            )

                    # Extract content - try multiple locations
                    content = None

                    # 1. Try content from context
                    if isinstance(context_data, dict) and "content" in context_data:
                        content = context_data.get("content")

                    # 2. Try content directly from item
                    if not content and item.get("content"):
                        content = item.get("content")

                    # If we still don't have content, use empty string
                    if content is None:
                        logger.warning(
                            f"No content found in memory item {item.get('id')}"
                        )
                        content = ""

                    # Log the content source and type for debugging
                    logger.debug(
                        f"Memory content type: {type(content).__name__}, length: {len(str(content))}"
                    )

                    # Parse as JSON if it looks like JSON
                    if (
                        content
                        and isinstance(content, str)
                        and (content.startswith("{") or content.startswith("["))
                    ):
                        try:
                            content_data = json.loads(content)
                            # Check for common memory format
                            if isinstance(content_data, dict):
                                if (
                                    "user_message" in content_data
                                    and "assistant_response" in content_data
                                ):
                                    # Format as conversation
                                    display_content = f"User: {content_data.get('user_message', '')}\nAssistant: {content_data.get('assistant_response', '')}"
                                    content = display_content
                        except json.JSONDecodeError:
                            # Not valid JSON, keep as is
                            pass

                    # Create memory entry
                    memory_item = {
                        "id": item.get("id"),
                        "content": content,
                        "metadata": metadata,
                        "created_at": context_data.get(
                            "created_at", item.get("created_at")
                        ),
                        "timestamp": metadata.get(
                            "timestamp",
                            context_data.get("created_at", item.get("created_at")),
                        ),
                        "relevance": 0.8,  # Placeholder for future relevance scores
                    }

                    # Add memory to results
                    memories.append(memory_item)

                except Exception as e:
                    logger.error(
                        f"Error parsing memory {item.get('id', 'unknown')}: {e}",
                        exc_info=True,
                    )

            logger.info(
                f"Successfully parsed {len(memories)} memories for patient {patient_id}"
            )
            return memories

        except Exception as e:
            logger.error(f"Error in get_relevant_memories: {e}", exc_info=True)
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

        logger.info(f"Formatting {len(memories)} memories for prompt")

        # Simple formatting of memories
        memory_text = []
        for i, memory in enumerate(memories):
            try:
                if not isinstance(memory, dict):
                    logger.warning(
                        f"Memory #{i} is not a dict: {type(memory).__name__}"
                    )
                    continue

                if "content" not in memory:
                    logger.warning(
                        f"Memory #{i} has no content field: {list(memory.keys())}"
                    )
                    continue

                content = memory.get("content", "")
                # Skip empty content
                if not content or not isinstance(content, str) or content.strip() == "":
                    logger.debug(f"Skipping empty content in memory #{i}")
                    continue

                # Format timestamp if available
                timestamp = ""
                if memory.get("timestamp"):
                    try:
                        # Try to parse timestamp in various formats
                        ts = memory.get("timestamp")
                        if isinstance(ts, str):
                            if "T" in ts:
                                # ISO format
                                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                            else:
                                # Try simple format
                                dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                            timestamp = f"[{dt.strftime('%Y-%m-%d %H:%M')}] "
                    except (ValueError, TypeError):
                        # If timestamp parsing fails, ignore it
                        pass

                # Add formatted memory to the list
                memory_text.append(f"- {timestamp}{content}")
                logger.debug(f"Added memory #{i} to prompt: {content[:50]}...")

            except Exception as e:
                logger.error(f"Error formatting memory #{i}: {e}")

        formatted_text = "\n".join(memory_text)
        logger.info(
            f"Formatted {len(memory_text)} memories into {len(formatted_text)} characters"
        )
        return formatted_text

    async def add_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        patient_id: Optional[str] = None,
    ) -> Memory:
        """
        Add a new memory.

        Args:
            content: Memory content
            metadata: Additional metadata
            session_id: Optional session ID
            patient_id: Optional patient ID

        Returns:
            Memory object representing the stored memory
        """
        # Generate session ID if not provided in metadata
        if session_id:
            if not metadata:
                metadata = {"session_id": session_id}
            else:
                metadata["session_id"] = session_id
        elif metadata and "session_id" in metadata:
            session_id = metadata["session_id"]
        else:
            session_id = f"default-{uuid.uuid4()}"
            if metadata:
                metadata["session_id"] = session_id
            else:
                metadata = {"session_id": session_id}

        # Add patient_id to metadata if provided
        if patient_id and metadata:
            metadata["patient_id"] = patient_id

        # Store the memory without ttl_minutes
        return await self.store_memory(content, metadata=metadata)

    async def get_recent_messages(
        self, patient_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get the most recent messages for a patient without semantic search.

        Args:
            patient_id: The patient ID to get messages for
            limit: Maximum number of messages to return (default: 5)

        Returns:
            List of message dictionaries, newest first
        """
        if not patient_id:
            logger.warning("No patient_id provided for get_recent_messages")
            return []

        # If database is not available, return empty list
        if not self.supabase or not self.table_exists:
            logger.warning("Database not available for get_recent_messages")
            return []

        try:
            # Log the query being made
            logger.info(
                f"Getting recent messages for patient_id={patient_id}, limit={limit}"
            )

            # Directly query the most recent messages by timestamp
            result = (
                self.supabase.table(self.table_name)
                .select("*")
                .eq("patient_id", patient_id)  # Filter by patient_id
                .order("id", desc=True)  # Order by ID (newest first)
                .limit(limit)  # Limit number of results
                .execute()
            )

            # Log results
            logger.info(
                f"Retrieved {len(result.data) if result.data else 0} recent messages for patient {patient_id}"
            )

            # Format the data
            messages = []
            for item in result.data:
                try:
                    # Extract the context and handle potential string/JSON format issues
                    context_data = {}
                    context = item.get("context", {})

                    # Handle string/JSON format issues - try multiple approaches
                    if isinstance(context, str):
                        try:
                            # Try to parse JSON string
                            context_data = json.loads(context)
                        except json.JSONDecodeError:
                            logger.warning(
                                f"Failed to parse context as JSON: {context[:50]}..."
                            )
                    elif isinstance(context, dict):
                        context_data = context
                    elif isinstance(context, int):
                        # Handle integer context (seen in some corrupted records)
                        logger.warning(f"Context is integer value: {context}")
                        continue

                    # Extract content - handle different formats
                    content = None
                    metadata = {}

                    # Try to get content from context
                    if isinstance(context_data, dict):
                        # Try to extract conversation data
                        conversation = context_data.get("conversation", {})
                        if conversation and isinstance(conversation, dict):
                            user_msg = conversation.get("user_message", "")
                            bot_msg = conversation.get("bot_response", "")
                            if user_msg or bot_msg:
                                content = f"User: {user_msg}\nAssistant: {bot_msg}"

                        # If no conversation found, try content field
                        if not content and "content" in context_data:
                            content_field = context_data.get("content")
                            # If content is a JSON string, try to parse it
                            if isinstance(content_field, str) and (
                                content_field.startswith("{")
                                or content_field.startswith("[")
                            ):
                                try:
                                    content_obj = json.loads(content_field)
                                    if (
                                        isinstance(content_obj, dict)
                                        and "user_message" in content_obj
                                    ):
                                        user_msg = content_obj.get("user_message", "")
                                        bot_msg = content_obj.get(
                                            "assistant_response", ""
                                        )
                                        content = (
                                            f"User: {user_msg}\nAssistant: {bot_msg}"
                                        )
                                    else:
                                        content = content_field
                                except json.JSONDecodeError:
                                    content = content_field
                            else:
                                content = content_field

                        # Get metadata
                        metadata = context_data.get("metadata", {})

                    # If we still don't have content, use fallback
                    if not content:
                        content = f"Memory record {item.get('id', 'unknown')}"

                    # Create memory dictionary
                    timestamp = None
                    if isinstance(context_data, dict):
                        timestamp = context_data.get("created_at")
                        if not timestamp and "conversation" in context_data:
                            timestamp = context_data["conversation"].get("timestamp")

                    # Add to results
                    messages.append(
                        {
                            "id": item.get("id"),
                            "content": content,
                            "metadata": metadata,
                            "timestamp": timestamp or datetime.now().isoformat(),
                            "patient_id": patient_id,
                        }
                    )

                except Exception as e:
                    logger.error(
                        f"Error parsing memory {item.get('id', 'unknown')}: {e}",
                        exc_info=True,
                    )

            return messages

        except Exception as e:
            logger.error(f"Error in get_recent_messages: {e}", exc_info=True)
            return []


def get_short_term_memory_manager():
    """Get a singleton instance of the short-term memory manager."""
    if not hasattr(get_short_term_memory_manager, "instance"):
        get_short_term_memory_manager.instance = ShortTermMemoryManager()

    return get_short_term_memory_manager.instance
