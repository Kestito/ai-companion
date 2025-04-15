#!/bin/bash
set -e

# Create logs directory
mkdir -p /app/logs

# Start the Telegram scheduler in the background
echo "Starting Telegram scheduler in background..."
python -m src.ai_companion.interfaces.telegram.scheduled_message_processor > /app/logs/telegram_scheduler.log 2>&1 &

# Start the main application in the foreground
echo "Starting main application..."
uvicorn src.ai_companion.api.main:app --host 0.0.0.0 --port 8000