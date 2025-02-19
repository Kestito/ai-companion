from ai_companion.graph.state import AICompanionState
from ai_companion.settings import settings

from langgraph.graph import END
from typing_extensions import Literal


def should_summarize_conversation(
    state: AICompanionState,
) -> Literal["summarize_conversation_node", "__end__"]:
    """Determine if conversation should be summarized based on message count.
    
    Args:
        state: Current state containing messages
        
    Returns:
        Next node to route to
    """
    messages = state.get("messages", [])
    
    # Check if messages is a list and has enough messages
    if isinstance(messages, list) and len(messages) > settings.TOTAL_MESSAGES_SUMMARY_TRIGGER:
        return "summarize_conversation_node"
    
    return END


def select_workflow(
    state: AICompanionState,
) -> Literal["conversation_node", "image_node", "audio_node"]:
    """Select the appropriate workflow based on router's decision.
    
    Args:
        state: Current state containing workflow decision
        
    Returns:
        The appropriate node to route to
    """
    workflow = state.get("workflow", "conversation")  # Default to conversation if not set
    
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
