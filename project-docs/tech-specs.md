# Technical Specifications

## RAG System Architecture

The Retrieval-Augmented Generation (RAG) system is the core knowledge component of the AI Companion, designed to provide accurate, factual responses based on retrieved information. The system is built with a focus on Lithuanian language support, accuracy, and performance.

### Core Components

1. **LithuanianRAGChain**
   - Central orchestrator that manages the entire RAG pipeline
   - Implements caching for improved performance
   - Provides granular error handling and retry mechanisms
   - Maintains metrics for monitoring and optimization

2. **Query Preprocessor**
   - Enhances user queries for better retrieval
   - Generates query variations to improve recall
   - Handles Lithuanian language nuances
   - Identifies query intent for context-aware processing

3. **Enhanced Retrieval**
   - Implements hybrid search strategies (semantic + keyword)
   - Supports reranking for improved precision
   - Filters results based on confidence thresholds
   - Handles multiple query variations

4. **Response Generator**
   - Creates coherent responses based on retrieved information
   - Ensures factual accuracy and source attribution
   - Maintains consistent tone and style
   - Handles cases with insufficient information

5. **Monitoring System**
   - Tracks performance metrics and error rates
   - Logs system behavior for debugging
   - Provides performance reports for optimization
   - Implements periodic metrics saving and cleanup

### Integration Points

1. **rag_node**
   - Primary graph node for RAG processing
   - Handles parameter validation and defaults
   - Manages conversation context integration
   - Returns structured response with source attribution

2. **rag_retry_node**
   - Implements fallback strategies when initial retrieval fails
   - Adjusts parameters for improved recall
   - Provides alternative response approaches
   - Logs retry attempts for monitoring

### Error Handling

The RAG system implements robust error handling at multiple levels:

1. **Component-Level Exceptions**
   - QueryError: For issues in query processing
   - RetrievalError: For failures in document retrieval
   - ResponseGenerationError: For problems in response generation

2. **Retry Mechanisms**
   - Targeted retries for specific components
   - Exponential backoff to prevent system overload
   - Parameter adjustment during retries
   - Graceful degradation when retries are exhausted

3. **Fallback Responses**
   - User-friendly error messages in Lithuanian
   - Context-appropriate responses for different error types
   - Clear indication when information is unavailable
   - System status updates during failures

### Performance Considerations

1. **Caching**
   - LRU cache for frequently asked questions
   - Time-based cache expiration (1 hour)
   - Cache key generation based on query and parameters
   - Cache hit/miss metrics for optimization

2. **Asynchronous Processing**
   - All components implement async/await patterns
   - Parallel processing where appropriate
   - Non-blocking I/O for external services
   - Background tasks for metrics and maintenance

3. **Metrics Tracking**
   - Rolling averages for response times
   - Success/failure rates by component
   - Cache performance metrics
   - Time-based statistics (hourly and daily)

### Recent Fixes and Improvements

1. **Parameter Handling**
   - Improved validation in rag_node and rag_retry_node
   - Better default values for optimal performance
   - Enhanced error messages for debugging
   - Type annotations for better code quality

2. **Monitoring Enhancements**
   - Comprehensive metrics initialization
   - Periodic metrics saving to prevent data loss
   - Time-based statistics for trend analysis
   - Enhanced performance reporting

3. **Caching Implementation**
   - Added LRU cache with configurable size
   - Implemented time-based expiration
   - Added cache hit/miss metrics
   - Optimized cache key generation

4. **Error Handling Improvements**
   - Component-specific exception types
   - Targeted retry mechanisms
   - More informative error messages
   - Better logging for debugging

### Future Improvements

1. **Performance Optimization**
   - Vector store caching for faster retrieval
   - Batch processing for multiple queries
   - Optimized embedding generation
   - Response streaming for faster user feedback

2. **Quality Improvements**
   - Fact verification for response validation
   - Confidence scoring for retrieved information
   - Alternative source suggestions
   - Query reformulation based on feedback

3. **Monitoring Expansion**
   - User feedback collection
   - A/B testing framework
   - Anomaly detection for system issues
   - Automated performance optimization

## Technology Stack

1. **Core Framework**
   - LangChain for component orchestration
   - Pydantic for data validation
   - FastAPI for API endpoints
   - Asyncio for asynchronous processing

2. **AI Models**
   - Azure OpenAI for text generation
   - Text-embedding-3-small for embeddings
   - GPT-4o for advanced reasoning

3. **Storage**
   - Qdrant for vector storage
   - Supabase for relational data
   - File system for logs and metrics

4. **Deployment**
   - Docker for containerization
   - Docker Compose for local development
   - GitHub Actions for CI/CD
   - Azure for cloud hosting

## Lithuanian Language Support

### Enhanced Query Preprocessing

Our system features advanced Lithuanian language support through the `LithuanianQueryPreprocessor` component, which handles the complexities of the Lithuanian language and accommodates user input that may contain spelling errors or missing diacritical marks.

#### Key Features:

1. **LLM-Based Text Normalization**
   - Automatically corrects misspelled Lithuanian words
   - Adds proper diacritical marks (ą, č, ę, ė, į, š, ų, ū, ž)
   - Applies proper capitalization for names and entities

2. **Common Misspelling Correction**
   - Handles frequent misspellings in Lithuanian
   - Corrects case-sensitive entities like "POLA kortelė"
   - Maps informal spellings to their formal equivalents

3. **Entity Detection**
   - Identifies various entities in queries (POLA card, medical terms, locations)
   - Supports robust pattern matching with regular expressions
   - Tolerates spelling variations in entity recognition

4. **Query Variation Generation**
   - Creates multiple variations of user queries to improve retrieval
   - Handles both Latin and Lithuanian character versions
   - Generates synonyms and alternative phrasings

5. **Intent Classification**
   - Categorizes queries by intent (how-to, location, time, etc.)
   - Supports Lithuanian-specific question patterns
   - Helps route queries to appropriate handling mechanisms

### Examples of Handled Variations

The system can correctly process variations like:

| User Input | Normalized Form |
|------------|-----------------|
| "Pola kortele" | "POLA kortelė" |
| "kokios ismokos vilnius miegste" | "kokios išmokos Vilniaus mieste" |
| "ka daryti sergant smegenu veziu" | "ką daryti sergant smegenų vėžiu" |
| "smegenu vezys" | "smegenų vėžys" |
| "pola savanoris klaipedoje" | "POLA savanoris Klaipėdoje" |

### Technical Implementation

The preprocessor operates in multiple stages:

1. Basic cleaning and normalization
2. Rule-based correction for common misspellings
3. LLM-based normalization for complex cases
4. Entity detection and intent classification
5. Query enhancement with relevant context
6. Generation of multiple query variations

This multi-stage approach ensures robust handling of Lithuanian text, even when users type quickly without proper diacritical marks or make common spelling errors. 