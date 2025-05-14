"""
Memory Service Layer for AI Companion.

This module provides a unified interface for memory management across different platforms.
It extracts and centralizes memory functionality from platform-specific implementations
and works with both short-term and long-term memory systems.
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union, Set
import uuid

from langchain_core.messages import BaseMessage as LangchainMessage
from langchain_community.chat_message_histories import ChatMessageHistory

from ai_companion.modules.memory.short_term import get_short_term_memory_manager
from ai_companion.modules.memory.long_term.memory_manager import get_memory_manager, get_initialized_memory_manager
from ai_companion.utils.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class MemoryService:
    """
    Unified memory service for AI Companion.

    This service provides a centralized interface for memory operations across
    different platforms and interfaces, handling both short-term and long-term memory.
    """

    def __init__(self):
        """Initialize the memory service with required components."""
        self.short_term_memory = get_short_term_memory_manager()
        self.long_term_memory = None  # Will be initialized async
        self.supabase = get_supabase_client()
        self._is_initialized = False
        self._initialization_lock = asyncio.Lock()

    async def ensure_initialized(self) -> None:
        """Ensure the memory service is fully initialized."""
        if not self._is_initialized:
            # Use a lock to prevent multiple concurrent initializations
            async with self._initialization_lock:
                # Double-check if initialized while waiting for lock
                if not self._is_initialized:
                    # Initialize the long-term memory manager asynchronously
                    self.long_term_memory = await get_initialized_memory_manager()
                    self._is_initialized = True
                    logger.info("Memory service initialized successfully")

    async def get_session_memory(
        self, platform: str, user_id: str, patient_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve session memory for a specific platform, user and patient.

        Args:
            platform: The platform identifier (e.g., "telegram", "whatsapp")
            user_id: The user identifier on the platform
            patient_id: The patient identifier (REQUIRED)
            limit: Maximum number of memories to retrieve

        Returns:
            List of memory entries as dictionaries
        """
        # Ensure service is initialized
        await self.ensure_initialized()
        
        try:
            # Create session ID with patient context
            session_id = f"{platform}-{user_id}-patient-{patient_id}"

            # First try to get messages using get_cached_messages (for backward compatibility)
            try:
                if hasattr(self.short_term_memory, "get_cached_messages"):
                    logger.debug(f"Using get_cached_messages for session {session_id}")
                    cached_messages = await self.short_term_memory.get_cached_messages(
                        session_id, limit, patient_id
                    )
                    if cached_messages:
                        logger.debug(
                            f"Retrieved {len(cached_messages)} cached messages using get_cached_messages"
                        )
                        return cached_messages
            except Exception as e:
                logger.warning(
                    f"Error using get_cached_messages: {e}, falling back to get_messages_parallel"
                )

            # Then try get_messages_parallel (preferred method)
            try:
                if hasattr(self.short_term_memory, "get_messages_parallel"):
                    logger.debug(
                        f"Using get_messages_parallel for session {session_id}"
                    )
                    cached_messages = (
                        await self.short_term_memory.get_messages_parallel(
                            session_id, limit, patient_id
                        )
                    )
                    if cached_messages:
                        logger.debug(
                            f"Retrieved {len(cached_messages)} cached messages using get_messages_parallel"
                        )
                        return cached_messages
            except Exception as e:
                logger.warning(
                    f"Error using get_messages_parallel: {e}, falling back to database query"
                )

            # If no cached messages or method calls failed, try to get from database directly
            if self.supabase:
                try:
                    # Get memories from the short_term_memory table
                    # Use PostgreSQL's JSONB extraction operator to query inside the nested JSON
                    result = (
                        self.supabase.table("short_term_memory")
                        .select("*")
                        .filter("context->'metadata'->>'session_id'", "eq", session_id)
                        .order("id", desc=True)  # Order by id instead of expires_at
                        .limit(limit)
                        .execute()
                    )

                    if result.data:
                        messages = []
                        for item in result.data:
                            try:
                                # Extract conversation and metadata
                                context = item.get("context", {})
                                metadata = context.get("metadata", {})

                                # Check if this is the right format
                                if "conversation" in context:
                                    # This is the new format with both messages
                                    conversation = context.get("conversation", {})
                                    messages.append(
                                        {
                                            "id": item.get("id"),
                                            "content": conversation.get(
                                                "user_message", ""
                                            ),
                                            "response": conversation.get(
                                                "bot_response", ""
                                            ),
                                            "metadata": metadata,
                                            "timestamp": conversation.get(
                                                "timestamp", datetime.now().isoformat()
                                            ),
                                        }
                                    )
                                else:
                                    # This is the older format with just content
                                    messages.append(
                                        {
                                            "id": item.get("id"),
                                            "content": context.get("content", ""),
                                            "metadata": metadata,
                                            "timestamp": context.get(
                                                "created_at", datetime.now().isoformat()
                                            ),
                                        }
                                    )
                            except Exception as e:
                                logger.warning(
                                    f"Error parsing memory from database: {e}"
                                )
                                continue

                        logger.debug(
                            f"Retrieved {len(messages)} memories from database for session {session_id}"
                        )
                        return messages
                except Exception as e:
                    logger.error(f"Error retrieving memories from database: {e}")

            return []
        except Exception as e:
            logger.error(f"Error in get_session_memory: {e}")
            return []

    async def store_session_memory(
        self,
        platform: str,
        user_id: str,
        patient_id: str,  # Now required
        state: Optional[Dict[str, Any]] = None,
        conversation: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Store session memory for a specific platform, user and patient.

        Args:
            platform: The platform identifier (e.g., "telegram", "whatsapp")
            user_id: The user identifier on the platform
            patient_id: The patient identifier (REQUIRED)
            state: Optional graph state to store
            conversation: Optional conversation data (user_message and bot_response)

        Returns:
            ID of the stored memory
        """
        # Ensure service is initialized
        await self.ensure_initialized()
        
        try:
            # Create session ID using consistent format with patient context
            session_id = f"{platform}-{user_id}-patient-{patient_id}"

            # Create metadata
            metadata = {
                "session_id": session_id,
                "user_id": user_id,
                "platform": platform,
                "patient_id": patient_id,  # Always include patient_id
                "timestamp": datetime.now().isoformat(),  # Add timestamp for easier tracking
            }

            # Create context object
            context = {"metadata": metadata, "state": state or {}}

            # Add conversation if provided with timestamp
            if conversation:
                context["conversation"] = {
                    "user_message": conversation.get("user_message", ""),
                    "bot_response": conversation.get("bot_response", ""),
                    "timestamp": datetime.now().isoformat(),
                    "patient_id": patient_id,  # Include patient context in conversation
                }

                # Also analyze for long-term memory if there's a user message
                if conversation.get("user_message"):
                    # Pass patient context to long-term memory
                    await self.long_term_memory.add_memory(
                        conversation["user_message"],
                        {
                            "patient_id": patient_id,
                            "user_id": user_id,
                            "platform": platform,
                        },
                    )

            # Generate a unique memory ID
            memory_id = str(uuid.uuid4())

            # Skip expiration date calculation per user request
            # We're not using expires_at field at all

            # Store in short-term memory
            try:
                await self.short_term_memory.add_memory(
                    session_id=session_id,
                    content=context,
                    metadata=metadata,
                    patient_id=patient_id,
                )
                logger.info(f"Stored memory using add_memory with ID: {memory_id}")
            except Exception as e:
                logger.error(f"Error storing memory with add_memory: {e}")

            # Also ensure we store in Supabase directly with the full state
            if self.supabase:
                try:
                    # Add a timestamp in the context to ensure we always have it
                    context["timestamp"] = datetime.now().isoformat()

                    # Check if created_at column exists by querying table information
                    try:
                        # Create record with fields we know exist in the database schema
                        record = {
                            "id": memory_id,
                            "context": context,
                            "patient_id": patient_id,  # Add patient_id at top level for easier queries
                        }

                        # Only add created_at if the column exists
                        # We'll catch any errors and retry without it
                        self.supabase.table("short_term_memory").insert(
                            record
                        ).execute()
                        logger.info(
                            f"Stored complete memory state in Supabase with ID: {memory_id}"
                        )
                    except Exception as column_error:
                        if "created_at" in str(column_error):
                            # Try again without the created_at field
                            record = {
                                "id": memory_id,
                                "context": context,
                                "patient_id": patient_id,
                            }
                            self.supabase.table("short_term_memory").insert(
                                record
                            ).execute()
                            logger.info(
                                f"Stored memory in Supabase without created_at: {memory_id}"
                            )
                        else:
                            # Re-raise if it's not a created_at column issue
                            raise
                except Exception as e:
                    logger.warning(f"Error storing complete memory in Supabase: {e}")

            return memory_id
        except Exception as e:
            logger.error(f"Error in store_session_memory: {e}")
            return str(uuid.uuid4())  # Return a new UUID as fallback

    async def load_memory_to_graph(
        self, graph: Any, config: Dict[str, Any], session_id: str
    ) -> Dict[str, Any]:
        """
        Load relevant memories into a graph for processing.

        Args:
            graph: The LangGraph instance
            config: Configuration for the graph
            session_id: Session identifier

        Returns:
            The updated graph state
        """
        try:
            # Get relevant memories
            if not hasattr(self, "long_term_memory"):
                self.long_term_memory = get_memory_manager()

            memory_context = ""

            # Extract query from config if available
            query = ""
            if config and "messages" in config:
                messages = config.get("messages", [])
                if messages and len(messages) > 0:
                    last_message = messages[-1]
                    if hasattr(last_message, "content"):
                        query = last_message.content
                    elif isinstance(last_message, dict) and "content" in last_message:
                        query = last_message["content"]

            # Get relevant memories based on the query
            if query:
                relevant_memories = self.long_term_memory.get_relevant_memories(query)
                memory_context = self.long_term_memory.format_memories_for_prompt(
                    relevant_memories
                )

            # Create initial state with memory context
            state = {
                "messages": config.get("messages", []),
                "memory_context": memory_context,
            }

            # Ensure session_id is in configurable
            if "configurable" not in config:
                config["configurable"] = {}
            config["configurable"]["session_id"] = session_id

            # Parse session_id to get platform and user_id
            parts = session_id.split("-")
            platform = parts[0] if len(parts) > 0 else "unknown"
            user_id = session_id.replace(f"{platform}-", "")

            # Try to retrieve existing state from Supabase
            existing_state = None
            if self.supabase:
                try:
                    # Query for the most recent state for this session
                    result = (
                        self.supabase.table("short_term_memory")
                        .select("*")
                        .filter("context->'metadata'->>'session_id'", "eq", session_id)
                        .order("id", desc=True)
                        .limit(1)
                        .execute()
                    )

                    if result.data and len(result.data) > 0:
                        context = result.data[0].get("context", {})
                        existing_state = context.get("state", {})
                        logger.info(
                            f"Retrieved existing state from Supabase for session {session_id}"
                        )

                        # Merge into the current state
                        if existing_state:
                            for key, value in existing_state.items():
                                if key not in state or not state[key]:
                                    state[key] = value
                except Exception as e:
                    logger.warning(
                        f"Error retrieving existing state from Supabase: {e}"
                    )

            # Invoke the graph with the enhanced state
            result = await graph.invoke(state, config)

            # Store the updated state back to Supabase
            try:
                # Get the graph state
                graph_state = await graph.aget_state(config)

                # Store the complete state
                conversation = None

                # Extract last message and response if available
                if result and "messages" in result and len(result["messages"]) >= 2:
                    messages = result["messages"]
                    last_user_msg = None
                    last_ai_msg = None

                    # Find the last user and AI messages
                    for msg in reversed(messages):
                        if hasattr(msg, "type"):
                            if msg.type == "human" and not last_user_msg:
                                last_user_msg = msg.content
                            elif msg.type == "ai" and not last_ai_msg:
                                last_ai_msg = msg.content

                        if last_user_msg and last_ai_msg:
                            break

                    if last_user_msg and last_ai_msg:
                        conversation = {
                            "user_message": last_user_msg,
                            "bot_response": last_ai_msg,
                        }

                # Store the updated state with conversation if available
                await self.store_session_memory(
                    platform=platform,
                    user_id=user_id,
                    patient_id=parts[2] if len(parts) > 2 else "unknown",
                    state=graph_state,
                    conversation=conversation,
                )
            except Exception as e:
                logger.error(f"Error storing updated graph state: {e}")

            return result
        except Exception as e:
            logger.error(f"Error in load_memory_to_graph: {e}")
            return {"messages": config.get("messages", []), "error": str(e)}

    async def get_messages(
        self, session_id: str, limit: int = 10, patient_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get messages from memory for a specific session or patient."""
        logger.debug(
            f"Getting memory messages for session_id={session_id}, patient_id={patient_id}"
        )
        try:
            # First try to get from cache
            messages = await self.message_cache.get_messages(
                session_id, limit, patient_id
            )

            # If no messages in cache and we have Supabase, try database directly
            if not messages and self.supabase:
                try:
                    # Construct query
                    query = self.supabase.table(self.table_name).select("*")

                    # Filter by patient_id if provided, otherwise by session_id
                    if patient_id:
                        query = query.eq("patient_id", patient_id)
                    else:
                        query = query.eq("session_id", session_id)

                    # Filter, order and limit
                    result = (
                        query.order(
                            "id", desc=True
                        )  # Order by id instead of expires_at
                        .limit(limit)
                        .execute()
                    )

                    if result.data:
                        # Try to parse messages from context
                        messages = []
                        for item in result.data:
                            try:
                                context = item.get("context", {})
                                if isinstance(context, str):
                                    context = json.loads(context)

                                # Extract conversation
                                conversation = context.get("conversation")
                                if conversation:
                                    messages.append(conversation)
                            except Exception as e:
                                logger.error(
                                    f"Error parsing message from database: {e}"
                                )

                        if messages:
                            logger.info(
                                f"Retrieved {len(messages)} messages from database directly"
                            )
                except Exception as e:
                    logger.error(f"Error getting messages from database: {e}")

            return messages
        except Exception as e:
            logger.error(f"Error in get_messages: {e}", exc_info=True)
            return []

    async def get_conversations(
        self, patient_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get a list of conversations for a patient."""
        if not patient_id:
            return []

        try:
            if not self.supabase:
                return []

            # Retrieve conversations
            result = (
                self.supabase.table(self.table_name)
                .select("id, created_at, patient_id, conversation_id, context")
                .eq("patient_id", patient_id)
                .order("id", desc=True)  # Order by id instead of expires_at
                .limit(limit)
                .execute()
            )

            if not result.data:
                return []

            # Process results
            conversations = []
            for item in result.data:
                try:
                    # Extract conversation info
                    conv_id = item.get("conversation_id") or item.get("id")
                    created_at = item.get("created_at")
                    context = item.get("context", {})

                    if isinstance(context, str):
                        try:
                            context = json.loads(context)
                        except:
                            context = {}

                    # Extract message from context
                    user_message = None
                    if isinstance(context, dict):
                        conversation = context.get("conversation", {})
                        if (
                            isinstance(conversation, dict)
                            and conversation.get("role") == "user"
                        ):
                            user_message = conversation.get("content", "")

                    # Create conversation summary
                    conversations.append(
                        {
                            "id": conv_id,
                            "created_at": created_at,
                            "preview": user_message[:100] + "..."
                            if user_message and len(user_message) > 100
                            else user_message or "No preview available",
                        }
                    )
                except Exception as e:
                    logger.error(f"Error processing conversation item: {e}")

            return conversations
        except Exception as e:
            logger.error(f"Error retrieving conversations: {e}", exc_info=True)
            return []


# Singleton instance for the memory service
_memory_service = None


def get_memory_service() -> MemoryService:
    """Get a singleton instance of the MemoryService."""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
