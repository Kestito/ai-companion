import os
from uuid import uuid4
import logging
from typing import Dict, Any

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
from ai_companion.modules.rag.core.rag_chain import get_rag_chain

logger = logging.getLogger(__name__)


async def router_node(state: AICompanionState) -> Dict[str, str]:
    """Route the conversation to the appropriate workflow."""
    logger.debug("Starting router node processing")
    try:
        chain = get_router_chain()
        last_message = state["messages"][-1].content.lower() if state["messages"] else ""
        
        # Check if it's a POLA card related question
        if "pola" in last_message and ("kortele" in last_message or "kortelė" in last_message):
            return {"workflow": "conversation_node"}
            
        response = await chain.ainvoke({"messages": last_message})
        workflow = response["text"].strip()
        
        # Map the workflow to the correct node name
        workflow_mapping = {
            "conversation": "conversation_node",
            "image": "image_node",
            "audio": "audio_node"
        }
        
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
        current_input = state["messages"][-1].content if state["messages"] else ""
        
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
    """Process the input through RAG for knowledge-based responses."""
    logger.debug("Starting RAG node processing")
    try:
        rag_chain = get_rag_chain()
        last_message = state["messages"][-1].content if state["messages"] else ""
        
        # Query the RAG chain
        response, relevant_docs = await rag_chain.query(last_message)
        logger.info(f"RAG response: {response}")
        
        # If no relevant docs found, return simple "no info" response
        if not relevant_docs:
            return {
                "rag_response": {
                    "has_relevant_info": False,
                    "response": "no info",
                    "sources": [],
                    "context": ""
                }
            }
        
        # Format sources if available
        sources_info = "\nŠaltiniai:\n" + "\n".join([
            f"- {s.get('source', 'Nežinomas šaltinis')}" 
            for s in [doc.metadata for doc in relevant_docs]
        ])
        
        return {
            "rag_response": {
                "has_relevant_info": True,
                "response": response,
                "sources": [doc.metadata for doc in relevant_docs],
                "context": response + sources_info
            }
        }
    except Exception as e:
        logger.error(f"Error in RAG node: {e}", exc_info=True)
        return {
            "rag_response": {
                "has_relevant_info": False,
                "response": "no info",
                "sources": [],
                "context": ""
            }
        }


async def web_search_node(state: AICompanionState, config: RunnableConfig):
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")

    chain = get_character_response_chain(state.get("summary", ""))

    response = await chain.ainvoke(
        {
            "messages": state["messages"],
            "current_activity": current_activity,
            "memory_context": memory_context,
        },
        config,
    )
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

    response = await chain.ainvoke(
        {
            "messages": updated_messages,
            "current_activity": current_activity,
            "memory_context": memory_context,
        },
        config,
    )

    return {"messages": AIMessage(content=response), "image_path": img_path}


async def hallucination_grader_node(state: AICompanionState, config: RunnableConfig):
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")

    chain = get_character_response_chain(state.get("summary", ""))

    response = await chain.ainvoke(
        {
            "messages": state["messages"],
            "current_activity": current_activity,
            "memory_context": memory_context,
        },
        config,
    )
    return {"messages": AIMessage(content=response)}


async def audio_node(state: AICompanionState, config: RunnableConfig):
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")

    chain = get_character_response_chain(state.get("summary", ""))
    text_to_speech_module = get_text_to_speech_module()

    response = await chain.ainvoke(
        {
            "messages": state["messages"],
            "current_activity": current_activity,
            "memory_context": memory_context,
        },
        config,
    )
    output_audio = await text_to_speech_module.synthesize(response)

    return {"messages": response, "audio_buffer": output_audio}


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

    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = await model.ainvoke(messages)

    delete_messages = [
        RemoveMessage(id=m.id)
        for m in state["messages"][: -settings.TOTAL_MESSAGES_AFTER_SUMMARY]
    ]
    return {"summary": response.content, "messages": delete_messages}


def memory_injection_node(state: AICompanionState) -> Dict[str, str]:
    """Inject relevant memories into the conversation state."""
    logger.debug("Starting memory injection node processing")
    try:
        memory_manager = get_memory_manager()
        last_message = state["messages"][-1].content if state["messages"] else ""
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
        current_message = state["messages"][-1].content if state["messages"] else ""
        
        # Get relevant memories
        relevant_memories = memory_manager.get_relevant_memories(current_message)
        
        # Format memories for context
        formatted_memories = memory_manager.format_memories_for_prompt(relevant_memories)
        
        if formatted_memories:
            logger.info(f"Found relevant memories: {formatted_memories}")
        else:
            logger.debug("No relevant memories found")
            
        # Store the current message as a potential memory
        await memory_manager.extract_and_store_memories(state["messages"][-1])
        
        return {"memory_context": formatted_memories}
    except Exception as e:
        logger.error(f"Error in memory extraction: {e}", exc_info=True)
        return {"memory_context": ""}
