"""Main FastAPI application for AI Companion."""

import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_companion.interfaces.whatsapp.whatsapp_response import whatsapp_router
from ai_companion.interfaces.monitor.api import monitor_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Companion",
    description="AI Companion with WhatsApp and Monitoring interfaces",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with path-based routing
app.include_router(whatsapp_router)
app.include_router(monitor_router)

@app.get("/health")
async def health_check():
    """Root health check endpoint."""
    return {
        "status": "healthy",
        "service": "ai-companion",
        "interfaces": {
            "whatsapp": "/whatsapp/health",
            "monitor": "/monitor/health"
        }
    }

@app.get("/")
async def root():
    """Root endpoint for the AI Companion."""
    # If INTERFACE environment variable is set to 'all' or 'chainlit',
    # this will be overridden by the Chainlit interface
    return {
        "message": "AI Companion API",
        "docs_url": "/docs",
        "whatsapp_url": "/whatsapp/webhook",
        "monitor_url": "/monitor/metrics",
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 