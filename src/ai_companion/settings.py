"""
Settings module for the AI companion.

This module provides access to application settings through environment variables.
"""

import os
from typing import Dict, Any, Optional

# Default settings that can be overridden by environment variables
class Settings:
    """Application settings."""
    
    def __init__(self):
        """Initialize settings with defaults and environment variables."""
        # Supabase settings
        self.supabase_url = os.environ.get("SUPABASE_URL", "http://localhost:8000")
        self.supabase_key = os.environ.get("SUPABASE_KEY", "")
        
        # Logging
        self.debug = os.environ.get("DEBUG", "false").lower() in ("true", "1", "yes")
        self.verbose = os.environ.get("VERBOSE", "false").lower() in ("true", "1", "yes")
        
        # Scheduled messaging
        self.max_pending_period = int(os.environ.get("MAX_PENDING_PERIOD", "30"))
        
        # General settings
        self.environment = os.environ.get("ENVIRONMENT", "development")
        self.use_managed_identity = os.environ.get("USE_MANAGED_IDENTITY", "false").lower() in ("true", "1", "yes")
        
        # Conversation summary settings
        self.TOTAL_MESSAGES_SUMMARY_TRIGGER = int(os.environ.get("TOTAL_MESSAGES_SUMMARY_TRIGGER", "10"))
        
        # Set maximum messages to analyze for the router
        self.ROUTER_MESSAGES_TO_ANALYZE = int(os.environ.get("ROUTER_MESSAGES_TO_ANALYZE", "5"))
        
        # Memory settings
        self.MEMORY_TOP_K = int(os.environ.get("MEMORY_TOP_K", "5"))
        
        # Azure OpenAI settings
        self.AZURE_OPENAI_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
        self.AZURE_EMBEDDING_DEPLOYMENT = os.environ.get("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
        self.AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "")
        self.AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
        self.AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
        
        # Qdrant settings
        self.QDRANT_URL = os.environ.get("QDRANT_URL", "")
        self.QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")

# Create a singleton instance
settings = Settings()
