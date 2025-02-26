from typing import Dict, List, Optional, Tuple, AsyncIterator, Any
from langchain_openai import AzureChatOpenAI
from langchain.schema import Document
from langchain.prompts import PromptTemplate
import os
import logging
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .monitoring import RAGMonitor
from .enhanced_retrieval import EnhancedRetrieval
from .response_generation import LithuanianResponseGenerator
from .query_preprocessor import LithuanianQueryPreprocessor
from .vector_store import VectorStoreRetriever
import time
import json
import hashlib
import asyncio
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Singleton instance
_rag_chain_instance = None

def get_rag_chain(
    model_deployment: Optional[str] = None,
    model_name: Optional[str] = None,
    prompt_template: Optional[str] = None
) -> 'LithuanianRAGChain':
    """Get or create a singleton instance of LithuanianRAGChain.
    
    Args:
        model_deployment: Azure OpenAI model deployment name
        model_name: Model name
        prompt_template: Custom prompt template for response generation
        
    Returns:
        Configured LithuanianRAGChain instance
    """
    global _rag_chain_instance
    if _rag_chain_instance is None:
        _rag_chain_instance = LithuanianRAGChain(
            model_deployment=model_deployment,
            model_name=model_name
        )
    return _rag_chain_instance

class QueryError(Exception):
    """Exception raised for errors in the query processing."""
    pass

class RetrievalError(Exception):
    """Exception raised for errors in the retrieval process."""
    pass

class ResponseGenerationError(Exception):
    """Exception raised for errors in the response generation."""
    pass

