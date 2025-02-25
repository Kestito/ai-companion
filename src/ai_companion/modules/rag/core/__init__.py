"""Core RAG components initialization."""

from typing import Optional, Type
from langchain_openai import AzureOpenAIEmbeddings
from .rag_chain import LithuanianRAGChain
from .enhanced_retrieval import EnhancedRetrieval
from .query_preprocessor import LithuanianQueryPreprocessor
from .response_generation import LithuanianResponseGenerator
from .vector_store import VectorStoreRetriever
from .monitoring import RAGMonitor
import logging

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

__all__ = [
    'LithuanianRAGChain',
    'EnhancedRetrieval',
    'LithuanianQueryPreprocessor',
    'LithuanianResponseGenerator',
    'VectorStoreRetriever',
    'RAGMonitor',
    'initialize_rag'
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