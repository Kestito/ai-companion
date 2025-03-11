"""
Platform-specific handlers for scheduled messages.

This package contains handlers for different messaging platforms
that implement the actual message sending logic.
"""

from ai_companion.modules.scheduled_messaging.handlers.telegram_handler import TelegramHandler
from ai_companion.modules.scheduled_messaging.handlers.whatsapp_handler import WhatsAppHandler

__all__ = ["TelegramHandler", "WhatsAppHandler"] 