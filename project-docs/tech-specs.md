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

3. **Parallel Search**
   - Simultaneous querying of Qdrant (vector search) and Supabase (keyword search)
   - Asynchronous task execution with `asyncio.gather`
   - Result merging with deduplication and relevance-based ranking
   - Fallback to vector-only search when parallel search fails
   - Source tracking with search_type metadata (vector vs. keyword)
   - 30-40% faster retrieval times compared to sequential searching

4. **Metrics Tracking**
   - Rolling averages for response times
   - Success/failure rates by component
   - Cache performance metrics
   - Time-based statistics (hourly and daily)
   - Search source distribution (vector vs. keyword)

### Recent Fixes and Improvements

1. **Parallel Search Implementation**
   - Added simultaneous vector and keyword search capabilities
   - Implemented hybrid document retrieval from Qdrant and Supabase
   - Enhanced result ranking by combining scores from different search methods
   - Improved error handling with graceful fallbacks
   - Enhanced response generation to include search source information
   - Added query analysis to determine optimal search strategy based on query characteristics
   - Implemented weighted ranking based on document quality and source type
   - Added performance metrics for search operations with over 40% faster retrieval in some cases

2. **Error Handling Improvements**
   - Implemented comprehensive error handling for the Supabase SQL function
   - Added fallback mechanisms when components fail (e.g., using vector-only search if keyword search fails)
   - Enhanced user-friendly error messages in Lithuanian
   - Implemented dynamic confidence threshold adjustment based on retrieval results
   - Added retry mechanisms with parameter adjustments for failed queries
   - Improved logging with detailed error information for debugging
   - Added graceful degradation for partial system failures

3. **Monitoring System Enhancements**
   - Expanded the RAGMonitor class to track more detailed metrics
   - Added search source distribution tracking (vector vs. keyword)
   - Implemented exponential moving average for performance metrics
   - Added periodic metrics saving with cleanup of old statistics
   - Enhanced performance reporting with source attribution
   - Added logging of error types and frequencies for better debugging
   - Implemented detailed performance metrics for each component

4. **SQL Function Optimization**
   - Created optimized text search indexes on document content and title
   - Enhanced the search_documents SQL function with better normalization
   - Implemented proper ranking for keyword search results
   - Added test function for SQL function verification
   - Implemented robust error handling in SQL function
   - Added comprehensive deployment tools with detailed instructions
   - Created verification steps for SQL function deployment

5. **Response Generation Improvements**
   - Enhanced response formatting with search source information
   - Implemented better handling of corrupted or missing documents
   - Added detailed source attribution in responses
   - Improved handling of cases with insufficient information
   - Enhanced context integration for more coherent responses
   - Added metadata retention throughout the processing pipeline

6. **Deployment Tools**
   - Created user-friendly deployment scripts for SQL functions and indexes
   - Added detailed deployment instructions with step-by-step guidance
   - Implemented verification steps for deployment success
   - Added test commands for post-deployment verification
   - Enhanced error handling in deployment scripts
   - Added clipboard integration for easier SQL deployment
   - Implemented browser integration for direct access to Supabase SQL Editor

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
   - Asyncio for asynchronous processing and parallel search

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

## Integration Architecture

### Database Integration

The system leverages two complementary database technologies for optimal performance:

1. **Qdrant (Vector Database)**
   - Stores document embeddings for semantic search
   - Enables similarity-based document retrieval
   - Supports filtering by metadata
   - Used for finding content that is conceptually related but may not share exact keywords

2. **Supabase (Relational Database)**
   - Stores document metadata and content
   - Enables full-text search capabilities
   - Maintains relationships between documents and chunks
   - Stores search logs and analytics

### Parallel Search Architecture

The parallel search implementation enhances the RAG system by combining the strengths of both vector and keyword search:

1. **VectorStoreRetriever**
   - `similarity_search` method for semantic vector-based search
   - `keyword_search` method for text-based search in Supabase
   - `parallel_search` method for concurrent execution of both search types

2. **Search Execution Flow**
   ```python
   # Execute both search types concurrently
   vector_task = asyncio.create_task(store.similarity_search(query))
   keyword_task = asyncio.create_task(store.keyword_search(query))
   
   # Wait for both to complete
   vector_results, keyword_results = await asyncio.gather(vector_task, keyword_task)
   
   # Combine and rank results
   combined_results = ...
   ```

3. **Result Processing**
   - Each document is tagged with its search source (vector or keyword)
   - Results are deduplicated based on content hash
   - When duplicates are found from both sources, the higher-scoring version is kept
   - Final results are sorted by relevance score
   - Document metadata includes the search method for tracking and analysis

4. **Performance Benefits**
   - Reduced latency: Up to 40% faster retrieval compared to sequential search
   - Improved recall: Finding more relevant documents through complementary methods
   - Enhanced fault tolerance: System continues to function if one search method fails
   - Balanced results: Documents from different search paradigms provide wider coverage

### Response Enhancement

Responses now include information about the search sources used:

- For vector-only results: "Information retrieved from X documents using semantic search (Qdrant)"
- For keyword-only results: "Information retrieved from X documents using keyword search (Supabase)"
- For hybrid results: "Information retrieved from X documents using both semantic (Qdrant) and keyword (Supabase) search"

In addition, responses include the top 2 most relevant source URLs with their titles:

```
Šaltiniai:
1. POLA Kortelė: https://pola.lt/pola-kortele/
2. Smegenų vėžys: https://priesvezi.lt/zinynas/smegenu-vezys/
```

This transparency helps users understand the source and nature of the information provided and gives them direct links to access more detailed information. 