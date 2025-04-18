# Memory Service Integration Documentation

## Overview

The Memory Service is a unified interface for memory management across different platforms and interfaces in the AI Companion project. It provides a centralized way to store, retrieve, and manage conversational memory across different interfaces (Telegram, Web, WhatsApp, etc.) while maintaining consistent behavior.

## Architecture

The Memory Service uses a layered approach to memory management:

1. **Short-term Memory**: Handles immediate conversation context storage, TTL-based expiration, and retrieval
2. **Long-term Memory**: Stores important information for permanent recall and retrieval using vector search
3. **Graph Integration**: Seamlessly integrates with LangGraph for stateful workflow processing

## Key Components

- `MemoryService`: The core service class providing a unified interface
- `get_memory_service()`: Factory function to get a singleton instance of the service
- Memory Manager instances: Underlying storage and retrieval engines

## Integration with Interfaces

### Telegram Interface

The Telegram interface has been updated to use the Memory Service for:
- Storing conversation history
- Retrieving recent memories
- Loading memory into graph workflows

Example usage:

```python
# Store conversation
conversation_data = {
    "user_message": user_message,
    "bot_response": bot_response
}
await memory_service.store_session_memory(
    platform="telegram",
    user_id=str(user_id),
    conversation=conversation_data
)

# Retrieve memories
memories = await memory_service.get_session_memory(
    platform="telegram",
    user_id=str(user_id),
    limit=10
)
```

### Web Interface

The Web interface uses the Memory Service for:
- Processing incoming messages with historical context
- Storing conversation state and messages
- Retrieving conversation history via websockets

Example usage:

```python
# Use memory service with graph
messages = state.get("messages", [])
result = await load_memory_to_graph(graph, messages, session_id)

# Store conversation
conversation_data = {
    "user_message": user_message,
    "bot_response": response
}
await memory_service.store_session_memory(
    platform="web",
    user_id=user_id,
    state=state,
    conversation=conversation_data
)
```

## LangGraph Integration

The Memory Service integrates with LangGraph through the `load_memory_to_graph` helper function, which:
1. Loads relevant memories for the current context
2. Adds memory context to the initial graph state
3. Invokes the graph with the enhanced state
4. Returns the processed result

## Database Integration

The Memory Service uses Supabase for persistent storage:
- Short-term memories stored in the `short_term_memory` table
- Session-based retrieval using metadata queries
- Consistent data schema across interfaces
- Fallback to in-memory cache when database is unavailable

## Usage Guidelines

### Creating a Session ID

Session IDs should follow the format `{platform}-{user_id}` for consistency across interfaces:

```python
session_id = f"telegram-{chat_id}-{user_id}"
session_id = f"web-{user_id}"
session_id = f"whatsapp-{phone_number}"
```

### Storing Memories

Always include the platform and user ID when storing memories:

```python
await memory_service.store_session_memory(
    platform="platform_name",
    user_id="unique_user_id",
    conversation={
        "user_message": "User's message",
        "bot_response": "Bot's response"
    }
)
```

### Using with Graph Workflows

For graph workflows, use the `load_memory_to_graph` helper:

```python
from ai_companion.graph.utils.helpers import load_memory_to_graph

result = await load_memory_to_graph(graph, messages, session_id)
```

## Future Enhancements

- Enhanced memory summarization for long conversations
- Cross-session memory retrieval
- Multi-user memory isolation and sharing
- Improved long-term memory extraction using LLM reasoning 