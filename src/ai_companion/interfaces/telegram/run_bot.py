#!/usr/bin/env python

"""
Simple module to run the Telegram bot
"""

import asyncio
from telegram_bot import run_telegram_bot

if __name__ == "__main__":
    asyncio.run(run_telegram_bot())
