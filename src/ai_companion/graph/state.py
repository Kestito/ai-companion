from typing import Dict, List, Optional, TypedDict, Any, Union
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langgraph.graph import MessagesState


class AICompanionState(TypedDict, total=False):
    """State type for the AI companion workflow.
    
    Attributes:
        messages: List of conversation messages
        workflow: Current workflow type
        summary: Conversation summary
        memory_context: Context from memory
        current_activity: Current activity context
        medical_knowledge: Medical knowledge from RAG
        rag_response: RAG system response
        image_path: Path to generated image
    """
    
    messages: List[Union[BaseMessage, AIMessage, HumanMessage]]
    workflow: str
    summary: str
    memory_context: str
    current_activity: str
    medical_knowledge: str
    rag_response: Dict[str, Any]
    image_path: str
