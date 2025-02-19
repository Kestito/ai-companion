from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_file_encoding="utf-8"
    )

    # API Keys
    GROQ_API_KEY: str = "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"
    ELEVENLABS_API_KEY: str = "sk_f8aaf95ce7c9bc93c1341eded4014382cd6444e84cb5c03d"
    ELEVENLABS_VOICE_ID: str = "qSfcmCS9tPikUrDxO8jt"
    TOGETHER_API_KEY: str = "f53a57cee7bfb44b930a4d2a6c5b4e9002389c600f931b4cf2e10e9bc4827dff"

    # Qdrant Configuration
    QDRANT_API_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwiZXhwIjoxNzQ3MDY5MzcyfQ.plLwDbnIi7ggn_d98e-OsxpF60lcNq9nzZ0EzwFAnQw"
    QDRANT_URL: str = "https://b88198bc-6212-4390-bbac-b1930f543812.europe-west3-0.gcp.cloud.qdrant.io"
    QDRANT_PORT: str = "6333"
    QDRANT_HOST: str | None = None

    # Model Names
    TEXT_MODEL_NAME: str = "gpt-4o"
    SMALL_TEXT_MODEL_NAME: str = "gpt-4o"
    STT_MODEL_NAME: str = "whisper-large-v3-turbo"
    TTS_MODEL_NAME: str = "eleven_flash_v2_5"
    TTI_MODEL_NAME: str = "black-forest-labs/FLUX.1-schnell-Free"
    ITT_MODEL_NAME: str = "llama-3.2-90b-vision-preview"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Memory Configuration
    MEMORY_TOP_K: int = 3
    ROUTER_MESSAGES_TO_ANALYZE: int = 3
    TOTAL_MESSAGES_SUMMARY_TRIGGER: int = 20
    TOTAL_MESSAGES_AFTER_SUMMARY: int = 5
    EMBEDDING_MAX_TOKEN_SIZE: int = 8192
    EMBEDDING_DIM: int = 384

    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY: str = "Ec1hyYbP5j6AokTzLWtc3Bp970VbCnpRMhNmQjxgJh1LrYzlsrrOJQQJ99ALACHYHv6XJ3w3AAAAACOG0Kyl"
    AZURE_OPENAI_ENDPOINT: str = "https://ai-kestutis9429ai265477517797.openai.azure.com"
    AZURE_OPENAI_API_VERSION: str = "2024-08-01-preview"
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o"
    AZURE_EMBEDDING_DEPLOYMENT: str = "text-embedding-3-small"
    AZURE_EMBEDDING_API_VERSION: str = "2023-05-15"
    LLM_MODEL: str = "gpt-4o"
    AZURE_OPENAI_DEPLOYMENT_TYPO: str = "gpt-4o"

    # WhatsApp Configuration
    WHATSAPP_PHONE_NUMBER_ID: str = "566612569868882"
    WHATSAPP_TOKEN: str = "EAAOp6lp8Xt4BO2BVhmHXMuAvwI1gXhi53y9OUDJs412MSnKtAo5FtVhyMqqMrU2y9ZBeZCtN9zSFhJ1WHN65wCX2jUcN3aBTpk4bVS2dAHjY5EJKxkWXGaMIuvTkZBJB4FKwpidRcy61d9GCOni3ZB8mXP6qr9HXx7poi75Wc00KbY2KfdbY2uIzoWIUXsVZBCgZDZD"
    WHATSAPP_VERIFY_TOKEN: str = "xxx"
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = "1342440093842225"
    WHATSAPP_ACCESS_TOKEN: str = "EAAOp6lp8Xt4BO2BVhmHXMuAvwI1gXhi53y9OUDJs412MSnKtAo5FtVhyMqqMrU2y9ZBeZCtN9zSFhJ1WHN65wCX2jUcN3aBTpk4bVS2dAHjY5EJKxkWXGaMIuvTkZBJB4FKwpidRcy61d9GCOni3ZB8mXP6qr9HXx7poi75Wc00KbY2KfdbY2uIzoWIUXsVZBCgZDZD"

    # Supabase Configuration
    SUPABASE_URL: str = "https://aubulhjfeszmsheonmpy.supabase.co"
    SUPABASE_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc"
    
    # Local Storage Configuration
    SHORT_TERM_MEMORY_DB_PATH: str = str(
        Path(os.getenv("LOCALAPPDATA", "C:/")).joinpath(
            "ai_companion/data/memory.db"
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ensure_db_path()

    def _ensure_db_path(self):
        """Create database directory structure if missing"""
        db_path = Path(self.SHORT_TERM_MEMORY_DB_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.touch(exist_ok=True)

settings = Settings()
