"""Vector store retrieval module."""

from typing import List, Optional, Dict, Any, Tuple
from langchain_openai import AzureOpenAIEmbeddings
from langchain_core.documents import Document
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse
from supabase import create_client
import logging
import asyncio
import re
import time
from openai import RateLimitError, BadRequestError  # Updated import for OpenAI v1.x
from ai_companion.settings import settings


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStoreRetriever:
    """Manages vector store retrieval operations."""

    def __init__(
        self,
        collection_name: str = "Information",
        embedding_deployment: Optional[str] = None,
        embedding_model: Optional[str] = None,
    ):
        """Initialize vector store retriever."""
        self.logger = logging.getLogger(__name__)

        try:
            self.collection_name = collection_name

            # Initialize embeddings
            self.embeddings = AzureOpenAIEmbeddings(
                azure_deployment=embedding_deployment
                or settings.AZURE_EMBEDDING_DEPLOYMENT,
                model=embedding_model
                or settings.FALLBACK_EMBEDDING_MODEL,  # Use FALLBACK_EMBEDDING_MODEL from settings
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_EMBEDDING_API_VERSION,  # Use API version from settings
            )

            # Initialize Qdrant client
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                # Use the new working API key directly for now
                api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.cdTvd4mc74giwx-ypkE8t4muYvpQqLqkc5P6IXuJAOw",
                timeout=60,
                check_compatibility=False,
            )

            # Initialize Supabase client
            self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

            logger.info(
                f"VectorStoreRetriever initialized with collection: {collection_name}"
            )

            self._initialized = True
        except Exception as e:
            logger.error(
                f"Failed to initialize VectorStoreRetriever: {e}", exc_info=True
            )
            self._initialized = False
            self.embeddings = None
            self.client = None
            self.supabase = None

    async def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Azure OpenAI."""
        if not text or len(text.strip()) == 0:
            self.logger.warning("Attempted to get embedding for empty text")
            return []

        if not self.embeddings or not self._initialized:
            self.logger.error("Azure OpenAI client not properly initialized")
            self.logger.error(f"Embeddings object: {self.embeddings}")
            self.logger.error(f"Initialization status: {self._initialized}")
            return []

        try:
            # Ensure text is not too long for the embedding model
            max_tokens = 8191  # For text-embedding-ada-002
            if len(text) > max_tokens * 4:  # Approximate character to token ratio
                self.logger.warning(
                    f"Text too long for embedding ({len(text)} chars), truncating"
                )
                text = text[: max_tokens * 4]

            # Wait for rate limiting if needed
            delay = 0
            for _ in range(3):  # Maximum 3 retries
                try:
                    if delay > 0:
                        self.logger.info(f"Rate limited, waiting {delay}s before retry")
                        time.sleep(delay)

                    # Get embedding from Azure OpenAI - properly await the coroutine
                    embedding_result = await self.embeddings.aembed_query(text)

                    # Check if embedding_result is already a list (direct embedding vector)
                    if isinstance(embedding_result, list):
                        if embedding_result:
                            self.logger.info(
                                f"Got embedding with {len(embedding_result)} dimensions"
                            )
                            return embedding_result
                        else:
                            self.logger.error(
                                "Azure OpenAI returned empty embedding list"
                            )
                            return []

                    # If not a list, could be older format with embeddings attribute
                    elif (
                        hasattr(embedding_result, "embeddings")
                        and embedding_result.embeddings
                        and len(embedding_result.embeddings) > 0
                    ):
                        self.logger.info(
                            f"Using embeddings attribute with {len(embedding_result.embeddings[0])} dimensions"
                        )
                        return embedding_result.embeddings[0]

                    # Unknown format
                    else:
                        self.logger.error(
                            f"Unknown embedding result format: {type(embedding_result)}"
                        )
                        return []

                except RateLimitError as rle:
                    # Extract retry-after if available
                    retry_after = getattr(rle, "retry_after", None) or 1
                    delay = min(retry_after * 1.5, 10)  # Avoid excessive waits
                    self.logger.warning(
                        f"Rate limit hit: {rle}. Will retry in {delay}s"
                    )
                    continue

                except BadRequestError as ire:
                    # Handle token limits or other invalid requests
                    if "token" in str(ire).lower():
                        # Further truncate and try again
                        text = text[: len(text) // 2]
                        self.logger.warning(
                            f"Token limit exceeded, truncating to {len(text)} chars"
                        )
                        continue
                    else:
                        # Other invalid request issues
                        self.logger.error(f"Invalid request for embedding: {ire}")
                        return []

                except Exception as e:
                    # Other OpenAI errors - increase backoff and retry
                    delay = (delay or 0.5) * 2
                    self.logger.warning(f"OpenAI error: {e}. Retrying in {delay}s")
                    continue

            # All retries failed
            self.logger.error("Failed to get embedding after multiple retries")
            return []

        except Exception as e:
            self.logger.error(f"Unexpected error in _get_embedding: {e}", exc_info=True)
            return []

    def _clean_query(self, query: str) -> str:
        """Remove special characters from query to prevent SQL injection."""
        return re.sub(r"[^\w\s]", "", query)

    async def similarity_search(
        self,
        query: str,
        k: int = 8,
        score_threshold: float = 0.65,
        filter_conditions: Optional[Dict] = None,
        max_retries: int = 2,
        retry_delay: float = 1.0,
    ) -> List[Tuple[Document, float]]:
        """Search for similar documents with advanced filtering."""
        retry_count = 0

        while retry_count <= max_retries:
            try:
                if not query or not query.strip():
                    logger.warning("Empty query provided to similarity_search")
                    return []

                if not self.client or not self._initialized:
                    self.logger.error("Qdrant client not properly initialized")
                    return []

                # Get query embedding
                query_embedding = await self._get_embedding(query)
                if not query_embedding:
                    self.logger.error("Failed to generate embedding for query")
                    return []

                # Prepare filter
                search_filter = None
                if filter_conditions:
                    try:
                        must_conditions = []
                        for key, value in filter_conditions.items():
                            if isinstance(value, dict):
                                # Handle nested conditions
                                for nested_key, nested_value in value.items():
                                    must_conditions.append(
                                        {
                                            "key": f"{key}.{nested_key}",
                                            "match": {"value": nested_value},
                                        }
                                    )
                            else:
                                must_conditions.append(
                                    {"key": key, "match": {"value": value}}
                                )
                        search_filter = {"must": must_conditions}
                    except Exception as filter_error:
                        self.logger.error(
                            f"Error creating search filter: {filter_error}",
                            exc_info=True,
                        )
                        # Continue with search but without filter
                        search_filter = None

                # Execute search with timeout safeguards
                start_time = time.time()
                search_results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    limit=k,
                    score_threshold=score_threshold,
                    query_filter=search_filter,
                )
                search_time = time.time() - start_time

                # Log performance metrics
                self.logger.info(f"Qdrant search completed in {search_time:.2f}s")

                if not search_results:
                    logger.warning(
                        f"No search results found for query (length: {len(query)})"
                    )
                    return []

                # Convert results to documents
                results = []
                for result in search_results:
                    if not result.payload:
                        self.logger.warning(
                            f"Missing payload in search result: {result.id}"
                        )
                        continue

                    # Extract document content and metadata
                    content = result.payload.get("content", "")
                    if not content:
                        self.logger.warning(f"Empty content in document: {result.id}")
                        continue

                    metadata = {
                        "score": result.score,
                        "id": result.id,
                        **{k: v for k, v in result.payload.items() if k != "content"},
                    }

                    doc = Document(page_content=content, metadata=metadata)
                    results.append((doc, result.score))

                logger.info(
                    f"Found {len(results)} relevant documents from {len(search_results)} total results"
                )
                return sorted(results, key=lambda x: x[1], reverse=True)

            except UnexpectedResponse as e:
                retry_count += 1
                error_msg = f"Qdrant returned unexpected response (attempt {retry_count}/{max_retries+1}): {e}"

                if retry_count <= max_retries:
                    logger.warning(
                        f"{error_msg} - Retrying in {retry_delay} seconds..."
                    )
                    await asyncio.sleep(retry_delay)
                    # Increase delay for next retry
                    retry_delay *= 2
                else:
                    logger.error(error_msg)
                    return []

            except Exception as e:
                self.logger.error(f"Error in similarity search: {e}", exc_info=True)
                # Log query length but not content for privacy reasons
                self.logger.info(
                    f"Failed query length: {len(query)}, Filter conditions: {filter_conditions}"
                )
                return []

        return []  # Fallback if all retries fail

    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            collection = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": collection.vectors_count,
                "status": collection.status,
                "vector_size": collection.config.params.vectors.size,
                "distance": collection.config.params.vectors.distance.name
                if collection.config.params.vectors.distance
                else None,
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}")
            return {}

    async def keyword_search(
        self, query: str, k: int = 10, score_threshold: float = 0.7
    ) -> List[Tuple[Document, float]]:
        """Search for documents using keyword search in Supabase.

        Args:
            query: The search query
            k: Maximum number of results to return
            score_threshold: Minimum score threshold for results

        Returns:
            List of documents with their scores
        """
        try:
            if not self.supabase or not self._initialized:
                self.logger.error("Supabase client not properly initialized")
                return []

            # Clean query to prevent injection
            cleaned_query = self._clean_query(query)
            if not cleaned_query:
                self.logger.warning("Query was empty after cleaning")
                return []

            # Execute search using the indexed search_documents function
            try:
                response = self.supabase.rpc(
                    "search_documents", {"query_text": cleaned_query, "limit_val": k}
                ).execute()

                # Check response data instead of looking for error attribute
                if not hasattr(response, "data") or response.data is None:
                    self.logger.error("Supabase search returned no data structure")
                    return []

                if not response.data:
                    self.logger.warning("No keyword search results found")
                    return []
            except Exception as supabase_error:
                # Log the error but continue with vector search only
                self.logger.error(f"Error in keyword search: {str(supabase_error)}")
                return []

            # Convert results to documents
            results = []
            for item in response.data:
                # Calculate score - normalize between 0 and 1
                # Higher rank means better match in full text search
                score = 1 - (item["rank"] / k) if k > 0 else 0

                # Skip if below threshold
                if score < score_threshold:
                    continue

                # Create document with metadata indicating it came from keyword search
                doc = Document(
                    page_content=item["chunk_content"],
                    metadata={
                        "score": score,
                        "id": item["id"],
                        "document_id": item["document_id"],
                        "title": item["title"],
                        "url": item.get("url", ""),
                        "source_type": item.get("source_type", ""),
                        "search_type": "keyword",  # Mark the source as keyword search
                    },
                )
                results.append((doc, score))

            logger.info(f"Found {len(results)} documents via keyword search")
            return sorted(results, key=lambda x: x[1], reverse=True)

        except Exception as e:
            logger.error(f"Error in keyword search: {str(e)}")
            # Return empty list to allow vector search to continue
            return []

    async def parallel_search(
        self,
        query: str,
        k: int = 15,
        score_threshold: float = 0.65,
        filter_conditions: Optional[Dict] = None,
        prioritized_urls: Optional[List[str]] = None,
    ) -> List[Tuple[Document, float]]:
        """Search for documents using parallel vector and keyword search.

        Combines results from both search methods for comprehensive retrieval.

        Args:
            query: The search query
            k: Maximum number of results to return
            score_threshold: Minimum score threshold for results
            filter_conditions: Optional filter conditions for vector search
            prioritized_urls: Optional list of URLs to prioritize in results

        Returns:
            List of documents with their scores, sorted by relevance
        """
        start_time = time.time()
        try:
            # Analyze query characteristics to determine search strategy
            is_short_query = len(query.split()) <= 3
            has_special_chars = bool(re.search(r"[^\w\s]", query))
            is_likely_keyword = is_short_query or has_special_chars

            # Optimize search strategy based on query analysis
            # For very short queries or those with special characters, prioritize keyword search
            if is_likely_keyword:
                logger.debug(f"Query '{query}' identified as likely keyword query")
                k_vector = k // 2  # Allocate half the slots to vector search
                k_keyword = k  # Allocate full slots to keyword search (will be deduplicated later)
            else:
                logger.debug(f"Query '{query}' identified as likely semantic query")
                k_vector = k  # Allocate full slots to vector search
                k_keyword = k // 2  # Allocate half the slots to keyword search

            # Run both searches in parallel with optimized parameters
            vector_task = asyncio.create_task(
                self.similarity_search(
                    query=query,
                    k=k_vector,
                    score_threshold=score_threshold,
                    filter_conditions=filter_conditions,
                )
            )

            keyword_task = asyncio.create_task(
                self.keyword_search(
                    query=query,
                    k=k_keyword,
                    score_threshold=score_threshold
                    * 0.9,  # Slightly lower threshold for keyword search
                )
            )

            # Gather results with exception handling
            results = await asyncio.gather(
                vector_task, keyword_task, return_exceptions=True
            )

            vector_results = []
            keyword_results = []

            # Handle results from tasks, handling any exceptions
            if isinstance(results[0], Exception):
                logger.error(f"Vector search failed: {str(results[0])}")
            else:
                vector_results = results[0]

            if isinstance(results[1], Exception):
                logger.error(f"Keyword search failed: {str(results[1])}")
            else:
                keyword_results = results[1]

            # Process and combine results from both searches
            all_results = []
            content_hash_set = set()  # For deduplication
            content_to_score = {}

            # Process vector results first (typically higher quality)
            for doc, score in vector_results:
                content_hash = hash(doc.page_content)
                if content_hash not in content_hash_set:
                    # Add new content
                    content_hash_set.add(content_hash)
                    content_to_score[content_hash] = score
                    # Tag as vector source
                    doc.metadata["search_type"] = "vector"
                    all_results.append((doc, score))
                elif score > content_to_score[content_hash]:
                    # Replace with higher score version
                    content_to_score[content_hash] = score
                    # Find and update the existing entry
                    for i, (existing_doc, _) in enumerate(all_results):
                        if hash(existing_doc.page_content) == content_hash:
                            all_results[i] = (doc, score)
                            break

            # Process keyword results with metadata indicating source
            for doc, score in keyword_results:
                content_hash = hash(doc.page_content)
                if content_hash not in content_hash_set:
                    # Add new content
                    content_hash_set.add(content_hash)
                    content_to_score[content_hash] = score
                    # Tag as keyword source
                    doc.metadata["search_type"] = "keyword"
                    all_results.append((doc, score))
                elif score > content_to_score[content_hash]:
                    # Replace with higher score version
                    content_to_score[content_hash] = score
                    # Find and update the existing entry
                    for i, (existing_doc, _) in enumerate(all_results):
                        if hash(existing_doc.page_content) == content_hash:
                            all_results[i] = (doc, score)
                            break

            # Apply final ranking with weighted scores
            # Boost scores based on document quality indicators
            for i, (doc, score) in enumerate(all_results):
                # Apply source-based weighting
                source_type = doc.metadata.get("search_type", "vector")
                source_boost = 1.0 if source_type == "vector" else 0.9

                # Apply content length weighting (prefer more substantial content)
                content_length = len(doc.page_content.strip())
                length_boost = min(1.0, content_length / 500)  # Max boost at 500 chars

                # Apply title presence weighting
                title_boost = 1.05 if doc.metadata.get("title", "") else 1.0

                # Apply prioritized URL boosting
                url_boost = 1.0
                if prioritized_urls and doc.metadata.get("url"):
                    doc_url = doc.metadata.get("url", "")
                    for priority_url in prioritized_urls:
                        if priority_url.lower() in doc_url.lower():
                            # Apply significant boost (50%) to the prioritized URL
                            url_boost = 1.5
                            logger.info(
                                f"Boosting document from prioritized URL: {doc_url}"
                            )
                            break

                # Calculate final weighted score
                weighted_score = (
                    score * source_boost * length_boost * title_boost * url_boost
                )
                all_results[i] = (doc, weighted_score)

            # Sort by score and limit to k results
            sorted_results = sorted(all_results, key=lambda x: x[1], reverse=True)[:k]

            # Count results by source for logging
            vector_count = sum(
                1
                for doc, _ in sorted_results
                if doc.metadata.get("search_type") == "vector"
            )
            keyword_count = sum(
                1
                for doc, _ in sorted_results
                if doc.metadata.get("search_type") == "keyword"
            )

            elapsed = time.time() - start_time
            logger.info(
                f"Parallel search found {len(sorted_results)} documents (Vector: {vector_count}, Keyword: {keyword_count}) in {elapsed:.2f} seconds"
            )

            return sorted_results

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error in parallel search: {str(e)}")

            # Fallback to vector search only if parallel search fails
            logger.info("Falling back to vector search only")
            try:
                vector_results = await self.similarity_search(
                    query=query,
                    k=k,
                    score_threshold=score_threshold,
                    filter_conditions=filter_conditions,
                )

                # Add metadata to indicate these are from vector search
                for doc, score in vector_results:
                    doc.metadata["search_type"] = "vector"

                fallback_elapsed = time.time() - start_time
                logger.info(
                    f"Fallback vector search found {len(vector_results)} documents in {fallback_elapsed:.2f} seconds"
                )
                return vector_results

            except Exception as fallback_error:
                logger.error(
                    f"Fallback vector search also failed: {str(fallback_error)}"
                )
                return []

    async def search_by_vector(
        self,
        embedding: list,
        collection: str,
        limit: int = 5,
        filter: Optional[Dict] = None,
    ):
        """
        Search for similar documents by vector.

        Args:
            embedding (list): The embedding vector to search for.
            collection (str): The name of the collection to search in.
            limit (int, optional): The maximum number of results to return. Defaults to 5.
            filter (Optional[Dict], optional): A filter to apply to the search. Defaults to None.

        Returns:
            list: A list of dictionaries with keys 'payload' and 'score'.
        """
        try:
            # Validate inputs
            if not embedding or not isinstance(embedding, list):
                self.logger.error(
                    f"Invalid embedding provided for search: {type(embedding)}"
                )
                return []

            if not collection or not isinstance(collection, str):
                self.logger.error(f"Invalid collection name provided: {collection}")
                return []

            if not self.client:
                self.logger.error("Qdrant client not initialized for search_by_vector")
                return []

            # Check if collection exists
            try:
                collections = self.client.get_collections()
                if collection not in [c.name for c in collections.collections]:
                    self.logger.warning(f"Collection '{collection}' does not exist")
                    return []
            except Exception as e:
                self.logger.error(f"Failed to verify collection existence: {e}")
                # Continue anyway as the search might still work

            # Prepare search filter if provided
            search_filter = None
            if filter:
                try:
                    must_conditions = []
                    for key, value in filter.items():
                        if isinstance(value, list):
                            should_conditions = []
                            for val in value:
                                should_conditions.append(
                                    models.FieldCondition(
                                        key=key, match=models.MatchValue(value=val)
                                    )
                                )
                            must_conditions.append(
                                models.Filter(should=should_conditions)
                            )
                        else:
                            must_conditions.append(
                                models.FieldCondition(
                                    key=key, match=models.MatchValue(value=value)
                                )
                            )
                    search_filter = models.Filter(must=must_conditions)
                except Exception as e:
                    self.logger.error(f"Error creating search filter: {e}")
                    # Continue with null filter rather than failing
                    search_filter = None

            # Implement retry logic for Qdrant search
            max_retries = 2
            retry_count = 0
            last_error = None

            while retry_count <= max_retries:
                try:
                    # Execute search with current parameters
                    self.logger.debug(
                        f"Executing vector search on collection '{collection}' with limit {limit}"
                    )
                    search_results = self.client.search(
                        collection_name=collection,
                        query_vector=embedding,
                        limit=limit,
                        query_filter=search_filter,
                        with_payload=True,
                    )

                    # Format results
                    results = []
                    for result in search_results:
                        results.append(
                            {"payload": result.payload, "score": result.score}
                        )

                    self.logger.info(f"Vector search found {len(results)} results")
                    return results

                except UnexpectedResponse as e:
                    last_error = e
                    retry_count += 1
                    self.logger.warning(
                        f"Qdrant search attempt {retry_count}/{max_retries} failed: {e}. Retrying..."
                    )
                    # Add a short delay before retrying
                    await asyncio.sleep(1.0)
                except Exception as e:
                    # For non-Qdrant specific exceptions, don't retry
                    self.logger.error(f"Error during vector search: {e}", exc_info=True)
                    # Fallback to similarity search if available
                    return self._fallback_similarity_search(embedding, limit)

            # If we've exhausted all retries
            if last_error:
                self.logger.error(f"All retries failed for vector search: {last_error}")
                # Try fallback mechanism
                return self._fallback_similarity_search(embedding, limit)

            return []

        except Exception as e:
            self.logger.error(
                f"Unexpected error in search_by_vector: {e}", exc_info=True
            )
            return []

    def _fallback_similarity_search(self, embedding: list, limit: int = 5):
        """
        Fallback method for when Qdrant search fails.
        Implements a basic in-memory similarity search if possible.

        Args:
            embedding (list): The embedding vector to search for
            limit (int): Maximum number of results to return

        Returns:
            list: A list of dictionaries with keys 'payload' and 'score', or empty list
        """
        try:
            self.logger.info("Attempting fallback similarity search")
            # If we have no cache or in-memory fallback mechanism, return empty results
            return []
        except Exception as e:
            self.logger.error(f"Fallback similarity search failed: {e}")
            return []

    async def search_memories(
        self, text: str, metadata_filter: Optional[Dict] = None, limit: int = 5
    ) -> List[Dict]:
        """
        Search memory collection for relevant memories.

        Args:
            text: The text to search for
            metadata_filter: Optional filter to apply to the search
            limit: Maximum number of results to return

        Returns:
            A list of memory items
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to search_memories")
            return []

        try:
            # Get the text embedding
            embedding = await self._get_embedding(text)
            if not embedding:
                self.logger.warning("Failed to generate embedding for memory search")
                return []

            # Search the memory collection
            search_results = self._fallback_similarity_search(embedding, limit)
            return search_results

        except Exception as e:
            logger.error(f"Error searching memories: {e}", exc_info=True)
            return []


def get_vector_store_instance(
    collection_name: str = "Information",
    embedding_deployment: Optional[str] = None,
    embedding_model: Optional[str] = None,
) -> VectorStoreRetriever:
    """Factory function to create and return a VectorStoreRetriever instance.

    Args:
        collection_name (str): Name of the collection to use
        embedding_deployment (Optional[str]): Azure deployment name for embeddings
        embedding_model (Optional[str]): Model name for embeddings

    Returns:
        VectorStoreRetriever: Configured instance of the vector store retriever
    """
    try:
        return VectorStoreRetriever(
            collection_name=collection_name,
            embedding_deployment=embedding_deployment,
            embedding_model=embedding_model,
        )
    except Exception as e:
        logger.error(f"Failed to create vector store instance: {str(e)}")
        raise
