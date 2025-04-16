import asyncio
import logging
from io import BytesIO
from typing import Dict, Optional, Union, Any, List
import signal
import json
import uuid
from datetime import datetime, timedelta
import sqlite3
import os

import httpx
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from ai_companion.graph import graph_builder
from ai_companion.modules.image import ImageToText
from ai_companion.modules.speech import SpeechToText, TextToSpeech
from ai_companion.settings import settings
from ai_companion.utils.supabase import get_supabase_client
from ai_companion.modules.memory.short_term import get_short_term_memory_manager, ShortTermMemoryManager

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
        self.memory_manager = get_short_term_memory_manager()
        self.supabase = get_supabase_client()
        
        # Setup checkpoint directory
        self.checkpoint_dir = os.path.join(os.getcwd(), "data", "checkpoints")
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        
        if not self.supabase:
            logger.error("Failed to initialize Supabase client for memory storage")

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
            
            # 2. Check if we can connect to Supabase for memory storage
            try:
                # Check Supabase connection via memory manager
                test_memories = await self.memory_manager.get_active_memories()
                logger.info(f"Supabase connection successful, found {len(test_memories)} active memories")
            except Exception as e:
                logger.warning(f"Supabase memory check warning: {e}")
                # Not critical, continue with warning
            
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
        try:
            # Extract message from update
            if "message" not in update:
                logger.warning(f"Update contains no message: {update}")
                return
            
            message = update["message"]
            chat_id = message.get("chat", {}).get("id")
            user_id = message.get("from", {}).get("id")
            
            if not chat_id or not user_id:
                logger.warning(f"Missing chat_id or user_id in message: {message}")
                return
            
            # Check if this is a file or text message
            message_type = None
            content = None
            
            # Generate a unique session ID for this chat
            session_id = f"telegram-{chat_id}-{user_id}"
            
            # Extract message content based on type
            if "text" in message:
                message_type = "text"
                content = message["text"]
            elif "voice" in message:
                message_type = "voice"
                file_id = message["voice"]["file_id"]
                voice_data = await self._download_file(file_id)
                
                # Convert voice to text
                content = await speech_to_text.transcribe(voice_data)
                logger.info(f"Transcribed voice message: {content}")
            elif "photo" in message:
                message_type = "photo"
                # Get the largest photo (last in array)
                file_id = message["photo"][-1]["file_id"]
                photo_data = await self._download_file(file_id)
                
                # Extract text from image
                content = await image_to_text.process_image(photo_data)
                logger.info(f"Extracted text from image: {content}")
            else:
                # Handle other message types or send a response about unsupported format
                logger.warning(f"Unsupported message type: {message}")
                await self._send_message(chat_id, 
                    "I can process text, voice messages, and images. Please send one of these formats.")
                return
            
            # Collect user metadata
            username = message.get("from", {}).get("username")
            first_name = message.get("from", {}).get("first_name", "")
            last_name = message.get("from", {}).get("last_name", "")
            
            user_metadata = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "chat_id": chat_id,
                "platform": "telegram"
            }
            
            # Create metadata for memory storage
            memory_metadata = {
                "user_id": user_id,
                "chat_id": chat_id,
                "session_id": session_id,
                "message_type": message_type
            }
            
            # Process message through the graph agent using memory manager for persistence
            try:
                logger.debug("Starting graph processing")
                
                # Get complete conversation history combining memory and database
                conversation_history = await self._get_conversation_history(chat_id, user_id, max_messages=10)
                
                # Format conversation history for better context retention
                formatted_history = []
                if conversation_history:
                    # Convert conversation history to a format the LLM can better understand
                    for entry in conversation_history:
                        if "user_message" in entry and "bot_response" in entry:
                            formatted_history.append({
                                "role": "human", 
                                "content": entry.get("user_message", "")
                            })
                            formatted_history.append({
                                "role": "ai", 
                                "content": entry.get("bot_response", "")
                            })
                
                # Create a context object with thread_id
                context = {
                    "thread_id": session_id,
                    "user_id": user_id,
                    "chat_id": chat_id
                }

                # Instead of using SQLite for checkpointing, use Supabase
                # First check if there's an existing memory record for this session
                memory_exists = False
                memory_data = None
                
                if self.supabase:
                    try:
                        # Query for existing memory - need to get all records and filter
                        # since session_id is inside the context JSON
                        result = self.supabase.table("short_term_memory").select("*").order("expires_at", desc=True).limit(20).execute()
                        
                        if result.data:
                            # Filter records that have session_id in their context metadata
                            for record in result.data:
                                context = record.get("context", {})
                                metadata = context.get("metadata", {})
                                if metadata and metadata.get("session_id") == session_id:
                                    memory_exists = True
                                    memory_data = record
                                    logger.info(f"Found existing memory in Supabase for session {session_id}")
                                    break
                    except Exception as e:
                        logger.error(f"Error checking for existing memory: {e}")
                
                # Setup checkpointer for the graph - ensure it's properly initialized
                checkpoint_file = os.path.join(self.checkpoint_dir, f"{session_id}.json")
                checkpointer = AsyncSqliteSaver(checkpoint_file)
                
                # Create a graph instance with embedded checkpointer
                config = {
                    "configurable": {
                        "thread_id": session_id,
                        "memory_exists": memory_exists,
                        "checkpointer": checkpointer  # Add checkpointer directly to graph config
                    }
                }
                
                # Inject existing memory if found
                if memory_exists and memory_data and "state" in memory_data:
                    config["configurable"]["existing_memory"] = memory_data.get("state", {})
                
                # Create a new graph instance with config
                graph = graph_builder.with_config(config)
                
                # Create HumanMessage with metadata
                human_message = HumanMessage(content=content, metadata={
                    **user_metadata,
                    "conversation_history": formatted_history,  # Use formatted history
                    "previous_interactions": len(formatted_history) // 2,  # Count of previous turns
                    "detailed_response": True,  # Request detailed RAG responses
                    "with_citations": True  # Include citations in responses
                })
                
                # Invoke the graph with the message using the checkpointer config
                result = await graph.ainvoke(
                    {"messages": [human_message]}
                    # No need for separate config here since checkpointer is in graph config
                )

                # Debug the result type
                logger.debug(f"Result type: {type(result).__name__}")
                
                # Extract the response message from the result
                # The graph returns a dict with a 'messages' key containing a list of messages
                # The last message in this list is the AI's response
                response_message = None
                workflow = "conversation"
                
                # Handle different result types
                if isinstance(result, dict) and "messages" in result:
                    messages = result["messages"]
                    if messages and len(messages) > 0:
                        last_message = messages[-1]
                        if isinstance(last_message, AIMessage):
                            response_message = last_message.content
                            
                            # Check for workflow directives in the message metadata
                            if hasattr(last_message, "metadata") and last_message.metadata:
                                metadata = last_message.metadata
                                # Check if workflow is explicitly defined
                                if "workflow" in metadata:
                                    workflow = metadata["workflow"]
                    elif "error" in result:
                        response_message = f"I encountered an error: {result['error']}"
                    else:
                        response_message = "I'm not sure how to respond to that."
                elif isinstance(result, dict) and "response" in result:
                    # For custom output formats
                    response_message = result["response"]
                    
                    # Check for workflow specification
                    if "workflow" in result:
                        workflow = result["workflow"]
                elif isinstance(result, str):
                    # Simple string response
                    response_message = result
                else:
                    # Fallback for unrecognized format
                    logger.warning(f"Unrecognized result format: {type(result)}")
                    response_message = "I processed your message but couldn't formulate a proper response."
                
                # Safe version of result for passing to response handler
                safe_result = {}
                if isinstance(result, dict):
                    # Only include safe keys that don't contain large data
                    for key, value in result.items():
                        if key not in ["full_context", "embeddings", "raw_response"]:
                            safe_result[key] = value
                
                # Get the graph state to store
                graph_state = {}
                try:
                    # Get the graph state - no need to pass checkpointer again
                    graph_state = await graph.aget_state()
                except Exception as e:
                    logger.error(f"Error getting graph state: {e}")
                
                # Format the conversation context according to the correct schema
                conversation_context = {
                    "conversation": {
                        "user_message": content,
                        "bot_response": response_message,
                        "timestamp": datetime.now().isoformat()
                    },
                    "metadata": {
                        "session_id": session_id,
                        "user_id": str(user_id),
                        "chat_id": str(chat_id),
                        "platform": "telegram",
                        "message_type": message_type
                    },
                    "state": graph_state
                }
                
                # Format the memory data according to the correct schema
                memory_data = {
                    "id": str(uuid.uuid4()),
                    "context": conversation_context,
                    "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
                }
                
                # Add patient_id if available
                if isinstance(result, dict) and "patient_id" in result:
                    patient_id = result["patient_id"]
                    memory_data["patient_id"] = patient_id
                
                # Add conversation_id if available
                if isinstance(result, dict) and "conversation_id" in result:
                    conversation_id = result["conversation_id"]
                    memory_data["conversation_id"] = conversation_id
                
                # Store in Supabase - with retries on failure
                if self.supabase:
                    for retry_attempt in range(3):  # Try up to 3 times
                        try:
                            memory_result = self.supabase.table("short_term_memory").insert(memory_data).execute()
                            if memory_result.data and len(memory_result.data) > 0:
                                memory_id = memory_result.data[0].get("id")
                                logger.info(f"Stored memory in Supabase: {memory_id}")
                                break
                            else:
                                logger.warning(f"Failed to get memory ID from Supabase (attempt {retry_attempt+1}/3)")
                        except Exception as e:
                            logger.error(f"Error storing memory in Supabase (attempt {retry_attempt+1}/3): {e}")
                            if retry_attempt < 2:  # Only sleep if we're going to retry
                                await asyncio.sleep(1 * (retry_attempt + 1))  # Simple backoff
                
                # NEW CODE: Save the conversation to the database
                patient_id = None
                if isinstance(result, dict) and "patient_id" in result:
                    patient_id = result["patient_id"]
                
                conversation_id = await self._save_to_database(
                    user_metadata, 
                    content, 
                    response_message,
                    patient_id
                )
                
                # Send the response
                logger.debug(f"Sending response with workflow: {workflow}")
                await self._send_response(chat_id, response_message, workflow, safe_result, message_type)
            
            except Exception as e:
                logger.error(f"Error in graph processing: {e}", exc_info=True)
                await self._send_message(chat_id, "Sorry, I encountered an error processing your message.")

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

    def _clean_response_text(self, text: str) -> str:
        """
        Remove markdown formatting symbols from response text.
        
        Args:
            text: The response text to clean
            
        Returns:
            Cleaned text without markdown symbols
        """
        if not text:
            return text
        
        # Remove asterisks (used for bold formatting in markdown)
        cleaned_text = text.replace("*", "")
        
        # Other potential formatting to clean if needed:
        # cleaned_text = cleaned_text.replace("_", "")  # Remove underscores (italic)
        # cleaned_text = cleaned_text.replace("`", "")  # Remove backticks (code)
        
        return cleaned_text

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
            
            # Clean response text to remove markdown formatting
            response_text = self._clean_response_text(response_text)
            
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
        
        # Clean caption to remove markdown formatting
        if caption:
            caption = self._clean_response_text(caption)
        
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
        
        # Clean and send caption as a separate message if provided
        if caption and isinstance(caption, str) and caption.strip():
            caption = self._clean_response_text(caption)
            await self._send_message(chat_id, caption)
        
        return voice_result

    async def _save_to_database(
        self, 
        user_metadata: Dict[str, Any], 
        user_message: str, 
        bot_response: str,
        patient_id: Optional[str] = None
    ) -> Optional[str]:
        """Save conversation to database with proper error handling."""
        try:
            # Get Supabase client
            supabase = get_supabase_client()
            
            if not supabase:
                logger.error("Failed to initialize Supabase client for database save")
                return None
                
            # Extract user details
            user_id = user_metadata.get("user_id")
            chat_id = user_metadata.get("chat_id")  # Extract chat_id from user_metadata
            platform = user_metadata.get("platform", "telegram")
            first_name = user_metadata.get("first_name", "")
            last_name = user_metadata.get("last_name", "")
            
            # Prepare user data for lookup or creation
            user_data = {
                "platform_id": str(user_id),
                "first_name": first_name,
                "last_name": last_name,
                "name": f"{first_name} {last_name}".strip(),
                "last_active": datetime.now().isoformat()
            }
            
            patient_info = {}
            created_new_patient = False
            
            # Check if we have an existing patient ID for this user
            if not patient_id:
                try:
                    # Look up patient by platform ID - using email field as metadata storage
                    # Store platform info in metadata JSON
                    platform_query = f'%"platform_id": "{user_id}"%'
                    result = supabase.table("patients").select("id").like("email", platform_query).execute()
                    
                    if result.data and len(result.data) > 0:
                        patient_id = result.data[0]["id"]
                        logger.info(f"Found existing patient: {patient_id}")
                        
                        # Update last_active timestamp
                        supabase.table("patients").update({"last_active": datetime.now().isoformat()}).eq("id", patient_id).execute()
                    else:
                        # Create new patient record
                        platform_metadata = {
                            "platform": platform,
                            "platform_id": str(user_id)
                        }
                        
                        new_patient = {
                            "first_name": first_name,
                            "last_name": last_name,
                            # Remove name field as it doesn't exist in the schema
                            "email": json.dumps(platform_metadata),  # Store platform info in email field
                            "channel": platform,  # Use channel instead of platform
                            "risk": "Low",
                            "created_at": datetime.now().isoformat(),
                            "last_active": datetime.now().isoformat(),
                            "preferred_language": "en",
                            "subsidy_eligible": False,
                            "legal_consents": {},
                            "support_status": "active"
                        }
                        
                        result = supabase.table("patients").insert(new_patient).execute()
                        
                        if result.data and len(result.data) > 0:
                            patient_id = result.data[0]["id"]
                            patient_info = new_patient
                            created_new_patient = True
                            logger.info(f"Created new patient: {patient_id}")
                        else:
                            logger.error("Failed to create patient record")
                            return None
                except Exception as e:
                    logger.error(f"Error looking up/creating patient: {e}")
                    return None
            
            # With patient_id confirmed, check for existing active conversation
            try:
                # Look for active conversation in last 15 minutes
                fifteen_min_ago = (datetime.now() - timedelta(minutes=15)).isoformat()
                
                # Use patient_id for conversation lookup
                result = supabase.table("conversations").select("id").eq("patient_id", patient_id).gt("start_time", fifteen_min_ago).eq("status", "active").execute()
                
                conversation_id = None
                
                if result.data and len(result.data) > 0:
                    # Use existing conversation
                    conversation_id = result.data[0]["id"]
                    logger.info(f"Found active conversation: {conversation_id}")
                    
                    # Update end_time
                    supabase.table("conversations").update({
                        "end_time": datetime.now().isoformat()
                    }).eq("id", conversation_id).execute()
                else:
                    # Create new conversation
                    conversation_data = {
                        "patient_id": patient_id,
                        "platform": platform,  # Use platform instead of platform_type
                        "start_time": datetime.now().isoformat(),
                        "end_time": datetime.now().isoformat(),
                        "conversation_type": "general",
                        "status": "active"
                    }
                    
                    result = supabase.table("conversations").insert(conversation_data).execute()
                    
                    if result.data and len(result.data) > 0:
                        conversation_id = result.data[0]["id"]
                        logger.info(f"Created new conversation: {conversation_id}")
                    else:
                        logger.error("Failed to create conversation record")
                        return None
                
                # Now save the user message
                user_message_data = {
                    "conversation_id": conversation_id,
                    "message_content": user_message,
                    "message_type": "text",
                    "sent_at": datetime.now().isoformat(),
                    "sender": "patient",
                    "metadata": {}
                }
                
                supabase.table("conversation_details").insert(user_message_data).execute()
                
                # Save the bot response
                bot_message_data = {
                    "conversation_id": conversation_id,
                    "message_content": bot_response,
                    "message_type": "text",
                    "sent_at": datetime.now().isoformat(),
                    "sender": "evelina",
                    "metadata": {}
                }
                
                supabase.table("conversation_details").insert(bot_message_data).execute()
                
                # Also save to short_term_memory table for database consistency
                try:
                    # Create a context object with both messages
                    context_data = {
                        "conversation": {
                            "user_message": user_message,
                            "bot_response": bot_response,
                            "timestamp": datetime.now().isoformat()
                        },
                        "metadata": {
                            "session_id": f"telegram-{chat_id}-{user_id}",
                            "user_id": str(user_id),
                            "chat_id": str(chat_id),
                            "platform": "telegram"
                        },
                        "state": {}  # Empty state since we don't have the graph state here
                    }
                    
                    # Set expiry for 30 minutes from now
                    expires_at = (datetime.now() + timedelta(minutes=30)).isoformat()
                    
                    memory_data = {
                        "id": str(uuid.uuid4()),
                        "patient_id": patient_id,
                        "conversation_id": conversation_id,
                        "context": context_data,
                        "expires_at": expires_at
                    }
                    
                    supabase.table("short_term_memory").insert(memory_data).execute()
                except Exception as e:
                    # Non-critical, just log the error
                    logger.warning(f"Failed to save to short_term_memory table: {e}")
                
                # If we created a new patient or found one, update any existing memories
                if patient_id and user_id:
                    await self._update_memory_with_patient_info(user_id, patient_id, patient_info)
                
                # Return the conversation ID for reference
                return conversation_id
                
            except Exception as e:
                logger.error(f"Error creating/updating conversation: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            return None

    async def _get_recent_memories(self, chat_id: int, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve recent memories for a specific user/chat combination.
        
        Args:
            chat_id: The Telegram chat ID
            user_id: The Telegram user ID
            limit: Maximum number of memories to retrieve
            
        Returns:
            List of memory contents as dictionaries
        """
        try:
            # Create session ID in the same format used when storing
            session_id = f"telegram-{chat_id}-{user_id}"
            
            # Get active memories
            memories = await self.memory_manager.get_active_memories()
            
            # Filter memories for this session
            session_memories = []
            for memory in memories:
                if memory.metadata.get("session_id") == session_id:
                    try:
                        # Parse the JSON content
                        content = json.loads(memory.content)
                        # Add memory metadata and ID
                        content["memory_id"] = memory.id
                        content["created_at"] = memory.created_at.isoformat()
                        content["expires_at"] = memory.expires_at.isoformat()
                        session_memories.append(content)
                    except json.JSONDecodeError:
                        self.logger.warning(f"Failed to parse memory content: {memory.content[:50]}...")
            
            # Sort by timestamp if available
            session_memories.sort(
                key=lambda m: m.get("timestamp", ""),
                reverse=True  # Most recent first
            )
            
            # Limit results
            return session_memories[:limit]
        except Exception as e:
            self.logger.error(f"Error retrieving recent memories: {e}")
            return []

    async def _update_memory_with_patient_info(self, user_id: int, patient_id: str, patient_info: Dict[str, Any]) -> None:
        """
        Update existing memories with patient information when it becomes available.
        
        Args:
            user_id: Telegram user ID
            patient_id: Patient ID from database
            patient_info: Additional patient information
        """
        try:
            # Get active memories
            memories = await self.memory_manager.get_active_memories()
            
            # Filter memories for this user
            user_memories = [
                mem for mem in memories 
                if mem.metadata.get("user_id") == user_id and not mem.metadata.get("patient_id")
            ]
            
            if not user_memories:
                return
            
            logger.info(f"Updating {len(user_memories)} memories with patient ID {patient_id}")
            
            # Update each memory with patient information
            for memory in user_memories:
                try:
                    # Update metadata with patient information
                    updated_metadata = memory.metadata.copy()
                    updated_metadata["patient_id"] = patient_id
                    
                    # Update any additional patient info
                    if patient_info:
                        for key, value in patient_info.items():
                            if key not in updated_metadata:
                                updated_metadata[f"patient_{key}"] = value
                    
                    # Store memory content with updated metadata
                    content = memory.content
                    await self.memory_manager.store_memory(
                        content=content,
                        ttl_minutes=60,  # Keep original TTL
                        metadata=updated_metadata
                    )
                    
                    # Delete the old memory
                    await self.memory_manager.delete_memory(memory.id)
                    
                except Exception as e:
                    logger.warning(f"Failed to update memory {memory.id}: {e}")
                
        except Exception as e:
            logger.error(f"Error updating memories with patient info: {e}")

    async def _get_conversation_history(self, chat_id: int, user_id: int, max_messages: int = 10) -> List[Dict[str, Any]]:
        """
        Get conversation history from Supabase short-term memory.
        
        Args:
            chat_id: Telegram chat ID
            user_id: Telegram user ID
            max_messages: Maximum number of messages to retrieve
            
        Returns:
            List of message pairs (user message and bot response)
        """
        try:
            # Generate session ID in the same format used when storing
            session_id = f"telegram-{chat_id}-{user_id}"
            
            # Try to get history from Supabase
            if self.supabase:
                try:
                    # Query for recent memories - need to get all and filter
                    # since session_id is inside the context JSON
                    result = self.supabase.table("short_term_memory")\
                        .select("*")\
                        .order("expires_at", desc=True)\
                        .limit(50)\
                        .execute()
                    
                    if result.data:
                        memories = []
                        
                        # Process each memory, filtering by session_id in metadata
                        for memory in result.data:
                            try:
                                # Get context data
                                context = memory.get("context", {})
                                # Check if this memory belongs to our session
                                metadata = context.get("metadata", {})
                                if metadata and metadata.get("session_id") == session_id:
                                    # Get conversation data
                                    conversation = context.get("conversation", {})
                                    if conversation:
                                        # Add metadata
                                        conversation["memory_id"] = memory.get("id")
                                        conversation["created_at"] = context.get("created_at")
                                        conversation["expires_at"] = memory.get("expires_at")
                                        
                                        memories.append(conversation)
                            except Exception as e:
                                logger.warning(f"Failed to parse memory content: {e}")
                        
                        # Sort by timestamp if available
                        memories.sort(
                            key=lambda m: m.get("timestamp", ""),
                            reverse=True  # Most recent first
                        )
                        
                        logger.info(f"Retrieved {len(memories)} memories from Supabase")
                        return memories[:max_messages]
                
                except Exception as e:
                    logger.error(f"Error retrieving memory from Supabase: {e}")
            
            # Fallback to using the older database approach if needed
            return await self._get_conversation_history_from_database(chat_id, user_id, max_messages)
            
        except Exception as e:
            logger.error(f"Error in conversation history retrieval: {e}")
            return []
    
    async def _get_conversation_history_from_database(self, chat_id: int, user_id: int, max_messages: int = 10) -> List[Dict[str, Any]]:
        """Fallback method to get conversation history from database."""
        try:
            # Try to find patient ID in database
            if self.supabase:
                try:
                    # Look for patient ID
                    platform_query = f'%"platform_id": "{user_id}"%'
                    result = self.supabase.table("patients").select("id").like("email", platform_query).execute()
                    
                    if result.data and len(result.data) > 0:
                        patient_id = result.data[0]["id"]
                        
                        # Query conversation details using patient_id
                        result = self.supabase.table("conversations")\
                            .select("id")\
                            .eq("patient_id", patient_id)\
                            .order("start_time", desc=True)\
                            .limit(1)\
                            .execute()
                        
                        if result.data and len(result.data) > 0:
                            conversation_id = result.data[0]["id"]
                            
                            # Get messages from this conversation
                            details = self.supabase.table("conversation_details")\
                                .select("*")\
                                .eq("conversation_id", conversation_id)\
                                .order("sent_at", desc=True)\
                                .limit(max_messages * 2)\
                                .execute()
                            
                            if details.data:
                                # Process messages
                                messages = []
                                
                                # Group by user/assistant pairs
                                for i in range(0, len(details.data), 2):
                                    if i+1 < len(details.data):
                                        user_msg = None
                                        bot_msg = None
                                        
                                        for msg in details.data[i:i+2]:
                                            if msg.get("sender") == "user":
                                                user_msg = msg
                                            elif msg.get("sender") == "assistant":
                                                bot_msg = msg
                                        
                                        if user_msg and bot_msg:
                                            messages.append({
                                                "user_message": user_msg.get("message_content", ""),
                                                "bot_response": bot_msg.get("message_content", ""),
                                                "timestamp": user_msg.get("sent_at", ""),
                                                "conversation_id": conversation_id
                                            })
                                
                                return messages[:max_messages]
                except Exception as e:
                    logger.error(f"Error getting conversation from database: {e}")
            
            # If all else fails, return empty
            return []
        
        except Exception as e:
            logger.error(f"Error in fallback conversation history: {e}")
            return []

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