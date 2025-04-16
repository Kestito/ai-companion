"""Vector store retrieval module."""

from typing import List, Optional, Dict, Any, Tuple
from langchain_openai import AzureOpenAIEmbeddings
from langchain.schema import Document
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, Condition
import os
import logging
import asyncio
from supabase import create_client, Client
import re
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStoreRetriever:
    """Manages vector store retrieval operations."""
    
    def __init__(
        self,
        collection_name: str = "Information",
        embedding_deployment: Optional[str] = None,
        embedding_model: Optional[str] = None
    ):
        """Initialize vector store retriever."""
        try:
            self.collection_name = collection_name
            
            # Initialize embeddings
            self.embeddings = AzureOpenAIEmbeddings(
                azure_deployment=embedding_deployment or os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
                model=embedding_model or os.getenv("EMBEDDING_MODEL"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version="2023-05-15"
            )
            
            # Initialize Qdrant client
            self.client = QdrantClient(
                url=os.getenv("QDRANT_URL"),
                api_key=os.getenv("QDRANT_API_KEY"),
                timeout=60
            )
            
            # Initialize Supabase client
            self.supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_KEY")
            )
            
            logger.info(f"VectorStoreRetriever initialized with collection: {collection_name}")
            
        except Exception as e:
            logger.error(f"Error initializing VectorStoreRetriever: {str(e)}")
            raise

    async def similarity_search(
        self,
        query: str,
        k: int = 8,
        score_threshold: float = 0.65,
        filter_conditions: Optional[Dict] = None
    ) -> List[Tuple[Document, float]]:
        """Search for similar documents with advanced filtering."""
        try:
            # Get query embedding
            query_embedding = await self.embeddings.aembed_query(query)
            
            # Prepare filter
            search_filter = None
            if filter_conditions:
                must_conditions = []
                for key, value in filter_conditions.items():
                    if isinstance(value, dict):
                        # Handle nested conditions
                        for nested_key, nested_value in value.items():
                            must_conditions.append(
                                {
                                    "key": f"{key}.{nested_key}",
                                    "match": {"value": nested_value}
                                }
                            )
                    else:
                        must_conditions.append(
                            {
                                "key": key,
                                "match": {"value": value}
                            }
                        )
                search_filter = {"must": must_conditions}
            
            # Execute search
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=k,
                score_threshold=score_threshold,
                query_filter=search_filter
            )
            
            if not search_results:
                logger.warning("No search results found")
                return []
            
            # Convert results to documents
            results = []
            for result in search_results:
                if not result.payload:
                    continue
                
                # Extract document content and metadata
                content = result.payload.get("content", "")
                metadata = {
                    "score": result.score,
                    "id": result.id,
                    **{k: v for k, v in result.payload.items() if k != "content"}
                }
                
                doc = Document(
                    page_content=content,
                    metadata=metadata
                )
                results.append((doc, result.score))
            
            logger.info(f"Found {len(results)} relevant documents")
            return sorted(results, key=lambda x: x[1], reverse=True)
            
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return []

    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            collection = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": collection.vectors_count,
                "status": collection.status,
                "vector_size": collection.config.params.vectors.size,
                "distance": collection.config.params.vectors.distance.name if collection.config.params.vectors.distance else None
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}")
            return {}

    async def keyword_search(
        self,
        query: str,
        k: int = 10,
        score_threshold: float = 0.7
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
            # Remove special characters and normalize for better search
            clean_query = re.sub(r'[^\w\s]', ' ', query).strip()
            if not clean_query:
                logger.warning("Empty search terms after cleaning query")
                return []
            
            # Execute search using the indexed search_documents function
            try:
                response = self.supabase.rpc(
                    'search_documents',
                    {
                        'query_text': clean_query,
                        'limit_val': k
                    }
                ).execute()
                
                # Check response data instead of looking for error attribute
                if not hasattr(response, 'data') or response.data is None:
                    logger.error("Supabase search returned no data structure")
                    return []
                    
                if not response.data:
                    logger.warning("No keyword search results found")
                    return []
            except Exception as supabase_error:
                # Log the error but continue with vector search only
                logger.error(f"Error in keyword search: {str(supabase_error)}")
                return []
            
            # Convert results to documents
            results = []
            for item in response.data:
                # Calculate score - normalize between 0 and 1
                # Higher rank means better match in full text search
                score = 1 - (item['rank'] / k) if k > 0 else 0
                
                # Skip if below threshold
                if score < score_threshold:
                    continue
                
                # Create document with metadata indicating it came from keyword search
                doc = Document(
                    page_content=item['chunk_content'],
                    metadata={
                        'score': score,
                        'id': item['id'],
                        'document_id': item['document_id'],
                        'title': item['title'],
                        'url': item.get('url', ''),
                        'source_type': item.get('source_type', ''),
                        'search_type': 'keyword'  # Mark the source as keyword search
                    }
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
        prioritized_urls: Optional[List[str]] = None
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
            has_special_chars = bool(re.search(r'[^\w\s]', query))
            is_likely_keyword = is_short_query or has_special_chars
            
            # Optimize search strategy based on query analysis
            # For very short queries or those with special characters, prioritize keyword search
            if is_likely_keyword:
                logger.debug(f"Query '{query}' identified as likely keyword query")
                k_vector = k // 2  # Allocate half the slots to vector search
                k_keyword = k      # Allocate full slots to keyword search (will be deduplicated later)
            else:
                logger.debug(f"Query '{query}' identified as likely semantic query")
                k_vector = k       # Allocate full slots to vector search
                k_keyword = k // 2 # Allocate half the slots to keyword search
            
            # Run both searches in parallel with optimized parameters
            vector_task = asyncio.create_task(self.similarity_search(
                query=query,
                k=k_vector,
                score_threshold=score_threshold,
                filter_conditions=filter_conditions
            ))
            
            keyword_task = asyncio.create_task(self.keyword_search(
                query=query,
                k=k_keyword,
                score_threshold=score_threshold * 0.9  # Slightly lower threshold for keyword search
            ))
            
            # Gather results with exception handling
            results = await asyncio.gather(vector_task, keyword_task, return_exceptions=True)
            
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
                            logger.info(f"Boosting document from prioritized URL: {doc_url}")
                            break
                
                # Calculate final weighted score
                weighted_score = score * source_boost * length_boost * title_boost * url_boost
                all_results[i] = (doc, weighted_score)
            
            # Sort by score and limit to k results
            sorted_results = sorted(all_results, key=lambda x: x[1], reverse=True)[:k]
            
            # Count results by source for logging
            vector_count = sum(1 for doc, _ in sorted_results if doc.metadata.get("search_type") == "vector")
            keyword_count = sum(1 for doc, _ in sorted_results if doc.metadata.get("search_type") == "keyword")
            
            elapsed = time.time() - start_time
            logger.info(f"Parallel search found {len(sorted_results)} documents (Vector: {vector_count}, Keyword: {keyword_count}) in {elapsed:.2f} seconds")
            
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
                    filter_conditions=filter_conditions
                )
                
                # Add metadata to indicate these are from vector search
                for doc, score in vector_results:
                    doc.metadata["search_type"] = "vector"
                
                fallback_elapsed = time.time() - start_time
                logger.info(f"Fallback vector search found {len(vector_results)} documents in {fallback_elapsed:.2f} seconds")
                return vector_results
                
            except Exception as fallback_error:
                logger.error(f"Fallback vector search also failed: {str(fallback_error)}")
                return []

def get_vector_store_instance(
    collection_name: str = "Information",
    embedding_deployment: Optional[str] = None,
    embedding_model: Optional[str] = None
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
            embedding_model=embedding_model
        )
    except Exception as e:
        logger.error(f"Failed to create vector store instance: {str(e)}")
        raise
