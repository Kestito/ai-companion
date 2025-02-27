import os
from uuid import uuid4
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from langchain_core.messages import HumanMessage, RemoveMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from ai_companion.graph.utils.chains import (
    get_character_response_chain,
    get_router_chain,
    get_rag_chain,
)
from ai_companion.graph.utils.helpers import (
    get_chat_model,
    get_text_to_speech_module,
    get_text_to_image_module,
)
from ai_companion.graph.state import AICompanionState
from ai_companion.modules.schedules.context_generation import ScheduleContextGenerator
from ai_companion.settings import settings
from ai_companion.modules.memory.long_term.memory_manager import get_memory_manager
from ai_companion.modules.rag.core.vector_store import get_vector_store_instance

logger = logging.getLogger(__name__)


def get_message_content(message) -> str:
    """Extract content from a message, handling both dict and object formats.
    
    Args:
        message: A message object or dictionary
        
    Returns:
        The content as a string
    """
    if hasattr(message, "content"):
        return message.content
    elif isinstance(message, dict) and "content" in message:
        return message["content"]
    return ""


async def router_node(state: AICompanionState) -> Dict[str, str]:
    """Route the conversation to the appropriate workflow."""
    logger.debug("Starting router node processing")
    try:
        # Get the message content, normalize the case for pattern matching
        last_message = get_message_content(state["messages"][-1]).lower() if state["messages"] else ""
        
        # Enhanced detection of POLA card related questions - handling misspellings
        pola_patterns = [
            r'(?i)pola',                     # Basic mention of POLA
            r'(?i)kort[eė]l[eė]',            # Various spellings of "kortelė"
            r'(?i)v[eė][zž][iy]',            # Various spellings of "vėžys"
            r'(?i)onkolog',                  # Oncology-related terms
            r'(?i)smegen[uų]',               # Brain-related terms
            r'(?i)i[sš]mok[oa]',             # Benefits/payments
            r'(?i)savanor[ií]',              # Volunteer-related terms
        ]
        
        # Check for pattern matches that would trigger RAG node
        if any(re.search(pattern, last_message) for pattern in pola_patterns):
            logger.info(f"Detected POLA-related query: '{last_message[:50]}...'")
            # Route to conversation_node which will then use the RAG system
            return {"workflow": "conversation_node"}
            
        # Use the router chain for other queries
        chain = get_router_chain()
        response = await chain.ainvoke({"messages": last_message})
        workflow = response["text"].strip()
        
        # Map the workflow to the correct node name
        workflow_mapping = {
            "conversation": "conversation_node",
            "image": "image_node",
            "audio": "audio_node"
        }
        
        logger.info(f"Router determined workflow: {workflow}")
        return {"workflow": workflow_mapping.get(workflow, "conversation_node")}
    except Exception as e:
        logger.error(f"Error in router node: {e}", exc_info=True)
        return {"workflow": "conversation_node"}  # Default to conversation node on error


def context_injection_node(state: AICompanionState):
    schedule_context = ScheduleContextGenerator.get_current_activity()
    if schedule_context != state.get("current_activity", ""):
        apply_activity = True
    else:
        apply_activity = False
    return {"apply_activity": apply_activity, "current_activity": schedule_context}


