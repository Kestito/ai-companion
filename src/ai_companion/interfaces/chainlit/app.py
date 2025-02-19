from io import BytesIO
import logging
import uuid

import chainlit as cl
from langchain_core.messages import AIMessageChunk, HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from ai_companion.graph.graph import create_workflow_graph  # Import the graph factory function
from ai_companion.modules.image import ImageToText
from ai_companion.modules.speech import SpeechToText, TextToSpeech

from ai_companion.settings import settings

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Global module instances
speech_to_text = SpeechToText()
text_to_speech = TextToSpeech()
image_to_text = ImageToText()


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session"""
    thread_id = str(uuid.uuid4())  # Generate unique thread ID
    cl.user_session.set("thread_id", thread_id)
    logger.info(f"Started new chat session with thread ID: {thread_id}")


@cl.on_message
async def on_message(message: cl.Message):
    """Handle text messages and images"""
    # Initialize message for streaming
    msg = cl.Message(content="")
    await msg.send()  # Start streaming

    # Process any attached images
    content = message.content
    if message.elements:
        for elem in message.elements:
            if isinstance(elem, cl.Image):
                # Read image file content
                with open(elem.path, "rb") as f:
                    image_bytes = f.read()

                # Analyze image and add to message content
                try:
                    description = await image_to_text.analyze_image(
                        image_bytes,
                        "Please describe what you see in this image in the context of our conversation.",
                    )
                    content += f"\n[Image Analysis: {description}]"
                except Exception as e:
                    cl.logger.warning(f"Failed to analyze image: {e}")

    # Process through graph with enriched message content
    thread_id = cl.user_session.get("thread_id")
    rag_used = False
    rag_info = None
    has_streamed_content = False

    async with cl.Step(type="run"):
        async with AsyncSqliteSaver.from_conn_string(
            settings.SHORT_TERM_MEMORY_DB_PATH
        ) as short_term_memory:
            # Create a new graph instance with the checkpointer
            graph = create_workflow_graph()
            graph.checkpointer = short_term_memory
            
            async for chunk in graph.astream(
                {"messages": [HumanMessage(content=content)]},
                {"configurable": {"thread_id": thread_id}},
                stream_mode="messages",
            ):
                # Log when RAG node is used
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    node_name = chunk[1].get("langgraph_node")
                    chunk_data = chunk[0]
                    
                    if node_name == "rag_node":
                        rag_used = True
                        if isinstance(chunk_data, dict) and "rag_response" in chunk_data:
                            rag_info = chunk_data["rag_response"]
                            logger.info("🔍 RAG System Used:")
                            logger.info(f"- Has Relevant Info: {rag_info['has_relevant_info']}")
                            if rag_info['has_relevant_info']:
                                logger.info(f"- Number of Sources: {len(rag_info['sources'])}")
                    
                    elif node_name == "conversation_node":
                        try:
                            if isinstance(chunk_data, AIMessageChunk):
                                await msg.stream_token(chunk_data.content)
                                has_streamed_content = True
                            elif isinstance(chunk_data, dict) and "messages" in chunk_data:
                                last_message = chunk_data["messages"][-1]
                                if isinstance(last_message, AIMessageChunk):
                                    await msg.stream_token(last_message.content)
                                    has_streamed_content = True
                                elif hasattr(last_message, 'content'):
                                    await msg.stream_token(last_message.content)
                                    has_streamed_content = True
                        except Exception as e:
                            logger.error(f"Error streaming message: {e}")
                            await msg.stream_token("Atsiprašau, įvyko klaida siunčiant žinutę.")
                            has_streamed_content = True

            # Get final state
            output_state = await graph.aget_state(
                config={"configurable": {"thread_id": thread_id}}
            )

    # Log final RAG usage summary
    if rag_used:
        logger.info("\n=== RAG Usage Summary ===")
        logger.info("✓ RAG system was used for this response")
        if rag_info:
            logger.info(f"✓ Found relevant information: {rag_info['has_relevant_info']}")
            if rag_info['has_relevant_info']:
                logger.info(f"✓ Number of sources used: {len(rag_info['sources'])}")
        logger.info("=====================\n")

    # Handle special cases like image responses
    if output_state.values.get("workflow") == "image":
        response = output_state.values["messages"][-1].content
        image = cl.Image(path=output_state.values["image_path"], display="inline")
        # For image responses, create a new message
        await cl.Message(content=response, elements=[image]).send()
    elif not has_streamed_content:
        # If no content was streamed, send a default message
        await msg.stream_token("Atsiprašau, negalėjau sugeneruoti atsakymo.")
    
    # Update the message content to mark it as complete
    await msg.update()

# Temporarily commenting out audio functionality
# @cl.on_audio_chunk
# async def on_audio_chunk(chunk: cl.AudioChunk):
#     """Handle incoming audio chunks"""
#     if chunk.isStart:
#         buffer = BytesIO()
#         buffer.name = f"input_audio.{chunk.mimeType.split('/')[1]}"
#         cl.user_session.set("audio_buffer", buffer)
#         cl.user_session.set("audio_mime_type", chunk.mimeType)
#     cl.user_session.get("audio_buffer").write(chunk.data)


# @cl.on_audio_end
# async def on_audio_end(elements):
#     """Process completed audio input"""
#     # Get audio data
#     audio_buffer = cl.user_session.get("audio_buffer")
#     audio_buffer.seek(0)
#     audio_data = audio_buffer.read()

#     # Show user's audio message
#     input_audio_el = cl.Audio(mime="audio/mpeg3", content=audio_data)
#     await cl.Message(
#         author="You", content="", elements=[input_audio_el, *elements]
#     ).send()

#     # Use global SpeechToText instance
#     transcription = await speech_to_text.transcribe(audio_data)

#     thread_id = cl.user_session.get("thread_id")

#     async with AsyncSqliteSaver.from_conn_string(
#         settings.SHORT_TERM_MEMORY_DB_PATH
#     ) as short_term_memory:
#         # Create a new graph instance with the checkpointer
#         graph = create_workflow_graph()
#         graph.checkpointer = short_term_memory
#         
#         output_state = await graph.ainvoke(
#             {"messages": [HumanMessage(content=transcription)]},
#             {"configurable": {"thread_id": thread_id}},
#         )

#     # Use global TextToSpeech instance
#     audio_buffer = await text_to_speech.synthesize(output_state["messages"][-1].content)

#     output_audio_el = cl.Audio(
#         name="Audio",
#         auto_play=True,
#         mime="audio/mpeg3",
#         content=audio_buffer,
#     )
#     await cl.Message(
#         content=output_state["messages"][-1].content, elements=[output_audio_el]
#     ).send()
