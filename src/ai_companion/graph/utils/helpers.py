import re
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import uuid

from langchain_core.output_parsers import StrOutputParser
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import BaseMessage

from ai_companion.modules.speech import TextToSpeech
from ai_companion.settings import settings
from ai_companion.modules.image.text_to_image import TextToImage
from ai_companion.modules.image.image_to_text import ImageToText
from ai_companion.modules.memory.service import get_memory_service

logger = logging.getLogger(__name__)


def get_chat_model(temperature: float = 0.7):
    return AzureChatOpenAI(
        deployment_name=settings.AZURE_OPENAI_DEPLOYMENT,
        openai_api_version=settings.AZURE_OPENAI_API_VERSION,
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        temperature=temperature,
    )


def get_text_to_speech_module():
    return TextToSpeech()


def get_text_to_image_module():
    return TextToImage()


def get_image_to_text_module():
    return ImageToText()


def remove_asterisk_content(text: str) -> str:
    """Remove content between asterisks from the text."""
    return re.sub(r"\*.*?\*", "", text).strip()


class AsteriskRemovalParser(StrOutputParser):
    def parse(self, text):
        return remove_asterisk_content(super().parse(text))


async def load_memory_to_graph(
    graph: Any, 
    messages: List[BaseMessage], 
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load memory into a graph state for processing.
    
    Args:
        graph: The graph instance to invoke
        messages: List of messages to process
        session_id: Optional session identifier
        
    Returns:
        The result of the graph invocation
    """
    try:
        # Get memory service
        memory_service = get_memory_service()
        
        # Create config for graph with standardized settings
        config = {
            "messages": messages,
            "configurable": {
                "memory_manager": memory_service.short_term_memory,
                "use_supabase_only": True,  # Always use Supabase for memory, no local checkpoints
                "session_id": session_id if session_id else str(uuid.uuid4())
            }
        }
        
        # Add session_id to config if provided
        if session_id:
            # Extract platform and user_id from session
            parts = session_id.split('-')
            platform = parts[0] if len(parts) > 0 else "unknown"
            
            # Try to get existing memories for context enhancement
            try:
                recent_memories = await memory_service.get_session_memory(
                    platform=platform, 
                    user_id=session_id.replace(f"{platform}-", ""),
                    limit=10
                )
                
                if recent_memories:
                    # Format memories for LLM consumption
                    formatted_history = []
                    for memory in recent_memories:
                        if "content" in memory and memory["content"]:
                            formatted_history.append({
                                "role": "human", 
                                "content": memory.get("content", "")
                            })
                        if "response" in memory and memory["response"]:
                            formatted_history.append({
                                "role": "ai", 
                                "content": memory.get("response", "")
                            })
                    
                    # Add conversation history to config
                    config["configurable"]["conversation_history"] = formatted_history
                    logger.debug(f"Added {len(formatted_history)} conversation turns from memory")
            except Exception as e:
                logger.warning(f"Error retrieving previous conversation turns: {e}")
            
            # Use memory service to load memory into graph
            result = memory_service.load_memory_to_graph(graph, config, session_id)
            
            return result
        else:
            # Invoke graph directly with standard config
            return graph.invoke({"messages": messages}, config)
    except Exception as e:
        logger.error(f"Error loading memory to graph: {e}")
        # Return basic state with messages
        return {"messages": messages, "error": str(e)}
