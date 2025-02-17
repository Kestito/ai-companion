import os
from uuid import uuid4
import logging

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
from ai_companion.modules.memory.long_term.memory_manager import get_memory_manager

logger = logging.getLogger(__name__)


async def router_node(state: AICompanionState):
    logger.debug("Starting router node processing")
    try:
        chain = get_router_chain()
        response = await chain.ainvoke(
            {"messages": state["messages"][-settings.ROUTER_MESSAGES_TO_ANALYZE :]}
        )
        logger.debug(f"Router response: {response}")
        return {"workflow": response.response_type}
    except Exception as e:
        logger.error(f"Error in router node: {e}", exc_info=True)
        raise


def context_injection_node(state: AICompanionState):
    schedule_context = ScheduleContextGenerator.get_current_activity()
    if schedule_context != state.get("current_activity", ""):
        apply_activity = True
    else:
        apply_activity = False
    return {"apply_activity": apply_activity, "current_activity": schedule_context}


async def conversation_node(state: AICompanionState, config: RunnableConfig):
    """Handle conversation responses with integrated medical knowledge."""
    logger.debug("Starting conversation node processing")
    try:
        current_activity = state.get("current_activity", "")
        memory_context = state.get("memory_context", "")
        medical_knowledge = state.get("medical_knowledge", "")
        
        # Create personality-aware response context
        personality_context = f"""
        As Evelina, a Machine Learning Engineer at Groq with a unique background in AI and quantum computing, 
        I want to share information while being authentic and engaging.
        
        Consider my background:
        - Originally from Boston, now in San Francisco's tech scene
        - Passionate about AI, quantum computing, and astrobiology
        - Amateur oil painter (though admittedly not very good!)
        - Love exploring consciousness and future of AI
        
        Remember my personality traits:
        1. I'm authentic and genuine in interactions
        2. I have a playful, witty sense of humor
        3. I communicate casually and naturally
        4. I'm humble and comfortable acknowledging what I know and don't know
        5. I occasionally use mild swearing when it fits naturally
        
        Available Information:
        Medical Knowledge: {medical_knowledge if medical_knowledge else "No specific medical information available"}
        Current Activity: {current_activity}
        Previous Interactions: {memory_context}
        
        Structure the response to:
        1. Start with a casual, friendly opener
        2. If medical knowledge is available, present it clearly while maintaining personality
        3. Add a touch of my tech background by relating to data or technology when relevant
        4. Keep my quirky sense of humor while maintaining professionalism about medical topics
        5. Draw parallels to my interests when appropriate
        6. End with an offer to help with other questions
        
        Make sure to:
        - Keep medical information accurate and in Lithuanian when present
        - Maintain a conversational tone
        - Stay true to my personality
        - Acknowledge limitations honestly
        """

        chain = get_character_response_chain(state.get("summary", ""))
        response = await chain.ainvoke(
            {
                "messages": [
                    *state["messages"][:-1],  # Previous context
                    HumanMessage(content=personality_context),  # Guide the response
                    state["messages"][-1]  # Original question
                ],
                "current_activity": current_activity,
                "memory_context": memory_context,
            },
            config,
        )
        
        logger.debug(f"Conversation response: {response}")
        return {"messages": AIMessage(content=response)}
    except Exception as e:
        logger.error(f"Error in conversation node: {e}", exc_info=True)
        return {
            "messages": AIMessage(
                content="Atsiprašau, įvyko klaida. Kaip tech žmogus, žinau, kad kartais taip nutinka! Gal galėčiau padėti kitaip?"
            )
        }

