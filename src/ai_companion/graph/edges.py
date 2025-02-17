from ai_companion.graph.state import AICompanionState
from ai_companion.settings import settings

from langgraph.graph import END
from typing_extensions import Literal


def should_summarize_conversation(
    state: AICompanionState,
) -> Literal["summarize_conversation_node", "__end__"]:
    messages = state["messages"]

    if len(messages) > settings.TOTAL_MESSAGES_SUMMARY_TRIGGER:
        return "summarize_conversation_node"

    return END


def select_workflow(
    state: AICompanionState,
) -> Literal["conversation_node", "image_node", "audio_node", "rag_node"]:
    workflow = state["workflow"]

    if workflow == "image":
        return "image_node"
    elif workflow == "audio":
        return "audio_node"
    elif workflow == "rag":
        return "rag_node"
    else:
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
    required_keys = {"rag_response", "context"}
    if required_keys.issubset(state["merged_results"].keys()):
        # Combine RAG and context information
        rag_info = state["merged_results"].get("rag_response", {})
        context_info = state["merged_results"].get("context", {})
        
        # Create combined state update
        combined_update = {
            "medical_knowledge": rag_info.get("medical_knowledge", ""),
            "current_activity": context_info.get("current_activity", ""),
            "apply_activity": context_info.get("apply_activity", False)
        }
        
        # Clear merged results
        state.pop("merged_results")
        
        return combined_update
    
    return {}
