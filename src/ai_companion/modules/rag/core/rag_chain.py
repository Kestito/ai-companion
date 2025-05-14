from typing import Dict, List, Optional, Tuple, Any
from langchain_core.documents import Document
import logging
from datetime import datetime
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from .monitoring import RAGMonitor
from .enhanced_retrieval import EnhancedRetrieval
from .response_generation import LithuanianResponseGenerator
from .query_preprocessor import LithuanianQueryPreprocessor
from .vector_store import VectorStoreRetriever
import time
import json
import hashlib
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Singleton instance
_rag_chain_instance = None


def get_rag_chain(
    model_deployment: Optional[str] = None,
    model_name: Optional[str] = None,
    prompt_template: Optional[str] = None,
) -> "LithuanianRAGChain":
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
            model_deployment=model_deployment, model_name=model_name
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
        cache_size: int = 100,
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
                temperature=temperature,
            )

            self.retriever = EnhancedRetrieval(
                model_deployment=model_deployment,
                model_name=model_name,
                temperature=temperature,
            )

            self.response_generator = LithuanianResponseGenerator(
                model_deployment=model_deployment,
                model_name=model_name,
                temperature=temperature,
            )

            self.store = VectorStoreRetriever(
                collection_name=collection_name,
                embedding_deployment=embedding_deployment,
                embedding_model=embedding_model,
            )

            # Initialize metrics
            self.metrics = {
                "total_queries": 0,
                "successful_queries": 0,
                "failed_queries": 0,
                "average_confidence": 0.0,
                "query_processing_time": 0.0,
                "retrieval_time": 0.0,
                "response_generation_time": 0.0,
                "total_processing_time": 0.0,
                "cache_hits": 0,
                "cache_misses": 0,
                "error_details": {},
                "last_updated": datetime.now().isoformat(),
            }

            # Initialize cache
            self.cache = {}
            self.cache_size = cache_size
            self.cache_lock = asyncio.Lock()
            self.cache_enabled = True  # Enable caching by default
            self.query_count = 0  # Initialize query counter

            self.collection_name = collection_name
            self.logger = logging.getLogger(__name__)

            logger.info("Lithuanian RAG chain initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing RAG chain: {str(e)}")
            raise

    def _generate_cache_key(
        self, query: str, min_confidence: float, kwargs: Dict[str, Any]
    ) -> str:
        """Generate a cache key from the query and parameters."""
        # Create a stable representation of kwargs
        sorted_kwargs = {
            k: kwargs.get(k)
            for k in sorted(kwargs.keys())
            if k not in ["memory_context", "query_variations"]
        }

        # Hash the combined parameters
        key_str = f"{query}:{min_confidence}:{str(sorted_kwargs)}"
        return hashlib.md5(key_str.encode()).hexdigest()

    async def _get_from_cache(self, key: str) -> Optional[Tuple[str, List[Document]]]:
        """Get a result from the cache if it exists."""
        async with self.cache_lock:
            if key in self.cache:
                entry = self.cache[key]
                # Check if the entry is still valid (not expired)
                if entry["expiry"] > time.time():
                    logger.info(f"Cache hit for key: {key[:8]}...")
                    return entry["value"]
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
                oldest_key = min(self.cache, key=lambda k: self.cache[k]["last_access"])
                del self.cache[oldest_key]
                logger.info(f"Evicted oldest cache entry: {oldest_key[:8]}...")

            self.cache[key] = {
                "value": value,
                "expiry": expiry,
                "last_access": time.time(),
            }
            logger.info(f"Added result to cache with key: {key[:8]}...")

    @retry(
        retry=retry_if_exception_type(
            (QueryError, RetrievalError, ResponseGenerationError)
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _process_query(
        self, query: str, context_type: Optional[str] = None
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
            result = await self.query_processor.process_query(
                query, context_type=context_type
            )
            processing_time = time.time() - start_time

            # Update metrics
            self.metrics["query_processing_time"] = (
                self.metrics["query_processing_time"] * 0.9 + processing_time * 0.1
            )

            if not result["success"]:
                raise QueryError(
                    f"Query processing failed: {result.get('error', 'Unknown error')}"
                )

            return result
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            await self.monitor.log_error("query_processing", query, str(e))
            raise QueryError(f"Query processing failed: {str(e)}")

    @retry(
        retry=retry_if_exception_type(RetrievalError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _retrieve_documents(
        self,
        query_variations: List[str],
        min_confidence: float = 0.7,
        prioritized_urls: Optional[List[str]] = None,
        **kwargs: Any,
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
                    if "k" in search_kwargs:
                        del search_kwargs["k"]

                    # Use parallel search for each query variation
                    results = await self.store.parallel_search(
                        query=query_variation,
                        k=10,
                        score_threshold=min_confidence,
                        filter_conditions=search_kwargs.get("filter_conditions"),
                        prioritized_urls=prioritized_urls,
                    )

                    if results:
                        docs.extend([doc for doc, _ in results])
                except Exception as e:
                    logger.warning(
                        f"Error in parallel search for variation {query_variation}: {str(e)}"
                    )
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
            self.metrics["retrieval_time"] = (
                self.metrics["retrieval_time"] * 0.9 + retrieval_time * 0.1
            )

            # Log the performance improvement
            logger.info(f"Parallel search completed in {retrieval_time:.2f} seconds")

            if not unique_docs:
                logger.warning(
                    "No relevant documents found with current threshold. Consider lowering min_confidence."
                )
                return []

            return unique_docs
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            raise RetrievalError(f"Document retrieval failed: {str(e)}")

    @retry(
        retry=retry_if_exception_type(ResponseGenerationError),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=5),
    )
    async def _generate_response(
        self, query: str, documents: List[Document], **kwargs: Any
    ) -> Dict[str, Any]:
        """Generate final response with enhanced context and details.

        Args:
            query: User query
            documents: Retrieved documents
            **kwargs: Additional parameters

        Returns:
            Dictionary with response and additional information
        """
        start_time = time.time()
        try:
            # Prioritize and reorder documents by relevance score and source quality
            documents = self._prioritize_documents(documents)

            # Extract memory context
            memory_context = kwargs.get("memory_context", "")

            # Organize documents by topic/source for better context grouping
            organized_docs = self._organize_documents(documents)

            # Prepare citation information
            citations = self._prepare_citations(documents)

            # Generate detailed response
            response = await self.response_generator.generate_response(
                query,
                documents,
                context=memory_context,
                organized_docs=organized_docs,
                citations=citations,
                detailed=True,  # Signal to response generator that we want detailed output
                **kwargs,
            )

            generation_time = time.time() - start_time

            return {
                "response": response,
                "response_time": generation_time,
                "document_count": len(documents),
                "citations": citations,
            }
        except Exception as e:
            logger.error(f"Error in response generation: {str(e)}")
            raise ResponseGenerationError(f"Failed to generate response: {str(e)}")

    def _prioritize_documents(self, documents: List[Document]) -> List[Document]:
        """Prioritize documents based on relevance and source quality."""
        # Sort by score first if available
        docs_with_scores = []
        for doc in documents:
            score = doc.metadata.get("score", 0.0) if hasattr(doc, "metadata") else 0.0
            docs_with_scores.append((doc, score))

        # Sort by score in descending order
        sorted_docs = [
            doc for doc, _ in sorted(docs_with_scores, key=lambda x: x[1], reverse=True)
        ]
        return sorted_docs

    def _organize_documents(
        self, documents: List[Document]
    ) -> Dict[str, List[Document]]:
        """Organize documents by source/category for better context."""
        organized = {}

        for doc in documents:
            if not hasattr(doc, "metadata"):
                continue

            source = doc.metadata.get("source", "unknown")
            if source not in organized:
                organized[source] = []

            organized[source].append(doc)

        return organized

    def _prepare_citations(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Prepare citation information for sources."""
        citations = []

        for i, doc in enumerate(documents):
            if not hasattr(doc, "metadata"):
                continue

            metadata = doc.metadata
            citation = {
                "id": i + 1,
                "source": metadata.get("source", "Unknown"),
                "title": metadata.get("title", "Untitled"),
                "url": metadata.get("url", ""),
                "date": metadata.get("date", ""),
            }
            citations.append(citation)

        return citations

    async def query(
        self,
        query: str,
        memory_context: str = "",
        max_retries: int = 0,
        min_confidence: float = 0.7,
        detailed: bool = False,
        with_citations: bool = True,
        platform: str = "",  # Platform parameter
        **kwargs,
    ) -> Tuple[str, List[Document]]:
        """Process a query and generate a response with Lithuanian support.

        Args:
            query: User query
            memory_context: Combined conversation history and memory context
            max_retries: Maximum number of retries for failed retrievals
            min_confidence: Minimum confidence threshold for document relevance
            detailed: Whether to generate a detailed response
            with_citations: Whether to include citations in the response
            platform: The platform where the query is coming from (e.g., "telegram")
            **kwargs: Additional parameters

        Returns:
            Tuple of (response_text, retrieved_documents)
        """
        self.query_count += 1
        start_time = datetime.now()

        try:
            # Process query with context
            query_result = await self.query_processor.process_query(
                query=query,
                context=memory_context,  # Pass full context for better query understanding
            )

            if not query_result["success"]:
                self.logger.error(
                    f"Query processing failed: {query_result.get('error', 'Unknown error')}"
                )
                error_response = "[AI] I apologize, but I encountered an error processing your query. Could you please rephrase or try again? [AI]"

                # Remove tags for Telegram
                if platform.lower() == "telegram":
                    import re

                    error_response = re.sub(r"\[RAG\]\s*", "", error_response)
                    error_response = re.sub(r"\[AI\]\s*", "", error_response)
                    error_response = re.sub(r"\s*\[RAG\]", "", error_response)
                    error_response = re.sub(r"\s*\[AI\]", "", error_response)
                    error_response = error_response.replace("[RAG]", "")
                    error_response = error_response.replace("[AI]", "")

                return error_response, []

            # Set platform attribute on response generator for proper tag handling
            self.response_generator.platform = platform

            # Get response from pre-processed documents
            response_text = await self.response_generator.generate_response(
                query=query_result["enhanced_query"],
                documents=await self._retrieve_documents(
                    query_result["variations"], min_confidence=min_confidence
                ),
                context=memory_context,
                organized_docs=None,
                citations=None,
                detailed=detailed,
                platform=platform,  # Pass platform to response generator
                **kwargs,
            )

            # Update metrics
            end_time = datetime.now()
            self._update_metrics(start_time, end_time, query=query, success=True)

            return response_text, []
        except Exception as e:
            self.logger.error(f"Error in RAG query: {e}", exc_info=True)
            error_response = "[AI] I apologize, but I encountered an error processing your query. Could you please rephrase or try again? [AI]"

            # Remove tags for Telegram
            if platform.lower() == "telegram":
                import re

                error_response = re.sub(r"\[RAG\]\s*", "", error_response)
                error_response = re.sub(r"\[AI\]\s*", "", error_response)
                error_response = re.sub(r"\s*\[RAG\]", "", error_response)
                error_response = re.sub(r"\s*\[AI\]", "", error_response)
                error_response = error_response.replace("[RAG]", "")
                error_response = error_response.replace("[AI]", "")

            return error_response, []

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return {
            **self.metrics,
            "query_processing_time": 0.0,
            "retrieval_time": 0.0,
            "response_generation_time": 0.0,
            "total_processing_time": 0.0,
            "error_details": {},
        }

    def _update_metrics(
        self, start_time: datetime, end_time: datetime, query: str, success: bool
    ) -> None:
        """Update metrics with new query information."""
        self.metrics["total_queries"] += 1
        if success:
            self.metrics["successful_queries"] += 1
        else:
            self.metrics["failed_queries"] += 1

        # Update query processing time
        self.metrics["query_processing_time"] = (
            self.metrics["query_processing_time"] * 0.9
            + (end_time - start_time).total_seconds() * 0.1
        )

        # Update retrieval time
        self.metrics["retrieval_time"] = (
            self.metrics["retrieval_time"] * 0.9
            + (end_time - start_time).total_seconds() * 0.1
        )

        # Update response generation time
        self.metrics["response_generation_time"] = (
            self.metrics["response_generation_time"] * 0.9
            + (end_time - start_time).total_seconds() * 0.1
        )

        # Update total processing time
        self.metrics["total_processing_time"] = (
            self.metrics["total_processing_time"] * 0.9
            + (end_time - start_time).total_seconds() * 0.1
        )

        # Update timestamp
        self.metrics["last_updated"] = datetime.now().isoformat()

    def _save_metrics(self) -> None:
        """Save metrics to file."""
        try:
            with open("rag_metrics.json", "w") as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metrics: {str(e)}")

    def _create_no_docs_response(
        self, query_info: Dict[str, Any]
    ) -> Tuple[str, List[Document]]:
        """Create Lithuanian response for no documents case."""
        response_text = f"[AI] Atsiprašau, bet nepavyko rasti jokių dokumentų, susijusių su jūsų klausimu. (Bandyta ieškoti Qdrant duomenų bazėje, kolekcija: {self.collection_name}) [AI]"
        return (response_text, [])

    def _create_no_results_response(
        self, query_info: Dict[str, Any]
    ) -> Tuple[str, List[Document]]:
        """Create Lithuanian response for no search results case."""
        response_text = f"[AI] Atsiprašau, bet nepavyko rasti pakankamai aktualios informacijos tiksliai atsakyti į jūsų klausimą. (Bandyta ieškoti Qdrant duomenų bazėje, kolekcija: {self.collection_name}) [AI]"
        return (response_text, [])

    def _create_no_relevant_docs_response(
        self, query_info: Dict[str, Any]
    ) -> Tuple[str, List[Document]]:
        """Create Lithuanian response for no relevant documents case."""
        response_text = f"[AI] Atsiprašau, bet turima informacija nėra pakankamai aktuali pateikti tikslų atsakymą. (Bandyta ieškoti Qdrant duomenų bazėje, kolekcija: {self.collection_name}) [AI]"
        return (response_text, [])

    def _create_error_response(self, error_msg: str) -> Tuple[str, List[Document]]:
        """Create error response."""
        return (
            f"[AI] Atsiprašau, įvyko klaida: {error_msg}. Prašome bandyti vėliau. (Bandyta ieškoti Qdrant duomenų bazėje, kolekcija: {self.collection_name}) [AI]",
            [],
        )

    async def process_query(self, query: str) -> List[str]:
        """Process a query and get variations.

        Args:
            query: The original user query

        Returns:
            List of query variations
        """
        result = await self.query_processor.process_query(query)
        return result["variations"]
