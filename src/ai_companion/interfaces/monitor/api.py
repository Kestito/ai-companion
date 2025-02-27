"""Monitoring API endpoints for the AI Companion."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ai_companion.modules.rag.core.monitoring import RAGMonitor

# Configure logging
logger = logging.getLogger(__name__)

# Create router
monitor_router = APIRouter(prefix="/monitor", tags=["monitoring"])

# Create a singleton instance of RAGMonitor
rag_monitor = RAGMonitor()

class MetricsResponse(BaseModel):
    """Response model for metrics endpoint."""
    metrics: Dict[str, Any]
    status: str = "success"

class ReportResponse(BaseModel):
    """Response model for performance report endpoint."""
    report: Dict[str, Any]
    status: str = "success"

class ResetResponse(BaseModel):
    """Response model for reset endpoint."""
    status: str = "success"
    message: str = "Metrics reset successfully"

@monitor_router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint for the monitoring API."""
    return {"status": "healthy", "service": "monitoring"}

@monitor_router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get current RAG metrics."""
    try:
        metrics = rag_monitor.get_metrics()
        return MetricsResponse(metrics=metrics)
    except Exception as e:
        logger.error(f"Error retrieving metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metrics: {str(e)}"
        )

@monitor_router.get("/report", response_model=ReportResponse)
async def get_performance_report():
    """Get RAG performance report."""
    try:
        report = rag_monitor.get_performance_report()
        return ReportResponse(report=report)
    except Exception as e:
        logger.error(f"Error generating performance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate performance report: {str(e)}"
        )

@monitor_router.post("/reset", response_model=ResetResponse)
async def reset_metrics():
    """Reset all RAG metrics."""
    try:
        rag_monitor.reset_metrics()
        return ResetResponse()
    except Exception as e:
        logger.error(f"Error resetting metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset metrics: {str(e)}"
        ) 