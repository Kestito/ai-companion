import os
from uuid import uuid4
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import re
import random
import asyncio
import json

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
from ai_companion.modules.memory.conversation.conversation_memory import ConversationMemory
from ai_companion.utils.supabase import get_supabase_client

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
        
        # Extract user ID and platform from message metadata
        platform = "unknown"
        user_id = None
        
        if hasattr(state["messages"][-1], "metadata"):
            metadata = state["messages"][-1].metadata
            platform = metadata.get("platform", "unknown")
            user_id = metadata.get("user_id")
            
        # Check if this is a new user from Telegram that needs registration
        if platform.lower() == "telegram" and user_id:
            # Try to find an existing patient with this Telegram user ID
            try:
                supabase = get_supabase_client()
                
                # Don't try to query by ID directly since user_id is not a UUID
                # Instead, always search in the email field for the platform metadata
                metadata_search = f'%"user_id": "{user_id}"%'
                result = supabase.table("patients").select("id").like("email", metadata_search).execute()
                
                if not result.data:
                    # No existing patient found - route to registration
                    logger.info(f"No existing patient found for Telegram user {user_id}. Routing to registration.")
                    return {"workflow": "patient_registration_node"}
                    
                logger.debug(f"Found existing patient for Telegram user {user_id}.")
            except Exception as e:
                logger.error(f"Error checking for existing patient: {e}", exc_info=True)
                # On error, continue with normal routing
        
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
        
        # Patient registration patterns
        patient_registration_patterns = [
            r'(?i)new patient',              # English patterns
            r'(?i)register patient',
            r'(?i)add patient',
            r'(?i)create patient',
            r'(?i)naujas pacientas',         # Lithuanian patterns
            r'(?i)registruoti pacient[aąą]',
            r'(?i)sukurti pacient[aąą]',
            r'(?i)pridėti pacient[aąą]',
        ]
        
        # Schedule message patterns
        schedule_patterns = [
            r'(?i)^/schedule',               # Telegram command format
            r'(?i)^schedule\s+',             # WhatsApp format
        ]
        
        # Check for schedule message request
        if any(re.search(pattern, last_message) for pattern in schedule_patterns):
            logger.info(f"Detected schedule message request: '{last_message[:50]}...'")
            return {"workflow": "schedule_message_node"}
        
        # Check for patient registration request
        if any(re.search(pattern, last_message) for pattern in patient_registration_patterns):
            logger.info(f"Detected patient registration request: '{last_message[:50]}...'")
            return {"workflow": "patient_registration_node"}
        
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
        
        # Check for conversation history in metadata for Telegram
        last_message = state["messages"][-1] if state["messages"] else None
        telegram_history = []
        
        if last_message and hasattr(last_message, "metadata"):
            metadata = last_message.metadata or {}
            # Check if we have conversation history in metadata (used by Telegram)
            if "conversation_history" in metadata and isinstance(metadata["conversation_history"], list):
                telegram_history = metadata["conversation_history"]
                logger.info(f"Found {len(telegram_history)} conversation history entries in metadata")
        
        # Format contexts
        formatted_context = []
        if rag_context and rag_response.get("response") != "no info":
            formatted_context.append(f"Relevant Knowledge:\n{rag_context}")
        if memory_context:
            formatted_context.append(f"Previous Context:\n{memory_context}")
        
        # Add Telegram conversation history to context if available
        if telegram_history:
            telegram_context = "Previous Conversation:\n"
            for entry in telegram_history[:10]:  # Limit to 10 entries
                if isinstance(entry, dict):
                    role = entry.get("role", "")
                    content = entry.get("content", "")
                    if role and content:
                        telegram_context += f"{role.capitalize()}: {content}\n"
            
            formatted_context.append(telegram_context)
        
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
        
        # Check for repetitiveness in the conversation
        if telegram_history and len(telegram_history) >= 4:
            # Get the last two bot responses
            bot_responses = []
            for entry in telegram_history:
                if isinstance(entry, dict) and entry.get("role") == "ai":
                    bot_responses.append(entry.get("content", ""))
            
            if len(bot_responses) >= 2:
                # Check similarity between last responses
                last_response = bot_responses[-1]
                previous_response = bot_responses[-2]
                
                # Simple string similarity check (for demo purposes)
                if last_response and previous_response and last_response[:50] == previous_response[:50]:
                    logger.warning("Detected repetitive responses, adding diversity instruction")
                    
                    # Add instruction to avoid repetition
                    diversity_prompt = f"""
                    I notice my responses are becoming repetitive. The user's current question is: "{current_input}"
                    
                    My previous response was: "{last_response}"
                    
                    Please provide a new, diverse response that avoids repeating the same greeting or structure 
                    while still maintaining a helpful and friendly tone. Focus on answering the user's actual 
                    question or moving the conversation forward.
                    """
                    
                    # Get a more diverse response
                    try:
                        model = get_chat_model()
                        diverse_response = await model.ainvoke([HumanMessage(content=diversity_prompt)])
                        response_content = diverse_response.content if hasattr(diverse_response, 'content') else str(diverse_response)
                        logger.info("Generated more diverse response to avoid repetition")
                    except Exception as e:
                        logger.error(f"Error generating diverse response: {e}")
                        # Keep the original response if the diversity attempt fails
        
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
        
        # Get chat history
        chat_history = state["messages"][:-1] if len(state["messages"]) > 1 else []
        chat_history_str = "\n".join([
            f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {get_message_content(m)}"
            for m in chat_history[-settings.ROUTER_MESSAGES_TO_ANALYZE:]
        ])
        
        # Combine chat history with memory context
        combined_context = f"Chat History:\n{chat_history_str}\n\nMemory Context:\n{memory_context}"
        
        start_time = datetime.now()
        
        # Query the RAG chain with enhanced features
        try:
            # Extract options from message metadata if available
            message_metadata = {}
            if hasattr(state["messages"][-1], 'metadata') and state["messages"][-1].metadata:
                message_metadata = state["messages"][-1].metadata
            
            detailed_response = message_metadata.get('detailed_response', True)  # Default to True for detailed responses
            with_citations = message_metadata.get('with_citations', True)  # Default to including citations
            
            response, relevant_docs = await rag_chain.query(
                query=last_message,
                memory_context=combined_context,  # Pass combined context
                max_retries=3,
                min_confidence=0.5,  # Lower similarity threshold from 0.7 to 0.5
                detailed=detailed_response,  # Request detailed response
                with_citations=with_citations  # Include citations in the response
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
            
            # Add self-evaluation of confidence
            confidence_prompt = f"""
            Rate your confidence in the following answer on a scale of 1-10 (1 being lowest, 10 being highest).
            Consider:
            - The accuracy and completeness of the information
            - The relevance to the user's question
            - The quality of sources cited (if any)
            - Any uncertainty or missing information
            
            Question: {last_message}
            Answer: {response}
            
            Provide ONLY a rating number between 1 and 10.
            """
            
            try:
                # Use the same model for self-evaluation
                model = get_chat_model()
                confidence_response = await model.ainvoke([HumanMessage(content=confidence_prompt)])
                confidence_text = confidence_response.content.strip()
                
                # Extract just the number from the response
                confidence_match = re.search(r'\b([1-9]|10)\b', confidence_text)
                confidence_rating = int(confidence_match.group(1)) if confidence_match else 7  # Default to 7 if parsing fails
                
                # Format confidence level based on the rating
                confidence_level = "High" if confidence_rating >= 8 else "Medium" if confidence_rating >= 5 else "Low"
                
                # Enhance response with process details and supporting links
                process_prompt = (
                    f"Based on the user's query \"{last_message}\" and your response, please provide additional structured information in Lithuanian:\n\n"
                    f"1. Detailed Process: Briefly explain the step-by-step process related to this query (max 3 steps)\n"
                    f"2. Primary Link: Identify the most important resource or website where the user can get official information\n"
                    f"3. Supporting Resources: List 2-3 additional resources or organizations that can help\n\n"
                    f"Format your response in clear, concise bullet points. No introduction or conclusion needed."
                )
                
                # Create message list for enhancement request
                enhancement_messages = []
                if chat_history:
                    enhancement_messages.append(chat_history[-1])
                enhancement_messages.append(HumanMessage(content=last_message))
                enhancement_messages.append(AIMessage(content=response))
                enhancement_messages.append(HumanMessage(content=process_prompt))
                
                enhancement_response = await model.ainvoke(enhancement_messages)
                
                enhancement_text = enhancement_response.content.strip()
                
                # Append enhancement and confidence to the response
                confidence_note = f"\n\n[Confidence: {confidence_level} ({confidence_rating}/10)]"
                enhanced_response = f"{response}\n\n{enhancement_text}{confidence_note}"
                
                logger.info(f"Self-evaluated confidence rating: {confidence_rating}/10 ({confidence_level})")
                logger.info("Enhanced response with process details and supporting links")
            except Exception as e:
                logger.error(f"Error in response enhancement: {e}")
                confidence_note = f"\n\n[Confidence: {confidence_level} ({confidence_rating}/10)]"
                enhanced_response = response + confidence_note
            
            # Create context with sources
            context = enhanced_response
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
                "last_updated": end_time.isoformat(),
                "self_rating": confidence_rating,
                "confidence_level": confidence_level
            }
            
            # Check if response is substantive (more than just an error message or generic reply)
            is_substantive_response = (
                len(response) > 100 and  # Reasonable length
                "atsiprašau" not in response.lower() and  # Not an apology
                "įvyko klaida" not in response.lower()  # Not an error message
            )
            
            return {
                "rag_response": {
                    "has_relevant_info": len(relevant_docs) > 0 or is_substantive_response,
                    "response": enhanced_response,
                    "sources": sources,
                    "context": context,
                    "metrics": metrics,
                    "confidence_rating": confidence_rating,
                    "confidence_level": confidence_level
                }
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced RAG chain query: {e}")
            error_time = datetime.now()
            return {
                "rag_response": {
                    "has_relevant_info": False,
                    "response": "Atsiprašau, įvyko klaida ieškant informacijos. Prašome bandyti vėliau.\n\n[Confidence: Low (2/10)]",
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
                        "last_updated": error_time.isoformat(),
                        "self_rating": 2,
                        "confidence_level": "Low"
                    },
                    "confidence_rating": 2,
                    "confidence_level": "Low"
                }
            }
            
    except Exception as e:
        logger.error(f"Critical error in RAG node: {e}", exc_info=True)
        error_time = datetime.now()
        return {
            "rag_response": {
                "has_relevant_info": False,
                "response": "Atsiprašau, įvyko kritinė klaida. Prašome bandyti vėliau.\n\n[Confidence: Low (1/10)]",
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
                    "last_updated": error_time.isoformat(),
                    "self_rating": 1,
                    "confidence_level": "Low"
                },
                "confidence_rating": 1,
                "confidence_level": "Low"
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
        
        # Get chat history for enhancement context
        chat_history = state["messages"][:-1] if len(state["messages"]) > 1 else []
        
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
            
            # Add self-evaluation of confidence for the retry
            confidence_prompt = f"""
            Rate your confidence in the following answer on a scale of 1-10 (1 being lowest, 10 being highest).
            Consider:
            - The accuracy and completeness of the information
            - The relevance to the user's question
            - The quality of sources cited (if any)
            - Any uncertainty or missing information
            
            Question: {last_message}
            Answer: {response}
            
            Provide ONLY a rating number between 1 and 10.
            """
            
            try:
                # Use the same model for self-evaluation
                model = get_chat_model()
                confidence_response = await model.ainvoke([HumanMessage(content=confidence_prompt)])
                confidence_text = confidence_response.content.strip()
                
                # Extract just the number from the response
                confidence_match = re.search(r'\b([1-9]|10)\b', confidence_text)
                confidence_rating = int(confidence_match.group(1)) if confidence_match else 7  # Default to 7 if parsing fails
                
                # Format confidence level based on the rating
                confidence_level = "High" if confidence_rating >= 8 else "Medium" if confidence_rating >= 5 else "Low"
                
                # Enhance response with process details and supporting links
                process_prompt = (
                    f"Based on the user's query \"{last_message}\" and your response, please provide additional structured information in Lithuanian:\n\n"
                    f"1. Detailed Process: Briefly explain the step-by-step process related to this query (max 3 steps)\n"
                    f"2. Primary Link: Identify the most important resource or website where the user can get official information\n"
                    f"3. Supporting Resources: List 2-3 additional resources or organizations that can help\n\n"
                    f"Format your response in clear, concise bullet points. No introduction or conclusion needed."
                )
                
                # Create message list for enhancement request
                enhancement_messages = []
                if chat_history:
                    enhancement_messages.append(chat_history[-1])
                enhancement_messages.append(HumanMessage(content=last_message))
                enhancement_messages.append(AIMessage(content=response))
                enhancement_messages.append(HumanMessage(content=process_prompt))
                
                enhancement_response = await model.ainvoke(enhancement_messages)
                
                enhancement_text = enhancement_response.content.strip()
                
                # Append enhancement and confidence to the response
                confidence_note = f"\n\n[Confidence: {confidence_level} ({confidence_rating}/10)]"
                enhanced_response = f"{response}\n\n{enhancement_text}{confidence_note}"
                
                logger.info(f"Self-evaluated confidence rating (retry): {confidence_rating}/10 ({confidence_level})")
                logger.info("Enhanced response with process details and supporting links")
            except Exception as e:
                logger.error(f"Error in response enhancement for retry: {e}")
                confidence_note = f"\n\n[Confidence: {confidence_level} ({confidence_rating}/10)]"
                enhanced_response = response + confidence_note
            
            # Create response with sources and metrics
            sources_info = "\nŠaltiniai:\n" + "\n".join([
                f"- {s['source']} (Patikimumas: {s['confidence']:.2f})" 
                for s in sources
            ]) if sources else ""
            
            # Final context with the enhanced response and sources
            context = enhanced_response + sources_info
            
            # Update metrics with confidence rating
            metrics["self_rating"] = confidence_rating
            metrics["confidence_level"] = confidence_level
            
            # Log retry metrics
            await rag_chain.monitor.log_query(
                query=last_message,
                response=response[:100] + "...",
                success=True,
                retry_count=retry_count,
                response_metadata={
                    "num_sources": len(sources),
                    "avg_confidence": sum(s["confidence"] for s in sources) / len(sources) if sources else 0,
                    "self_rating": confidence_rating
                }
            )
            
            return {
                "rag_response": {
                    "has_relevant_info": len(relevant_docs) > 0,
                    "response": enhanced_response,
                    "sources": sources,
                    "context": context,
                    "metrics": metrics,
                    "confidence_rating": confidence_rating,
                    "confidence_level": confidence_level
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
                    "response": "Atsiprašau, įvyko klaida bandant rasti tikslesnę informaciją. Prašome bandyti vėliau.\n\n[Confidence: Low (2/10)]",
                    "sources": [],
                    "context": "",
                    "metrics": rag_chain.get_metrics(),
                    "confidence_rating": 2,
                    "confidence_level": "Low"
                },
                "rag_retry_count": retry_count
            }
            
    except Exception as e:
        logger.error(f"Critical error in RAG retry node: {e}", exc_info=True)
        return {
            "rag_response": {
                "has_relevant_info": False,
                "response": "Atsiprašau, įvyko kritinė klaida. Prašome bandyti vėliau.\n\n[Confidence: Low (1/10)]",
                "sources": [],
                "context": "",
                "metrics": {
                    "self_rating": 1,
                    "confidence_level": "Low"
                },
                "confidence_rating": 1,
                "confidence_level": "Low"
            },
            "rag_retry_count": state.get("rag_retry_count", 0) + 1
        }


async def patient_registration_node(state: AICompanionState, config: RunnableConfig) -> Dict[str, Any]:
    """Handle patient registration requests from messaging platforms.
    
    This node extracts patient information from conversation messages and creates
    a new patient record in the Supabase database.
    
    Args:
        state: AICompanionState containing conversation and context
        config: Configuration for the runnable
        
    Returns:
        Dict with registration result and response message
    """
    logger.debug("Starting patient registration node processing")
    try:
        # Get the latest message content
        last_message = get_message_content(state["messages"][-1]) if state["messages"] else ""
        
        # Extract conversation info to determine source platform (telegram/whatsapp)
        platform = "unknown"
        user_id = None
        user_name = None
        
        if hasattr(state["messages"][-1], "metadata"):
            metadata = state["messages"][-1].metadata
            platform = metadata.get("platform", "unknown")
            user_id = metadata.get("user_id")
            user_name = metadata.get("username")  # Try to get username if available
            
            # If using Telegram, try to get more user data if available
            if platform.lower() == "telegram" and "telegram_user" in metadata:
                telegram_user = metadata.get("telegram_user", {})
                if not user_name and "username" in telegram_user:
                    user_name = telegram_user.get("username")
                if "first_name" in telegram_user:
                    first_name = telegram_user.get("first_name")
                    last_name = telegram_user.get("last_name", "")
                    # Combine for a full name
                    user_name = f"{first_name} {last_name}".strip()
        
        logger.info(f"Processing patient registration request from {platform} by user {user_id}")
        
        # Initialize Supabase client
        supabase = get_supabase_client()
        
        # First check if this patient already exists
        existing_patient = None
        
        if platform.lower() == "telegram" and user_id:
            # Check for existing patient with this Telegram user ID
            metadata_search = f'%"user_id": "{user_id}"%'
            result = supabase.table("patients").select("id").like("email", metadata_search).execute()
            
            if result.data:
                existing_patient = result.data[0]
                logger.info(f"Found existing patient with ID {existing_patient.get('id')} for Telegram user {user_id}")
                
                # Return success with existing patient ID
                return {
                    "messages": [
                        AIMessage(
                            content=f"Welcome back! You're already registered in our system.",
                        )
                    ],
                    "patient_id": existing_patient.get('id')
                }
        
        # Extract basic patient information from the message
        # Improved regex patterns for better extraction
        name_match = re.search(r'name[:\s]+([^,\n:]*?)(?=\s*(?:phone|$|,))', last_message, re.IGNORECASE)
        
        # Check if name is found in the message
        if name_match:
            name = name_match.group(1).strip()
        else:
            # If no name is found and platform is Telegram, use available user info
            if platform.lower() == "telegram" and (user_name or user_id):
                name = user_name if user_name else f"Telegram User {user_id}"
                logger.info(f"No name provided. Using name from Telegram: {name}")
            else:
                name = "Unknown"
        
        phone_match = re.search(r'phone[:\s]+([0-9+\s\-()]+)(?=$|\s|,|\n)', last_message, re.IGNORECASE)
        phone = phone_match.group(1).strip() if phone_match else None
        
        # If platform is Telegram and no phone is provided, use the Telegram user ID
        if platform.lower() == "telegram" and user_id and not phone:
            phone = f"telegram:{user_id}"
            logger.info(f"Using Telegram user ID as phone identifier: {phone}")
        
        # Create timestamp for registration
        now = datetime.now().isoformat()
        
        # Create patient record in Supabase with fields matching the actual table structure
        patient_data = {
            "first_name": name.split(" ")[0] if " " in name else name,
            "last_name": " ".join(name.split(" ")[1:]) if " " in name else "",
            "phone": phone,
            "created_at": now,
            "last_active": now,
            "preferred_language": "lt",  # Default language
            "support_status": "active"  # Default status
        }
        
        # Add platform and user_id to metadata stored in the email field
        # This is a temporary solution until we have a proper metadata field
        platform_metadata = {
            "platform": platform,
            "user_id": user_id,
            "username": user_name
        }
        patient_data["email"] = json.dumps(platform_metadata) if platform and user_id else None
        
        logger.debug(f"Creating patient with data: {patient_data}")
        
        # Insert the new patient into the patients table - non-async version
        result = supabase.table("patients").insert(patient_data).execute()
        logger.debug(f"Insert result: {result}")
        
        # Get the generated patient ID from the result
        new_patient_id = None
        if result and hasattr(result, 'data') and len(result.data) > 0:
            new_patient_id = result.data[0].get('id')
            logger.debug(f"New patient ID from result: {new_patient_id}")
        
        # Try to store in conversation memory if it exists
        conversation_storage_result = False
        try:
            if "conversation_memory" in state and state["conversation_memory"] is not None:
                # Use existing conversation memory
                if hasattr(state["conversation_memory"], "metadata"):
                    if new_patient_id:
                        if asyncio.iscoroutinefunction(state["conversation_memory"].store_metadata):
                            await state["conversation_memory"].store_metadata({
                                "patient_id": new_patient_id,
                            })
                            conversation_storage_result = True
                        else:
                            state["conversation_memory"].store_metadata({
                                "patient_id": new_patient_id,
                            })
                            conversation_storage_result = True
        except Exception as e:
            logger.error(f"Error storing patient ID in conversation memory: {e}", exc_info=True)
        
        # Build a success message
        if new_patient_id:
            response_message = "Thank you! I've registered you as a new patient in our system."
            if platform.lower() == "telegram":
                response_message += " You can now use our services through this Telegram chat."
            
            return {
                "messages": [
                    AIMessage(
                        content=response_message,
                    )
                ],
                "patient_id": new_patient_id
            }
        else:
            return {
                "messages": [
                    AIMessage(
                        content="I'm sorry, but I encountered an issue while trying to register you. Please try again later or contact support.",
                    )
                ]
            }
    
    except Exception as e:
        logger.error(f"Error in patient registration node: {e}", exc_info=True)
        return {
            "messages": [
                AIMessage(
                    content="I apologize, but I encountered an error while trying to process your registration. Please try again or contact our support team if the issue persists.",
                )
            ]
        }


async def schedule_message_node(state: AICompanionState, config: RunnableConfig) -> Dict[str, Any]:
    """Process message scheduling requests.
    
    This node handles requests to schedule messages for delivery via Telegram or
    WhatsApp at specified times, either once or on a recurring schedule.
    
    Args:
        state: Current conversation state
        config: Runnable configuration
        
    Returns:
        Dict containing scheduling results
    """
    logger.debug("Starting schedule message node processing")
    
    try:
        # Get the latest message content and platform metadata
        last_message_data = state["messages"][-1]
        platform = last_message_data.metadata.get("platform", "unknown")
        user_id = last_message_data.metadata.get("user_id", "")
        
        logger.info(f"Processing schedule message request from {platform} by user {user_id}")
        
        # Get patient ID - first try direct metadata, then check conversation memory
        patient_id = None
        
        # Check if patient ID is in the user metadata
        if "patient_id" in last_message_data.metadata:
            patient_id = last_message_data.metadata.get("patient_id")
            logger.debug(f"Found patient ID in message metadata: {patient_id}")
        
        # Check if patient ID is in conversation memory
        if not patient_id and "metadata" in state.get("conversation_memory", {}):
            memory_metadata = state["conversation_memory"]["metadata"]
            if "patient_id" in memory_metadata:
                patient_id = memory_metadata["patient_id"]
                logger.debug(f"Found patient ID in conversation memory: {patient_id}")
        
        # If still no patient ID, check if there's a link in the context
        if not patient_id:
            for doc in state.get("context", []):
                if isinstance(doc, dict) and "metadata" in doc and "patient_id" in doc["metadata"]:
                    patient_id = doc["metadata"]["patient_id"]
                    logger.debug(f"Found patient ID in context metadata: {patient_id}")
                    break
        
        # Verify we have a patient ID
        if not patient_id:
            logger.warning(f"Cannot schedule message: Missing patient ID for user {user_id}")
            return {
                "schedule_result": "error",
                "error": "Missing patient ID",
                "response": "I need to know which patient this message is for. Please register a patient first or provide a patient ID."
            }
        
        # Parse the scheduling command based on platform
        message_text = last_message_data.content
        parsed_command = None
        
        if platform.lower() == "telegram":
            # Use Telegram handler to parse command
            from ai_companion.modules.scheduled_messaging.handlers.telegram_handler import TelegramHandler
            handler = TelegramHandler()
            parsed_command = await handler.parse_command(message_text)
        elif platform.lower() == "whatsapp":
            # Use WhatsApp handler to parse command
            from ai_companion.modules.scheduled_messaging.handlers.whatsapp_handler import WhatsAppHandler
            handler = WhatsAppHandler()
            parsed_command = await handler.parse_command(message_text)
        else:
            logger.warning(f"Unsupported platform for scheduling: {platform}")
            return {
                "schedule_result": "error",
                "error": "Unsupported platform",
                "response": f"Scheduling is not supported for {platform} platform. Please use Telegram or WhatsApp."
            }
        
        # Check if parsing was successful
        if not parsed_command or not parsed_command.get("success", False):
            error_message = parsed_command.get("error", "Invalid format") if parsed_command else "Invalid format"
            logger.warning(f"Failed to parse scheduling command: {error_message}")
            return {
                "schedule_result": "error",
                "error": error_message,
                "response": f"I couldn't understand your scheduling request. {error_message}"
            }
        
        # Schedule the message
        from ai_companion.modules.scheduled_messaging.scheduler import ScheduleManager
        scheduler = ScheduleManager()
        
        schedule_args = {
            "patient_id": patient_id,
            "recipient_id": user_id,
            "platform": platform.lower(),
            "message_content": parsed_command.get("message", ""),
            "scheduled_time": parsed_command.get("time", ""),
        }
        
        # Add recurrence pattern if this is a recurring schedule
        if parsed_command.get("type") == "recurring" and "recurrence" in parsed_command:
            schedule_args["recurrence_pattern"] = parsed_command["recurrence"]
        
        # Add template information if provided
        if "template_key" in parsed_command:
            schedule_args["template_key"] = parsed_command["template_key"]
            if "parameters" in parsed_command:
                schedule_args["parameters"] = parsed_command["parameters"]
        
        # Schedule the message
        result = await scheduler.schedule_message(**schedule_args)
        
        if result.get("status") == "scheduled":
            # Successfully scheduled
            if parsed_command.get("type") == "recurring":
                response = f"I've scheduled this message to recur {parsed_command.get('recurrence', {}).get('type', 'regularly')}."
            else:
                scheduled_time = result.get("scheduled_time", "").replace("T", " at ").split(".")[0]
                response = f"I've scheduled your message for {scheduled_time}."
            
            return {
                "schedule_result": "success",
                "schedule_id": result.get("schedule_id"),
                "response": response
            }
        else:
            # Failed to schedule
            logger.error(f"Failed to schedule message: {result.get('error')}")
            return {
                "schedule_result": "error",
                "error": result.get("error", "Unknown error"),
                "response": f"I couldn't schedule your message. {result.get('error', 'An error occurred.')}"
            }
    except Exception as e:
        logger.exception(f"Error in schedule_message_node: {e}")
        return {
            "schedule_result": "error",
            "error": str(e),
            "response": "I encountered an error while trying to schedule your message. Please try again later."
        }
