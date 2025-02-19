from functools import lru_cache
from typing import Dict, List, Optional, Tuple, TypedDict, Annotated, Any, Callable

from langgraph.graph import END, START, StateGraph

from ai_companion.graph.edges import (
    select_workflow,
    should_summarize_conversation,
    merge_parallel_results,
)
from ai_companion.graph.nodes import (
    audio_node,
    conversation_node,
    image_node,
    router_node,
    summarize_conversation_node,
    context_injection_node,
    memory_extraction_node,
    memory_injection_node,
    hallucination_grader_node,
    web_search_node,
    rag_node,
)
from ai_companion.graph.state import AICompanionState


def create_merge_edge(node: str) -> Callable[[Dict], Dict]:
    """Create a merge edge function for a specific node.
    
    Args:
        node: The node name
        
    Returns:
        A function that merges the results
    """
    def merge_edge(state: Dict) -> Dict:
        # Get the result from the node
        result = state.get(node, {})
        # Merge it using our merge function
        return merge_parallel_results(state, result)
    return merge_edge


@lru_cache(maxsize=1)
def create_workflow_graph() -> StateGraph:
    """Create the main workflow graph for the AI companion.
    
    Returns:
        StateGraph: The compiled workflow graph
    """
    # Initialize graph with state type
    graph_builder = StateGraph(AICompanionState)

    # Add all nodes
    graph_builder.add_node("memory_extraction_node", memory_extraction_node)
    graph_builder.add_node("router_node", router_node)
    graph_builder.add_node("rag_node", rag_node)
    graph_builder.add_node("memory_injection_node", memory_injection_node)
    graph_builder.add_node("conversation_node", conversation_node)
    graph_builder.add_node("image_node", image_node)
    graph_builder.add_node("audio_node", audio_node)
    graph_builder.add_node("summarize_conversation_node", summarize_conversation_node)

    # Set up the graph flow
    # 1. Start with memory extraction
    graph_builder.add_edge(START, "memory_extraction_node")

    # 2. Route to router node
    graph_builder.add_edge("memory_extraction_node", "router_node")

    # 3. Always use RAG for knowledge gathering before any response
    graph_builder.add_edge("router_node", "rag_node")
    
    # 4. Inject memory after RAG
    graph_builder.add_edge("rag_node", "memory_injection_node")

    # 5. Route to appropriate response node based on workflow
    graph_builder.add_conditional_edges(
        "memory_injection_node",
        select_workflow,
        {
            "conversation_node": "conversation_node",
            "image_node": "image_node",
            "audio_node": "audio_node"
        }
    )

    # 6. Check for summarization from each response node
    for node in ["conversation_node", "image_node", "audio_node"]:
        graph_builder.add_conditional_edges(
            node,
            should_summarize_conversation,
            {
                "summarize_conversation_node": "summarize_conversation_node",
                END: END
            }
        )

    graph_builder.add_edge("summarize_conversation_node", END)

    return graph_builder.compile()


# Create the graph instance
graph = create_workflow_graph()
