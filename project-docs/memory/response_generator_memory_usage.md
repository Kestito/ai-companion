# Memory Usage in LithuanianResponseGenerator

This document explains how the `LithuanianResponseGenerator` class (located in `src/ai_companion/modules/rag/core/response_generation.py`) utilizes memory and context to generate responses.

## Overview

The `LithuanianResponseGenerator` itself does not store or manage memory long-term. Instead, it relies on receiving pre-compiled context from the calling parts of the AI Companion system. This context is crucial for maintaining conversational flow and incorporating relevant information from past interactions.

## Key Method: `generate_response`

The primary method responsible for using memory is `generate_response`.

```python
async def generate_response(
    self,
    query: str,
    documents: List[Document],
    context: str = "",  # This is the key input for memory
    organized_docs: Optional[Dict[str, List[Document]]] = None,
    citations: Optional[List[Dict[str, Any]]] = None,
    detailed: bool = False,
    **kwargs
) -> str:
    # ...
```

### `context` Parameter

The `context` parameter is a string expected to contain both chat history and other relevant memory information. The `LithuanianResponseGenerator` method processes this `context` string as follows:

```python
chat_history = ""
memory_info = ""
if context:
    parts = context.split("\nMemory Context:\n")
    if len(parts) > 1:
        chat_history = parts[0].replace("Chat History:\n", "").strip()
        memory_info = parts[1].strip()
```

-   **`chat_history`**: This extracted portion is intended to be the recent conversation history, typically supplied by a short-term memory management component.
-   **`memory_info`**: This is expected to contain other relevant information retrieved from the broader memory system, specifically **long-term memories**. This part should be populated by an upstream component (e.g., a "Memory Injection Node" as described in `project-docs/memory.md`) that utilizes the `MemoryManager` (from `src/ai_companion/modules/memory/long_term/memory_manager.py`) to fetch and format relevant long-term memories for the current user and query.

Both `chat_history` and `memory_info` are then directly inserted into the prompt sent to the Language Model (LLM):

```python
prompt = f"""As a Lithuanian-speaking AI assistant, generate a {'comprehensive and detailed' if detailed else 'clear and informative'} response to the user's query.
Consider the conversation history and memory context to maintain continuity.

Chat History:
{chat_history}

Memory Context:
{memory_info}

Retrieved Information:
{organized_text}
# ... rest of the prompt
"""
```

## Dependency on Calling System

The effectiveness of the "memory" perceived by the user when interacting with responses from `LithuanianResponseGenerator` heavily depends on:

1.  **Quality and Completeness of `context`**: The calling system is responsible for populating the `context` string.
    *   The `chat_history` portion is typically managed by short-term memory mechanisms.
    *   The `memory_info` portion, crucial for long-term recall, must be actively populated by an upstream node using the `MemoryManager` to retrieve and format relevant long-term memories. If this `memory_info` is empty or not properly supplied, the generator will not have access to long-term memories.
2.  **Memory Management Strategy**: The overall memory management (short-term and long-term storage, retrieval, and summarization strategies) is handled by other components of the AI Companion, as outlined in `project-docs/memory.md` and implemented in `src/ai_companion/modules/memory/`. The `LithuanianResponseGenerator` is a consumer of this processed memory.

## Role of the Upstream "Memory Injection Node" (or equivalent)

For long-term memory to be utilized by the `LithuanianResponseGenerator`, a component *before* it in the processing chain (referred to as the "Memory Injection Node" in `project-docs/memory.md`) must perform the following tasks:

1.  **Identify User Context**: Determine the current `patient_id` and the relevant query/context for memory retrieval.
2.  **Retrieve Long-Term Memories**: Call the `MemoryManager.get_relevant_memories(context=current_query_context, patient_id=current_patient_id)` method.
3.  **Format Memories**: Take the list of memory strings returned and pass it to `MemoryManager.format_memories_for_prompt(retrieved_memories)` to get a single formatted string.
4.  **Construct `context` String**: Combine the short-term `chat_history` with the formatted long-term memories (as `memory_info`) into the structure expected by `LithuanianResponseGenerator`:
    ```
    Chat History:
    [recent chat messages]
    Memory Context:
    [formatted long-term memories from MemoryManager]
    ```
5.  **Pass to Generator**: Provide this complete `context` string to the `LithuanianResponseGenerator`.

If this upstream node fails to perform these steps correctly, the `memory_info` part of the prompt will be empty or incorrect, and the `LithuanianResponseGenerator` will not be able to leverage long-term memory.

## Limitations within `LithuanianResponseGenerator`

-   The generator does not implement its own memory storage.
-   It does not decide how much history to load or which long-term memories are relevant.
-   Its ability to seem "memoryful" is entirely gated by the `context` it receives.

## Implications for "Long Memory" Issues

If the bot appears to have a short memory, the investigation should primarily focus on the upstream components that construct and pass the `context` string to `LithuanianResponseGenerator`. According to `project-docs/memory.md`, the system retrieves the "5 most recent conversation turns" for short-term memory context, which could be a factor in the perception of memory length. The effectiveness of long-term memory retrieval by the "Memory Injection Node" also plays a significant role. 