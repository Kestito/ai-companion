from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, status, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import logging
import json
import uuid
import asyncio

from ..graph.graph import create_workflow_graph
from ..graph.state import AICompanionState
from ..graph.nodes import (
    router_node,
    conversation_node,
    memory_extraction_node,
    memory_injection_node,
    rag_node
)
from ..graph.edges import select_workflow, merge_parallel_results

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/web-chat", tags=["web-chat"])

# In-memory store for conversation states (in production, use Redis or a database)
conversation_states: Dict[str, Dict[str, Any]] = {}
conversation_graphs: Dict[str, Any] = {}

# Input and output models
class MessageRequest(BaseModel):
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    message: str
    user_info: Optional[Dict[str, Any]] = None

class MessageResponse(BaseModel):
    session_id: str
    response: str
    error: Optional[str] = None

def create_conversation_graph():
    """
    Create a conversation graph for processing web chat messages
    This uses the workflow graph from the graph module
    """
    # Use the workflow graph from the graph module
    return create_workflow_graph()

@router.post("/message", response_model=MessageResponse)
async def process_message(request: MessageRequest) -> MessageResponse:
    """
    Process a message from the web UI using the graph framework
    """
    try:
        # Get or create session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get or create conversation state and graph
        if session_id not in conversation_states:
            # Initialize with empty state following AICompanionState structure
            conversation_states[session_id] = {
                "messages": [],
                "workflow": "conversation",
                "input_message": ""
            }
            # Create a new graph instance
            conversation_graphs[session_id] = create_conversation_graph()
        
        state = conversation_states[session_id]
        graph = conversation_graphs[session_id]
        
        # Update user info in state if provided
        if request.user_info:
            state["user_info"] = request.user_info
        
        # Add user_id to state if provided
        if request.user_id:
            state["user_id"] = request.user_id
        
        # Set input message in state
        state["input_message"] = request.message
        
        # Add the user message to messages history
        from langchain_core.messages import HumanMessage
        state["messages"] = state.get("messages", []) + [HumanMessage(content=request.message)]
        
        # Process the message through the graph
        result = await graph.ainvoke(state)
        
        # Get the response from the result
        response = result.get("output_message", "Sorry, I couldn't process your message.")
        
        return MessageResponse(
            session_id=session_id,
            response=response
        )
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        return MessageResponse(
            session_id=request.session_id or str(uuid.uuid4()),
            response="",
            error=f"Error processing message: {str(e)}"
        )

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time communication with the web UI
    """
    await websocket.accept()
    
    try:
        # Get or create conversation state and graph
        if session_id not in conversation_states:
            # Initialize with empty state following AICompanionState structure
            conversation_states[session_id] = {
                "messages": [],
                "workflow": "conversation",
                "input_message": ""
            }
            # Create a new graph instance
            conversation_graphs[session_id] = create_conversation_graph()
        
        state = conversation_states[session_id]
        graph = conversation_graphs[session_id]
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Update state with message data
            user_message = message_data.get("message", "")
            state["input_message"] = user_message
            
            if "user_id" in message_data:
                state["user_id"] = message_data["user_id"]
            if "user_info" in message_data:
                state["user_info"] = message_data["user_info"]
            
            # Add the user message to messages history
            from langchain_core.messages import HumanMessage
            state["messages"] = state.get("messages", []) + [HumanMessage(content=user_message)]
            
            # Process the message through the graph
            result = await graph.ainvoke(state)
            
            # Get the response from the result
            response = result.get("output_message", "Sorry, I couldn't process your message.")
            
            # Send response back to client
            await websocket.send_json({
                "response": response,
                "session_id": session_id
            })
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket: {str(e)}", exc_info=True)
        await websocket.send_json({
            "error": f"Error processing message: {str(e)}",
            "session_id": session_id
        }) 