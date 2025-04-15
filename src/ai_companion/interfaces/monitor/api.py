"""Monitoring API endpoints for the AI Companion."""

import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List

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

class SchedulerStatusResponse(BaseModel):
    """Response model for Telegram scheduler status endpoint."""
    status: str
    message: str
    last_run: Optional[str] = None
    pending_messages: Optional[int] = None
    recent_messages: Optional[List[Dict[str, Any]]] = None
    pending_messages_details: Optional[List[Dict[str, Any]]] = None

@monitor_router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint for the monitoring API."""
    return {"status": "healthy", "service": "monitoring"}

@monitor_router.get("/health/telegram-scheduler-status", response_model=SchedulerStatusResponse)
async def telegram_scheduler_status():
    """Check if the Telegram scheduler is running and its status."""
    try:
        # Try to import Supabase client to query the database
        try:
            from supabase import create_client, Client
            
            # Supabase credentials (same as in the scheduler)
            SUPABASE_URL = "https://aubulhjfeszmsheonmpy.supabase.co"
            SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc"
            
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # Get pending messages explicitly to show in UI
            pending_messages_result = supabase.table("scheduled_messages") \
                .select("id, patient_id, message_content, scheduled_time, created_at, status") \
                .eq("status", "pending") \
                .order("scheduled_time", desc=False) \
                .limit(10) \
                .execute()
            
            pending_messages = pending_messages_result.data or []
            pending_count = len(pending_messages)
            
            # Get patient names for pending messages
            if pending_messages:
                patient_ids = [msg["patient_id"] for msg in pending_messages if msg.get("patient_id")]
                if patient_ids:
                    patients_result = supabase.table("patients") \
                        .select("id, first_name, last_name") \
                        .in_("id", patient_ids) \
                        .execute()
                    
                    patients_by_id = {}
                    for patient in patients_result.data or []:
                        name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
                        patients_by_id[patient["id"]] = name or f"Patient {patient['id']}"
                    
                    # Add patient names to messages
                    for msg in pending_messages:
                        patient_id = msg.get("patient_id")
                        msg["patient_name"] = patients_by_id.get(patient_id, f"Patient {patient_id}")
                        
                        # Format the scheduled time for better display
                        if scheduled_time := msg.get("scheduled_time"):
                            try:
                                from datetime import datetime
                                dt = datetime.fromisoformat(scheduled_time.replace("Z", "+00:00"))
                                msg["formatted_time"] = dt.strftime("%Y-%m-%d %H:%M:%S")
                            except Exception as e:
                                logger.error(f"Error formatting time: {e}")
                                msg["formatted_time"] = scheduled_time
            
            # Check for recent processed messages (in the last 15 minutes - more lenient for containers)
            fifteen_minutes_ago = datetime.utcnow() - timedelta(minutes=15)
            fifteen_minutes_ago_iso = fifteen_minutes_ago.isoformat()
            
            # Get recently processed messages using last_attempt_time instead of processed_at
            recent_messages_response = supabase.table("scheduled_messages") \
                .select("*") \
                .gt("last_attempt_time", fifteen_minutes_ago_iso) \
                .order("last_attempt_time", desc=True) \
                .limit(5) \
                .execute()
            
            recent_messages = recent_messages_response.data
            
            # If there are recent messages, the scheduler is running
            if recent_messages:
                # Map processed_at reference to last_attempt_time for frontend compatibility
                for msg in recent_messages:
                    if "last_attempt_time" in msg:
                        msg["processed_at"] = msg["last_attempt_time"]
                
                last_run = max([msg.get("last_attempt_time") for msg in recent_messages if msg.get("last_attempt_time")])
                return SchedulerStatusResponse(
                    status="running",
                    message="Telegram scheduler is active and processing messages",
                    last_run=last_run,
                    pending_messages=pending_count,
                    recent_messages=recent_messages,
                    pending_messages_details=pending_messages
                )
            
            # For Azure Container App deployments, we need to check more indicators
            # Check for more recent activity in scheduled_messages table
            # Check the latest update to any row, regardless of status
            all_messages_response = supabase.table("scheduled_messages") \
                .select("last_attempt_time") \
                .not_.is_("last_attempt_time", "null") \
                .order("last_attempt_time", desc=True) \
                .limit(1) \
                .execute()
            
            if all_messages_response.data:
                last_update = all_messages_response.data[0].get("last_attempt_time")
                last_update_time = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
                
                # If there was activity in the last hour, consider it running
                if datetime.utcnow() - last_update_time < timedelta(hours=1):
                    return SchedulerStatusResponse(
                        status="running",
                        message="Telegram scheduler appears to be active (database activity detected)",
                        last_run=last_update,
                        pending_messages=pending_count,
                        pending_messages_details=pending_messages
                    )
            
            # Check log file for recent activity (fallback for local deployments)
            log_path = os.path.join("logs", "telegram_scheduler.log")
            if os.path.exists(log_path):
                # Check if log file was modified in the last 5 minutes
                log_modified_time = datetime.fromtimestamp(os.path.getmtime(log_path))
                if datetime.utcnow() - log_modified_time < timedelta(minutes=5):
                    return SchedulerStatusResponse(
                        status="running",
                        message="Telegram scheduler is running (detected from log activity)",
                        pending_messages=pending_count,
                        pending_messages_details=pending_messages
                    )
            
            # If we got here, we couldn't confirm the scheduler is running
            return SchedulerStatusResponse(
                status="not_running",
                message=f"Telegram scheduler does not appear to be running. There are {pending_count} pending messages waiting to be processed.",
                pending_messages=pending_count,
                pending_messages_details=pending_messages
            )
            
        except ImportError:
            logger.error("Supabase client not found.")
            return SchedulerStatusResponse(
                status="unknown",
                message="Could not check scheduler status - missing Supabase client"
            )
    except Exception as e:
        logger.error(f"Error checking Telegram scheduler status: {e}")
        return SchedulerStatusResponse(
            status="error",
            message=f"Error checking scheduler status: {str(e)}"
        )

@monitor_router.get("/telegram-scheduler-status", response_model=SchedulerStatusResponse)
async def telegram_scheduler_status_legacy():
    """Legacy endpoint for checking Telegram scheduler status - redirects to /health/telegram-scheduler-status."""
    return await telegram_scheduler_status()

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

@monitor_router.post("/telegram/send-message", status_code=status.HTTP_200_OK)
async def send_telegram_message(message_id: str):
    """
    Manually send a scheduled Telegram message by ID.
    Used for debugging and manual intervention.
    """
    logger.info(f"Manual request to send Telegram message ID: {message_id}")
    
    try:
        # Import necessary modules
        try:
            from supabase import create_client, Client
            from telegram.ext import Application
            import json
            
            # Credentials
            SUPABASE_URL = "https://aubulhjfeszmsheonmpy.supabase.co"
            SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc"
            TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "5933996374:AAGZDvHg3tYoXnGIa1wKVAsCO-iqFnCmGMw")
            
            # Connect to Supabase
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # Fetch the message
            message_response = supabase.table("scheduled_messages") \
                .select("*") \
                .eq("id", message_id) \
                .execute()
            
            if not message_response.data:
                logger.error(f"Message {message_id} not found")
                return {"status": "error", "message": f"Message {message_id} not found"}
            
            message = message_response.data[0]
            patient_id = message.get("patient_id")
            content = message.get("message_content")
            
            logger.info(f"Found message: {message_id} for patient: {patient_id}")
            
            # Get patient's Telegram ID
            patient_response = supabase.table("patients") \
                .select("telegram_id") \
                .eq("id", patient_id) \
                .execute()
            
            if not patient_response.data:
                logger.error(f"Patient {patient_id} not found")
                return {"status": "error", "message": f"Patient {patient_id} not found"}
            
            telegram_id = patient_response.data[0].get("telegram_id")
            if not telegram_id:
                logger.error(f"Patient {patient_id} has no telegram_id")
                return {"status": "error", "message": f"Patient {patient_id} has no telegram_id"}
            
            # Initialize Telegram bot
            telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
            
            # Send the message
            await telegram_app.bot.send_message(
                chat_id=telegram_id,
                text=content
            )
            
            logger.info(f"Message sent successfully to patient {patient_id} (Telegram ID: {telegram_id})")
            
            # Update message status
            now_iso = datetime.now(timezone.utc).isoformat()
            update_data = {
                "status": "sent",
                "last_attempt_time": now_iso,
                "attempts": message.get("attempts", 0) + 1
            }
            
            supabase.table("scheduled_messages") \
                .update(update_data) \
                .eq("id", message_id) \
                .execute()
            
            return {
                "status": "success", 
                "message": f"Message {message_id} sent successfully", 
                "details": {
                    "patient_id": patient_id,
                    "telegram_id": telegram_id,
                    "content": content,
                    "sent_at": now_iso
                }
            }
            
        except ImportError as e:
            logger.error(f"Required module not found: {e}")
            return {"status": "error", "message": f"Required module not found: {e}"}
            
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        return {"status": "error", "message": f"Error sending message: {str(e)}"} 