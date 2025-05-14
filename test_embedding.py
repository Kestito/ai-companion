"""
Test script to debug embedding functionality.
"""
import asyncio
import logging
from ai_companion.settings import settings
from langchain_openai import AzureOpenAIEmbeddings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_embedding():
    """Test embedding functionality."""
    logger.info("Starting embedding test")
    logger.info(f"API Version: {settings.AZURE_EMBEDDING_API_VERSION}")
    logger.info(f"Deployment: {settings.AZURE_EMBEDDING_DEPLOYMENT}")
    logger.info(f"Model: {settings.FALLBACK_EMBEDDING_MODEL}")
    logger.info(f"Endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
    
    try:
        # Initialize embeddings with both Azure deployment name and model name
        embeddings = AzureOpenAIEmbeddings(
            azure_deployment=settings.AZURE_EMBEDDING_DEPLOYMENT,
            model=settings.FALLBACK_EMBEDDING_MODEL,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_EMBEDDING_API_VERSION,
        )
        
        logger.info(f"Embeddings object: {embeddings}")
        logger.info(f"Embeddings model: {embeddings.model}")
        logger.info(f"Embeddings deployment parameter: {settings.AZURE_EMBEDDING_DEPLOYMENT}")
        
        # Test with a simple text
        text = "This is a test for embedding functionality"
        logger.info(f"Embedding text: {text}")
        
        # Try the async variant
        logger.info("Using aembed_query")
        result = await embeddings.aembed_query(text)
        logger.info(f"Result type: {type(result)}")
        logger.info(f"Result attributes: {dir(result)}")
        
        # Check if result has embeddings attribute
        if hasattr(result, 'embeddings'):
            logger.info(f"Embeddings attribute exists with length: {len(result.embeddings)}")
            if result.embeddings:
                logger.info(f"First embedding dimensions: {len(result.embeddings[0])}")
        else:
            logger.info(f"Result has no 'embeddings' attribute. Available attributes: {dir(result)}")
            # Check if result itself is the embedding array
            if isinstance(result, list):
                logger.info(f"Result is a list with length: {len(result)}")

        # Also try the synchronous variant
        logger.info("Using embed_query")
        sync_result = embeddings.embed_query(text)
        logger.info(f"Sync result type: {type(sync_result)}")
        logger.info(f"Sync result length: {len(sync_result)}")
        
        logger.info("Embedding test completed successfully")
        
    except Exception as e:
        logger.error(f"Error in embedding test: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_embedding()) 