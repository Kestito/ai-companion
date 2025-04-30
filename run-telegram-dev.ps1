#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Runs the Telegram bot in development mode with fixed chat validation
.DESCRIPTION
    This script runs the Telegram bot with a development token to avoid conflicts with production
    and includes fixes for chat ID validation
#>

# Set environment variables for development
$env:TELEGRAM_BOT_TOKEN = "7764956576:AAE2C57S9jzihsYvoA2R7fjvLPjoopFbNxU" # Replace with your development bot token
$env:TELEGRAM_API_BASE = "https://api.telegram.org"
$env:ENVIRONMENT = "development"
$env:PYTHONPATH = "$PSScriptRoot"  # Add project root to Python path

Write-Host "Starting Telegram bot in DEVELOPMENT mode..." -ForegroundColor Cyan
Write-Host "Using development token: $env:TELEGRAM_BOT_TOKEN" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the bot" -ForegroundColor Yellow

# Create a validator version that doesn't require imports
$validatorCode = @'
import os
import httpx
import logging

# Create validator directly in the telegram_bot.py file
validator_code = """
class TelegramChatValidator:
    def __init__(self, bot_token, api_base):
        self.bot_token = bot_token
        self.api_base = api_base
        self._valid_cache = {}
        
    async def is_valid_chat(self, chat_id):
        # Convert to string for cache lookup
        str_chat_id = str(chat_id)
        
        # Check cache first
        if str_chat_id in self._valid_cache:
            return self._valid_cache[str_chat_id]
        
        url = f'{self.api_base}/bot{self.bot_token}/getChat'
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json={'chat_id': chat_id}, timeout=10.0)
                is_valid = response.status_code == 200
                self._valid_cache[str_chat_id] = is_valid
                return is_valid
        except Exception:
            self._valid_cache[str_chat_id] = False
            return False
"""

# Check if telegram_bot.py needs to be patched
telegram_bot_path = 'src/ai_companion/interfaces/telegram/telegram_bot.py'
with open(telegram_bot_path, 'r') as f:
    content = f.read()

if 'TelegramChatValidator' not in content:
    print("Adding TelegramChatValidator to telegram_bot.py")
    # Find the imports section to insert our validator code
    import_end = content.find("# Define color codes for terminal output")
    if import_end > 0:
        new_content = content[:import_end] + "\n# Validator for chat existence\n" + validator_code + "\n" + content[import_end:]
        with open(telegram_bot_path, 'w') as f:
            f.write(new_content)
        print("Added TelegramChatValidator to telegram_bot.py")
    else:
        print("Could not find a place to insert the validator code")
'@

# Save the validator python script to a temporary file
$tempScriptPath = Join-Path $env:TEMP "fix_telegram_imports.py"
Set-Content -Path $tempScriptPath -Value $validatorCode

# Run the script to add the validator directly to telegram_bot.py
python $tempScriptPath

# Run the Telegram bot
python src/ai_companion/interfaces/telegram/telegram_bot.py 