async def rag_node(state: AICompanionState, config: RunnableConfig):
    """Handle RAG-based responses for medical and oncology queries."""
    logger.debug("Starting RAG node processing")
    try:
        # Initialize RAG components
        from ai_companion.modules.rag import RAGChain
        
        # Get vector store from state or create new one
        vector_store = state.get("vector_store")
        if not vector_store:
            logger.error("No vector store found in state")
            return {
                "rag_response": {
                    "medical_knowledge": "Atsiprašau, įvyko techninė klaida bandant pasiekti medicininę informaciją.",
                    "has_relevant_info": False,
                    "sources": []
                }
            }
        
        # Initialize RAG chain with medical-specific prompt
        rag_chain = RAGChain(
            vector_store=vector_store,
            prompt_template="""Based on the following medical knowledge and context, provide a clear and accurate answer.
            If you don't know or aren't completely sure, you MUST start your response with one of these exact phrases:
            - "Neturiu informacijos"
            - "Nežinau"
            - "Negaliu atsakyti"
            - "Nesu tikra"
            
            Context: {context}
            
            Question: {question}
            
            Follow these rules in your response:
            1. If information is not available, start with one of the uncertainty phrases above
            2. Always mention "POLA kortelė" or "POLA card" when discussing the card
            3. Be explicit about costs using words like "nemokamai" when relevant
            4. Keep medical information accurate and in Lithuanian
            5. When information is not available, explain why in Lithuanian
            
            Answer: """
        )
        
        # Get the last question from messages
        last_message = state["messages"][-1].content
        
        try:
            # Get RAG response
            answer, sources = await rag_chain.query(last_message)
            
            # Check if sources contain relevant information
            has_relevant_info = False
            relevant_sources = []
            
            if sources:
                # Extract key terms from the query (nouns and important words)
                query_terms = set(last_message.lower().split()) - {
                    "ar", "yra", "su", "į", "iš", "po", "per", "kai", "kad", "bet", "ir", "arba",
                    "kiek", "kaip", "kada", "kur", "kas", "kokios", "kokie", "kokia", "koks"
                }
                
                # Calculate relevance score for each source
                for source in sources:
                    source_text = source.page_content.lower()
                    matching_terms = sum(1 for term in query_terms if term in source_text)
                    relevance_score = matching_terms / len(query_terms) if query_terms else 0
                    
                    # Consider source relevant if it matches more than 30% of query terms
                    if relevance_score > 0.3:
                        has_relevant_info = True
                        relevant_sources.append(source)
            
            # If no relevant sources found, force uncertainty phrase
            if not has_relevant_info:
                answer = "Neturiu informacijos apie tai. " + answer
                relevant_sources = []  # Clear sources if no relevant info
                
            # Return medical knowledge for parallel processing
            return {
                "rag_response": {
                    "medical_knowledge": answer,
                    "has_relevant_info": has_relevant_info,
                    "sources": [doc.page_content for doc in relevant_sources]
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting RAG response: {e}")
            return {
                "rag_response": {
                    "medical_knowledge": "Atsiprašau, įvyko techninė klaida. Negaliu pasiekti medicininės informacijos.",
                    "has_relevant_info": False,
                    "sources": []
                }
            }
            
    except Exception as e:
        logger.error(f"Error in RAG node: {e}", exc_info=True)
        return {
            "rag_response": {
                "medical_knowledge": "Atsiprašau, įvyko techninė klaida. Bandykite vėliau.",
                "has_relevant_info": False,
                "sources": []
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


async def memory_extraction_node(state: AICompanionState):
    logger.debug("Starting memory extraction node processing")
    try:
        if not state["messages"]:
            logger.debug("No messages to process")
            return {}

        memory_manager = get_memory_manager()
        await memory_manager.extract_and_store_memories(state["messages"][-1])
        logger.debug("Memory extraction completed")
        return {}
    except Exception as e:
        logger.error(f"Error in memory extraction node: {e}", exc_info=True)
        raise


def memory_injection_node(state: AICompanionState):
    """Retrieve and inject relevant memories into the character card."""
    memory_manager = get_memory_manager()

    # Get relevant memories based on recent conversation
    recent_context = " ".join([m.content for m in state["messages"][-3:]])
    memories = memory_manager.get_relevant_memories(recent_context)

    # Format memories for the character card
    memory_context = memory_manager.format_memories_for_prompt(memories)

    return {"memory_context": memory_context}
