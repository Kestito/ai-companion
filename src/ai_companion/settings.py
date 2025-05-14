"""
Settings module for the AI companion.

This module provides access to application settings through environment variables.
"""

import os


# Default settings that can be overridden by environment variables
class Settings:
    """Application settings."""

    def __init__(self):
        """Initialize settings with defaults and environment variables."""
        # Supabase settings - hardcoded values
        self.supabase_url = "https://aubulhjfeszmsheonmpy.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc"
        # Also add uppercase versions for compatibility
        self.SUPABASE_URL = self.supabase_url
        self.SUPABASE_KEY = self.supabase_key

        # Add Next.js specific environment variable names for frontend compatibility
        self.NEXT_PUBLIC_SUPABASE_URL = self.supabase_url
        self.NEXT_PUBLIC_SUPABASE_ANON_KEY = self.supabase_key

        # Logging
        self.debug = os.environ.get("DEBUG", "false").lower() in ("true", "1", "yes")
        self.verbose = os.environ.get("VERBOSE", "false").lower() in (
            "true",
            "1",
            "yes",
        )
        # General logging level
        self.LOGGING_LEVEL = os.environ.get("LOGGING_LEVEL", "INFO")
        # Scheduler logging level
        self.SCHEDULER_LOG_LEVEL = os.environ.get("SCHEDULER_LOG_LEVEL", "ERROR")

        # Scheduled messaging
        self.max_pending_period = int(os.environ.get("MAX_PENDING_PERIOD", "30"))

        # General settings
        self.environment = os.environ.get("ENVIRONMENT", "development")
        self.use_managed_identity = os.environ.get(
            "USE_MANAGED_IDENTITY", "false"
        ).lower() in ("true", "1", "yes")

        # Conversation summary settings
        self.TOTAL_MESSAGES_SUMMARY_TRIGGER = int(
            os.environ.get("TOTAL_MESSAGES_SUMMARY_TRIGGER", "10")
        )

        # Set maximum messages to analyze for the router
        self.ROUTER_MESSAGES_TO_ANALYZE = int(
            os.environ.get("ROUTER_MESSAGES_TO_ANALYZE", "5")
        )

        # Memory settings
        self.MEMORY_TOP_K = int(os.environ.get("MEMORY_TOP_K", "5"))
        self.MEMORY_EMBEDDING_RETRIES = int(
            os.environ.get("MEMORY_EMBEDDING_RETRIES", "3")
        )  # Retry count for embeddings

        # Azure OpenAI settings
        self.AZURE_OPENAI_DEPLOYMENT = os.environ.get(
            "AZURE_OPENAI_DEPLOYMENT", "o4-mini"
        )
        self.AZURE_EMBEDDING_DEPLOYMENT = os.environ.get(
            "AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"
        )
        self.AZURE_OPENAI_API_KEY = os.environ.get(
            "AZURE_OPENAI_API_KEY",
            "Ec1hyYbP5j6AokTzLWtc3Bp970VbCnpRMhNmQjxgJh1LrYzlsrrOJQQJ99ALACHYHv6XJ3w3AAAAACOG0Kyl",
        )
        self.AZURE_OPENAI_ENDPOINT = os.environ.get(
            "AZURE_OPENAI_ENDPOINT",
            "https://ai-kestutis9429ai265477517797.openai.azure.com",
        )
        self.AZURE_OPENAI_API_VERSION = os.environ.get(
            "AZURE_OPENAI_API_VERSION", "2025-04-16"
        )
        self.LLM_MODEL = os.environ.get("LLM_MODEL", "o4-mini")

        # Embedding fallback settings
        self.USE_FALLBACK_EMBEDDING = os.environ.get(
            "USE_FALLBACK_EMBEDDING", "false"
        ).lower() in ("true", "1", "yes")
        self.FALLBACK_EMBEDDING_MODEL = os.environ.get(
            "FALLBACK_EMBEDDING_MODEL", "text-embedding-3-small"
        )
        self.EMBEDDING_DIMENSION = int(os.environ.get("EMBEDDING_DIMENSION", "1536"))
        self.EMBEDDING_TIMEOUT = int(
            os.environ.get("EMBEDDING_TIMEOUT", "30")
        )  # Timeout in seconds
        self.AZURE_EMBEDDING_API_VERSION = os.environ.get(
            "AZURE_EMBEDDING_API_VERSION", "2023-05-15"
        )

        # Qdrant settings
        self.QDRANT_URL = os.environ.get(
            "QDRANT_URL",
            "https://b88198bc-6212-4390-bbac-b1930f543812.europe-west3-0.gcp.cloud.qdrant.io",
        )
        self.QDRANT_API_KEY = os.environ.get(
            "QDRANT_API_KEY",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.cdTvd4mc74giwx-ypkE8t4muYvpQqLqkc5P6IXuJAOw",
        )

        # Speech-to-text and text-to-speech settings
        self.STT_MODEL_NAME = os.environ.get("STT_MODEL_NAME", "whisper")
        self.TTS_MODEL_NAME = os.environ.get("TTS_MODEL_NAME", "eleven_flash_v2_5")

        # ElevenLabs settings
        self.ELEVENLABS_API_KEY = os.environ.get(
            "ELEVENLABS_API_KEY", "sk_f8aaf95ce7c9bc93c1341eded4014382cd6444e84cb5c03d"
        )
        self.ELEVENLABS_VOICE_ID = os.environ.get(
            "ELEVENLABS_VOICE_ID", "qSfcmCS9tPikUrDxO8jt"
        )

        # Telegram settings
        # Use different bot tokens for production and test/local environments
        if self.environment.lower() == "production":
            # Production bot token
            self.TELEGRAM_BOT_TOKEN = os.environ.get(
                "TELEGRAM_BOT_TOKEN", "7602202107:AAH-7E6Dy6DGy1yaYQoZYFeJNpf4Z1m_Vmk"
            )
        else:
            # Test/local bot token
            self.TELEGRAM_BOT_TOKEN = os.environ.get(
                "TELEGRAM_BOT_TOKEN", "7764956576:AAE2C57S9jzihsYvoA2R7fjvLPjoopFbNxU"
            )

        self.TELEGRAM_API_BASE = os.environ.get(
            "TELEGRAM_API_BASE", "https://api.telegram.org"
        )

        # SQLite Database path for short-term memory
        self._setup_database_paths()

    def _setup_database_paths(self):
        """Set up database paths for legacy code compatibility."""
        try:
            # Set to use Supabase exclusively
            self.USE_SUPABASE_FOR_MEMORY = True

            # Memory storage settings
            self.MEMORY_STORAGE_TYPE = os.environ.get("MEMORY_STORAGE_TYPE", "supabase")

            # For legacy code compatibility, set SHORT_TERM_MEMORY_DB_PATH to None
            # This will signal to use Supabase instead
            self.SHORT_TERM_MEMORY_DB_PATH = None

            print("Using Supabase for short-term memory storage")

        except Exception as e:
            print(f"Error setting up memory configuration: {str(e)}")
            # Fallback to in-memory database only if absolutely necessary
            self.SHORT_TERM_MEMORY_DB_PATH = ":memory:"
            self.MEMORY_STORAGE_TYPE = "memory"
            print("Using in-memory database as fallback (should not happen)")


# Create a singleton instance
settings = Settings()
