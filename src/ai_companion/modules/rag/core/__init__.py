"""Core RAG components initialization."""

from typing import Optional, Type, Dict, List, Tuple, Any
from langchain_openai import AzureOpenAIEmbeddings
from .rag_chain import LithuanianRAGChain, get_rag_chain
from .enhanced_retrieval import EnhancedRetrieval
from .query_preprocessor import LithuanianQueryPreprocessor
from .response_generation import LithuanianResponseGenerator
from .vector_store import VectorStoreRetriever
from .monitoring import RAGMonitor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_rag(
    collection_name: str = "Information",
    model_deployment: Optional[str] = None,
    model_name: Optional[str] = None,
    embedding_deployment: Optional[str] = None,
    embedding_model: Optional[str] = None,
    temperature: float = 0.0
) -> LithuanianRAGChain:
    """Initialize RAG chain with specified configuration.
    
    Args:
        collection_name: Name of the vector store collection
        model_deployment: Azure OpenAI model deployment name
        model_name: Model name
        embedding_deployment: Azure OpenAI embedding deployment name
        embedding_model: Embedding model name
        temperature: Temperature for generation
        
    Returns:
        Configured LithuanianRAGChain instance
    """
    try:
        chain = LithuanianRAGChain(
            collection_name=collection_name,
            model_deployment=model_deployment,
            model_name=model_name,
            embedding_deployment=embedding_deployment,
            embedding_model=embedding_model,
            temperature=temperature
        )
        return chain
    except Exception as e:
        logger.error(f"Error initializing RAG chain: {str(e)}")
        raise

async def query_with_url_priority(
    query: str,
    priority_url: str,
    min_confidence: float = 0.7,
    **kwargs: Any
) -> Tuple[str, List[Any]]:
    """Query the RAG system with a prioritized URL.
    
    This function makes it easy to boost specific URLs in RAG results.
    
    Args:
        query: The user query
        priority_url: The URL to prioritize in results
        min_confidence: Minimum confidence score threshold
        **kwargs: Additional parameters to pass to the RAG query
        
    Returns:
        Tuple of (response text, retrieved documents)
    """
    try:
        # Get the RAG chain
        rag_chain = get_rag_chain()
        
        # Execute query with prioritized URL
        response, docs = await rag_chain.query(
            query=query,
            min_confidence=min_confidence,
            prioritized_urls=[priority_url],
            **kwargs
        )
        
        # Log prioritized documents
        prioritized_count = 0
        for doc in docs:
            if doc.metadata.get("url") and priority_url.lower() in doc.metadata.get("url", "").lower():
                prioritized_count += 1
                
        logger.info(f"Query with prioritized URL returned {len(docs)} documents, {prioritized_count} from priority URL")
        
        return response, docs
        
    except Exception as e:
        logger.error(f"Error in query_with_url_priority: {str(e)}")
        raise

__all__ = [
    "LithuanianQueryPreprocessor",
    "LithuanianRAGChain",
    "get_rag_chain",
    "VectorStoreRetriever",
    "LithuanianResponseGenerator",
    "RAGMonitor",
    "EnhancedRetrieval", 
    "query_with_url_priority"
]

# Singleton instance
_rag_instance = None

def get_rag(
    collection_name: str = "Information",
    model_deployment: str = None,
    model_name: str = None
) -> LithuanianRAGChain:
    """Get or create singleton RAG instance."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = LithuanianRAGChain(
            collection_name=collection_name,
            model_deployment=model_deployment,
            model_name=model_name
        )
    return _rag_instance 