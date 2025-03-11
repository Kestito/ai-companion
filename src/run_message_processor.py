#!/usr/bin/env python
"""
Run the scheduled message processor as a background process.

This script starts the background process that handles sending scheduled messages.
"""

import asyncio
import logging
import sys
import os
import time

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from ai_companion.modules.scheduled_messaging.processor import main

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='message_processor.log'
    )
    
    # Also log to console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    
    # Start the processor
    logging.info("Starting message processor")
    main() 