async def conversation_node(state: AICompanionState, config: RunnableConfig):
    """Handle conversation responses with integrated knowledge."""
    logger.debug("Starting conversation node processing")
    try:
        chain = get_character_response_chain()
        chat_history = state["messages"][:-1] if len(state["messages"]) > 1 else []
        current_input = get_message_content(state["messages"][-1]) if state["messages"] else ""
        
        # Get RAG and memory context
        rag_response = state.get("rag_response", {})
        rag_context = rag_response.get("context", "")
        memory_context = state.get("memory_context", "")
        
        # Format contexts
        formatted_context = []
        if rag_context and rag_response.get("response") != "no info":
            formatted_context.append(f"Relevant Knowledge:\n{rag_context}")
        if memory_context:
            formatted_context.append(f"Previous Context:\n{memory_context}")
        
        combined_context = "\n\n".join(formatted_context)
        logger.debug(f"Combined context for conversation: {combined_context}")
        
        # Add context to the response if available
        response = await chain.ainvoke(
            {
                "chat_history": chat_history,
                "input": current_input,
                "current_activity": state.get("current_activity", ""),
                "memory_context": combined_context
            },
            config
        )
        
        response_content = response.content if hasattr(response, 'content') else str(response)
        logger.info(f"Conversation response: {response_content}")
        
        # Store the response in memory
        memory_manager = get_memory_manager()
        await memory_manager.add_memory(response_content)
        
        return {
            "messages": [
                *state["messages"],
                AIMessage(content=response_content)
            ]
        }
    except Exception as e:
        logger.error(f"Error in conversation node: {e}", exc_info=True)
        return {
            "messages": [
                *state["messages"],
                AIMessage(content="Atsiprašau, įvyko klaida. Prašome bandyti vėliau.")
            ]
        }


