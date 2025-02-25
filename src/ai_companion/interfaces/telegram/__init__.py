"""
Telegram interface module for AI Companion.
Handles Telegram bot integration and message processing using long polling.
"""

from .telegram_bot import TelegramBot, run_telegram_bot

__all__ = ["TelegramBot", "run_telegram_bot"]