import pytest
from dotenv import load_dotenv
import os

@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables before any tests run."""
    load_dotenv()
    
    # Verify critical environment variables are loaded
    required_vars = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_EMBEDDING_DEPLOYMENT",
        "AZURE_EMBEDDING_API_VERSION",
        "EMBEDDING_MODEL",
        "QDRANT_URL",
        "QDRANT_API_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        pytest.fail(f"Missing required environment variables: {', '.join(missing_vars)}") 