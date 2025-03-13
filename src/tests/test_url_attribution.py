"""
Test script for URL attribution in RAG responses.

This script tests whether the RAG system correctly includes top URLs 
from source documents in its responses.
"""

import asyncio
import logging
from langchain.schema import Document
from dotenv import load_dotenv

from ai_companion.modules.rag.core.response_generation import LithuanianResponseGenerator

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def test_url_attribution():
    """Test URL attribution in responses."""
    logger.info("Testing URL attribution in responses")
    
    # Create a test generator
    generator = LithuanianResponseGenerator()
    
    # Create test documents with URLs and scores
    test_documents = [
        Document(
            page_content="POLA kortelė yra pagalbos onkologiniams ligoniams asociacijos kortelė.",
            metadata={
                "title": "POLA Kortelė",
                "url": "https://pola.lt/pola-kortele/",
                "score": 0.95,
                "search_type": "vector"
            }
        ),
        Document(
            page_content="Smegenų vėžys yra rimta onkologinė liga, reikalaujanti specialisto pagalbos.",
            metadata={
                "title": "Smegenų vėžys",
                "url": "https://priesvezi.lt/zinynas/smegenu-vezys/",
                "score": 0.85,
                "search_type": "vector"
            }
        ),
        Document(
            page_content="Vilniuje yra keletas onkologijos centrų, teikiančių pagalbą pacientams.",
            metadata={
                "title": "Onkologijos centrai",
                "url": "https://priesvezi.lt/pagalba/centrai/vilnius/",
                "score": 0.75,
                "search_type": "keyword"
            }
        ),
    ]
    
    # Test query
    test_query = "Kaip gauti POLA kortelę?"
    
    # Generate response with test documents
    response = await generator._generate_response(test_query, test_documents)
    
    # Check if URLs are included in the response
    logger.info("Generated response:")
    logger.info(response)
    
    # Verify the top 2 URLs are included
    if "pola.lt/pola-kortele" in response and "priesvezi.lt/zinynas/smegenu-vezys" in response:
        logger.info("✅ SUCCESS: Top 2 URLs are included in the response")
    else:
        logger.error("❌ ERROR: Top 2 URLs are not included in the response")
    
    # Check for source attribution
    if "Information retrieved from 3 documents" in response:
        logger.info("✅ SUCCESS: Source attribution is included")
    else:
        logger.error("❌ ERROR: Source attribution is missing")
    
    # Check for source category counts
    if "(2 results)" in response and "(1 results)" in response:
        logger.info("✅ SUCCESS: Source categories are included")
    else:
        logger.error("❌ ERROR: Source categories are missing")
    
    return response

if __name__ == "__main__":
    asyncio.run(test_url_attribution()) 