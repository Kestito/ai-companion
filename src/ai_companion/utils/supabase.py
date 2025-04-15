"""Supabase client utilities for database operations.

This module provides a singleton Supabase client for interacting with the Supabase database.
"""

import logging
import os
from functools import lru_cache
from supabase import create_client, Client
from supabase.client import ClientOptions
from ai_companion.settings import settings

# Add Azure Identity imports for managed identity support
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential

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
        # Check if running in Azure Container Apps
        if os.environ.get("CONTAINER_APP_ENV"):
            logger.info("Running in Azure Container App environment")
            
            # If using Managed Identity for secrets
            if os.environ.get("USE_MANAGED_IDENTITY", "false").lower() == "true":
                try:
                    # Use DefaultAzureCredential to get token
                    credential = DefaultAzureCredential()
                    # For key vault access if needed
                    # Note: This is just preparation - actual key vault integration would need more code
                    logger.info("Using Azure Managed Identity for authentication")
                except Exception as e:
                    logger.warning(f"Failed to use Managed Identity: {e}. Falling back to standard auth.")
        
        client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY,
            options=ClientOptions(
                schema="public",
                headers={
                    "Content-Type": "application/json",
                    "Accept-Profile": "public"
                }
            )
        )
        logger.info("Supabase client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Error initializing Supabase client: {e}", exc_info=True)
        # Re-raise to allow caller to handle
        raise 