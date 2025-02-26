#!/usr/bin/env python
"""
URL Prioritization Example for RAG System

This example demonstrates how to prioritize specific URLs in RAG results
so that content from those URLs is boosted in the ranking.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from src.ai_companion.modules.rag.core import query_with_url_priority

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def main():
    """Run the URL prioritization example."""
    # URL to prioritize
    priority_url = "https://priesvezi.lt/zinynas/onkologines-ligos/plauciu-vezys/"
    
    # Example queries about lung cancer (Plaučių vėžys)
    queries = [
        "Kas yra plaučių vėžys?",
        "Kokie yra plaučių vėžio simptomai?",
        "Kaip gydomas plaučių vėžys?",
        "Plaučių vėžio rizikos faktoriai",
    ]
    
    # Process each query
    for query in queries:
        logger.info(f"\n\n==== QUERY: {query} ====")
        
        # Get response with URL prioritization
        response, docs = await query_with_url_priority(query, priority_url)
        
        # Print response
        logger.info(f"\nRESPONSE:\n{response}\n")
        
        # Print source documents
        logger.info("SOURCE DOCUMENTS:")
        for i, doc in enumerate(docs[:3]):  # Show top 3 documents
            url = doc.metadata.get("url", "Unknown")
            is_priority = priority_url.lower() in url.lower()
            score = doc.metadata.get("score", 0.0)
            priority_tag = " [PRIORITY]" if is_priority else ""
            
            logger.info(f"Document {i+1}{priority_tag} (Score: {score:.2f}):")
            logger.info(f"URL: {url}")
            logger.info(f"Content: {doc.page_content[:200]}...\n")
        
        # Pause between queries
        if query != queries[-1]:
            logger.info("Waiting 2 seconds before next query...")
            await asyncio.sleep(2)

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 