import os
import httpx
import logging
from typing import Dict, Optional, Union

logger = logging.getLogger(__name__)


class TelegramChatValidator:
    """Utility for validating Telegram chat IDs"""

    def __init__(self, bot_token: Optional[str] = None, api_base: Optional[str] = None):
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
        self.api_base = api_base or os.environ.get(
            "TELEGRAM_API_BASE", "https://api.telegram.org"
        )
        self._valid_cache: Dict[str, bool] = {}

    async def is_valid_chat(self, chat_id: Union[str, int]) -> bool:
        """
        Check if a chat ID is valid by calling Telegram's getChat API

        Args:
            chat_id: The Telegram chat ID to validate

        Returns:
            bool: True if the chat exists, False otherwise
        """
        # Convert to string for cache lookup
        str_chat_id = str(chat_id)

        # Check cache first
        if str_chat_id in self._valid_cache:
            return self._valid_cache[str_chat_id]

        url = f"{self.api_base}/bot{self.bot_token}/getChat"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, json={"chat_id": chat_id}, timeout=10.0
                )

                is_valid = response.status_code == 200
                self._valid_cache[str_chat_id] = is_valid

                if not is_valid:
                    logger.warning(
                        f"Invalid chat ID: {chat_id}. Response: {response.text}"
                    )

                return is_valid

        except Exception as e:
            logger.error(f"Error validating chat ID {chat_id}: {str(e)}")
            self._valid_cache[str_chat_id] = False
            return False
