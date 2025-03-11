"""Supabase client utilities for database operations.

This module provides a singleton Supabase client for interacting with the Supabase database.
"""

import logging
from functools import lru_cache
from supabase import create_client, Client
from ai_companion.settings import settings

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Get a Supabase client instance.
    
    This function returns a singleton Supabase client using the credentials
    from settings. It caches the client to avoid creating multiple connections.
    
    Returns:
        A Supabase client instance
    """
    logger.debug("Initializing Supabase client")
    
    try:
        client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        logger.info("Supabase client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Error initializing Supabase client: {e}", exc_info=True)
        # Re-raise to allow caller to handle
        raise 