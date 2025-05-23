import logging
from io import BytesIO
from typing import Dict

import httpx
from fastapi import APIRouter, Request, Response
from langchain_core.messages import HumanMessage

from ai_companion.graph import graph_builder
from ai_companion.modules.image import ImageToText
from ai_companion.modules.speech import SpeechToText, TextToSpeech
from ai_companion.modules.memory.service import get_memory_service
from ai_companion.graph.nodes import get_patient_id_from_platform_id


# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global module instances
speech_to_text = SpeechToText()
text_to_speech = TextToSpeech()
image_to_text = ImageToText()
memory_service = get_memory_service()  # Initialize memory service

# Router for WhatsApp responses with path-based routing
whatsapp_router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

# WhatsApp API credentials from settings
WHATSAPP_TOKEN = "EAAOp6lp8Xt4BO2BVhmHXMuAvwI1gXhi53y9OUDJs412MSnKtAo5FtVhyMqqMrU2y9ZBeZCtN9zSFhJ1WHN65wCX2jUcN3aBTpk4bVS2dAHjY5EJKxkWXGaMIuvTkZBJB4FKwpidRcy61d9GCOni3ZB8mXP6qr9HXx7poi75Wc00KbY2KfdbY2uIzoWIUXsVZBCgZDZD"
WHATSAPP_PHONE_NUMBER_ID = "566612569868882"
WHATSAPP_VERIFY_TOKEN = "xxx"

# Add debug logging for environment variables
logger.debug(f"WHATSAPP_TOKEN: {'Set' if WHATSAPP_TOKEN else 'Not Set'}")
logger.debug(
    f"WHATSAPP_PHONE_NUMBER_ID: {'Set' if WHATSAPP_PHONE_NUMBER_ID else 'Not Set'}"
)
logger.debug(f"WHATSAPP_VERIFY_TOKEN: {'Set' if WHATSAPP_VERIFY_TOKEN else 'Not Set'}")


@whatsapp_router.api_route("/webhook", methods=["GET", "POST"])
async def whatsapp_handler(request: Request) -> Response:
    logger.debug("Received WhatsApp request")
    logger.debug(f"Method: {request.method}")

    if request.method == "GET":
        params = request.query_params
        logger.debug(f"Query params: {params}")
        if params.get("hub.verify_token") == WHATSAPP_VERIFY_TOKEN:
            logger.info("Verification token matched successfully")
            return Response(content=params.get("hub.challenge"), status_code=200)
        logger.warning("Verification token mismatch")
        return Response(content="Verification token mismatch", status_code=403)

    try:
        data = await request.json()
        logger.debug(f"Received webhook data: {data}")

        change_value = data["entry"][0]["changes"][0]["value"]
        logger.debug(f"Change value: {change_value}")

        if "messages" in change_value:
            message = change_value["messages"][0]
            from_number = message["from"]
            session_id = from_number
            logger.info(f"Processing message from {from_number}")
            logger.debug(f"Message content: {message}")

            # Get user message and handle different message types
            content = ""
            is_voice_message = False
            if message["type"] == "audio":
                logger.info("Processing audio message")
                content = await process_audio_message(message)
                logger.debug(f"Transcribed content: {content}")
                is_voice_message = True
            elif message["type"] == "image":
                logger.info("Processing image message")
                # Get image caption if any
                content = message.get("image", {}).get("caption", "")
                # Download and analyze image
                image_bytes = await download_media(message["image"]["id"])
                try:
                    description = await image_to_text.analyze_image(
                        image_bytes,
                        "Please describe what you see in this image in the context of our conversation.",
                    )
                    content += f"\n[Image Analysis: {description}]"
                except Exception as e:
                    logger.warning(f"Failed to analyze image: {e}")
            else:
                content = message["text"]["body"]
                logger.info(f"Received text message: {content}")

            # Process message through the graph agent
            logger.debug("Starting graph processing")
            try:
                # Create a unique patient ID or get existing one
                patient_id = await get_patient_id_from_platform_id(
                    "whatsapp", from_number
                )
                if not patient_id:
                    logger.warning(
                        f"No patient ID found for WhatsApp user {from_number}"
                    )
                    # Default to using the WhatsApp number itself as identifier
                    patient_id = f"whatsapp:{from_number}"

                # Create a new graph instance with user metadata
                config = {
                    "configurable": {
                        "thread_id": session_id,
                        "user_metadata": {
                            "platform": "whatsapp",
                            "external_system_id": from_number,
                            "patient_id": patient_id,
                        },
                    }
                }
                logger.debug(f"Graph configuration set with patient_id: {patient_id}")

                # Set metadata on the message
                message_metadata = {
                    "platform": "whatsapp",
                    "external_system_id": from_number,
                    "patient_id": patient_id,
                }

                # Invoke the graph with the message
                result = await graph_builder.ainvoke(
                    {
                        "messages": [
                            HumanMessage(content=content, metadata=message_metadata)
                        ]
                    },
                    config,
                )
                logger.debug("Graph invocation completed")

                # Get the workflow type and response from the state
                output_state = await graph_builder.aget_state(config)
                logger.debug(f"Retrieved state: {output_state}")
            except Exception as e:
                logger.error(f"Error during graph processing: {e}", exc_info=True)
                return Response(content="Error processing message", status_code=500)

            workflow = output_state.values.get("workflow", "conversation")
            response_message = output_state.values["messages"][-1].content
            logger.debug(f"Workflow: {workflow}, Response: {response_message}")

            # Handle different response types based on workflow
            if workflow == "audio":
                audio_buffer = output_state.values["audio_buffer"]
                success = await send_response(
                    from_number, response_message, "audio", audio_buffer
                )
            elif workflow == "image":
                image_path = output_state.values["image_path"]
                with open(image_path, "rb") as f:
                    image_data = f.read()
                success = await send_response(
                    from_number, response_message, "image", image_data
                )
            elif is_voice_message:
                # For voice input messages, also generate and send a voice response
                try:
                    audio_buffer = await text_to_speech.synthesize(response_message)
                    # First send the voice response
                    voice_success = await send_response(
                        from_number, response_message, "audio", audio_buffer
                    )
                    # Then send the text response
                    text_success = await send_response(
                        from_number, response_message, "text"
                    )
                    success = voice_success and text_success
                except Exception as e:
                    logger.error(f"Error generating voice response: {e}", exc_info=True)
                    # Fall back to text-only response
                    success = await send_response(from_number, response_message, "text")
            else:
                success = await send_response(from_number, response_message, "text")

            if not success:
                return Response(content="Failed to send message", status_code=500)

            return Response(content="Message processed", status_code=200)

        elif "statuses" in change_value:
            return Response(content="Status update received", status_code=200)

        else:
            return Response(content="Unknown event type", status_code=400)

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return Response(content="Internal server error", status_code=500)


