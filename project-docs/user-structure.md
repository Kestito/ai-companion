# User Flow & Project Structure

## User Journey

The AI Companion provides a conversational interface where users can interact through multiple modalities. Here's the typical user journey:

### 1. Initial Interaction
- User sends a message to the AI Companion
- System routes the message to the appropriate workflow
- Initial response is generated based on the message type

### 2. Knowledge Retrieval Flow
- User asks a knowledge-based question
- System processes the query through the RAG pipeline:
  1. Query is preprocessed and enhanced
  2. The system performs parallel searches:
     - Vector search retrieves semantically similar documents from Qdrant
     - Keyword search finds exact matches in Supabase
     - Results are combined, deduplicated, and ranked
  3. Response is generated based on retrieved information
  4. Sources are provided for transparency with search type attribution
- If initial retrieval is insufficient, the system may retry with adjusted parameters
- If specific components fail, the system gracefully falls back to alternative methods

### 3. Conversation Flow
- User continues the conversation
- System maintains context through:
  1. Short-term memory (recent messages)
  2. Long-term memory (important information)
  3. Activity context (current user activity)
- Responses are generated considering all available context
- Long conversations are summarized for context preservation when needed

### 4. Multimodal Interactions
- **Image Generation**:
  1. User requests an image
  2. System creates a scenario and image prompt
  3. Image is generated and presented to the user
  4. Conversation continues with the image as context

- **Audio Response**:
  1. User requests audio output
  2. System generates text response
  3. Text is converted to speech
  4. Audio is delivered to the user

### 5. Memory Management
- Important information is extracted from conversations
- Relevant memories are injected into future conversations
- Long conversations are summarized for context preservation

## Data Flow

```
User Input → Router → Specialized Node → Response Generation → User Output
    ↑                      ↓
    |                      |
    ↑                      ↓
Memory Storage ←→ Memory Retrieval
    ↑                      ↓
    |                      |
    ↑                      ↓
    Vector Database   ←→   Document Retrieval
           ↑               ↓  ↑
           |               |  |
           ↑               ↓  ↑
    Relational Database ←→ Keyword Search
```

### Parallel Search Implementation

The RAG system implements a parallel search strategy that combines the strengths of both vector and keyword search methods:

1. **Parallel Execution**
   ```
   Query → Query Preprocessing
        ↙               ↘
   Vector Search    Keyword Search
   (Qdrant)         (Supabase)
        ↘               ↙
       Result Combination
        ↓
     Deduplication
        ↓
    Ranking & Scoring
        ↓
   Final Results
   ```

2. **Query Analysis**
   - Analyzes query characteristics to determine optimal search strategy
   - Allocates resources based on query type (keyword-like or semantic)
   - Adapts parameter settings for each search type accordingly

3. **Result Processing**
   - Deduplicates results based on content hash
   - Adds search source metadata for tracking
   - Applies weighted scoring based on document quality indicators
   - Sorts by final relevance score
   - Limits to the requested number of documents

4. **Fallback Mechanisms**
   - Falls back to vector-only search if keyword search fails
   - Dynamically adjusts confidence thresholds if no results are found
   - Provides detailed error information for troubleshooting

5. **Performance Metrics**
   - Tracks execution time for each search component
   - Logs result counts by search type
   - Monitors success/failure rates for each search method
   - Calculates performance improvements compared to sequential search

## Project Structure

The AI Companion codebase is organized into the following structure:

```
src/
├── ai_companion/
│   ├── core/               # Core functionality and base classes
│   │   ├── prompts.py      # System prompts and templates
│   │   └── ...
│   ├── graph/              # Conversation graph implementation
│   │   ├── nodes.py        # Node implementations for conversation flow
│   │   ├── edges.py        # Edge definitions connecting nodes
│   │   ├── graph.py        # Graph orchestration
│   │   ├── state.py        # Conversation state management
│   │   └── utils/          # Graph utilities
│   │       ├── chains.py   # LLM chain definitions
│   │       ├── helpers.py  # Helper functions
│   │       └── ...
│   ├── interfaces/         # External interface implementations
│   │   ├── whatsapp/       # WhatsApp integration
│   │   └── ...
│   ├── modules/            # Feature-specific modules
│   │   ├── image/          # Image generation and processing
│   │   ├── memory/         # Memory management
│   │   │   ├── long_term/  # Long-term memory storage
│   │   │   └── ...
│   │   ├── rag/            # Retrieval-Augmented Generation
│   │   │   ├── core/       # Core RAG functionality
│   │   │   │   ├── enhanced_retrieval.py  # Advanced retrieval methods
│   │   │   │   ├── monitoring.py          # RAG monitoring and metrics
│   │   │   │   ├── query_preprocessor.py  # Query enhancement
│   │   │   │   ├── rag_chain.py           # Main RAG chain implementation
│   │   │   │   ├── response_generation.py # Response creation
│   │   │   │   └── vector_store.py        # Vector database interface
│   │   │   └── ...
│   │   ├── schedules/      # Scheduling and context generation
│   │   ├── speech/         # Text-to-speech functionality
│   │   └── ...
│   ├── api/                # API endpoints and routing
│   ├── utils/              # Shared utilities and helpers
│   └── settings.py         # Application settings
├── tests/                  # Test suite
└── ...
```

## Key Components

### 1. Conversation Graph

The conversation flow is managed through a directed graph where:
- **Nodes**: Represent processing steps (e.g., routing, RAG, conversation, image, audio)
- **Edges**: Define the flow between nodes based on conditions
- **State**: Maintains conversation context across nodes
- **Flow**: 
  1. Memory extraction
  2. Message routing
  3. RAG processing (with retry capability)
  4. Memory injection
  5. Response generation (conversation, image, or audio)
  6. Conversation summarization (when needed)

### 2. RAG System

The RAG system is implemented as a modular pipeline:
- **Query Preprocessor**: Enhances queries for better retrieval
- **Vector Store**: Manages document embeddings and retrieval
- **Enhanced Retrieval**: Implements advanced search strategies
- **Response Generator**: Creates coherent responses from retrieved documents
- **Monitoring**: Tracks performance and errors

### 3. Memory Management

Memory is handled at multiple levels:
- **Short-term**: Recent conversation turns
- **Long-term**: Important information extracted from conversations
- **Contextual**: Activity-specific information

### 4. Multimodal Processing

The system supports multiple modalities:
- **Text**: Primary input/output format
- **Images**: Generation based on text prompts
- **Audio**: Text-to-speech conversion

## Integration Points

The AI Companion integrates with external systems through:
- **API Endpoints**: For web and mobile applications
- **Messaging Interfaces**: For platforms like WhatsApp
- **Vector Database**: For knowledge retrieval
- **Relational Database**: For user data and settings 