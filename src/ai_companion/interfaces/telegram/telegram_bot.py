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
import random

import httpx
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from ai_companion.graph import graph_builder
from ai_companion.modules.image import ImageToText
from ai_companion.modules.speech import SpeechToText, TextToSpeech
from ai_companion.settings import settings
from ai_companion.utils.supabase import get_supabase_client
from ai_companion.modules.memory.service import get_memory_service
from ai_companion.modules.memory.short_term import get_short_term_memory_manager, ShortTermMemoryManager

# Define color codes for terminal output
GREEN = "\033[32m"
RESET = "\033[0m"

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

# Helper function to print colored messages to terminal
def print_green(message: str):
    """Print message in green color to terminal."""
    print(f"{GREEN}{message}{RESET}")

class TelegramBot:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.api_base = settings.TELEGRAM_API_BASE
        self.base_url = f"{self.api_base}/bot{self.token}"
        self.offset = 0
        self.client = httpx.AsyncClient(timeout=60.0)
        self._running = True
        self._setup_signal_handlers()
        # Use memory service instead of direct memory manager
        self.memory_service = get_memory_service()
        # Keep memory_manager for backward compatibility
        self.memory_manager = get_short_term_memory_manager()
        self.supabase = get_supabase_client()
        
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
            
            # Print user message in green to terminal
            print_green(f"USER ({chat_id}): {content}")
            
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
            
            # Log memory information before processing
            await self._log_memory_contents(chat_id, user_id)
            
            # Process the message and generate response
            await self._send_typing_action(chat_id)
            
            # Process message through the graph agent using memory manager for persistence
            try:
                logger.debug("Starting graph processing")
                
                # Get complete conversation history combining memory and database
                # Increase max_messages to use more history
                conversation_history = await self._get_conversation_history(chat_id, user_id, max_messages=20)
                
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
                
                # DIRECT LANGGRAPH EXECUTION: Ensure we use the exact same graph processing as standalone LangGraph
                # ================================================================================================
                
                # Create a config that exactly matches what would be used in direct LangGraph execution
                config = {
                    "configurable": {
                        "thread_id": session_id,
                        "memory_manager": self.memory_manager,
                        "rag_enabled": True,
                        "detailed_response": True,
                        "search_threshold": 0.7,
                        "conversation_history": formatted_history,
                        "interface": "telegram",  # Identify the interface for conversation_node
                        "user_metadata": user_metadata,  # Pass user metadata to conversation_node
                        "use_supabase_only": True,  # Flag to use only Supabase for memory, no local checkpoints
                    }
                }
                
                # Look for existing memory in Supabase only
                memory_data = None
                
                if self.supabase:
                    try:
                        result = self.supabase.table("short_term_memory").select("*").order("expires_at", desc=True).limit(100).execute()
                        
                        if result.data:
                            for record in result.data:
                                context = record.get("context", {})
                                metadata = context.get("metadata", {})
                                if metadata and metadata.get("session_id") == session_id:
                                    memory_data = record
                                    logger.info(f"Found existing memory in Supabase for session {session_id}")
                                    break
                    except Exception as e:
                        logger.error(f"Error checking for existing memory: {e}")
                
                # Inject existing memory state if found
                if memory_data and "state" in memory_data:
                    config["configurable"]["existing_memory"] = memory_data.get("state", {})
                    logger.info("Loaded existing memory state from Supabase")
                
                # Create a new graph instance with identical config to direct LangGraph usage
                graph = graph_builder.with_config(config)
                
                # Create HumanMessage with minimal metadata - let conversation_node handle all processing
                human_message = HumanMessage(content=content, metadata={
                    "user_id": user_id,
                    "session_id": session_id,
                    "platform": "telegram",
                })
                
                # Invoke the graph - rely on conversation_node for final response text
                result = await graph.ainvoke(
                    {"messages": [human_message]}
                )
                
                # Debug the result type
                logger.debug(f"Result type: {type(result).__name__}")
                logger.debug(f"Result structure: {json.dumps(str(result)[:500], indent=2)}")
                
                # Extract the response message - use exactly as provided by conversation_node
                response_message = None
                workflow = "conversation"
                
                # Handle different result types
                if isinstance(result, dict) and "messages" in result:
                    messages = result["messages"]
                    if messages and len(messages) > 0:
                        last_message = messages[-1]
                        if isinstance(last_message, AIMessage):
                            # Use response directly from conversation_node without modifications
                            response_message = last_message.content
                            
                            # Get workflow info
                            if hasattr(last_message, "metadata") and last_message.metadata:
                                metadata = last_message.metadata
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
                    # Get the graph state from LangGraph without requiring a checkpoint file
                    # This will be stored in Supabase only
                    graph_state = await graph.aget_state(config)
                    logger.info("Retrieved graph state from LangGraph")
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
                
                # Save the conversation to the database
                patient_id = None
                if isinstance(result, dict) and "patient_id" in result:
                    patient_id = result["patient_id"]
                
                conversation_id = await self._save_to_database(
                    user_metadata, 
                    content, 
                    response_message,
                    patient_id
                )
                
                # Send the response directly from conversation_node
                logger.debug(f"Sending response with workflow: {workflow}")
                await self._send_direct_response(chat_id, response_message, workflow, safe_result, message_type)
            
            except Exception as e:
                logger.error(f"Error in graph processing: {e}", exc_info=True)
                await self._send_message(chat_id, "Sorry, I encountered an error processing your message.")

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            await self._send_message(chat_id, "Sorry, I encountered an error processing your message.")

    async def _send_direct_response(
        self,
        chat_id: int,
        response_text: str,
        workflow: str,
        result: Union[Dict, Any],
        message_type: Optional[str] = None
    ):
        """Send response directly from conversation_node without modifications."""
        try:
            # Ensure we have a valid response text
            if not response_text or not isinstance(response_text, str):
                logger.warning(f"Invalid response text: {response_text}")
                response_text = "Sorry, I encountered an error generating a response."
            
            # Print bot response in green to terminal
            print_green(f"BOT → {chat_id}: {response_text}")
            
            logger.info(f"Sending direct response with workflow '{workflow}', length: {len(response_text)} chars")
            
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
            
            # Check if response contains structured RAG information - don't modify these
            contains_structured_info = any(marker in response_text for marker in [
                "**", "##", "1.", "2.", "3.", "4.", "5.", "•", "*Registracija*", "*Dokument", "*Patvirtinim"
            ])
            
            # Only apply response variations if it's NOT a structured RAG response
            if not contains_structured_info:
                response_text = self._add_response_variation(response_text)
            else:
                logger.info("Detected structured RAG response - preserving original format")
            
            # Clean response text to remove markdown formatting ONLY if it's not a RAG response
            if not contains_structured_info:
                response_text = self._clean_response_text(response_text)
            
            # Print bot response in green to terminal
            print_green(f"BOT → {chat_id}: {response_text}")
            
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

    def _add_response_variation(self, text: str) -> str:
        """
        Detect and break repetitive patterns in responses to make them more natural.
        
        Args:
            text: The original response text
            
        Returns:
            Modified response with more variation
        """
        # Check for overused starting phrases
        common_starts = ["Žinoma!", "Žinoma, ", "Sveiki!", "Labas!", "Suprantu tavo klausimą"]
        
        # Alternative starters in Lithuanian
        alt_starters = [
            "", # Sometimes start directly without a greeting
            "Žiūrėk, ",
            "Na, ",
            "Hmm, ",
            "Nu tai, ",
            "Klausyk, ",
            "Matai, ",
            "Ai, ",
            "Tai jo, ",
            "Oj, ",
            "Na gerai, ",
            "Okay, ",
        ]
        
        modified_text = text
        
        # Replace standard openings with more varied ones
        for start in common_starts:
            if text.startswith(start):
                # 70% chance to replace with alternative
                if random.random() < 0.7:
                    replacement = random.choice(alt_starters)
                    modified_text = replacement + text[len(start):].lstrip()
                break
                
        # Detect if the message follows the "I need more context" pattern
        context_phrases = [
            "reikia daugiau konteksto",
            "galėčiau tiksliai atsakyti",
            "reikėtų daugiau informacijos",
            "galėtumėte patikslinti",
            "norėčiau daugiau konteksto"
        ]
        
        # Check if the message is asking for clarification
        asks_for_clarification = any(phrase in modified_text.lower() for phrase in context_phrases)
        
        if asks_for_clarification and random.random() < 0.6:
            # Replace with more direct response 60% of the time
            simple_responses = [
                "Apie ką tiksliai nori sužinoti?",
                "Būtų šaunu jei patikslintum, kuo domiesi? 😊",
                "Tiesiog pasakyk konkrečiau, kuo galiu padėti?",
                "Nu tai kokia konkreti tema tave domina?",
                "Įdomu! O ką būtent norėtum sužinoti?",
                "Papasakok daugiau, kuo galiu padėti?",
                "Ką būtent nori išsiaiškinti?",
                "Sakyk drąsiai, kuo domiesi? Padėsiu kuo galėsiu!",
            ]
            modified_text = random.choice(simple_responses)
            
        # Break up long sentences - if we have more than 3 commas, 
        # have a 50% chance to split into multiple sentences
        if modified_text.count(',') > 3 and random.random() < 0.5:
            parts = modified_text.split(',')
            if len(parts) > 3:
                # Convert some commas to periods
                for i in range(1, len(parts)-1):
                    if random.random() < 0.4:  # 40% chance to convert each comma
                        parts[i] = parts[i].strip().capitalize() + "."
                modified_text = ' '.join([p.strip() for p in parts])
                
        # Add some filler words and speech particles randomly
        filler_words = ["nu", "tai", "na", "žinai", "tipo", "mmm", "ane"]
        
        words = modified_text.split()
        if len(words) > 5 and random.random() < 0.3:  # 30% chance to add filler
            insert_pos = random.randint(1, min(4, len(words)-1))
            filler = random.choice(filler_words)
            words.insert(insert_pos, filler)
            modified_text = ' '.join(words)
            
        # Add an emoji at the end sometimes
        emojis = ["😊", "👍", "🙂", "😉", "🤔", "👌", "💪", "👏", "😁", "😄"]
        if random.random() < 0.2 and not any(emoji in modified_text for emoji in emojis):
            modified_text += f" {random.choice(emojis)}"
            
        return modified_text

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
        """
        Save the conversation to the database and update memory.
        
        Args:
            user_metadata: User metadata including platform and IDs
            user_message: The user's message
            bot_response: The bot's response
            patient_id: Optional patient ID if already known
            
        Returns:
            The conversation ID if successful, None otherwise
        """
        try:
            supabase = self.supabase
            if not supabase:
                return None
                
            # Extract user information
            chat_id = user_metadata.get("chat_id")
            user_id = user_metadata.get("user_id")
            platform = user_metadata.get("platform", "telegram")
            first_name = user_metadata.get("first_name", "")
            last_name = user_metadata.get("last_name", "")
            
            # Store in memory service
            conversation_data = {
                "user_message": user_message,
                "bot_response": bot_response
            }
            
            # Store the memory with the conversation data
            memory_id = await self.memory_service.store_session_memory(
                platform=platform,
                user_id=str(user_id),
                conversation=conversation_data,
                ttl_minutes=30
            )
            
            logger.info(f"Stored memory with ID: {memory_id}")
            
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
                    "conversation_id": memory_id,
                    "context": context_data,
                    "expires_at": expires_at
                }
                
                supabase.table("short_term_memory").insert(memory_data).execute()
            except Exception as e:
                # Non-critical, just log the error
                logger.warning(f"Failed to save to short_term_memory table: {e}")
            
            # If we created a new patient or found one, update any existing memories
            if patient_id and user_id:
                await self._update_memory_with_patient_info(user_id, patient_id, {
                    "first_name": first_name,
                    "last_name": last_name,
                    "platform": platform
                })
            
            # Return the conversation ID for reference
            return memory_id
                
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
            # Use memory service to get session memories
            memories = await self.memory_service.get_session_memory(
                platform="telegram",
                user_id=str(user_id),
                limit=limit
            )
            
            return memories
        except Exception as e:
            logger.error(f"Error retrieving recent memories: {e}", exc_info=True)
            return []

    async def _update_memory_with_patient_info(self, user_id: int, patient_id: str, patient_info: Dict[str, Any]) -> None:
        """
        Update memory entries with patient information.
        
        Args:
            user_id: Telegram user ID
            patient_id: Database patient ID
            patient_info: Patient information to store
        """
        try:
            if not self.supabase:
                return
                
            # Create session ID in the same format used when storing
            session_id = f"telegram-{user_id}"
            
            # Get recent memories for this session
            result = self.supabase.table("short_term_memory") \
                .select("id") \
                .like("context", f'%"session_id":"{session_id}"%') \
                .execute()
                
            if not result.data:
                logger.debug(f"No existing memories found for session {session_id}")
                return
                
            # Update each memory with patient ID
            for memory in result.data:
                try:
                    self.supabase.table("short_term_memory") \
                        .update({"patient_id": patient_id}) \
                        .eq("id", memory["id"]) \
                        .execute()
                except Exception as e:
                    logger.warning(f"Error updating memory {memory['id']} with patient ID: {e}")
                    
            logger.info(f"Updated {len(result.data)} memories with patient ID {patient_id}")
        except Exception as e:
            logger.error(f"Error updating memories with patient info: {e}")

    async def _get_conversation_history(self, chat_id: int, user_id: int, max_messages: int = 20) -> List[Dict[str, Any]]:
        """
        Get the conversation history for a user.
        
        Args:
            chat_id: Telegram chat ID
            user_id: Telegram user ID
            max_messages: Maximum number of messages to retrieve
            
        Returns:
            List of message dictionaries with content and role
        """
        try:
            # Use memory service to get conversation history
            raw_memories = await self.memory_service.get_session_memory(
                platform="telegram",
                user_id=str(user_id),
                limit=max_messages
            )
            
            # Format the conversation history
            conversation_history = []
            
            for memory in raw_memories:
                try:
                    # Check for new format with both user message and bot response
                    if "response" in memory:
                        # Add user message
                        conversation_history.append({
                            "role": "user",
                            "content": memory.get("content", "")
                        })
                        # Add bot response
                        conversation_history.append({
                            "role": "assistant",
                            "content": memory.get("response", "")
                        })
                    else:
                        # Old format may have just content
                        content = memory.get("content", "")
                        if content:
                            # Try to determine the role based on metadata
                            metadata = memory.get("metadata", {})
                            role = "user" if metadata.get("sender") == "patient" else "assistant"
                            conversation_history.append({
                                "role": role,
                                "content": content
                            })
                except Exception as e:
                    logger.warning(f"Error parsing conversation history entry: {e}")
                    continue
            
            # Limit to max_messages
            return conversation_history[-max_messages:] if conversation_history else []
            
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}", exc_info=True)
            # Fallback to database method if memory service fails
            return await self._get_conversation_history_from_database(chat_id, user_id, max_messages)

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

    async def _log_memory_contents(self, chat_id: int, user_id: int):
        """
        Log the contents of short-term memory for debugging.
        
        Args:
            chat_id: Telegram chat ID
            user_id: Telegram user ID
        """
        logger.info(f"=== MEMORY CONTENTS FOR CHAT {chat_id}, USER {user_id} ===")
        print_green(f"=== MEMORY CONTENTS FOR CHAT {chat_id}, USER {user_id} ===")
        
        # Log short-term memory contents from Supabase
        try:
            # Query and log data from Supabase
            if self.supabase:
                result = self.supabase.table("short_term_memory")\
                    .select("*")\
                    .order("expires_at", desc=True)\
                    .limit(10)\
                    .execute()
                
                if result.data:
                    logger.info(f"SUPABASE SHORT-TERM MEMORY: Found {len(result.data)} records")
                    print_green(f"SUPABASE SHORT-TERM MEMORY: Found {len(result.data)} records")
                    
                    session_id = f"telegram-{chat_id}-{user_id}"
                    for i, record in enumerate(result.data):
                        try:
                            context = record.get("context", {})
                            metadata = context.get("metadata", {})
                            session = metadata.get("session_id", "unknown")
                            
                            if session == session_id:
                                logger.info(f"  Record {i+1} (matching session):")
                                print_green(f"  Record {i+1} (matching session):")
                            else:
                                logger.info(f"  Record {i+1} (different session: {session}):")
                                print_green(f"  Record {i+1} (different session: {session}):")
                                
                            logger.info(f"    ID: {record.get('id', 'N/A')}")
                            logger.info(f"    Created: {context.get('created_at', 'N/A')}")
                            logger.info(f"    Expires: {record.get('expires_at', 'N/A')}")
                            
                            # Print conversation data if available
                            conversation = context.get("conversation", {})
                            if conversation:
                                logger.info(f"    User message: {conversation.get('user_message', 'N/A')}")
                                logger.info(f"    Bot response: {conversation.get('bot_response', 'N/A')}")
                                print_green(f"    User message: {conversation.get('user_message', 'N/A')}")
                                print_green(f"    Bot response: {conversation.get('bot_response', 'N/A')}")
                        except Exception as e:
                            logger.warning(f"Failed to parse record {i+1}: {e}")
                else:
                    logger.info("SUPABASE SHORT-TERM MEMORY: No records found")
                    print_green("SUPABASE SHORT-TERM MEMORY: No records found")
        except Exception as e:
            logger.error(f"Error logging short-term memory: {e}")
            
        logger.info("=== END MEMORY CONTENTS ===")
        print_green("=== END MEMORY CONTENTS ===")
        
    async def _send_typing_action(self, chat_id: int):
        """Send typing action to indicate the bot is processing the message."""
        try:
            await self._make_request("sendChatAction", params={
                "chat_id": chat_id,
                "action": "typing"
            })
        except Exception as e:
            logger.warning(f"Failed to send typing action: {e}")

    async def _generate_memory_summary(self, chat_id: int, user_id: int, conversation_history: List[Dict]) -> str:
        """
        Generate a summary of key topics and information from memory to enhance context.
        
        Args:
            chat_id: Telegram chat ID
            user_id: Telegram user ID
            conversation_history: Recent conversation history
            
        Returns:
            A concise summary of important information from memory
        """
        try:
            # Get all memory sources for comprehensive context
            # 1. Check cache memory first
            session_id = f"telegram-{chat_id}-{user_id}"
            cache_path = os.path.join(self.checkpoint_dir, f"{session_id}.json")
            
            # Track important entities and topics mentioned
            important_topics = set()
            user_preferences = {}
            key_facts = []
            
            # Extract topics from conversation history
            for entry in conversation_history:
                user_msg = entry.get("user_message", "").lower()
                bot_msg = entry.get("bot_response", "").lower()
                
                # Look for key entities (names, places, conditions, topics)
                for msg in [user_msg, bot_msg]:
                    # Simple keyword extraction
                    words = msg.split()
                    for word in words:
                        if len(word) > 5 and word.isalpha():  # Focus on longer words as potential topics
                            important_topics.add(word)
                
                # Extract potential preferences or factual statements
                if "prefer" in user_msg or "like" in user_msg or "want" in user_msg:
                    key_facts.append(f"User preference: {user_msg}")
                if "my name is" in user_msg or "i am" in user_msg or "i have" in user_msg:
                    key_facts.append(f"User info: {user_msg}")
            
            # Get patient information if available
            patient_info = {}
            if self.supabase:
                try:
                    platform_query = f'%"platform_id": "{user_id}"%'
                    result = self.supabase.table("patients").select("*").like("email", platform_query).execute()
                    
                    if result.data and len(result.data) > 0:
                        patient_info = result.data[0]
                        # Extract relevant patient fields
                        for field in ["first_name", "last_name", "risk", "preferred_language", "support_status"]:
                            if field in patient_info and patient_info[field]:
                                key_facts.append(f"Patient {field}: {patient_info[field]}")
                except Exception as e:
                    logger.warning(f"Failed to retrieve patient info: {e}")
            
            # Build the summary
            summary = []
            
            if key_facts:
                summary.append("Key user information:")
                for fact in key_facts[:5]:  # Limit to most important facts
                    summary.append(f"- {fact}")
            
            if important_topics:
                summary.append("\nFrequently discussed topics:")
                topic_list = list(important_topics)
                topic_summary = ", ".join(topic_list[:10])  # Limit to top topics
                summary.append(f"- {topic_summary}")
            
            if patient_info:
                summary.append("\nUser is a registered patient.")
            
            # Add interaction history summary
            summary.append(f"\nConversation history: {len(conversation_history)} recent interactions.")
            
            # Combine into one string
            return "\n".join(summary)
        
        except Exception as e:
            logger.error(f"Error generating memory summary: {e}")
            return "No memory summary available."

    async def _generate_personality_variation(self) -> Dict[str, Any]:
        """
        Generate slightly varied personality traits to make responses feel more human and diverse.
        
        Returns:
            Dictionary of personality instructions with slight variations each time
        """
        # Base personality elements
        empathy_levels = ["high", "very high", "warm", "compassionate"]
        tones = ["warm and friendly", "caring and personal", "casual and approachable", "warm and understanding"]
        speaking_styles = ["conversational", "friendly chat", "relaxed and informal", "personal and direct"]
        
        # Lithuanian-specific expressions to randomly include
        lt_expressions = [
            "Tai va", "Na žinai", "Nu gerai", "Žiūrėk", "Klausyk", "Supranti",
            "Matai kaip", "Tai štai", "Įsivaizduok", "Na tipo", "Nu jo"
        ]
        
        # Select random expressions to highlight (3-5 of them)
        highlighted_expressions = random.sample(lt_expressions, random.randint(3, 5))
        expressions_text = ", ".join([f"'{exp}'" for exp in highlighted_expressions])
        
        # Randomly vary emoji usage
        emoji_chance = random.choice([True, True, False])  # 2/3 chance of using emojis
        
        # Create randomly varied personality with Lithuanian traits
        personality = {
            "tone": random.choice(tones),
            "speaking_style": random.choice(speaking_styles),
            "empathy_level": random.choice(empathy_levels),
            "use_emoji": emoji_chance,
            "human_qualities": [
                "uses casual language",
                "shows genuine care",
                "uses everyday expressions",
                "speaks with emotion",
                "uses contractions and informal language"
            ],
            "lithuanian_traits": [
                "uses Lithuanian colloquialisms and slang",
                f"uses phrases like {expressions_text}",
                "occasionally shortens words like Lithuanians do in casual conversation",
                "uses friendly diminutives in appropriate contexts"
            ],
            "avoid": [
                "robotic language",
                "overly formal tone", 
                "perfect grammar",
                "lengthy explanations without breaks",
                "AI-like phrases",
                "repetitive sentence structures",
                "overly clinical language",
                "too formal Lithuanian expressions typical in documentation"
            ]
        }
        
        # Randomly decide if the bot should include a small joke (30% chance)
        if random.random() < 0.3:
            personality["human_qualities"].append("makes a light-hearted comment or gentle joke")
        
        # Randomly decide if the bot should ask a follow-up question (60% chance)
        if random.random() < 0.6:
            personality["human_qualities"].append("asks a thoughtful follow-up question")
            
        return personality

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