@whatsapp_router.get("/health")
async def health_check():
    """Health check endpoint for WhatsApp webhook."""
    return {"status": "healthy", "service": "whatsapp"}


async def download_media(media_id: str) -> bytes:
    logger.debug(f"Downloading media with ID: {media_id}")
    media_metadata_url = f"https://graph.facebook.com/v22.0/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}

    async with httpx.AsyncClient() as client:
        metadata_response = await client.get(media_metadata_url, headers=headers)
        metadata_response.raise_for_status()
        metadata = metadata_response.json()
        download_url = metadata.get("url")

        media_response = await client.get(download_url, headers=headers)
        media_response.raise_for_status()
        return media_response.content


async def process_audio_message(message: Dict) -> str:
    logger.debug(f"Processing audio message: {message}")
    audio_id = message["audio"]["id"]
    media_metadata_url = f"https://graph.facebook.com/v22.0/{audio_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}

    async with httpx.AsyncClient() as client:
        metadata_response = await client.get(media_metadata_url, headers=headers)
        metadata_response.raise_for_status()
        metadata = metadata_response.json()
        download_url = metadata.get("url")

    # Download the audio file
    async with httpx.AsyncClient() as client:
        audio_response = await client.get(download_url, headers=headers)
        audio_response.raise_for_status()

    # Prepare for transcription
    audio_buffer = BytesIO(audio_response.content)
    audio_buffer.seek(0)
    audio_data = audio_buffer.read()

    return await speech_to_text.transcribe(audio_data)


async def send_response(
    from_number: str,
    response_text: str,
    message_type: str = "text",
    media_content: bytes = None,
) -> bool:
    logger.debug(f"Sending {message_type} response to {from_number}")
    logger.debug(f"Response text: {response_text}")
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    if message_type in ["audio", "image"]:
        try:
            mime_type = "audio/mpeg" if message_type == "audio" else "image/png"
            media_buffer = BytesIO(media_content)
            media_id = await upload_media(media_buffer, mime_type)
            json_data = {
                "messaging_product": "whatsapp",
                "to": from_number,
                "type": message_type,
                message_type: {"id": media_id},
            }

            # Add caption for images
            if message_type == "image":
                json_data["image"]["caption"] = response_text
        except Exception as e:
            logger.error(f"Media upload failed, falling back to text: {e}")
            message_type = "text"

    if message_type == "text":
        json_data = {
            "messaging_product": "whatsapp",
            "to": from_number,
            "type": "text",
            "text": {"body": response_text},
        }

    print(headers)
    print(json_data)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://graph.facebook.com/v22.0/{WHATSAPP_PHONE_NUMBER_ID}/messages",
            headers=headers,
            json=json_data,
        )

    return response.status_code == 200


async def upload_media(media_content: BytesIO, mime_type: str) -> str:
    """Upload media to WhatsApp servers."""
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    files = {"file": ("response.mp3", media_content, mime_type)}
    data = {"messaging_product": "whatsapp", "type": mime_type}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://graph.facebook.com/v22.0/{WHATSAPP_PHONE_NUMBER_ID}/media",
            headers=headers,
            files=files,
            data=data,
        )
        result = response.json()

    if "id" not in result:
        raise Exception("Failed to upload media")
    return result["id"]
