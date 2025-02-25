"""Vector store retrieval module."""

from typing import List, Optional, Dict, Any, Tuple
from langchain_openai import AzureOpenAIEmbeddings
from langchain.schema import Document
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, Condition
import os
import logging

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
            
            logger.info(f"VectorStoreRetriever initialized with collection: {collection_name}")
            
        except Exception as e:
            logger.error(f"Error initializing VectorStoreRetriever: {str(e)}")
            raise

    async def similarity_search(
        self,
        query: str,
        k: int = 4,
        score_threshold: float = 0.7,
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
