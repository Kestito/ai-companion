from ai_companion.graph.state import AICompanionState
from ai_companion.settings import settings
from ai_companion.utils.logging import get_logger

from langgraph.graph import END
from typing_extensions import Literal
from typing import Dict, Union

logger = get_logger(__name__)

def should_summarize_conversation(
    state: AICompanionState,
) -> Union[Literal["summarize_conversation_node"], str]:
    """Determine if conversation should be summarized based on message count.
    
    Args:
        state: Current state containing messages
        
    Returns:
        Next node to route to
    """
    messages = state.get("messages", [])
    
    # Check if messages is a list and has enough messages
    if isinstance(messages, list) and len(messages) > settings.TOTAL_MESSAGES_SUMMARY_TRIGGER:
        logger.debug("Returning 'summarize_conversation_node'")
        return "summarize_conversation_node"
    
    logger.debug(f"Returning END constant: {END}")
    return END


def select_workflow(
    state: AICompanionState,
) -> Literal["conversation_node", "image_node", "audio_node", "patient_registration_node", "schedule_message_node"]:
    """Select the appropriate workflow based on router's decision.
    
    Args:
        state: Current state containing workflow decision
        
    Returns:
        The appropriate node to route to
    """
    workflow = state.get("workflow", "conversation")  # Default to conversation if not set
    
    # Handle patient registration workflow
    if workflow == "patient_registration_node":
        return "patient_registration_node"
        
    # Handle schedule message workflow
    if workflow == "schedule_message_node":
        return "schedule_message_node"
    
    # Ensure we have RAG information
    if "rag_response" not in state:
        return "conversation_node"

    if workflow == "image":
        return "image_node"
    elif workflow == "audio":
        return "audio_node"
    else:  # Default to conversation for any other value
        return "conversation_node"


def merge_parallel_results(state: AICompanionState, result: dict) -> dict:
    """Merge results from parallel processing branches.
    
    Args:
        state: Current state
        result: Result from parallel branch
        
    Returns:
        Updated state dictionary
    """
    # Initialize merged state if not exists
    if "merged_results" not in state:
        state["merged_results"] = {}
    
    # Merge new results
    state["merged_results"].update(result)
    
    # Check if we have all required results
    required_keys = {"rag_response", "memory_context"}
    if required_keys.issubset(state["merged_results"].keys()):
        # Get RAG and memory information
        rag_info = state["merged_results"].get("rag_response", {})
        memory_info = state["merged_results"].get("memory_context", "")
        
        # Create combined state update
        combined_update = {
            "rag_response": rag_info,
            "memory_context": memory_info,
            "has_knowledge": bool(rag_info.get("has_relevant_info", False))
        }
        
        # Clear merged results
        state.pop("merged_results")
        
        return combined_update
    
    return {}


def should_retry_rag(state: Dict) -> str:
    """Determine if RAG query should be retried based on response quality and retry count.
    
    Args:
        state: The current state dictionary
        
    Returns:
        str: The next node to route to ("rag_retry_node" or "memory_injection_node")
    """
    rag_response = state.get("rag_response", {})
    metrics = rag_response.get("metrics", {})
    retry_count = state.get("rag_retry_count", 0)
    MAX_RAG_RETRIES = 3
    # Check if we should retry based on various conditions
    should_retry = (
        # Don't exceed max retries
        retry_count < MAX_RAG_RETRIES and
        (
            # No relevant info found
            not rag_response.get("has_relevant_info") or
            # Low preprocessing success rate
            metrics.get("preprocessing_success_rate", 1.0) < 0.7 or
            # Low average confidence in sources
            (
                len(rag_response.get("sources", [])) > 0 and
                sum(s.get("confidence", 0) for s in rag_response["sources"]) / len(rag_response["sources"]) < 0.6
            )
        )
    )
    
    if should_retry:
        return "rag_retry_node"
    return "memory_injection_node"
