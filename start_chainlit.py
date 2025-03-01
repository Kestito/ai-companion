#!/usr/bin/env python
"""Script to start Chainlit with Uvicorn."""

import os
import subprocess
import sys
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chainlit_starter")

# Chainlit server settings
CHAINLIT_PORT = 8080

def start_chainlit():
    """Start Chainlit service using Uvicorn."""
    logger.info("Starting Chainlit service with Uvicorn on port %s", CHAINLIT_PORT)
    
    try:
        # Start chainlit with Uvicorn directly
        cmd = [
            "uvicorn", 
            "chainlit.server:app", 
            "--host", "0.0.0.0",
            "--port", str(CHAINLIT_PORT),
            "--log-level", "info"
        ]
        
        logger.info("Executing command: %s", " ".join(cmd))
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Log the output
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            
        # Wait for process to complete (should never happen unless error)
        process.wait()
        logger.error("Chainlit process exited with code %d", process.returncode)
        
    except Exception as e:
        logger.error("Failed to start Chainlit: %s", str(e))
        raise

if __name__ == "__main__":
    start_chainlit() 