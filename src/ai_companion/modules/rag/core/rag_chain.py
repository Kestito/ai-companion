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
            
            logger.info("Lithuanian RAG chain initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing RAG chain: {str(e)}")
            raise
    
    async def _get_cache_key(self, query: str, **kwargs) -> str:
        """Generate a cache key for the query and parameters.
        
        Args:
            query: The user query
            **kwargs: Additional parameters that affect the result
            
        Returns:
            A string hash representing the cache key
        """
        # Create a string representation of the query and relevant parameters
        cache_str = f"{query.lower().strip()}"
        
        # Add relevant parameters that would affect the result
        if kwargs.get('min_confidence'):
            cache_str += f"|conf:{kwargs['min_confidence']}"
        if kwargs.get('collection_name'):
            cache_str += f"|coll:{kwargs['collection_name']}"
        
        # Generate a hash of the string
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    async def _get_from_cache(self, key: str) -> Optional[Tuple[str, List[Document]]]:
        """Get a result from the cache if it exists and is not expired.
        
        Args:
            key: The cache key
            
        Returns:
            The cached result or None if not found
        """
        async with self.cache_lock:
            if key in self.cache:
                entry = self.cache[key]
                # Check if the entry is expired (older than 1 hour)
                if datetime.now() - entry['timestamp'] < timedelta(hours=1):
                    self.metrics['cache_hits'] += 1
                    logger.debug(f"Cache hit for key: {key}")
                    return entry['result']
                else:
                    # Remove expired entry
                    del self.cache[key]
        
        self.metrics['cache_misses'] += 1
        logger.debug(f"Cache miss for key: {key}")
        return None
    
    async def _add_to_cache(self, key: str, result: Tuple[str, List[Document]]) -> None:
        """Add a result to the cache.
        
        Args:
            key: The cache key
            result: The result to cache
        """
        async with self.cache_lock:
            # If cache is full, remove the oldest entry
            if len(self.cache) >= self.cache_size:
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['timestamp'])
                del self.cache[oldest_key]
            
            # Add new entry
            self.cache[key] = {
                'result': result,
                'timestamp': datetime.now()
            }
            logger.debug(f"Added result to cache with key: {key}")
    
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
        **kwargs: Any
    ) -> List[Document]:
        """Retrieve documents for query variations with error handling.
        
        Args:
            query_variations: List of query variations to search for
            min_confidence: Minimum confidence score for results
            **kwargs: Additional parameters for retrieval
            
        Returns:
            List of retrieved documents
            
        Raises:
            RetrievalError: If retrieval fails or no documents are found
        """
        try:
            start_time = time.time()
            docs = []
            
            for query_variation in query_variations:
                try:
                    # Remove 'k' from kwargs if it's present to avoid parameter duplication
                    search_kwargs = kwargs.copy()
                    if 'k' in search_kwargs:
                        del search_kwargs['k']
                        
                    results = await self.store.similarity_search(
                        query=query_variation,
                        k=10,
                        score_threshold=min_confidence,
                        **search_kwargs
                    )
                    if results:
                        docs.extend([doc for doc, _ in results])
                except Exception as e:
                    logger.warning(f"Error in similarity search for variation {query_variation}: {str(e)}")
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
        docs: List[Document],
        memory_context: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Generate a response based on retrieved documents with error handling.
        
        Args:
            query: The user query
            docs: Retrieved documents
            memory_context: Additional context from memory
            **kwargs: Additional parameters for response generation
            
        Returns:
            Generated response
            
        Raises:
            ResponseGenerationError: If response generation fails
        """
        try:
            start_time = time.time()
            
            # Handle empty document list
            if not docs:
                logger.warning("No documents provided for response generation")
                return "Atsiprašau, bet neturiu pakankamai informacijos apie šią temą. Galbūt galėtumėte užduoti klausimą kitaip arba pasiteirauti apie kitą temą?"
            
            # Create a default query_intent if not provided
            if 'query_intent' not in kwargs:
                kwargs['query_intent'] = {
                    'type': 'general',
                    'intent': 'information'
                }
            
            response = await self.response_generator.generate_response(
                query=query,
                docs=docs,
                query_intent=kwargs.get('query_intent'),
                confidence_threshold=kwargs.get('min_confidence', 0.7)
            )
            
            generation_time = time.time() - start_time
            
            # Update metrics
            self.metrics['response_generation_time'] = (
                self.metrics['response_generation_time'] * 0.9 + generation_time * 0.1
            )
            
            # Extract the response text from the response dict
            if isinstance(response, dict) and 'response' in response:
                response_text = response['response']
                # Add database source information
                response_text += f"\n\n(Informacija gauta iš Qdrant duomenų bazės, kolekcija: {self.store.collection_name})"
                return response_text
            
            # Add database source information to string response
            response_str = str(response)
            response_str += f"\n\n(Informacija gauta iš Qdrant duomenų bazės, kolekcija: {self.store.collection_name})"
            return response_str
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            await self.monitor.log_error('response_generation', query, str(e))
            raise ResponseGenerationError(f"Response generation failed: {str(e)}")
    
    async def query(
        self,
        query: str,
        memory_context: Optional[str] = None,
        max_retries: int = 3,
        min_confidence: float = 0.5,
        use_cache: bool = True,
        **kwargs: Any
    ) -> Tuple[str, List[Document]]:
        """Process Lithuanian query through the enhanced RAG pipeline.
        
        Args:
            query: The user query
            memory_context: Additional context from memory
            max_retries: Maximum number of retries for failed operations
            min_confidence: Minimum confidence score for retrieval results
            use_cache: Whether to use the cache for this query
            **kwargs: Additional parameters for processing
            
        Returns:
            Tuple of (response, documents)
        """
        start_time = time.time()
        
        try:
            # Check cache first if enabled
            if use_cache:
                cache_key = await self._get_cache_key(query, min_confidence=min_confidence, **kwargs)
                cached_result = await self._get_from_cache(cache_key)
                if cached_result:
                    logger.info(f"Returning cached result for query: {query}")
                    return cached_result
            
            # Process query
            query_info = await self._process_query(query)
            
            # Retrieve documents
            docs = await self._retrieve_documents(
                query_variations=query_info['variations'],
                min_confidence=min_confidence,
                **kwargs
            )
            
            # If no documents found with current threshold, try with a lower threshold
            if not docs and min_confidence > 0.3:
                logger.info(f"No documents found with threshold {min_confidence}, trying with lower threshold 0.3")
                docs = await self._retrieve_documents(
                    query_variations=query_info['variations'],
                    min_confidence=0.3,
                    **kwargs
                )
            
            # Generate response
            response = await self._generate_response(
                query=query,
                docs=docs,
                memory_context=memory_context,
                **kwargs
            )
            
            # Update metrics
            total_time = time.time() - start_time
            self.metrics['total_processing_time'] = (
                self.metrics['total_processing_time'] * 0.9 + total_time * 0.1
            )
            self.metrics['successful_queries'] += 1
            self.metrics['total_queries'] += 1
            
            # Log success
            await self.monitor.log_success(
                question=query,
                num_docs=len(docs),
                response_metadata={
                    'query_time': self.metrics['query_processing_time'],
                    'retrieval_time': self.metrics['retrieval_time'],
                    'response_time': self.metrics['response_generation_time'],
                    'total_time': total_time
                }
            )
            
            # Cache result if enabled
            if use_cache:
                await self._add_to_cache(cache_key, (response, docs))
            
            return response, docs
            
        except QueryError as e:
            logger.error(f"Query processing error: {str(e)}")
            await self.monitor.log_error('query_processing', query, str(e))
            self.metrics['failed_queries'] += 1
            self.metrics['total_queries'] += 1
            return f"Atsiprašau, bet nepavyko apdoroti jūsų klausimo. {str(e)} (Bandyta ieškoti Qdrant duomenų bazėje, kolekcija: {self.store.collection_name})", []
            
        except RetrievalError as e:
            logger.error(f"Retrieval error: {str(e)}")
            await self.monitor.log_error('insufficient_info', query, str(e))
            self.metrics['failed_queries'] += 1
            self.metrics['total_queries'] += 1
            return f"Atsiprašau, bet neturiu pakankamai informacijos atsakyti į šį klausimą. (Bandyta ieškoti Qdrant duomenų bazėje, kolekcija: {self.store.collection_name})", []
            
        except ResponseGenerationError as e:
            logger.error(f"Response generation error: {str(e)}")
            await self.monitor.log_error('response_generation', query, str(e))
            self.metrics['failed_queries'] += 1
            self.metrics['total_queries'] += 1
            return f"Atsiprašau, bet nepavyko sugeneruoti atsakymo. Prašome bandyti dar kartą. (Bandyta ieškoti Qdrant duomenų bazėje, kolekcija: {self.store.collection_name})", []
            
        except Exception as e:
            logger.error(f"Unexpected error in RAG chain: {str(e)}")
            await self.monitor.log_error('system', query, str(e))
            self.metrics['failed_queries'] += 1
            self.metrics['total_queries'] += 1
            return f"Atsiprašau, bet įvyko sistemos klaida. Prašome bandyti vėliau. (Bandyta ieškoti Qdrant duomenų bazėje, kolekcija: {self.store.collection_name})", []
    
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
    
    def _create_no_docs_response(self, query_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create Lithuanian response for no documents case."""
        return {
            'query_info': query_info,
            'response': f"Atsiprašau, bet nepavyko rasti jokių dokumentų, susijusių su jūsų klausimu. (Bandyta ieškoti Qdrant duomenų bazėje, kolekcija: {self.store.collection_name})",
            'confidence': 0.0,
            'sources': [],
            'success': False,
            'error': "Nerasta dokumentų"
        }
    
    def _create_no_results_response(self, query_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create Lithuanian response for no search results case."""
        return {
            'query_info': query_info,
            'response': f"Atsiprašau, bet nepavyko rasti pakankamai aktualios informacijos tiksliai atsakyti į jūsų klausimą. (Bandyta ieškoti Qdrant duomenų bazėje, kolekcija: {self.store.collection_name})",
            'confidence': 0.0,
            'sources': [],
            'success': False,
            'error': "Nerasta aktualių rezultatų"
        }
    
    def _create_no_relevant_docs_response(self, query_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create Lithuanian response for no relevant documents case."""
        return {
            'query_info': query_info,
            'response': f"Atsiprašau, bet turima informacija nėra pakankamai aktuali pateikti tikslų atsakymą. (Bandyta ieškoti Qdrant duomenų bazėje, kolekcija: {self.store.collection_name})",
            'confidence': 0.0,
            'sources': [],
            'success': False,
            'error': "Nerasta aktualių dokumentų"
        }
    
    def _create_error_response(self, error_msg: str) -> Tuple[str, List[Document]]:
        """Create error response."""
        return (
            f"Atsiprašau, įvyko klaida: {error_msg}. Prašome bandyti vėliau. (Bandyta ieškoti Qdrant duomenų bazėje, kolekcija: {self.store.collection_name})",
            []
        )
