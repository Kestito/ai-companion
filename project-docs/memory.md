# Memory System

The AI Companion uses a sophisticated memory system to provide contextual awareness and continuity in conversations with users. This document outlines the architecture, components, and functionality of the memory system.

## Architecture Overview

The memory system consists of two main components:

1. **Short-Term Memory**: Stores recent conversations and interactions
2. **Long-Term Memory**: Stores important information with vector embeddings for semantic retrieval

Both memory systems work together to provide a comprehensive context to the AI Companion during conversations.

## Short-Term Memory

### Purpose
- Store recent conversation history
- Maintain conversation context across multiple messages
- Provide immediate access to recent interactions

### Implementation
- Uses Supabase as the storage backend
- Table structure: `short_term_memory`
  - `id`: UUID primary key
  - `patient_id`: UUID reference to the patient
  - `context`: JSONB field containing the memory data:
    - `metadata`: Additional data about the memory
    - `content`: The actual content of the memory
    - `created_at`: Timestamp of when the memory was created

### Key Components
- `ShortTermMemory`: Class that handles storage and retrieval of memories
- `get_recent_messages`: Function to retrieve the most recent messages for a patient
- Direct database access in the `memory_injection_node` for maximum reliability

## Long-Term Memory

### Purpose
- Store important information that may be relevant across multiple conversations
- Enable semantic search to find related memories based on context
- Preserve patient history and important details

### Implementation
- Uses Qdrant vector database for storing embeddings
- Azure OpenAI for generating embeddings
- Supports filtering by patient_id and other metadata

### Key Components
- `VectorStore`: Handles vector storage and retrieval
- `_get_embedding`: Generates embeddings for text using Azure OpenAI
- `search_memories`: Performs semantic search over stored memories

## Memory Integration

The memory system is integrated into the AI Companion's processing graph through two key nodes:

### Memory Injection Node
- Retrieves relevant memories for the current conversation
- Combines short-term conversation history with semantically relevant long-term memories
- Formats memories into a clear context for the language model

### Memory Extraction Node
- Analyzes conversations to identify important information
- Stores new memories in the appropriate system (short or long-term)
- Handles metadata and proper formatting

## Usage Example

When the AI Companion processes a message:

1. The `memory_injection_node` retrieves:
   - The 5 most recent conversation turns from short-term memory
   - Semantically relevant memories from long-term memory
   
2. These memories are formatted as context and provided to the language model:
   ```
   Recent Conversation:
   User: What's the weather like today?
   Assistant: It's sunny and warm!
   User: What about tomorrow?
   
   Previous Memories:
   The patient mentioned they have an outdoor event planned for tomorrow.
   The patient prefers detailed weather forecasts with temperature in Celsius.
   ```

3. After the conversation, the `memory_extraction_node` may identify important information to store in long-term memory.

## Error Handling & Reliability

The memory system includes robust error handling to ensure conversation flow isn't disrupted:

- Graceful fallbacks when embedding generation fails
- Comprehensive logging for debugging
- Database connection error handling
- JSON parsing and format handling for varied data formats

## Configuration

Memory system configuration is defined in `settings.py`:

- `MEMORY_TTL_MINUTES`: Default time-to-live for memories (default: 525600, or 1 year)
- `AZURE_OPENAI_API_KEY`: API key for embedding generation
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`: Embedding model deployment name
- `SUPABASE_URL` and `SUPABASE_KEY`: Credentials for Supabase database
- `QDRANT_URL` and `QDRANT_API_KEY`: Credentials for Qdrant vector database 