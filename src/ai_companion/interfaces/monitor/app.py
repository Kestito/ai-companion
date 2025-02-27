"""FastAPI app for the monitoring interface."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_companion.interfaces.monitor import monitor_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Companion Monitoring API",
    description="API for monitoring the AI Companion system",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(monitor_router)

@app.get("/health")
async def health_check():
    """Health check endpoint for the monitoring API."""
    return {"status": "healthy", "service": "monitoring"}

@app.get("/")
async def root():
    """Root endpoint for the monitoring API."""
    return {
        "message": "AI Companion Monitoring API",
        "docs_url": "/docs",
        "metrics_url": "/monitor/metrics",
        "report_url": "/monitor/report",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090) 