async def rag_node(state: AICompanionState, config: RunnableConfig) -> Dict[str, Any]:
    """Process the input through enhanced RAG for knowledge-based responses."""
    logger.debug("Starting enhanced RAG node processing")
    try:
        # Initialize RAG chain with test collection
        from ai_companion.modules.rag.core.rag_chain import get_rag_chain
        rag_chain = get_rag_chain(
            model_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            model_name=os.getenv("LLM_MODEL"),
        )
        
        last_message = get_message_content(state["messages"][-1]) if state["messages"] else ""
        memory_context = state.get("memory_context", "")
        start_time = datetime.now()
        
        # Query the RAG chain with enhanced features
        try:
            response, relevant_docs = await rag_chain.query(
                query=last_message,
                memory_context=memory_context,
                max_retries=3,
                min_confidence=0.7
            )
            
            # Format sources with proper error handling
            sources = []
            for doc in relevant_docs:
                try:
                    metadata = doc.metadata or {}
                    sources.append({
                        "title": metadata.get("title", "Be pavadinimo"),
                        "source": metadata.get("source", metadata.get("url", "Nežinomas šaltinis")),
                        "date": metadata.get("processed_at", datetime.now().isoformat()),
                        "confidence": metadata.get("confidence_score", 0.8)
                    })
                except Exception as e:
                    logger.warning(f"Error formatting source metadata: {e}")
                    continue
            
            # Create context with sources
            context = response
            if sources:
                sources_info = "\nŠaltiniai:\n" + "\n".join([
                    f"- {s['source']} (Patikimumas: {s['confidence']:.2f})" 
                    for s in sources
                ])
                context += sources_info
            
            # Calculate metrics
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            # Create metrics
            metrics = {
                "total_queries": 1,
                "successful_queries": 1 if relevant_docs else 0,
                "failed_queries": 0 if relevant_docs else 1,
                "average_confidence": sum(s["confidence"] for s in sources) / len(sources) if sources else 0.0,
                "query_processing_time": total_time * 0.2,
                "retrieval_time": total_time * 0.4,
                "response_generation_time": total_time * 0.4,
                "total_processing_time": total_time,
                "error_details": {},
                "last_updated": end_time.isoformat()
            }
            
            return {
                "rag_response": {
                    "has_relevant_info": len(relevant_docs) > 0,
                    "response": response,
                    "sources": sources,
                    "context": context,
                    "metrics": metrics
                }
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced RAG chain query: {e}")
            error_time = datetime.now()
            return {
                "rag_response": {
                    "has_relevant_info": False,
                    "response": "Atsiprašau, įvyko klaida ieškant informacijos. Prašome bandyti vėliau.",
                    "sources": [],
                    "context": "",
                    "metrics": {
                        "total_queries": 1,
                        "successful_queries": 0,
                        "failed_queries": 1,
                        "average_confidence": 0.0,
                        "query_processing_time": 0.0,
                        "retrieval_time": 0.0,
                        "response_generation_time": 0.0,
                        "total_processing_time": 0.0,
                        "error_details": {"error": str(e)},
                        "last_updated": error_time.isoformat()
                    }
                }
            }
            
    except Exception as e:
        logger.error(f"Critical error in RAG node: {e}", exc_info=True)
        error_time = datetime.now()
        return {
            "rag_response": {
                "has_relevant_info": False,
                "response": "Atsiprašau, įvyko kritinė klaida. Prašome bandyti vėliau.",
                "sources": [],
                "context": "",
                "metrics": {
                    "total_queries": 1,
                    "successful_queries": 0,
                    "failed_queries": 1,
                    "average_confidence": 0.0,
                    "query_processing_time": 0.0,
                    "retrieval_time": 0.0,
                    "response_generation_time": 0.0,
                    "total_processing_time": 0.0,
                    "error_details": {"error": str(e)},
                    "last_updated": error_time.isoformat()
                }
            }
        }


async def web_search_node(state: AICompanionState, config: RunnableConfig):
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")

    chain = get_character_response_chain(state.get("summary", ""))
    
    # Extract last message from the state
    last_message = get_message_content(state["messages"][-1]) if state["messages"] else ""
    # Get previous messages for chat history
    chat_history = state["messages"][:-1] if len(state["messages"]) > 1 else []

    response = await chain.ainvoke(
        {
            "chat_history": chat_history,
            "input": last_message,
            "current_activity": current_activity,
            "memory_context": memory_context,
        },
        config,
    )
    
    # Check if response is already an AIMessage to avoid wrapping an AIMessage inside another AIMessage
    if isinstance(response, AIMessage):
        return {"messages": response}
    else:
        return {"messages": AIMessage(content=response)}


async def image_node(state: AICompanionState, config: RunnableConfig):
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")

    chain = get_character_response_chain(state.get("summary", ""))
    text_to_image_module = get_text_to_image_module()

    scenario = await text_to_image_module.create_scenario(state["messages"][-5:])
    os.makedirs("generated_images", exist_ok=True)
    img_path = f"generated_images/image_{str(uuid4())}.png"
    await text_to_image_module.generate_image(scenario.image_prompt, img_path)

    # Inject the image prompt information as an AI message
    scenario_message = HumanMessage(
        content=f"<image attached by Evelina generated from prompt: {scenario.image_prompt}>"
    )
    updated_messages = state["messages"] + [scenario_message]
    
    # Extract last message from the state including the scenario message
    last_message = updated_messages[-1].content if updated_messages else ""
    # Get previous messages for chat history
    chat_history = updated_messages[:-1] if len(updated_messages) > 1 else []

    response = await chain.ainvoke(
        {
            "chat_history": chat_history,
            "input": last_message,
            "current_activity": current_activity,
            "memory_context": memory_context,
        },
        config,
    )

    # Check if response is already an AIMessage to avoid wrapping an AIMessage inside another AIMessage
    if isinstance(response, AIMessage):
        return {"messages": response, "image_path": img_path}
    else:
        return {"messages": AIMessage(content=response), "image_path": img_path}


async def hallucination_grader_node(state: AICompanionState, config: RunnableConfig):
    """Process responses to check for and reduce hallucinations.
    
    Note: This node is currently not used in the graph structure but is kept for potential future use.
    
    Args:
        state: Current conversation state
        config: Runtime configuration
        
    Returns:
        Updated state with processed messages
    """
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")

    chain = get_character_response_chain(state.get("summary", ""))
    
    # Extract last message from the state
    last_message = get_message_content(state["messages"][-1]) if state["messages"] else ""
    # Get previous messages for chat history
    chat_history = state["messages"][:-1] if len(state["messages"]) > 1 else []

    response = await chain.ainvoke(
        {
            "chat_history": chat_history,
            "input": last_message,
            "current_activity": current_activity,
            "memory_context": memory_context,
        },
        config,
    )
    
    # Check if response is already an AIMessage to avoid wrapping an AIMessage inside another AIMessage
    if isinstance(response, AIMessage):
        return {"messages": response}
    else:
        return {"messages": AIMessage(content=response)}


async def audio_node(state: AICompanionState, config: RunnableConfig):
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")

    chain = get_character_response_chain(state.get("summary", ""))
    text_to_speech_module = get_text_to_speech_module()

    # Extract last message from the state
    last_message = get_message_content(state["messages"][-1]) if state["messages"] else ""
    # Get previous messages for chat history
    chat_history = state["messages"][:-1] if len(state["messages"]) > 1 else []

    response = await chain.ainvoke(
        {
            "chat_history": chat_history,
            "input": last_message,
            "current_activity": current_activity,
            "memory_context": memory_context,
        },
        config,
    )
    
    # Extract text content for speech synthesis
    text_content = response.content if isinstance(response, AIMessage) else response
    output_audio = await text_to_speech_module.synthesize(text_content)

    # Return the response as a message and the audio buffer
    if isinstance(response, AIMessage):
        return {"messages": response, "audio_buffer": output_audio}
    else:
        return {"messages": AIMessage(content=response), "audio_buffer": output_audio}


async def summarize_conversation_node(state: AICompanionState):
    model = get_chat_model()
    summary = state.get("summary", "")

    if summary:
        summary_message = (
            f"This is summary of the conversation to date between Evelina and the user: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
        )
    else:
        summary_message = (
            "Create a summary of the conversation above between Evelina and the user. "
            "The summary must be a short description of the conversation so far, "
            "but that captures all the relevant information shared between Evelina and the user:"
        )

    # Convert messages to the proper format if they're dictionaries
    processed_messages = []
    for msg in state["messages"]:
        if isinstance(msg, dict):
            if msg.get("role") == "user":
                processed_messages.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                processed_messages.append(AIMessage(content=msg.get("content", "")))
            else:
                # For any other role, use the appropriate message type or default to HumanMessage
                processed_messages.append(HumanMessage(content=msg.get("content", "")))
        else:
            processed_messages.append(msg)

    messages = processed_messages + [HumanMessage(content=summary_message)]
    response = await model.ainvoke(messages)

    delete_messages = [
        RemoveMessage(id=m.id) if hasattr(m, "id") else m
        for m in state["messages"][: -settings.TOTAL_MESSAGES_AFTER_SUMMARY]
    ]
    return {"summary": response.content, "messages": delete_messages}


def memory_injection_node(state: AICompanionState) -> Dict[str, str]:
    """Inject relevant memories into the conversation state."""
    logger.debug("Starting memory injection node processing")
    try:
        memory_manager = get_memory_manager()
        last_message = get_message_content(state["messages"][-1]) if state["messages"] else ""
        memory_context = memory_manager.get_relevant_memories(last_message)
        return {"memory_context": memory_manager.format_memories_for_prompt(memory_context)}
    except Exception as e:
        logger.error(f"Error in memory injection: {e}", exc_info=True)
        return {"memory_context": ""}


async def memory_extraction_node(state: AICompanionState) -> Dict[str, Dict]:
    """Extract and format relevant memories for the current context."""
    logger.debug("Starting memory extraction")
    try:
        memory_manager = get_memory_manager()
        
        # Get the current message
        current_message = get_message_content(state["messages"][-1]) if state["messages"] else ""
        
        # Get relevant memories
        relevant_memories = memory_manager.get_relevant_memories(current_message)
        
        # Format memories for context
        formatted_memories = memory_manager.format_memories_for_prompt(relevant_memories)
        
        if formatted_memories:
            logger.info(f"Found relevant memories: {formatted_memories}")
        else:
            logger.debug("No relevant memories found")
            
        # Store the current message as a potential memory
        message_obj = state["messages"][-1]
        message_content = get_message_content(message_obj)
        # Create a proper message object if we got a dict
        if isinstance(message_obj, dict):
            message_obj = HumanMessage(content=message_content)
        await memory_manager.extract_and_store_memories(message_obj)
        
        return {"memory_context": formatted_memories}
    except Exception as e:
        logger.error(f"Error in memory extraction: {e}", exc_info=True)
        return {"memory_context": ""}


async def rag_retry_node(state: AICompanionState, config: RunnableConfig) -> Dict[str, Any]:
    """Retry RAG query with enhanced parameters and different retrieval strategy.
    
    This node is called when the initial RAG query doesn't produce satisfactory results.
    It uses different retrieval parameters and strategies to try to get better results.
    """
    logger.debug("Starting RAG retry node processing")
    try:
        # Get the RAG chain instance
        from ai_companion.modules.rag.core.rag_chain import get_rag_chain
        rag_chain = get_rag_chain()
        
        last_message = get_message_content(state["messages"][-1]) if state["messages"] else ""
        memory_context = state.get("memory_context", "")
        retry_count = state.get("rag_retry_count", 0) + 1
        
        # Adjust retrieval parameters based on retry count
        retrieval_params = {
            "k": 5 + retry_count * 2,  # Increase number of documents
            "min_confidence": max(0.5, 0.7 - retry_count * 0.1),  # Gradually lower similarity threshold
            "max_retries": 3,
        }
        
        try:
            # Query with enhanced parameters
            response, relevant_docs = await rag_chain.query(
                query=last_message,
                memory_context=memory_context,
                **retrieval_params
            )
            logger.info(f"RAG retry response received: {response[:100]}...")
            
            # Get metrics for monitoring
            metrics = rag_chain.get_metrics()
            logger.debug(f"RAG retry metrics: {metrics}")
            
            # Format sources with confidence scores
            sources = []
            for doc in relevant_docs:
                try:
                    metadata = doc.metadata or {}
                    sources.append({
                        "title": metadata.get("title", "Be pavadinimo"),
                        "source": metadata.get("source", metadata.get("url", "Nežinomas šaltinis")),
                        "date": metadata.get("processed_at", "Data nenurodyta"),
                        "confidence": metadata.get("confidence_score", 0.0)
                    })
                except Exception as e:
                    logger.warning(f"Error formatting source metadata in retry: {e}")
                    continue
            
            # Create response with sources and metrics
            sources_info = "\nŠaltiniai:\n" + "\n".join([
                f"- {s['source']} (Patikimumas: {s['confidence']:.2f})" 
                for s in sources
            ]) if sources else ""
            
            # Log retry metrics
            await rag_chain.monitor.log_query(
                query=last_message,
                response=response[:100] + "...",
                success=True,
                retry_count=retry_count,
                response_metadata={
                    "num_sources": len(sources),
                    "avg_confidence": sum(s["confidence"] for s in sources) / len(sources) if sources else 0
                }
            )
            
            return {
                "rag_response": {
                    "has_relevant_info": len(relevant_docs) > 0,
                    "response": response,
                    "sources": sources,
                    "context": response + sources_info,
                    "metrics": metrics
                },
                "rag_retry_count": retry_count
            }
            
        except Exception as e:
            logger.error(f"Error in RAG retry node query: {e}", exc_info=True)
            await rag_chain.monitor.log_error(
                "rag_retry_error",
                last_message,
                str(e)
            )
            return {
                "rag_response": {
                    "has_relevant_info": False,
                    "response": "Atsiprašau, įvyko klaida bandant rasti tikslesnę informaciją. Prašome bandyti vėliau.",
                    "sources": [],
                    "context": "",
                    "metrics": rag_chain.get_metrics()
                },
                "rag_retry_count": retry_count
            }
            
    except Exception as e:
        logger.error(f"Critical error in RAG retry node: {e}", exc_info=True)
        return {
            "rag_response": {
                "has_relevant_info": False,
                "response": "Atsiprašau, įvyko kritinė klaida. Prašome bandyti vėliau.",
                "sources": [],
                "context": "",
                "metrics": {}
            },
            "rag_retry_count": state.get("rag_retry_count", 0) + 1
        }
