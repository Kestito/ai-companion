#!/usr/bin/env python
"""
Telegram Bot Runner

This script starts the Telegram bot from the project root.
"""

import asyncio
import logging
from ai_companion.interfaces.telegram.telegram_bot import run_telegram_bot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting Telegram bot from project root...")
    try:
        asyncio.run(run_telegram_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot stopped due to error: {e}", exc_info=True)
    finally:
        logger.info("Bot shutdown complete")
