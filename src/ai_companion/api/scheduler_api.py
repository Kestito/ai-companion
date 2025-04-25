from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from ..modules.scheduler import get_scheduled_message_service

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/scheduler", tags=["scheduler"])


# Models for the API
class RecurrencePattern(BaseModel):
    type: str = Field(
        ..., description="Recurrence type: 'daily', 'weekly', 'monthly', or 'custom'"
    )
    interval: Optional[int] = Field(1, description="Interval between occurrences")
    days: Optional[List[int]] = Field(
        None, description="Days of week for weekly recurrence (0-6, 0 is Monday)"
    )
    day: Optional[int] = Field(None, description="Day of month for monthly recurrence")
    minutes: Optional[int] = Field(
        None, description="Minutes interval for custom recurrence"
    )


class ScheduledMessageCreate(BaseModel):
    chat_id: int = Field(..., description="Telegram chat ID to send the message to")
    message_content: str = Field(..., description="Content of the message to send")
    scheduled_time: datetime = Field(..., description="When to send the message")
    patient_id: Optional[str] = Field(None, description="Optional patient ID")
    recurrence_pattern: Optional[RecurrencePattern] = Field(
        None, description="Recurrence pattern if recurring"
    )
    priority: int = Field(1, description="Priority of the message (1-5, 1 is highest)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ScheduledMessageResponse(BaseModel):
    id: str
    chat_id: int
    message_content: str
    scheduled_time: datetime
    status: str
    platform: str
    created_at: datetime
    attempts: int
    priority: int
    last_attempt_time: Optional[datetime] = None
    patient_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    delivery_window_seconds: Optional[int] = None
    is_recurring: bool = False


@router.post("/messages", response_model=str, summary="Create a new scheduled message")
async def create_scheduled_message(message: ScheduledMessageCreate):
    """
    Create a new scheduled message with optional recurrence
    """
    try:
        # Get the scheduled message service
        service = get_scheduled_message_service()

        # Create the message
        message_id = await service.create_scheduled_message(
            chat_id=message.chat_id,
            message_content=message.message_content,
            scheduled_time=message.scheduled_time,
            platform="telegram",
            patient_id=message.patient_id,
            priority=message.priority,
            metadata=message.metadata or {},
            recurrence_pattern=message.recurrence_pattern.dict()
            if message.recurrence_pattern
            else None,
        )

        return message_id
    except Exception as e:
        logger.error(f"Error creating scheduled message: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create scheduled message: {str(e)}"
        )


@router.get(
    "/messages",
    response_model=List[ScheduledMessageResponse],
    summary="List scheduled messages",
)
async def list_scheduled_messages(
    chat_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
):
    """
    List scheduled messages with optional filters
    """
    try:
        service = get_scheduled_message_service()

        # Handle different filter scenarios
        if chat_id:
            # Get messages for specific chat
            messages = await service.get_messages_by_chat_id(
                chat_id=chat_id, status=status, limit=limit
            )
        else:
            # TODO: Implement method to get all messages with filters
            # For now, we'll raise an exception requiring chat_id
            raise HTTPException(status_code=400, detail="chat_id is required")

        # Format response
        response = []
        for msg in messages:
            # Extract chat_id from metadata
            metadata = msg.get("metadata", {})
            platform_data = metadata.get("platform_data", {})
            chat_id = platform_data.get("chat_id")

            # Check if recurring
            is_recurring = bool(metadata.get("recurrence"))

            # Convert scheduled time string to datetime
            scheduled_time = msg.get("scheduled_time")
            if isinstance(scheduled_time, str):
                scheduled_time = datetime.fromisoformat(
                    scheduled_time.replace("Z", "+00:00")
                )

            # Same for created_at and last_attempt_time
            created_at = msg.get("created_at")
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

            last_attempt_time = msg.get("last_attempt_time")
            if last_attempt_time and isinstance(last_attempt_time, str):
                last_attempt_time = datetime.fromisoformat(
                    last_attempt_time.replace("Z", "+00:00")
                )

            response.append(
                {
                    "id": msg.get("id"),
                    "chat_id": chat_id,
                    "message_content": msg.get("message_content"),
                    "scheduled_time": scheduled_time,
                    "status": msg.get("status"),
                    "platform": msg.get("platform"),
                    "created_at": created_at,
                    "attempts": msg.get("attempts", 0),
                    "priority": msg.get("priority", 1),
                    "last_attempt_time": last_attempt_time,
                    "patient_id": msg.get("patient_id"),
                    "metadata": metadata,
                    "delivery_window_seconds": msg.get("delivery_window_seconds"),
                    "is_recurring": is_recurring,
                }
            )

        return response
    except Exception as e:
        logger.error(f"Error listing scheduled messages: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list scheduled messages: {str(e)}"
        )


@router.get(
    "/messages/{message_id}",
    response_model=ScheduledMessageResponse,
    summary="Get a scheduled message by ID",
)
async def get_scheduled_message(message_id: str):
    """
    Get details of a specific scheduled message
    """
    try:
        service = get_scheduled_message_service()
        msg = await service.get_message_by_id(message_id)

        if not msg:
            raise HTTPException(
                status_code=404, detail=f"Message with ID {message_id} not found"
            )

        # Extract chat_id from metadata
        metadata = msg.get("metadata", {})
        platform_data = metadata.get("platform_data", {})
        chat_id = platform_data.get("chat_id")

        # Check if recurring
        is_recurring = bool(metadata.get("recurrence"))

        # Convert scheduled time string to datetime
        scheduled_time = msg.get("scheduled_time")
        if isinstance(scheduled_time, str):
            scheduled_time = datetime.fromisoformat(
                scheduled_time.replace("Z", "+00:00")
            )

        # Same for created_at and last_attempt_time
        created_at = msg.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        last_attempt_time = msg.get("last_attempt_time")
        if last_attempt_time and isinstance(last_attempt_time, str):
            last_attempt_time = datetime.fromisoformat(
                last_attempt_time.replace("Z", "+00:00")
            )

        return {
            "id": msg.get("id"),
            "chat_id": chat_id,
            "message_content": msg.get("message_content"),
            "scheduled_time": scheduled_time,
            "status": msg.get("status"),
            "platform": msg.get("platform"),
            "created_at": created_at,
            "attempts": msg.get("attempts", 0),
            "priority": msg.get("priority", 1),
            "last_attempt_time": last_attempt_time,
            "patient_id": msg.get("patient_id"),
            "metadata": metadata,
            "delivery_window_seconds": msg.get("delivery_window_seconds"),
            "is_recurring": is_recurring,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scheduled message: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get scheduled message: {str(e)}"
        )


@router.delete(
    "/messages/{message_id}", response_model=bool, summary="Cancel a scheduled message"
)
async def cancel_scheduled_message(message_id: str):
    """
    Cancel a scheduled message by ID
    """
    try:
        service = get_scheduled_message_service()

        # Check if message exists
        msg = await service.get_message_by_id(message_id)
        if not msg:
            raise HTTPException(
                status_code=404, detail=f"Message with ID {message_id} not found"
            )

        # Cancel the message
        success = await service.cancel_message(message_id)

        if not success:
            raise HTTPException(
                status_code=500, detail=f"Failed to cancel message {message_id}"
            )

        return success
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling scheduled message: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to cancel scheduled message: {str(e)}"
        )
