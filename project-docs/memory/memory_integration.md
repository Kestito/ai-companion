# Memory Integration Points

This document outlines the memory integration points across all interfaces in the AI Companion project.

## Overview

To ensure consistent memory management and state persistence across all interfaces (Telegram, Web, WhatsApp, etc.), we've implemented standard integration points for memory handling with LangGraph.

## Standard Processing Model Across All Interfaces

All interfaces (including Telegram and Web) now use the same standardized approach:

1. **Internal Graph Structure**: State is managed internally in a graph structure using LangGraph
2. **Memory Extraction**: All interfaces use `graph.aget_state(config)` to capture complete state
3. **Configuration**: All interfaces include `use_supabase_only: true` flag
4. **Processing**: All interfaces follow a node-based workflow pattern
5. **Memory Service**: All interfaces use the standardized memory service exclusively

This standardization ensures perfect continuity between different interfaces and platforms.

## Unified Memory Service Approach

The memory service is now the exclusive interface for all memory operations:

```python
# Initialize standardized memory service
memory_service = get_memory_service()

# Store memory using standardized approach
await memory_service.store_session_memory(
    platform="platform_name",
    user_id=user_id,
    state=graph_state,
    conversation=conversation_data,
    ttl_minutes=1440  # Standard 24-hour TTL
)

# Retrieve memory using standardized approach
memories = await memory_service.get_session_memory(
    platform="platform_name",
    user_id=user_id,
    limit=10
)
```

Key standardization elements:
- No direct database access in interface code
- Single source of truth for all memory operations
- Consistent TTL (24 hours) across all platforms
- Standard session ID format: `{platform}-{user_id}`

## Graph Builder Configuration

All graph configurations now include the following standard settings:

```python
config = {
    "configurable": {
        "memory_manager": memory_service.short_term_memory,
        "use_supabase_only": True,  # Always use Supabase for memory
        "session_id": session_id
    }
}
```

Key aspects:
- `memory_manager` is provided by the memory service
- `use_supabase_only` is always set to `True` to ensure database persistence
- `session_id` follows a consistent format across all platforms

## Session Management

### Session ID Format

Session IDs follow a standard format across all interfaces:

```
{platform}-{user_id}
```

Examples:
- `telegram-123456789`
- `web-abcd1234`
- `whatsapp-+1234567890`

### Memory Expiration

All memory records have consistent expiration times:
- Default: 24 hours (1440 minutes)
- Can be customized per interface if needed
- Implemented in both cache and database layers

## State Transfer

### Graph State Extraction

All interfaces use the asynchronous state method to get the complete graph state:

```python
graph_state = await graph.aget_state(config)
```

This ensures we capture all state variables managed by LangGraph, including:
- Message history
- Workflow information
- Context variables
- Current processing state

### State Storage

All graph states are stored in the Supabase `short_term_memory` table with a consistent schema:

```json
{
  "id": "unique-id",
  "context": {
    "metadata": {
      "session_id": "platform-user_id",
      "user_id": "user_id",
      "platform": "platform"
    },
    "state": {
      // Complete graph state
    },
    "conversation": {
      "user_message": "User's message",
      "bot_response": "Bot's response",
      "timestamp": "ISO timestamp"
    }
  },
  "expires_at": "ISO timestamp"
}
```

## Memory Processing

### Memory Formatting

Memories are consistently formatted for LLM consumption:

```python
formatted_history = []
for memory in memories:
    if "content" in memory:
        formatted_history.append({
            "role": "human", 
            "content": memory.get("content", "")
        })
    if "response" in memory:
        formatted_history.append({
            "role": "ai", 
            "content": memory.get("response", "")
        })
```

### Conversation History

Previous conversation turns are included in all interactions via:

1. The `memory_service.get_session_memory()` method to retrieve recent memories
2. Formatting those memories into a conversation history
3. Including the history in the graph configuration:
   ```python
   config["configurable"]["conversation_history"] = formatted_history
   ```

## Implementation in Different Interfaces

### Telegram Interface

The Telegram bot now exclusively uses the standardized memory service:
- Direct initialization: `memory_service = get_memory_service()`
- No direct database access or custom storage methods
- All memory operations routed through memory service
- Shared memory service instance with other platforms
- Same standardized serialization and TTL (24 hours)
- Conversation retrieval through memory service API

### Web Interface

The Web API also uses the same standardized memory service implementation:
- HTTP endpoints (`/message`) 
- WebSocket connections (`/ws/{session_id}`)
- Maintaining consistent session IDs across page reloads
- The same state extraction and storage as Telegram

## Benefits

1. **Consistency**: Uniform memory handling across all interfaces
2. **Persistence**: Reliable state storage in Supabase
3. **Continuity**: Conversations can seamlessly continue across sessions and interfaces
4. **Context**: Complete conversation history for better responses
5. **Scalability**: Design supports multiple interface types
6. **Interoperability**: Users can switch between interfaces while maintaining context
7. **Maintainability**: Single implementation reduces code duplication 