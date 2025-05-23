import logging
import uuid

import chainlit as cl
from langchain_core.messages import AIMessageChunk, HumanMessage
# Remove SQLite import
# from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from ai_companion.graph.graph import (
    create_workflow_graph,
)  # Import the graph factory function
from ai_companion.modules.image import ImageToText
from ai_companion.modules.speech import SpeechToText, TextToSpeech
from ai_companion.graph.nodes import (
    get_patient_id_from_platform_id,
)  # Import patient_id helper
from ai_companion.modules.memory.service import get_memory_service


# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Global module instances
speech_to_text = SpeechToText()
text_to_speech = TextToSpeech()
image_to_text = ImageToText()
memory_service = get_memory_service()  # Add memory service instance


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session"""
    thread_id = str(uuid.uuid4())  # Generate unique thread ID
    cl.user_session.set("thread_id", thread_id)
    logger.info(f"Started new chat session with thread ID: {thread_id}")


@cl.on_message
async def on_message(message: cl.Message):
    """Handle text messages and images with enhanced RAG support"""
    # Initialize message for streaming
    msg = cl.Message(content="")
    await msg.send()  # Start streaming

    # Add processing indicator
    with cl.Step("Processing") as step:
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
        sources_to_display = []

        async with cl.Step(type="run"):
            # Create a unique patient ID or get existing for this session
            patient_id = cl.user_session.get("patient_id")
            if not patient_id:
                user_id = (
                    f"web_{thread_id}"  # Create a unique user ID for web interface
                )
                patient_id = await get_patient_id_from_platform_id("web", user_id)
                cl.user_session.set("patient_id", patient_id)
                logger.info(f"Using patient ID: {patient_id} for web session")

            # Create a new graph instance with user metadata
            graph = create_workflow_graph()
            config = {
                "configurable": {
                    "thread_id": thread_id,
                    "user_metadata": {
                        "platform": "web",
                        "external_system_id": thread_id,
                        "patient_id": patient_id,
                    },
                }
            }

            # Add metadata to the message
            message_metadata = {
                "platform": "web",
                "external_system_id": thread_id,
                "patient_id": patient_id,
            }

            # Create message with metadata
            human_message = HumanMessage(content=content, metadata=message_metadata)

            # Invoke the graph with the message
            async for chunk in graph.astream(
                {"messages": [human_message]},
                config,
                stream_mode="messages",
            ):
                # Handle different types of chunks
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    node_name = chunk[1].get("langgraph_node")
                    chunk_data = chunk[0]

                    if node_name == "rag_node":
                        rag_used = True
                        # Handle streaming chunks from RAG
                        if isinstance(chunk_data, dict):
                            if "chunk" in chunk_data and chunk_data["type"] == "stream":
                                await msg.stream_token(chunk_data["chunk"])
                                has_streamed_content = True
                            elif "rag_response" in chunk_data:
                                rag_info = chunk_data["rag_response"]
                                # Update step with RAG info
                                step.output = f"""
                                    🔍 RAG System Results:
                                    - Found Relevant Info: {rag_info['has_relevant_info']}
                                    - Confidence: {rag_info.get('confidence', 0.0):.2f}
                                    - Sources Used: {len(rag_info.get('sources', []))}
                                    """

                                # Prepare sources for display
                                if rag_info["has_relevant_info"]:
                                    sources_to_display = [
                                        f"📚 {s['title']}\n   🔗 {s['source']}\n   📅 {s['date']}"
                                        for s in rag_info["sources"]
                                    ]

                    elif node_name == "conversation_node":
                        try:
                            if isinstance(chunk_data, AIMessageChunk):
                                await msg.stream_token(chunk_data.content)
                                has_streamed_content = True
                            elif (
                                isinstance(chunk_data, dict)
                                and "messages" in chunk_data
                            ):
                                last_message = chunk_data["messages"][-1]
                                if isinstance(last_message, AIMessageChunk):
                                    await msg.stream_token(last_message.content)
                                    has_streamed_content = True
                                elif hasattr(last_message, "content"):
                                    await msg.stream_token(last_message.content)
                                    has_streamed_content = True
                        except Exception as e:
                            logger.error(f"Error streaming message: {e}")
                            await msg.stream_token(
                                "Atsiprašau, įvyko klaida siunčiant žinutę."
                            )
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
                logger.info(
                    f"✓ Found relevant information: {rag_info['has_relevant_info']}"
                )
                logger.info(f"✓ Confidence: {rag_info.get('confidence', 0.0):.2f}")
                logger.info(
                    f"✓ Number of sources used: {len(rag_info.get('sources', []))}"
                )

                # Add sources as elements if available
                if sources_to_display:
                    sources_element = cl.Text(
                        name="Sources",
                        content="\n\n".join(sources_to_display),
                        language="markdown",
                    )
                    await msg.add_elements([sources_element])
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

#     # Get or create patient ID
#     patient_id = cl.user_session.get("patient_id")
#     if not patient_id:
#         user_id = f"web_{thread_id}"
#         patient_id = await get_patient_id_from_platform_id("web", user_id)
#         cl.user_session.set("patient_id", patient_id)
#
#     # Create config with patient metadata
#     config = {
#         "configurable": {
#             "thread_id": thread_id,
#             "user_metadata": {
#                 "platform": "web",
#                 "external_system_id": thread_id,
#                 "patient_id": patient_id
#             }
#         }
#     }
#
#     # Create message with metadata
#     message_metadata = {
#         "platform": "web",
#         "external_system_id": thread_id,
#         "patient_id": patient_id
#     }
#
#     # Create graph with proper configuration
#     graph = create_workflow_graph()
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
