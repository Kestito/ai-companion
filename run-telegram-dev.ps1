#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Runs the Telegram bot in development mode
.DESCRIPTION
    This script runs the Telegram bot with a development token to avoid conflicts with production
#>

# Set environment variables for development
$env:TELEGRAM_BOT_TOKEN = "7764956576:AAE2C57S9jzihsYvoA2R7fjvLPjoopFbNxU" # Replace with your development bot token
$env:TELEGRAM_API_BASE = "https://api.telegram.org"
$env:ENVIRONMENT = "development"

Write-Host "Starting Telegram bot in DEVELOPMENT mode..." -ForegroundColor Cyan
Write-Host "Using development token: $env:TELEGRAM_BOT_TOKEN" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the bot" -ForegroundColor Yellow

# Run the Telegram bot
python src/ai_companion/interfaces/telegram/telegram_bot.py 