class LithuanianRAGChain:
    """Advanced RAG chain with Lithuanian language support and maximum accuracy."""
    
    def __init__(
        self,
        collection_name: str = "Information",
        model_deployment: Optional[str] = None,
        model_name: Optional[str] = None,
        embedding_deployment: Optional[str] = None,
        embedding_model: Optional[str] = None,
        temperature: float = 0.0,
        cache_size: int = 100
    ):
        """Initialize RAG chain with Lithuanian components.
        
        Args:
            collection_name: Name of the vector store collection
            model_deployment: Azure OpenAI model deployment name
            model_name: Model name
            embedding_deployment: Azure OpenAI embedding deployment name
            embedding_model: Embedding model name
            temperature: Temperature for generation
            cache_size: Size of the LRU cache for query results
        """
        try:
            # Initialize monitor first
            self.monitor = RAGMonitor()
            
            # Initialize components
            self.query_processor = LithuanianQueryPreprocessor(
                model_deployment=model_deployment,
                model_name=model_name,
                temperature=temperature
            )
            
            self.retriever = EnhancedRetrieval(
                model_deployment=model_deployment,
                model_name=model_name,
                temperature=temperature
            )
            
            self.response_generator = LithuanianResponseGenerator(
                model_deployment=model_deployment,
                model_name=model_name,
                temperature=temperature
            )
            
            self.store = VectorStoreRetriever(
                collection_name=collection_name,
                embedding_deployment=embedding_deployment,
                embedding_model=embedding_model
            )

            # Initialize metrics
            self.metrics = {
                'total_queries': 0,
                'successful_queries': 0,
                'failed_queries': 0,
                'average_confidence': 0.0,
                'query_processing_time': 0.0,
                'retrieval_time': 0.0,
                'response_generation_time': 0.0,
                'total_processing_time': 0.0,
                'cache_hits': 0,
                'cache_misses': 0,
                'error_details': {},
                'last_updated': datetime.now().isoformat()
            }
            
            # Initialize cache
            self.cache = {}
            self.cache_size = cache_size
            self.cache_lock = asyncio.Lock()
            self.cache_enabled = True  # Enable caching by default
            self.query_count = 0  # Initialize query counter
            
            self.collection_name = collection_name
            
            logger.info("Lithuanian RAG chain initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing RAG chain: {str(e)}")
            raise
    
    def _generate_cache_key(self, query: str, min_confidence: float, kwargs: Dict[str, Any]) -> str:
        """Generate a cache key from the query and parameters."""
        # Create a stable representation of kwargs
        sorted_kwargs = {k: kwargs.get(k) for k in sorted(kwargs.keys()) 
                         if k not in ['memory_context', 'query_variations']}
        
        # Hash the combined parameters
        key_str = f"{query}:{min_confidence}:{str(sorted_kwargs)}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def _get_from_cache(self, key: str) -> Optional[Tuple[str, List[Document]]]:
        """Get a result from the cache if it exists."""
        async with self.cache_lock:
            if key in self.cache:
                entry = self.cache[key]
                # Check if the entry is still valid (not expired)
                if entry['expiry'] > time.time():
                    logger.info(f"Cache hit for key: {key[:8]}...")
                    return entry['value']
                else:
                    # Remove expired entry
                    del self.cache[key]
                    logger.info(f"Cache entry expired for key: {key[:8]}...")
        return None
    
    async def _add_to_cache(self, key: str, value: Tuple[str, List[Document]]) -> None:
        """Add a result to the cache with expiry."""
        async with self.cache_lock:
            # Set expiry to current time + 1 hour
            expiry = time.time() + 3600  # 1 hour cache lifetime
            
            # Add to cache, with LRU eviction if needed
            if len(self.cache) >= self.cache_size:
                # Find the oldest entry
                oldest_key = min(self.cache, key=lambda k: self.cache[k]['last_access'])
                del self.cache[oldest_key]
                logger.info(f"Evicted oldest cache entry: {oldest_key[:8]}...")
            
            self.cache[key] = {
                'value': value,
                'expiry': expiry,
                'last_access': time.time()
            }
            logger.info(f"Added result to cache with key: {key[:8]}...")
    
    @retry(
        retry=retry_if_exception_type((QueryError, RetrievalError, ResponseGenerationError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _process_query(
        self,
        query: str,
        context_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process and enhance the query with error handling.
        
        Args:
            query: The user query
            context_type: Type of context to consider
            
        Returns:
            Dictionary with processed query information
            
        Raises:
            QueryError: If query processing fails
        """
        try:
            start_time = time.time()
            result = await self.query_processor.process_query(query, context_type=context_type)
            processing_time = time.time() - start_time
            
            # Update metrics
            self.metrics['query_processing_time'] = (
                self.metrics['query_processing_time'] * 0.9 + processing_time * 0.1
            )
            
            if not result['success']:
                raise QueryError(f"Query processing failed: {result.get('error', 'Unknown error')}")
            
            return result
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            await self.monitor.log_error('query_processing', query, str(e))
            raise QueryError(f"Query processing failed: {str(e)}")
    
    @retry(
        retry=retry_if_exception_type(RetrievalError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _retrieve_documents(
        self,
        query_variations: List[str],
        min_confidence: float = 0.7,
        prioritized_urls: Optional[List[str]] = None,
        **kwargs: Any
    ) -> List[Document]:
        """Retrieve documents for query variations with error handling.
        
        Args:
            query_variations: List of query variations to search for
            min_confidence: Minimum confidence score for results
            prioritized_urls: URLs to prioritize in the ranking (boosted score)
            **kwargs: Additional parameters for retrieval
            
        Returns:
            List of retrieved documents
            
        Raises:
            RetrievalError: If retrieval fails or no documents are found
        """
        try:
            start_time = time.time()
            docs = []
            
            # Process query variations
            for query_variation in query_variations:
                try:
                    # Remove 'k' from kwargs if it's present to avoid parameter duplication
                    search_kwargs = kwargs.copy()
                    if 'k' in search_kwargs:
                        del search_kwargs['k']
                    
                    # Use parallel search for each query variation
                    results = await self.store.parallel_search(
                        query=query_variation,
                        k=10,
                        score_threshold=min_confidence,
                        filter_conditions=search_kwargs.get('filter_conditions'),
                        prioritized_urls=prioritized_urls
                    )
                    
                    if results:
                        docs.extend([doc for doc, _ in results])
                except Exception as e:
                    logger.warning(f"Error in parallel search for variation {query_variation}: {str(e)}")
                    continue
            
            # Remove duplicates while preserving order
            unique_docs = []
            seen = set()
            for doc in docs:
                doc_hash = hash(doc.page_content)
                if doc_hash not in seen:
                    unique_docs.append(doc)
                    seen.add(doc_hash)
            
            retrieval_time = time.time() - start_time
            
            # Update metrics
            self.metrics['retrieval_time'] = (
                self.metrics['retrieval_time'] * 0.9 + retrieval_time * 0.1
            )
            
            # Log the performance improvement
            logger.info(f"Parallel search completed in {retrieval_time:.2f} seconds")
            
            if not unique_docs:
                logger.warning("No relevant documents found with current threshold. Consider lowering min_confidence.")
                return []
            
            return unique_docs
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            raise RetrievalError(f"Document retrieval failed: {str(e)}")
    
    @retry(
        retry=retry_if_exception_type(ResponseGenerationError),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=5)
    )
    async def _generate_response(
        self,
        query: str,
        documents: List[Document],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Generate a response to the query using the retrieved documents.
        
        Args:
            query: Original user query
            documents: Retrieved documents
            **kwargs: Additional parameters for response generation
            
        Returns:
            Dictionary with response text and metadata
        """
        try:
            start_time = time.time()
            
            # Get source info and track search sources
            source_info = []
            vector_count = 0
            keyword_count = 0
            
            for doc in documents:
                metadata = doc.metadata
                search_type = metadata.get('search_type', 'vector')  # Default to 'vector' if not specified
                
                if search_type == 'vector':
                    vector_count += 1
                elif search_type == 'keyword':
                    keyword_count += 1
                
                if 'title' in metadata and 'url' in metadata:
                    source_info.append({
                        'title': metadata.get('title', 'Unknown'),
                        'url': metadata.get('url', '#'),
                        'score': metadata.get('score', 0.0),
                        'search_type': search_type
                    })
            
            # Generate response
            try:
                # Extract memory_context from kwargs if provided
                memory_context = kwargs.get('memory_context', None)
                
                # Call the response generator's _generate_response method directly
                response = await self.response_generator._generate_response(
                    query=query,
                    documents=documents,
                    memory_context=memory_context
                )
            except Exception as e:
                logger.error(f"Error in response generation: {str(e)}")
                response = f"Nepavyko sugeneruoti detalaus atsakymo. Bandykite dar kartą arba užduokite kitą klausimą."
            
            generation_time = time.time() - start_time
            
            # Update metrics
            self.metrics['response_generation_time'] = (
                self.metrics['response_generation_time'] * 0.9 + generation_time * 0.1
            )
            
            # Track different source types in the final response metadata
            source_distribution = {
                'vector_count': vector_count,
                'keyword_count': keyword_count,
                'total_count': len(documents)
            }
            
            # Log response metrics for monitoring
            await self.monitor.log_success(
                question=query,
                num_docs=len(documents),
                response_metadata={
                    'source_distribution': source_distribution,
                    'generation_time': generation_time,
                    'search_types': ['vector' if vector_count > 0 else None, 'keyword' if keyword_count > 0 else None]
                }
            )
            
            return {
                'response': response,
                'sources': source_info,
                'document_count': len(documents),
                'vector_sources': vector_count,
                'keyword_sources': keyword_count,
                'confidence': 1.0 if len(documents) > 0 else 0.5,  # Adjust confidence based on document count
                'generation_time': generation_time,
                'search_types_used': ['vector' if vector_count > 0 else None, 'keyword' if keyword_count > 0 else None]
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            
            # Log the error for monitoring
            await self.monitor.log_error('response_generation', query, str(e))
            
            # Create a detailed error response
            error_response = {
                'response': f"Atsiprašau, įvyko klaida apdorojant duomenis. Bandykite dar kartą. (Collection: {self.collection_name})",
                'sources': [],
                'document_count': 0,
                'confidence': 0.0,
                'generation_time': 0.0,
                'error': str(e),
                'error_type': type(e).__name__
            }
            
            return error_response
    
    async def query(
        self,
        query: str,
        min_confidence: float = 0.7,
        query_variations: Optional[List[str]] = None,
        memory_context: Optional[str] = None,
        prioritized_urls: Optional[List[str]] = None,
        **kwargs: Any
    ) -> Tuple[str, List[Document]]:
        """Execute the RAG pipeline for a query.
        
        Args:
            query: User query
            min_confidence: Minimum confidence threshold for vector search
            query_variations: Optional pre-computed query variations
            memory_context: Optional memory/conversation context
            prioritized_urls: URLs to prioritize in the ranking (boosted score)
            **kwargs: Additional parameters for retrieval
            
        Returns:
            Tuple of (response text, retrieved documents)
        """
        # Increment query counter
        self.query_count += 1
        
        # Generate cache key
        cache_key = self._generate_cache_key(query, min_confidence, kwargs)
        
        # Check cache if enabled
        if self.cache_enabled:
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                logger.info(f"Cache hit for query: {query}")
                # Update metrics for cache hit
                self.metrics['cache_hits'] += 1
                return cached_result
        
        start_time = time.time()
        
        try:
            # Process query and generate variations
            query_info = await self._process_query(query, kwargs.get("context_type"))
            variations = query_info.get("variations", [query])
            if query_variations:
                variations.extend(query_variations)
            
            # Get unique variations
            unique_variations = list(set(variations))
            logger.info(f"Generated {len(unique_variations)} query variations")
            
            # Retrieve documents
            documents = await self._retrieve_documents(
                query_variations=unique_variations,
                min_confidence=min_confidence,
                prioritized_urls=prioritized_urls,
                **kwargs
            )
            
            # If no documents found, return special response
            if not documents:
                logger.warning(f"No documents found for query: {query}")
                return self._create_no_docs_response(query_info)
            
            # Generate response
            response_info = await self._generate_response(
                query=query,
                documents=documents,
                memory_context=memory_context,
                **kwargs
            )
            
            response_text = response_info.get("response", "")
            enhanced_documents = response_info.get("documents", documents)
            
            # Store in cache if enabled
            if self.cache_enabled:
                await self._add_to_cache(cache_key, (response_text, enhanced_documents))
            
            # Update metrics for successful query
            elapsed_time = time.time() - start_time
            self._update_metrics(
                success=True,
                confidence=response_info.get("confidence", 0.5),
                response_time=elapsed_time
            )
            
            return response_text, enhanced_documents
        
        except QueryError as qe:
            logger.error(f"Query processing error: {str(qe)}")
            return self._create_error_response(f"Failed to process query: {str(qe)}")
            
        except RetrievalError as re:
            logger.error(f"Retrieval error: {str(re)}")
            return self._create_error_response(f"Failed to retrieve relevant information: {str(re)}")
            
        except ResponseGenerationError as ge:
            logger.error(f"Response generation error: {str(ge)}")
            return self._create_error_response(f"Failed to generate response: {str(ge)}")
            
        except Exception as e:
            logger.error(f"Unexpected error in RAG chain: {str(e)}")
            return self._create_error_response(f"An unexpected error occurred: {str(e)}")
        
        finally:
            # Periodically save metrics
            if self.query_count % 10 == 0:
                self._save_metrics()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return {
            **self.metrics,
            'query_processing_time': 0.0,
            'retrieval_time': 0.0,
            'response_generation_time': 0.0,
            'total_processing_time': 0.0,
            'error_details': {}
        }
    
    def _update_metrics(
        self,
        success: bool,
        confidence: float,
        response_time: float
    ) -> None:
        """Update metrics with new query information."""
        self.metrics['total_queries'] += 1
        if success:
            self.metrics['successful_queries'] += 1
        else:
            self.metrics['failed_queries'] += 1
            
        # Update average confidence
        total_queries = self.metrics['total_queries']
        current_avg = self.metrics['average_confidence']
        self.metrics['average_confidence'] = (
            (current_avg * (total_queries - 1) + confidence) / total_queries
        )
        
        # Update timestamp
        self.metrics['last_updated'] = datetime.now().isoformat()
    
    def _save_metrics(self) -> None:
        """Save metrics to file."""
        try:
            with open("rag_metrics.json", "w") as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metrics: {str(e)}")
    
    def _create_no_docs_response(self, query_info: Dict[str, Any]) -> Tuple[str, List[Document]]:
        """Create Lithuanian response for no documents case."""
        response_text = f"Atsiprašau, bet nepavyko rasti jokių dokumentų, susijusių su jūsų klausimu. (Bandyta ieškoti Qdrant duomenų bazėje, kolekcija: {self.collection_name})"
        return (response_text, [])
    
    def _create_no_results_response(self, query_info: Dict[str, Any]) -> Tuple[str, List[Document]]:
        """Create Lithuanian response for no search results case."""
        response_text = f"Atsiprašau, bet nepavyko rasti pakankamai aktualios informacijos tiksliai atsakyti į jūsų klausimą. (Bandyta ieškoti Qdrant duomenų bazėje, kolekcija: {self.collection_name})"
        return (response_text, [])
    
    def _create_no_relevant_docs_response(self, query_info: Dict[str, Any]) -> Tuple[str, List[Document]]:
        """Create Lithuanian response for no relevant documents case."""
        response_text = f"Atsiprašau, bet turima informacija nėra pakankamai aktuali pateikti tikslų atsakymą. (Bandyta ieškoti Qdrant duomenų bazėje, kolekcija: {self.collection_name})"
        return (response_text, [])
    
    def _create_error_response(self, error_msg: str) -> Tuple[str, List[Document]]:
        """Create error response."""
        return (
            f"Atsiprašau, įvyko klaida: {error_msg}. Prašome bandyti vėliau. (Bandyta ieškoti Qdrant duomenų bazėje, kolekcija: {self.collection_name})",
            []
        )

    async def process_query(self, query: str) -> List[str]:
        """Process a query and get variations.
        
        Args:
            query: The original user query
            
        Returns:
            List of query variations
        """
        result = await self.query_processor.process_query(query)
        return result['variations']
