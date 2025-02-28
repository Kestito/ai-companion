import asyncio
import logging
from io import BytesIO
from typing import Dict, Optional, Union, Any
import signal

import httpx
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from ai_companion.graph import graph_builder
from ai_companion.modules.image import ImageToText
from ai_companion.modules.speech import SpeechToText, TextToSpeech
from ai_companion.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global module instances
speech_to_text = SpeechToText()
text_to_speech = TextToSpeech()
image_to_text = ImageToText()

class TelegramBot:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.api_base = settings.TELEGRAM_API_BASE
        self.base_url = f"{self.api_base}/bot{self.token}"
        self.offset = 0
        self.client = httpx.AsyncClient(timeout=60.0)
        self._running = True
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._handle_signal)

    def _handle_signal(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self._running = False

    async def start(self):
        """Start the bot and begin polling for updates."""
        logger.info("Starting Telegram bot...")
        try:
            # Check bot health before starting
            await self._check_health()
            
            me = await self._make_request("getMe")
            logger.info(f"Bot started successfully: @{me['result']['username']}")
            await self._poll_updates()
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise
        finally:
            await self.client.aclose()
            logger.info("Bot shutdown complete")

    async def _check_health(self):
        """Check the health of the bot and its dependencies."""
        logger.info("Performing health check...")
        try:
            # 1. Check if we can connect to Telegram API
            start_time = asyncio.get_event_loop().time()
            me = await self._make_request("getMe")
            api_time = asyncio.get_event_loop().time() - start_time
            
            if not me.get("ok"):
                logger.error(f"Health check failed: Unable to connect to Telegram API")
                raise Exception("Telegram API connection failed")
                
            logger.info(f"Telegram API connection successful ({api_time:.2f}s): @{me['result']['username']}")
            
            # More health checks could be added here:
            # - Database connections
            # - Required external services
            # - Memory usage
            
            logger.info("Health check completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise

    async def _poll_updates(self):
        """Long polling for updates from Telegram."""
        while self._running:
            try:
                # Create params for getUpdates
                params = {
                    "offset": self.offset,
                    "timeout": 30,
                    "allowed_updates": ["message"]
                }
                
                # Get updates with error handling for conflict
                try:
                    updates = await self._make_request("getUpdates", params=params)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 409:
                        # Handle conflict error - reset offset and wait
                        logger.warning("Conflict detected in getUpdates, resetting offset")
                        # Get the latest updates to reset
                        reset_params = {"timeout": 1, "allowed_updates": ["message"]}
                        try:
                            reset_updates = await self._make_request("getUpdates", params=reset_params)
                            if reset_updates.get("result") and len(reset_updates["result"]) > 0:
                                # Update offset to the latest update_id + 1
                                latest = reset_updates["result"][-1]
                                self.offset = latest["update_id"] + 1
                                logger.info(f"Reset offset to {self.offset}")
                            else:
                                # If no updates, advance offset by 1 as a fallback
                                self.offset += 1
                                logger.info(f"No updates found, advanced offset to {self.offset}")
                        except Exception as reset_err:
                            logger.error(f"Failed to reset offset: {reset_err}")
                            self.offset += 1  # Still advance offset as last resort
                        
                        await asyncio.sleep(2)  # Wait before retrying
                        continue
                    else:
                        # Re-raise other HTTP errors
                        raise
                
                # Process each update
                for update in updates.get("result", []):
                    if not self._running:
                        break
                    await self._process_update(update)
                    self.offset = update["update_id"] + 1
                    
            except httpx.TimeoutException:
                logger.debug("Polling timeout, continuing...")
                continue
            except Exception as e:
                if isinstance(e, asyncio.CancelledError):
                    logger.info("Polling cancelled, shutting down...")
                    break
                logger.error(f"Error in polling loop: {e}")
                if self._running:
                    await asyncio.sleep(5)

    async def _process_update(self, update: Dict):
        """Process incoming update from Telegram."""
        message = update.get("message")
        if not message:
            return

        chat_id = message["chat"]["id"]
        session_id = str(chat_id)
        
        try:
            content_result = await self._extract_message_content(message)
            if not content_result or not content_result[0]:
                return

            content, message_type = content_result
            
            # Process message through the graph agent
            async with AsyncSqliteSaver.from_conn_string(
                settings.SHORT_TERM_MEMORY_DB_PATH
            ) as short_term_memory:
                logger.debug("Starting graph processing")
                
                # Create a new graph instance with the checkpointer
                graph = graph_builder.with_config(
                    {"configurable": {"thread_id": session_id}},
                    checkpointer=short_term_memory
                )
                
                # Invoke the graph with the message
                result = await graph.ainvoke(
                    {"messages": [HumanMessage(content=content)]}
                )

                # Debug the result type
                logger.debug(f"Result type: {type(result).__name__}")
                
                # DIRECT FIX: Extract the response message from the result
                # The graph returns a dict with a 'messages' key containing a list of messages
                # The last message in this list is the AI's response
                response_message = None
                workflow = "conversation"  # Default workflow
                
                try:
                    # Case 1: Direct message object
                    if isinstance(result, (AIMessage, BaseMessage)):
                        logger.debug("Processing direct message object")
                        response_message = result.content
                    
                    # Case 2: Dictionary with messages list
                    elif isinstance(result, dict) and "messages" in result:
                        logger.debug("Processing dictionary with messages list")
                        messages = result["messages"]
                        
                        # The messages could be a list or a single message
                        if isinstance(messages, list):
                            # Get the last message in the list
                            if messages:
                                last_message = messages[-1]
                                
                                # Extract content based on message type
                                if isinstance(last_message, (AIMessage, BaseMessage)):
                                    response_message = last_message.content
                                elif isinstance(last_message, dict) and "content" in last_message:
                                    response_message = last_message["content"]
                                else:
                                    response_message = str(last_message)
                        
                        # It could be a single message object
                        elif isinstance(messages, (AIMessage, BaseMessage)):
                            response_message = messages.content
                        
                        # It could be a single message dictionary
                        elif isinstance(messages, dict) and "content" in messages:
                            response_message = messages["content"]
                        
                        # It could be something else we can stringify
                        else:
                            response_message = str(messages)
                    
                    # Case 3: Dictionary with direct content
                    elif isinstance(result, dict) and "content" in result:
                        logger.debug("Processing dictionary with direct content")
                        response_message = result["content"]
                    
                    # Case 4: Any other type - try to convert to string
                    else:
                        logger.warning(f"Unknown result type: {type(result).__name__}")
                        response_message = str(result)
                
                except Exception as e:
                    logger.error(f"Error extracting response: {e}", exc_info=True)
                    response_message = "Sorry, I encountered an error processing your request."
                
                # If we still don't have a response, use a fallback
                if not response_message:
                    logger.warning("Could not extract response message")
                    response_message = "Sorry, I couldn't process your request properly."
                else:
                    logger.debug(f"Successfully extracted response: {response_message[:50]}...")
                
                # Get workflow if present
                if isinstance(result, dict) and "workflow" in result:
                    workflow = result["workflow"]
                
                # Create a safe result dictionary
                safe_result = {"workflow": workflow}
                
                # Send the response
                logger.debug(f"Sending response with workflow: {workflow}")
                await self._send_response(chat_id, response_message, workflow, safe_result, message_type)

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            await self._send_message(chat_id, "Sorry, I encountered an error processing your message.")

    async def _extract_message_content(self, message: Dict) -> Optional[tuple]:
        """Extract content from different types of messages."""
        message_type = None
        
        if "text" in message:
            return message["text"], None
        
        elif "voice" in message:
            file_id = message["voice"]["file_id"]
            audio_data = await self._download_file(file_id)
            transcript = await speech_to_text.transcribe(audio_data)
            # Return both the transcript and mark this as a voice message
            return transcript, "voice"
            
        elif "photo" in message:
            # Get the largest photo (last in array)
            photo = message["photo"][-1]
            file_id = photo["file_id"]
            image_data = await self._download_file(file_id)
            
            caption = message.get("caption", "")
            try:
                description = await image_to_text.analyze_image(
                    image_data,
                    "Please describe what you see in this image in the context of our conversation.",
                )
                return f"{caption}\n[Image Analysis: {description}]", None
            except Exception as e:
                logger.warning(f"Failed to analyze image: {e}")
                return caption or "Image received but could not be analyzed", None
                
        return None, None

    async def _send_response(
        self,
        chat_id: int,
        response_text: str,
        workflow: str,
        result: Union[Dict, Any],
        message_type: Optional[str] = None
    ):
        """Send response based on workflow type."""
        try:
            # Ensure we have a valid response text
            if not response_text or not isinstance(response_text, str):
                logger.warning(f"Invalid response text: {response_text}")
                response_text = "Sorry, I encountered an error generating a response."
            
            logger.info(f"Sending response with workflow '{workflow}', length: {len(response_text)} chars")
            
            # Handle the case where result is not a dictionary
            if not isinstance(result, dict):
                if message_type == "voice":
                    # For voice messages, also generate and send a voice response
                    try:
                        audio_data = await text_to_speech.synthesize(response_text)
                        await self._send_voice(chat_id, audio_data)
                        await self._send_message(chat_id, response_text)
                    except Exception as e:
                        logger.error(f"Error generating voice response: {e}", exc_info=True)
                        await self._send_message(chat_id, response_text)
                else:
                    await self._send_message(chat_id, response_text)
                return

            # Handle different workflow types with appropriate response formats
            if workflow == "audio":
                audio_buffer = result.get("audio_buffer")
                if audio_buffer:
                    await self._send_voice(chat_id, audio_buffer, response_text)
                else:
                    await self._send_message(chat_id, response_text)
            
            elif workflow == "image":
                image_path = result.get("image_path")
                if image_path:
                    try:
                        with open(image_path, "rb") as f:
                            image_data = f.read()
                        await self._send_photo(chat_id, image_data, response_text)
                    except FileNotFoundError:
                        logger.error(f"Image file not found: {image_path}")
                        await self._send_message(chat_id, response_text)
                else:
                    await self._send_message(chat_id, response_text)
            
            elif message_type == "voice":
                # For voice input messages, also generate and send a voice response
                try:
                    audio_data = await text_to_speech.synthesize(response_text)
                    await self._send_voice(chat_id, audio_data)
                    await self._send_message(chat_id, response_text)
                except Exception as e:
                    logger.error(f"Error generating voice response: {e}", exc_info=True)
                    await self._send_message(chat_id, response_text)
            
            else:  # Default to conversation workflow
                await self._send_message(chat_id, response_text)
                
            logger.info(f"Successfully sent response to chat {chat_id}")
                
        except Exception as e:
            logger.error(f"Error sending response: {e}", exc_info=True)
            try:
                # Try to send a simplified error message
                simple_msg = "Sorry, I encountered an error sending the response."
                await self._send_message(chat_id, simple_msg)
            except Exception as e2:
                logger.error(f"Failed to send error message: {e2}", exc_info=True)

    async def _send_message(self, chat_id: int, text: str) -> Dict:
        """Send text message with chunking for long messages."""
        # Telegram has a 4096 character limit per message
        MAX_MESSAGE_LENGTH = 4000  # Using 4000 to be safe
        
        if not text:
            logger.warning("Attempted to send empty message")
            return {"ok": False, "description": "Empty message"}
            
        # Check if we need to split the message
        if len(text) <= MAX_MESSAGE_LENGTH:
            return await self._send_single_message(chat_id, text)
        
        # Split long messages into chunks
        chunks = []
        for i in range(0, len(text), MAX_MESSAGE_LENGTH):
            chunks.append(text[i:i + MAX_MESSAGE_LENGTH])
            
        logger.info(f"Splitting long message into {len(chunks)} chunks")
        
        # Send each chunk with progress indicator
        results = []
        for i, chunk in enumerate(chunks):
            # Add chunk indicator for multi-part messages
            if len(chunks) > 1:
                chunk_header = f"[Part {i+1}/{len(chunks)}]\n"
                chunk = chunk_header + chunk
            
            result = await self._send_single_message(chat_id, chunk)
            results.append(result)
            
            # Small delay between chunks to avoid rate limiting
            if i < len(chunks) - 1:
                await asyncio.sleep(0.5)
                
        # Return the last result as the overall result
        return results[-1]
        
    async def _send_single_message(self, chat_id: int, text: str) -> Dict:
        """Send a single text message with improved error handling."""
        return await self._make_request(
            "sendMessage",
            params={"chat_id": chat_id, "text": text}
        )

    async def _make_request(
        self,
        method: str,
        params: Dict = None,
        files: Dict = None,
        data: Dict = None,
        retries: int = 5  # Increased from 3 to 5
    ) -> Dict:
        """Make request to Telegram Bot API with improved retry logic and exponential backoff."""
        url = f"{self.base_url}/{method}"
        
        for attempt in range(retries):
            try:
                if files:
                    response = await self.client.post(
                        url, 
                        params=params, 
                        files=files, 
                        data=data,
                        timeout=60.0  # Increased from 30 to 60 seconds
                    )
                else:
                    response = await self.client.post(
                        url, 
                        json=params if params else {},
                        timeout=60.0  # Increased from 30 to 60 seconds
                    )
                
                # Check specifically for 409 Conflict and other client errors
                # Let these propagate up immediately for special handling
                if response.status_code == 409 or (response.status_code >= 400 and response.status_code < 500):
                    response.raise_for_status()
                    
                # For other status codes, use normal error handling
                response.raise_for_status()
                return response.json()
                
            except httpx.TimeoutException:
                if attempt == retries - 1:
                    logger.error(f"Request timed out after {retries} attempts")
                    raise
                # Exponential backoff with jitter
                backoff_time = min(2 ** attempt + (0.1 * attempt), 30)
                logger.warning(f"Request timeout, attempt {attempt + 1}/{retries}, retrying in {backoff_time:.2f}s")
                await asyncio.sleep(backoff_time)
                
            except httpx.HTTPStatusError as e:
                # Don't retry for client errors - let the caller handle these
                if e.response.status_code == 409 or (400 <= e.response.status_code < 500):
                    raise
                
                if attempt == retries - 1:
                    logger.error(f"API request failed after {retries} attempts: {e}")
                    raise
                    
                # Exponential backoff with jitter for server errors
                backoff_time = min(2 ** attempt + (0.1 * attempt), 30)
                logger.warning(f"Request failed with status {e.response.status_code}, attempt {attempt + 1}/{retries}, retrying in {backoff_time:.2f}s: {e}")
                await asyncio.sleep(backoff_time)
                
            except Exception as e:
                if attempt == retries - 1:
                    logger.error(f"API request failed after {retries} attempts: {e}")
                    raise
                    
                # Exponential backoff with jitter for other errors
                backoff_time = min(2 ** attempt + (0.1 * attempt), 30)
                logger.warning(f"Request failed, attempt {attempt + 1}/{retries}, retrying in {backoff_time:.2f}s: {e}")
                await asyncio.sleep(backoff_time)

    async def _download_file(self, file_id: str) -> bytes:
        """Download file from Telegram servers."""
        try:
            # Get file path
            file_info = await self._make_request("getFile", params={"file_id": file_id})
            file_path = file_info["result"]["file_path"]
            
            # Download file
            download_url = f"{self.api_base}/file/bot{self.token}/{file_path}"
            response = await self.client.get(download_url)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            raise

    async def _send_photo(self, chat_id: int, photo: bytes, caption: str = None) -> Dict:
        """Send photo message with proper handling of long captions."""
        files = {"photo": ("image.jpg", photo, "image/jpeg")}
        data = {"chat_id": chat_id}
        
        # Telegram has a 1024 character limit for photo captions
        MAX_CAPTION_LENGTH = 1000  # Using 1000 to be safe
        
        if not caption:
            return await self._make_request("sendPhoto", data=data, files=files)
        
        # If caption is short enough, send it with the photo
        if len(caption) <= MAX_CAPTION_LENGTH:
            data["caption"] = caption
            return await self._make_request("sendPhoto", data=data, files=files)
        
        # For long captions, send the photo first, then the caption as a separate message
        logger.info(f"Caption too long ({len(caption)} chars), sending separately")
        photo_result = await self._make_request("sendPhoto", data=data, files=files)
        
        # Send a shorter caption with the photo to give context
        short_caption = caption[:MAX_CAPTION_LENGTH] + "..."
        data["caption"] = short_caption
        await self._make_request("sendPhoto", data=data, files=files)
        
        # Send the full caption as a separate message
        await self._send_message(chat_id, caption)
        
        return photo_result

    async def _send_voice(self, chat_id: int, voice: bytes, caption: str = None) -> Dict:
        """Send voice message with proper handling of captions."""
        files = {"voice": ("voice.ogg", voice, "audio/ogg")}
        data = {"chat_id": chat_id}
        
        # Send voice message first
        voice_result = await self._make_request("sendVoice", data=data, files=files)
        
        # Send caption as a separate message if provided
        if caption and isinstance(caption, str) and caption.strip():
            await self._send_message(chat_id, caption)
            
        return voice_result

async def run_telegram_bot():
    """Run the Telegram bot with proper shutdown handling."""
    bot = TelegramBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Bot encountered an error: {e}", exc_info=True)
        raise
    finally:
        bot._running = False

if __name__ == "__main__":
    asyncio.run(run_telegram_bot()) 