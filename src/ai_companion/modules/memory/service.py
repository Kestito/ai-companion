"""
Memory Service Layer for AI Companion.

This module provides a unified interface for memory management across different platforms.
It extracts and centralizes memory functionality from platform-specific implementations
and works with both short-term and long-term memory systems.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid


from ai_companion.modules.memory.short_term import get_short_term_memory_manager
from ai_companion.modules.memory.long_term.memory_manager import get_memory_manager
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
        self.long_term_memory = get_memory_manager()
        self.supabase = get_supabase_client()

    async def get_session_memory(
        self, platform: str, user_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve session memory for a specific platform and user.

        Args:
            platform: The platform identifier (e.g., "telegram", "whatsapp")
            user_id: The user identifier on the platform
            limit: Maximum number of memories to retrieve

        Returns:
            List of memory entries as dictionaries
        """
        try:
            # Create session ID in the same format used when storing
            session_id = f"{platform}-{user_id}"

            # Get messages from cache first
            cached_messages = await self.short_term_memory.get_cached_messages(
                session_id, limit
            )

            if cached_messages:
                logger.debug(
                    f"Retrieved {len(cached_messages)} cached messages for session {session_id}"
                )
                return cached_messages

            # If no cached messages, try to get from database
            if self.supabase:
                try:
                    # Get memories from the short_term_memory table
                    result = (
                        self.supabase.table("short_term_memory")
                        .select("*")
                        .like("metadata", f'%"session_id":"{session_id}"%')
                        .order("created_at", desc=True)
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
        state: Optional[Dict[str, Any]] = None,
        conversation: Optional[Dict[str, str]] = None,
        ttl_minutes: int = 1440,  # Default to 24 hours (1440 minutes)
    ) -> str:
        """
        Store session memory for a specific platform and user.

        Args:
            platform: The platform identifier (e.g., "telegram", "whatsapp")
            user_id: The user identifier on the platform
            state: Optional graph state to store
            conversation: Optional conversation data (user_message and bot_response)
            ttl_minutes: Time-to-live in minutes for the memory (default: 24 hours)

        Returns:
            ID of the stored memory
        """
        try:
            # Create session ID using consistent format
            session_id = f"{platform}-{user_id}"

            # Create metadata
            metadata = {
                "session_id": session_id,
                "user_id": user_id,
                "platform": platform,
            }

            # Create context object
            context = {"metadata": metadata, "state": state or {}}

            # Add conversation if provided
            if conversation:
                context["conversation"] = {
                    "user_message": conversation.get("user_message", ""),
                    "bot_response": conversation.get("bot_response", ""),
                    "timestamp": datetime.now().isoformat(),
                }

                # Also analyze for long-term memory if there's a user message
                if conversation.get("user_message"):
                    await self.long_term_memory.add_memory(conversation["user_message"])

            # Store in short-term memory
            memory = await self.short_term_memory.store_with_cache(
                content=json.dumps(context),
                session_id=session_id,
                metadata=metadata,
                ttl_minutes=ttl_minutes,
            )

            # Also ensure we store in Supabase directly with the full state
            memory_id = memory.get("id", str(uuid.uuid4()))

            if self.supabase:
                try:
                    # Set expiry for specified TTL from now
                    expires_at = (
                        datetime.now() + timedelta(minutes=ttl_minutes)
                    ).isoformat()

                    # Create record with the same schema used in other interfaces
                    record = {
                        "id": memory_id,
                        "context": context,
                        "expires_at": expires_at,
                    }

                    # Store directly in Supabase
                    self.supabase.table("short_term_memory").insert(record).execute()
                    logger.info(
                        f"Stored complete memory state in Supabase with ID: {memory_id}"
                    )
                except Exception as e:
                    logger.warning(f"Error storing complete memory in Supabase: {e}")

            return memory_id
        except Exception as e:
            logger.error(f"Error in store_session_memory: {e}")
            return ""

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
                        .like("context", f'%"session_id":"{session_id}"%')
                        .order("expires_at", desc=True)
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
                    state=graph_state,
                    conversation=conversation,
                    ttl_minutes=1440,  # 24 hours default
                )
            except Exception as e:
                logger.error(f"Error storing updated graph state: {e}")

            return result
        except Exception as e:
            logger.error(f"Error in load_memory_to_graph: {e}")
            return {"messages": config.get("messages", []), "error": str(e)}


# Singleton instance for the memory service
_memory_service = None


def get_memory_service() -> MemoryService:
    """Get a singleton instance of the MemoryService."""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
