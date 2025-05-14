"""
Test script to check Qdrant API key.
"""
import logging
from ai_companion.settings import settings
from qdrant_client import QdrantClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_qdrant_connection():
    """Test connection to Qdrant."""
    logger.info("Testing Qdrant connection")
    
    # Try different URL formats
    url_formats = [
        settings.QDRANT_URL,  # Original URL
        settings.QDRANT_URL.replace("https://", "http://"),  # Try HTTP instead of HTTPS
        settings.QDRANT_URL + ":6333",  # Add explicit port
        settings.QDRANT_URL + ":443",  # Try HTTPS port
    ]
    
    # Use the new API key directly
    new_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.cdTvd4mc74giwx-ypkE8t4muYvpQqLqkc5P6IXuJAOw"
    
    for url in url_formats:
        logger.info(f"\nTrying Qdrant URL: {url}")
        logger.info(f"Using new API key")
        
        try:
            # Initialize Qdrant client
            client = QdrantClient(
                url=url,
                api_key=new_api_key,
                timeout=60,
                check_compatibility=False,
            )
            
            # Get list of collections
            logger.info("Attempting to get collections...")
            collections = client.get_collections()
            logger.info(f"Collections: {collections}")
            
            logger.info(f"SUCCESS! Qdrant connection worked with URL: {url}")
            return  # Stop once we find a working URL
            
        except Exception as e:
            logger.error(f"Error connecting to Qdrant with {url}: {e}")
    
    logger.error("All connection attempts failed.")

if __name__ == "__main__":
    test_qdrant_connection() 