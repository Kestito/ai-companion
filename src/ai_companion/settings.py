"""
Settings module for the AI companion.

This module provides access to application settings through environment variables.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path

# Default settings that can be overridden by environment variables
class Settings:
    """Application settings."""
    
    def __init__(self):
        """Initialize settings with defaults and environment variables."""
        # Supabase settings
        self.supabase_url = os.environ.get("SUPABASE_URL", "http://localhost:8000")
        self.supabase_key = os.environ.get("SUPABASE_KEY", "")
        # Also add uppercase versions for compatibility
        self.SUPABASE_URL = self.supabase_url
        self.SUPABASE_KEY = self.supabase_key
        
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
        
        # Speech-to-text and text-to-speech settings
        self.STT_MODEL_NAME = os.environ.get("STT_MODEL_NAME", "whisper")
        self.TTS_MODEL_NAME = os.environ.get("TTS_MODEL_NAME", "eleven_flash_v2_5")
        
        # ElevenLabs settings
        self.ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "sk_f8aaf95ce7c9bc93c1341eded4014382cd6444e84cb5c03d")
        self.ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "qSfcmCS9tPikUrDxO8jt")
        
        # Telegram settings
        # Use different bot tokens for production and test/local environments
        if self.environment.lower() == "production":
            # Production bot token
            self.TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "7602202107:AAH-7E6Dy6DGy1yaYQoZYFeJNpf4Z1m_Vmk")
        else:
            # Test/local bot token
            self.TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "7764956576:AAE2C57S9jzihsYvoA2R7fjvLPjoopFbNxU")
        
        self.TELEGRAM_API_BASE = os.environ.get("TELEGRAM_API_BASE", "https://api.telegram.org")
        
        # SQLite Database path for short-term memory
        self._setup_database_paths()
        
    def _setup_database_paths(self):
        """Set up database paths and ensure directories exist."""
        try:
            # Get database directory from environment or use default
            data_dir = os.environ.get("DATA_DIR", "data")
            
            # Create Path object for better path handling
            data_path = Path(data_dir)
            
            # Ensure the data directory exists with absolute path
            os.makedirs(data_path.absolute(), exist_ok=True)
            
            # Create the database file path
            db_file = data_path.absolute() / "short_term_memory.db"
            
            # Make sure parent directory permissions allow writing
            try:
                os.chmod(data_path.absolute(), 0o777)
            except Exception as e:
                print(f"Warning: Could not set permissions on data directory: {e}")
            
            # Touch the file to ensure it exists and is writable
            if not db_file.exists():
                db_file.touch()
                
            # Set permissions on the file
            try:
                os.chmod(db_file, 0o666)
            except Exception as e:
                print(f"Warning: Could not set permissions on database file: {e}")
            
            # The connection string format needed by the AsyncSqliteSaver
            self.SHORT_TERM_MEMORY_DB_PATH = str(db_file)
            
            print(f"Database file created at: {self.SHORT_TERM_MEMORY_DB_PATH}")
            
        except Exception as e:
            print(f"Error setting up database path: {str(e)}")
            # Fallback to in-memory database
            self.SHORT_TERM_MEMORY_DB_PATH = ":memory:"
            print("Using in-memory database as fallback")

# Create a singleton instance
settings = Settings()
