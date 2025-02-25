import asyncio
import logging
from io import BytesIO
from typing import Dict, Optional, Union
import signal

import httpx
from langchain_core.messages import HumanMessage
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
        self.client = httpx.AsyncClient(timeout=30.0)
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
            me = await self._make_request("getMe")
            logger.info(f"Bot started successfully: @{me['result']['username']}")
            await self._poll_updates()
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise
        finally:
            await self.client.aclose()
            logger.info("Bot shutdown complete")

    async def _poll_updates(self):
        """Long polling for updates from Telegram."""
        while self._running:
            try:
                updates = await self._make_request(
                    "getUpdates",
                    params={
                        "offset": self.offset,
                        "timeout": 30,
                        "allowed_updates": ["message"]
                    }
                )
                
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
            content = await self._extract_message_content(message)
            if not content:
                return

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

                # Get the workflow type and response from the result
                workflow = result.get("workflow", "conversation")
                response_message = result["messages"][-1].content

                # Handle different response types
                await self._send_response(chat_id, response_message, workflow, result)

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            await self._send_message(chat_id, "Sorry, I encountered an error processing your message.")

    async def _extract_message_content(self, message: Dict) -> Optional[str]:
        """Extract content from different types of messages."""
        if "text" in message:
            return message["text"]
        
        elif "voice" in message:
            file_id = message["voice"]["file_id"]
            audio_data = await self._download_file(file_id)
            return await speech_to_text.transcribe(audio_data)
            
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
                return f"{caption}\n[Image Analysis: {description}]"
            except Exception as e:
                logger.warning(f"Failed to analyze image: {e}")
                return caption or "Image received but could not be analyzed"
                
        return None

    async def _send_response(
        self,
        chat_id: int,
        response_text: str,
        workflow: str,
        result: Dict
    ):
        """Send response based on workflow type."""
        try:
            if workflow == "audio":
                audio_buffer = result.get("audio_buffer")
                if audio_buffer:
                    await self._send_voice(chat_id, audio_buffer, response_text)
                else:
                    await self._send_message(chat_id, response_text)
            
            elif workflow == "image":
                image_path = result.get("image_path")
                if image_path:
                    with open(image_path, "rb") as f:
                        image_data = f.read()
                    await self._send_photo(chat_id, image_data, response_text)
                else:
                    await self._send_message(chat_id, response_text)
            
            else:
                await self._send_message(chat_id, response_text)
                
        except Exception as e:
            logger.error(f"Error sending response: {e}")
            await self._send_message(
                chat_id,
                "Sorry, I encountered an error sending the response."
            )

    async def _make_request(
        self,
        method: str,
        params: Dict = None,
        files: Dict = None,
        data: Dict = None,
        retries: int = 3
    ) -> Dict:
        """Make request to Telegram Bot API with retries."""
        url = f"{self.base_url}/{method}"
        
        for attempt in range(retries):
            try:
                if files:
                    response = await self.client.post(
                        url, 
                        params=params, 
                        files=files, 
                        data=data,
                        timeout=30.0
                    )
                else:
                    response = await self.client.post(
                        url, 
                        json=params if params else {},
                        timeout=30.0
                    )
                
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException:
                if attempt == retries - 1:
                    raise
                logger.warning(f"Request timeout, attempt {attempt + 1}/{retries}")
                await asyncio.sleep(1)
            except Exception as e:
                if attempt == retries - 1:
                    logger.error(f"API request failed after {retries} attempts: {e}")
                    raise
                logger.warning(f"Request failed, attempt {attempt + 1}/{retries}: {e}")
                await asyncio.sleep(1)

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

    async def _send_message(self, chat_id: int, text: str) -> Dict:
        """Send text message."""
        return await self._make_request(
            "sendMessage",
            params={"chat_id": chat_id, "text": text}
        )

    async def _send_photo(self, chat_id: int, photo: bytes, caption: str = None) -> Dict:
        """Send photo message."""
        files = {"photo": ("image.jpg", photo, "image/jpeg")}
        data = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption
        return await self._make_request("sendPhoto", data=data, files=files)

    async def _send_voice(self, chat_id: int, voice: bytes, caption: str = None) -> Dict:
        """Send voice message."""
        files = {"voice": ("voice.ogg", voice, "audio/ogg")}
        data = {"chat_id": chat_id}
        if caption:
            await self._send_message(chat_id, caption)
        return await self._make_request("sendVoice", data=data, files=files)

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