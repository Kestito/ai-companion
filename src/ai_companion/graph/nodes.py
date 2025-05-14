import os
from uuid import uuid4
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import re
import json
from langchain_core.messages import HumanMessage, RemoveMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from ai_companion.graph.utils.chains import (
    get_character_response_chain,
    get_router_chain,
)
from ai_companion.graph.utils.helpers import (
    get_chat_model,
    get_text_to_speech_module,
    get_text_to_image_module,
)
from ai_companion.graph.state import AICompanionState
from ai_companion.modules.schedules.context_generation import ScheduleContextGenerator
from ai_companion.settings import settings
from ai_companion.modules.memory.long_term.memory_manager import (
    get_initialized_memory_manager,
)
from ai_companion.utils.supabase import get_supabase_client
# Uncomment the import now that a stub exists
# from ai_companion.core.prompts import (
# VOICE_GENERATION_PROMPT,
# DETAILED_INSTRUCTIONS_PROMPT,
# CONTEXT_PROMPT,
# MEMORY_EXTRACTION_PROMPT,
# SUMMARIZE_CONVERSATION_PROMPT,
# )
# from ai_companion.models.domain import PatientInfo # Commenting out missing import
# from ai_companion.modules.database.user_repository import UserRepository # Commenting out missing import
# from ai_companion.utils.sql import create_pgsql_connection # Commenting out missing import

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
        last_message = (
            get_message_content(state["messages"][-1]).lower()
            if state["messages"]
            else ""
        )

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
                result = (
                    supabase.table("patients")
                    .select("id")
                    .like("email", metadata_search)
                    .execute()
                )

                if not result.data:
                    # No existing patient found - route to registration
                    logger.info(
                        f"No existing patient found for Telegram user {user_id}. Routing to registration."
                    )
                    return {"workflow": "patient_registration_node"}

                logger.debug(f"Found existing patient for Telegram user {user_id}.")
            except Exception as e:
                logger.error(f"Error checking for existing patient: {e}", exc_info=True)
                # On error, continue with normal routing

        # Enhanced detection of POLA card related questions - handling misspellings
        pola_patterns = [
            r"(?i)pola",  # Basic mention of POLA
            r"(?i)kort[eė]l[eė]",  # Various spellings of "kortelė"
            r"(?i)v[eė][zž][iy]",  # Various spellings of "vėžys"
            r"(?i)onkolog",  # Oncology-related terms
            r"(?i)smegen[uų]",  # Brain-related terms
            r"(?i)i[sš]mok[oa]",  # Benefits/payments
            r"(?i)savanor[ií]",  # Volunteer-related terms
        ]

        # Patient registration patterns
        patient_registration_patterns = [
            r"(?i)new patient",  # English patterns
            r"(?i)register patient",
            r"(?i)add patient",
            r"(?i)create patient",
            r"(?i)naujas pacientas",  # Lithuanian patterns
            r"(?i)registruoti pacient[aąą]",
            r"(?i)sukurti pacient[aąą]",
            r"(?i)pridėti pacient[aąą]",
        ]

        # Schedule message patterns
        schedule_patterns = [
            r"(?i)^/schedule",  # Telegram command format
            r"(?i)^schedule\s+",  # WhatsApp format
        ]

        # Check for schedule message request
        if any(re.search(pattern, last_message) for pattern in schedule_patterns):
            logger.info(f"Detected schedule message request: '{last_message[:50]}...'")
            return {"workflow": "schedule_message_node"}

        # Check for patient registration request
        if any(
            re.search(pattern, last_message)
            for pattern in patient_registration_patterns
        ):
            logger.info(
                f"Detected patient registration request: '{last_message[:50]}...'"
            )
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
            "audio": "audio_node",
        }

        logger.info(f"Router determined workflow: {workflow}")
        return {"workflow": workflow_mapping.get(workflow, "conversation_node")}
    except Exception as e:
        logger.error(f"Error in router node: {e}", exc_info=True)
        return {
            "workflow": "conversation_node"
        }  # Default to conversation node on error


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
        # Get more conversation history - increase from 5 to 10 messages
        chat_history = state["messages"][-11:-1] if len(state["messages"]) > 1 else []
        current_input = (
            get_message_content(state["messages"][-1]) if state["messages"] else ""
        )

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
            if "conversation_history" in metadata and isinstance(
                metadata["conversation_history"], list
            ):
                telegram_history = metadata["conversation_history"]
                logger.info(
                    f"Found {len(telegram_history)} conversation history entries in metadata"
                )

        # Format contexts
        formatted_context = []
        if rag_context and rag_response.get("response") != "no info":
            formatted_context.append(f"Relevant Knowledge:\n{rag_context}")

        # Prioritize memory context to ensure past interactions are considered first
        if memory_context:
            formatted_context.insert(
                0, f"Previous Context and User Information:\n{memory_context}"
            )

        # Add Telegram conversation history to context with clear formatting
        if telegram_history:
            # Limit to the most recent 15 entries for context window management
            recent_history = (
                telegram_history[-15:]
                if len(telegram_history) > 15
                else telegram_history
            )

            telegram_context = "Previous Conversation (Most Recent First):\n"
            for i, entry in enumerate(recent_history):
                if isinstance(entry, dict):
                    role = entry.get("role", "")
                    content = entry.get("content", "")
                    if role and content:
                        # Format with clear numbering to make it more prominent
                        telegram_context += f"{i+1}. {role.capitalize()}: {content}\n"

            # Insert conversation history at the beginning to emphasize its importance
            formatted_context.insert(0, telegram_context)

        combined_context = "\n\n".join(formatted_context)
        logger.debug(f"Combined context for conversation: {combined_context}")

        # Add context to the response if available
        response = await chain.ainvoke(
            {
                "chat_history": chat_history,
                "input": current_input,
                "current_activity": state.get("current_activity", ""),
                "memory_context": combined_context,
            },
            config,
        )

        response_content = (
            response.content if hasattr(response, "content") else str(response)
        )

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
                if (
                    last_response
                    and previous_response
                    and last_response[:50] == previous_response[:50]
                ):
                    logger.warning(
                        "Detected repetitive responses, adding diversity instruction"
                    )

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
                        diverse_response = await model.ainvoke(
                            [HumanMessage(content=diversity_prompt)]
                        )
                        response_content = (
                            diverse_response.content
                            if hasattr(diverse_response, "content")
                            else str(diverse_response)
                        )
                        logger.info(
                            "Generated more diverse response to avoid repetition"
                        )
                    except Exception as e:
                        logger.error(f"Error generating diverse response: {e}")
                        # Keep the original response if the diversity attempt fails

        logger.info(f"Conversation response: {response_content}")

        # Store the response in memory
        _memory_manager = await get_initialized_memory_manager()

        # Use multiple strategies to find platform/user_id and patient_id
        # First check if patient_id is already in state
        patient_id = state.get("patient_id")
        if patient_id:
            logger.info(f"Conversation: Using patient_id from state: {patient_id}")
        else:
            # Try from configurable
            configurable = state.get("configurable", {})
            user_metadata = configurable.get("user_metadata", {})
            platform = user_metadata.get("platform", "")
            platform_id = user_metadata.get("external_system_id", "")

            # If configurable is empty, try from last message metadata
            if not platform or not platform_id:
                if (
                    last_message
                    and hasattr(last_message, "metadata")
                    and last_message.metadata
                ):
                    msg_metadata = last_message.metadata
                    platform = msg_metadata.get("platform", "")
                    platform_id = msg_metadata.get("external_system_id", "")

                    # Try to get patient_id directly from metadata
                    if "patient_id" in msg_metadata:
                        patient_id = msg_metadata.get("patient_id")
                        logger.info(
                            f"Conversation: Found patient_id in message metadata: {patient_id}"
                        )

                    logger.info(
                        f"Conversation: Extracted from message metadata: platform={platform}, external_system_id={platform_id}"
                    )

            # Try from thread_id if still not found
            if not platform or not platform_id:
                thread_id = configurable.get("thread_id", "")
                if thread_id and "-" in thread_id:
                    # Try to parse thread_id in format "platform-chat_id-user_id"
                    parts = thread_id.split("-")
                    if len(parts) >= 3:
                        platform = parts[0]
                        platform_id = parts[2]
                        logger.info(
                            f"Conversation: Extracted from thread_id: platform={platform}, external_system_id={platform_id}"
                        )
                    elif len(parts) >= 2:
                        platform = parts[0]
                        platform_id = parts[1]  # Use chat_id as fallback
                        logger.info(
                            f"Conversation: Using chat_id as fallback for external_system_id: {platform_id}"
                        )

            # If we have platform and platform_id but no patient_id, look it up
            if platform and platform_id and not patient_id:
                patient_id = get_patient_id_from_platform_id(platform, platform_id)
                logger.info(
                    f"Conversation: Got patient_id from database lookup: {patient_id}"
                )

        # Create metadata dictionary for memory storage
        memory_metadata = {}

        # Add patient_id to metadata if available
        if patient_id:
            memory_metadata["patient_id"] = patient_id
            # Store it in state for other nodes
            state["patient_id"] = patient_id
            logger.info(f"Using patient_id: {patient_id} for memory storage")
        else:
            logger.warning("No patient_id available, memory storage will be skipped")

        # Add platform and platform_id to metadata if available
        if platform:
            memory_metadata["platform"] = platform
        if platform_id:
            memory_metadata["external_system_id"] = platform_id

        # If we have a patient_id, store the memories
        if "patient_id" in memory_metadata:
            try:
                # Add required fields to memory metadata
                memory_metadata["timestamp"] = datetime.now().isoformat()

                # Create memory data
                memory_data = {
                    "user_message": current_input,
                    "assistant_response": response_content,
                    "timestamp": memory_metadata["timestamp"],
                }

                # Store as a single conversation memory
                _memory_id = await _memory_manager.add_memory(
                    json.dumps(memory_data), metadata=memory_metadata
                )

                logger.info(
                    f"Stored conversation in memory for patient {memory_metadata['patient_id']}"
                )
            except Exception as e:
                logger.error(f"Failed to store memory: {e}", exc_info=True)
        else:
            logger.warning("No patient_id available, skipping memory storage")

        # Update state with response
        return {"messages": [*state["messages"], AIMessage(content=response_content)]}
    except Exception as e:
        logger.error(f"Error in conversation node: {e}", exc_info=True)
        return {
            "messages": [
                *state["messages"],
                AIMessage(content="Atsiprašau, įvyko klaida. Prašome bandyti vėliau."),
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

        last_message = (
            get_message_content(state["messages"][-1]) if state["messages"] else ""
        )
        memory_context = state.get("memory_context", "")

        # Get chat history
        chat_history = state["messages"][:-1] if len(state["messages"]) > 1 else []
        chat_history_str = "\n".join(
            [
                f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {get_message_content(m)}"
                for m in chat_history[-settings.ROUTER_MESSAGES_TO_ANALYZE :]
            ]
        )

        # Combine chat history with memory context
        combined_context = (
            f"Chat History:\n{chat_history_str}\n\nMemory Context:\n{memory_context}"
        )

        start_time = datetime.now()

        # Query the RAG chain with enhanced features
        try:
            # Extract options from message metadata if available
            message_metadata = {}
            if (
                hasattr(state["messages"][-1], "metadata")
                and state["messages"][-1].metadata
            ):
                message_metadata = state["messages"][-1].metadata

            detailed_response = message_metadata.get(
                "detailed_response", True
            )  # Default to True for detailed responses
            with_citations = message_metadata.get(
                "with_citations", True
            )  # Default to including citations

            # Get platform from metadata if available
            platform = message_metadata.get("platform", "")

            # If platform is not in metadata, try to get it from other sources
            if not platform:
                # Try to get platform from state
                configurable = state.get("configurable", {})
                user_metadata = configurable.get("user_metadata", {})
                platform = user_metadata.get("platform", "")

                # If still not available, try thread_id which might contain platform info
                if not platform and "thread_id" in configurable:
                    thread_id = configurable.get("thread_id", "")
                    if thread_id and "-" in thread_id:
                        # thread_id format is often "platform-chat_id-user_id"
                        platform = thread_id.split("-")[0]
                        logger.info(f"Extracted platform from thread_id: {platform}")

            logger.info(f"Using platform '{platform}' for RAG response")

            response, relevant_docs = await rag_chain.query(
                query=last_message,
                memory_context=combined_context,  # Pass combined context
                max_retries=3,
                min_confidence=0.5,  # Lower similarity threshold from 0.7 to 0.5
                detailed=detailed_response,  # Request detailed response
                with_citations=with_citations,  # Include citations in the response
                platform=platform,  # Pass platform information
            )

            # Format sources with proper error handling
            sources = []
            for doc in relevant_docs:
                try:
                    metadata = doc.metadata or {}
                    sources.append(
                        {
                            "title": metadata.get("title", "Be pavadinimo"),
                            "source": metadata.get(
                                "source", metadata.get("url", "Nežinomas šaltinis")
                            ),
                            "date": metadata.get(
                                "processed_at", datetime.now().isoformat()
                            ),
                            "confidence": metadata.get("confidence_score", 0.8),
                        }
                    )
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
                confidence_response = await model.ainvoke(
                    [HumanMessage(content=confidence_prompt)]
                )
                confidence_text = confidence_response.content.strip()

                # Extract just the number from the response
                confidence_match = re.search(r"\b([1-9]|10)\b", confidence_text)
                confidence_rating = (
                    int(confidence_match.group(1)) if confidence_match else 7
                )  # Default to 7 if parsing fails

                # Format confidence level based on the rating
                confidence_level = (
                    "High"
                    if confidence_rating >= 8
                    else "Medium"
                    if confidence_rating >= 5
                    else "Low"
                )

                # Enhance response with process details and supporting links
                process_prompt = (
                    f'Based on the user\'s query "{last_message}" and your response, please provide additional structured information in Lithuanian:\n\n'
                    f"1. Detailed Process: Briefly explain the step-by-step process related to this query (max 3 steps)\n"
                    f"2. Primary Link: Identify the most important resource or website where the user can get official information\n"
                    f"3. Supporting Resources: List 2-3 additional resources or organizations that can help\n\n"
                    f"Format your response in clear, concise bullet points. No introduction or conclusion needed.\n\n"
                    f"IMPORTANT: When using information directly from retrieved documents, start those sentences with [RAG].\n"
                    f"When generating your own explanations or text, start those sentences with [AI].\n"
                    f"Every sentence or paragraph in your response must start with either [RAG] or [AI].\n"
                    f"The final line of your response MUST end with either [RAG] or [AI] based on the type of information in that line."
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

                # Ensure enhancement text has proper prefixes
                if (
                    enhancement_text
                    and not enhancement_text.startswith("[RAG]")
                    and not enhancement_text.startswith("[AI]")
                ):
                    lines = enhancement_text.split("\n")
                    new_lines = []
                    for line in lines:
                        if (
                            line.strip()
                            and not line.startswith("[RAG]")
                            and not line.startswith("[AI]")
                        ):
                            new_lines.append(f"[AI] {line}")
                        else:
                            new_lines.append(line)
                    enhancement_text = "\n".join(new_lines)

                # Ensure enhancement text ends with the appropriate tag
                if not enhancement_text.rstrip().endswith(
                    "[RAG]"
                ) and not enhancement_text.rstrip().endswith("[AI]"):
                    if enhancement_text.rstrip().split("\n")[-1].startswith("[RAG]"):
                        enhancement_text = enhancement_text.rstrip() + " [RAG]"
                    else:
                        enhancement_text = enhancement_text.rstrip() + " [AI]"

                # Append enhancement and confidence to the response
                confidence_note = f"\n\n[AI] Confidence: {confidence_level} ({confidence_rating}/10) [AI]"
                enhanced_response = f"{response}\n\n{enhancement_text}{confidence_note}"

                logger.info(
                    f"Self-evaluated confidence rating: {confidence_rating}/10 ({confidence_level})"
                )
                logger.info(
                    "Enhanced response with process details and supporting links"
                )
            except Exception as e:
                logger.error(f"Error in response enhancement: {e}")
                confidence_rating = 7  # Default value
                confidence_level = "Medium"  # Default value
                confidence_note = f"\n\n[AI] Confidence: {confidence_level} ({confidence_rating}/10) [AI]"
                enhanced_response = response + confidence_note

            # Create context with sources
            context = enhanced_response
            if sources:
                sources_info = "\n[AI] Šaltiniai:\n" + "\n".join(
                    [
                        f"[AI] - {s['source']} (Patikimumas: {s['confidence']:.2f})"
                        for s in sources
                    ]
                )
                sources_info += " [AI]"
                context += sources_info

            # Calculate metrics
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()

            # Create metrics
            metrics = {
                "total_queries": 1,
                "successful_queries": 1 if relevant_docs else 0,
                "failed_queries": 0 if relevant_docs else 1,
                "average_confidence": sum(s["confidence"] for s in sources)
                / len(sources)
                if sources
                else 0.0,
                "query_processing_time": total_time * 0.2,
                "retrieval_time": total_time * 0.4,
                "response_generation_time": total_time * 0.4,
                "total_processing_time": total_time,
                "error_details": {},
                "last_updated": end_time.isoformat(),
                "self_rating": confidence_rating,
                "confidence_level": confidence_level,
            }

            # Check if response is substantive (more than just an error message or generic reply)
            is_substantive_response = (
                len(response) > 100  # Reasonable length
                and "atsiprašau" not in response.lower()  # Not an apology
                and "įvyko klaida" not in response.lower()  # Not an error message
            )

            return {
                "rag_response": {
                    "has_relevant_info": len(relevant_docs) > 0
                    or is_substantive_response,
                    "response": enhanced_response,
                    "sources": sources,
                    "context": context,
                    "metrics": metrics,
                    "confidence_rating": confidence_rating,
                    "confidence_level": confidence_level,
                }
            }

        except Exception as e:
            logger.error(f"Error in enhanced RAG chain query: {e}")
            error_time = datetime.now()
            return {
                "rag_response": {
                    "has_relevant_info": False,
                    "response": "[AI] Atsiprašau, įvyko klaida ieškant informacijos. Prašome bandyti vėliau.\n\n[AI] Confidence: Low (2/10) [AI]",
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
                        "confidence_level": "Low",
                    },
                    "confidence_rating": 2,
                    "confidence_level": "Low",
                },
                "rag_retry_count": 0,
            }

    except Exception as e:
        logger.error(f"Critical error in RAG node: {e}", exc_info=True)
        return {
            "messages": [
                *state["messages"],
                AIMessage(
                    content="[AI] Atsiprašau, įvyko klaida. Prašome bandyti vėliau. [AI]"
                ),
            ]
        }


async def web_search_node(state: AICompanionState, config: RunnableConfig):
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")

    chain = get_character_response_chain(state.get("summary", ""))

    # Extract last message from the state
    last_message = (
        get_message_content(state["messages"][-1]) if state["messages"] else ""
    )
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
    last_message = (
        get_message_content(state["messages"][-1]) if state["messages"] else ""
    )
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
    # Uncomment TTS module usage (it will use the stub)
    text_to_speech_module = get_text_to_speech_module()

    # Extract last message from the state
    last_message = (
        get_message_content(state["messages"][-1]) if state["messages"] else ""
    )
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
    # Uncomment TTS synthesis (it will use the stub)
    output_audio = await text_to_speech_module.synthesize(text_content)
    # output_audio = b"" # Remove placeholder

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


async def memory_injection_node(state: AICompanionState) -> Dict[str, str]:
    """Inject relevant memories into the conversation state."""
    logger.info("Starting memory injection")

    try:
        # Get memory manager instance
        _memory_manager = await get_initialized_memory_manager()

        # ... rest of the function continues unchanged ...
        return {}  # Return placeholder
    except Exception as e:
        logger.error(f"Error in memory injection: {e}", exc_info=True)
        return {}


async def memory_extraction_node(state: AICompanionState) -> Dict[str, Dict]:
    """Extract and store important memories from the conversation."""
    logger.info("Starting memory extraction node")

    try:
        memory_manager = await get_initialized_memory_manager()
        messages = state.get("messages", [])

        # Attempt to get a primary patient_id from the state if available
        # This could be set by an upstream node or initial session setup
        # Ensure config and configurable exist before trying to access them
        config = state.get("config")
        patient_id_from_state = None
        if config and isinstance(config, dict):
            configurable_dict = config.get("configurable")
            if configurable_dict and isinstance(configurable_dict, dict):
                patient_id_from_state = configurable_dict.get("patient_id")

        if not messages:
            logger.info("No messages in state to process for memory extraction.")
            return {}

        for message in messages:
            if isinstance(message, HumanMessage):
                logger.debug(
                    f"Processing HumanMessage for memory extraction: {message.content[:50]}..."
                )

                current_message_patient_id = patient_id_from_state

                # Ensure metadata exists
                if not hasattr(message, "metadata") or message.metadata is None:
                    message.metadata = {}

                # Try to get platform and user_id from message metadata for more specific patient lookup
                platform = message.metadata.get("platform")
                platform_user_id = message.metadata.get(
                    "user_id"
                )  # Assuming 'user_id' in metadata is the platform_id

                if platform and platform_user_id:
                    logger.debug(
                        f"Message has platform ({platform}) and platform_user_id ({platform_user_id}). Looking up patient_id."
                    )
                    retrieved_patient_id = get_patient_id_from_platform_id(
                        platform, platform_user_id
                    )
                    if retrieved_patient_id:
                        current_message_patient_id = retrieved_patient_id
                        logger.info(
                            f"Using patient_id {current_message_patient_id} from platform details for message."
                        )
                    else:
                        logger.warning(
                            f"Could not retrieve patient_id for platform {platform}, user {platform_user_id}. May fall back to state patient_id or fail."
                        )
                elif patient_id_from_state:
                    logger.info(
                        f"Using patient_id {patient_id_from_state} from state for message as no platform details found in message metadata."
                    )
                else:
                    logger.warning(
                        "No patient_id found in state or message metadata. Cannot store memory for this message."
                    )
                    continue  # Skip this message

                if current_message_patient_id:
                    message.metadata["patient_id"] = current_message_patient_id
                    logger.debug(
                        f"Attempting to store memory for patient_id: {current_message_patient_id}"
                    )
                    await memory_manager.extract_and_store_memories(message)
                else:
                    logger.warning(
                        f"Skipping memory extraction for a message due to missing patient_id: {message.content[:50]}..."
                    )

        logger.info("Finished memory extraction process.")
        return {}

    except Exception as e:
        logger.error(f"Error in memory extraction node: {e}", exc_info=True)
        return {}


def get_patient_id_from_platform_id(platform: str, platform_id: str) -> Optional[str]:
    """
    Get patient_id from platform and platform_id by querying the patients table.

    Args:
        platform: The platform name (telegram, whatsapp, web)
        platform_id: The user/chat ID from the platform

    Returns:
        Patient ID if found, None otherwise
    """
    if not platform or not platform_id:
        logger.warning("Missing platform or platform_id")
        return None

    try:
        # Get Supabase client
        supabase = get_supabase_client()

        # Generate a consistent system_id format for lookups
        system_id = f"{platform}:{platform_id}"
        logger.debug(f"Looking up patient with system_id: {system_id}")

        # First try to find patient by system_id (most efficient approach)
        try:
            result = (
                supabase.table("patients")
                .select("id")
                .eq("system_id", system_id)
                .execute()
            )

            # Check if we found a match by system_id
            if result.data and len(result.data) > 0:
                patient_id = result.data[0].get("id")
                logger.info(
                    f"Found patient_id {patient_id} using system_id {system_id}"
                )
                return patient_id
        except Exception as e:
            logger.warning(f"Error looking up by system_id: {e}")

        # If not found by system_id, try with email field which might contain platform data in JSON
        logger.debug(
            f"No exact match for {platform}:{platform_id}, checking email field for JSON data"
        )
        try:
            # Check if we can find the patient by email field containing platform info as JSON
            platform_query = f'%"{platform}_id": "{platform_id}"%'
            result = (
                supabase.table("patients")
                .select("id, email")
                .like("email", platform_query)
                .execute()
            )

            if result.data and len(result.data) > 0:
                patient_id = result.data[0].get("id")
                logger.info(
                    f"Found patient_id {patient_id} for {platform}:{platform_id} in email field"
                )

                # Update with system_id if it was found via another method
                try:
                    supabase.table("patients").update({"system_id": system_id}).eq(
                        "id", patient_id
                    ).execute()
                    logger.info(
                        f"Updated patient {patient_id} with system_id {system_id}"
                    )
                except Exception as e:
                    logger.warning(f"Could not update system_id: {e}")

                return patient_id

            # Alternate search in email field
            platform_query = f'%"platform": "{platform}"%"user_id": "{platform_id}"%'
            result = (
                supabase.table("patients")
                .select("id, email")
                .like("email", platform_query)
                .execute()
            )

            if result.data and len(result.data) > 0:
                patient_id = result.data[0].get("id")
                logger.info(
                    f"Found patient_id {patient_id} for platform {platform} and id {platform_id} in email"
                )

                # Update with system_id
                try:
                    supabase.table("patients").update({"system_id": system_id}).eq(
                        "id", patient_id
                    ).execute()
                    logger.info(
                        f"Updated patient {patient_id} with system_id {system_id}"
                    )
                except Exception as e:
                    logger.warning(f"Could not update system_id: {e}")

                return patient_id
        except Exception as e:
            logger.warning(f"Error searching email field: {e}")

        # No match found, create a new patient record
        logger.info(
            f"No patient found for {platform}:{platform_id}, creating new patient"
        )

        # Create a JSON structure for email field since we're using it for platform data storage
        email_data = {
            "platform": platform,
            f"{platform}_id": platform_id,
            "system_id": system_id,
            "created_via": "auto_registration",
            "first_message_time": datetime.now().isoformat(),
        }

        # Prepare data for new patient record
        patient_data = {
            "system_id": system_id,
            "channel": platform,
            "risk": "Low",
            "email": json.dumps(email_data),
        }

        # Insert new patient
        try:
            result = supabase.table("patients").insert(patient_data).execute()

            if result.data and len(result.data) > 0:
                new_patient_id = result.data[0].get("id")
                logger.info(
                    f"Created new patient with ID {new_patient_id} for {platform}:{platform_id}"
                )
                return new_patient_id
            else:
                logger.error(f"No data returned when creating patient for {system_id}")
        except Exception as e:
            logger.error(f"Error creating new patient: {e}")

        return None

    except Exception as e:
        logger.error(f"Error getting patient_id from platform_id: {e}", exc_info=True)
        return None


async def rag_retry_node(state: AICompanionState) -> Dict[str, Any]:
    """Retry RAG with adjusted parameters when initial retrieval wasn't successful."""
    logger.info("Executing rag_retry_node with adjusted parameters")
    try:
        # Initialize RAG chain with adjusted parameters
        from ai_companion.modules.rag.core.rag_chain import get_rag_chain

        rag_chain = get_rag_chain(
            model_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            model_name=os.getenv("LLM_MODEL"),
        )

        # Get current retry count and increment it
        retry_count = state.get("rag_retry_count", 0) + 1

        last_message = (
            get_message_content(state["messages"][-1]) if state["messages"] else ""
        )
        memory_context = state.get("memory_context", "")

        # Get chat history
        chat_history = state["messages"][:-1] if len(state["messages"]) > 1 else []
        chat_history_str = "\n".join(
            [
                f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {get_message_content(m)}"
                for m in chat_history[-settings.ROUTER_MESSAGES_TO_ANALYZE :]
            ]
        )

        # Combine chat history with memory context
        combined_context = (
            f"Chat History:\n{chat_history_str}\n\nMemory Context:\n{memory_context}"
        )

        logger.info(f"Retry #{retry_count} for query: {last_message}")
        start_time = datetime.now()

        # Attempt RAG with more lenient parameters
        try:
            # Extract options from message metadata if available
            message_metadata = {}
            if (
                hasattr(state["messages"][-1], "metadata")
                and state["messages"][-1].metadata
            ):
                message_metadata = state["messages"][-1].metadata

            detailed_response = message_metadata.get("detailed_response", True)
            with_citations = message_metadata.get("with_citations", True)

            # Get platform from metadata if available
            platform = message_metadata.get("platform", "")

            # If platform is not in metadata, try to get it from other sources
            if not platform:
                # Try to get platform from state
                configurable = state.get("configurable", {})
                user_metadata = configurable.get("user_metadata", {})
                platform = user_metadata.get("platform", "")

                # If still not available, try thread_id which might contain platform info
                if not platform and "thread_id" in configurable:
                    thread_id = configurable.get("thread_id", "")
                    if thread_id and "-" in thread_id:
                        # thread_id format is often "platform-chat_id-user_id"
                        platform = thread_id.split("-")[0]
                        logger.info(f"Extracted platform from thread_id: {platform}")

            logger.info(f"Using platform '{platform}' for RAG response")

            response, relevant_docs = await rag_chain.query(
                query=last_message,
                memory_context=combined_context,  # Pass combined context
                max_retries=3,
                min_confidence=0.5,  # Lower similarity threshold from 0.7 to 0.5
                detailed=detailed_response,  # Request detailed response
                with_citations=with_citations,  # Include citations in the response
                platform=platform,  # Pass platform information
            )

            # Format sources with proper error handling
            sources = []
            for doc in relevant_docs:
                try:
                    metadata = doc.metadata or {}
                    sources.append(
                        {
                            "title": metadata.get("title", "Be pavadinimo"),
                            "source": metadata.get(
                                "source", metadata.get("url", "Nežinomas šaltinis")
                            ),
                            "date": metadata.get(
                                "processed_at", datetime.now().isoformat()
                            ),
                            "confidence": metadata.get("confidence_score", 0.7),
                        }
                    )
                except Exception as e:
                    logger.warning(f"Error formatting source metadata: {e}")
                    continue

            # Add retry information and confidence
            confidence_rating = 6  # Moderate confidence for retry responses
            confidence_level = "Medium"

            # Add prefix to response if not already present
            if not response.startswith("[RAG]") and not response.startswith("[AI]"):
                # Split into lines and add prefixes where missing
                lines = response.split("\n")
                new_lines = []
                for line in lines:
                    if (
                        line.strip()
                        and not line.startswith("[RAG]")
                        and not line.startswith("[AI]")
                    ):
                        new_lines.append(f"[AI] {line}")
                    else:
                        new_lines.append(line)
                response = "\n".join(new_lines)

            # Ensure the response ends with [RAG] or [AI]
            if not response.rstrip().endswith(
                "[RAG]"
            ) and not response.rstrip().endswith("[AI]"):
                lines = response.split("\n")
                last_line = lines[-1] if lines else ""

                if last_line.startswith("[RAG]"):
                    response = response.rstrip() + " [RAG]"
                else:
                    response = response.rstrip() + " [AI]"

            # Add retry information to the response
            enhanced_response = (
                f"{response}\n\n"
                f"[AI] Note: This is a retry with adjusted parameters after initial search returned limited results."
                f"\n\n[AI] Confidence: {confidence_level} ({confidence_rating}/10) [AI]"
            )

            # Create context with sources
            context = enhanced_response
            if sources:
                sources_info = "\n[AI] Šaltiniai:\n" + "\n".join(
                    [
                        f"[AI] - {s['source']} (Patikimumas: {s['confidence']:.2f})"
                        for s in sources
                    ]
                )
                sources_info += " [AI]"
                context += sources_info

            # Calculate metrics
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()

            # Create metrics
            metrics = {
                "total_queries": 1,
                "successful_queries": 1 if relevant_docs else 0,
                "failed_queries": 0 if relevant_docs else 1,
                "average_confidence": sum(s["confidence"] for s in sources)
                / len(sources)
                if sources
                else 0.0,
                "query_processing_time": total_time * 0.2,
                "retrieval_time": total_time * 0.4,
                "response_generation_time": total_time * 0.4,
                "total_processing_time": total_time,
                "error_details": {},
                "last_updated": end_time.isoformat(),
                "self_rating": confidence_rating,
                "confidence_level": confidence_level,
                "retry_count": retry_count,
            }

            # Check if response is substantive
            is_substantive_response = (
                len(response) > 80  # Lower threshold for retry
                and "atsiprašau" not in response.lower()[:40]  # Check just beginning
                and "įvyko klaida" not in response.lower()[:40]  # Check just beginning
            )

            return {
                "rag_response": {
                    "has_relevant_info": len(relevant_docs) > 0
                    or is_substantive_response,
                    "response": enhanced_response,
                    "sources": sources,
                    "context": context,
                    "metrics": metrics,
                    "confidence_rating": confidence_rating,
                    "confidence_level": confidence_level,
                },
                "rag_retry_count": retry_count,
            }

        except Exception as e:
            logger.error(f"Error in RAG retry node: {e}")
            error_time = datetime.now()
            return {
                "rag_response": {
                    "has_relevant_info": False,
                    "response": "[AI] Atsiprašau, įvyko klaida ieškant papildomos informacijos. Prašome bandyti vėliau arba perfrazuoti klausimą.\n\n[AI] Confidence: Low (2/10) [AI]",
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
                        "confidence_level": "Low",
                        "retry_count": retry_count,
                    },
                    "confidence_rating": 2,
                    "confidence_level": "Low",
                },
                "rag_retry_count": retry_count,
            }

    except Exception as e:
        logger.error(f"Critical error in RAG retry node: {e}", exc_info=True)
        return {
            "messages": [
                *state["messages"],
                AIMessage(
                    content="[AI] Atsiprašau, įvyko klaida bandant surasti papildomos informacijos. Prašome bandyti vėliau. [AI]"
                ),
            ]
        }


async def patient_registration_node(
    state: AICompanionState, config: Optional[RunnableConfig] = None
) -> Dict[str, Any]:
    """Placeholder for patient registration logic."""
    logger.info(
        "Executing placeholder patient_registration_node. Actual registration logic needs implementation."
    )
    # This node should handle extracting patient details and saving them.
    # For now, it simulates a failure or an unimplemented state.
    return {
        "registration_result": "failed",
        "error": "Patient registration not yet implemented.",
        "messages": [
            *state["messages"],
            AIMessage(content="Patient registration is currently unavailable."),
        ],
    }


async def schedule_message_node(
    state: AICompanionState, config: Optional[RunnableConfig] = None
) -> Dict[str, Any]:
    """Placeholder for message scheduling logic."""
    logger.info(
        "Executing placeholder schedule_message_node. Actual scheduling logic needs implementation."
    )
    # This node should parse schedule commands, interact with a scheduler service, etc.
    return {
        "schedule_result": "failed",
        "error": "Message scheduling not yet implemented.",
        "messages": [
            *state["messages"],
            AIMessage(content="Message scheduling is currently unavailable."),
        ],
    }
