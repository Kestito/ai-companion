# Telegram Interface

The Telegram interface allows users to interact with the AI Companion through Telegram messaging.

## Configuration

The AI Companion system supports separate Telegram bots for production and test/local environments:

- **Production Bot**: `7602202107:AAH-7E6Dy6DGy1yaYQoZYFeJNpf4Z1m_Vmk`
  - Used in production environment
  - Username: @Cancer247Bot

- **Test/Local Bot**: `7764956576:AAE2C57S9jzihsYvoA2R7fjvLPjoopFbNxU`
  - Used in development and testing environments
  - Username: @cancerinformation_bot

The bot to use is determined by the `ENVIRONMENT` setting in the application. If the environment is set to "production", the production bot token is used; otherwise, the test bot token is used.

## Environment Variables

The following environment variables are used to configure the Telegram interface:

- `TELEGRAM_BOT_TOKEN`: Bot token to use for API authentication (defaults based on environment)
- `TELEGRAM_API_BASE`: Base URL for Telegram API (default: "https://api.telegram.org")
- `ENVIRONMENT`: Determines which bot token to use (default: "development")

## Usage

The Telegram bot can be started in several ways:

1. **As a standalone service**:
   ```bash
   python -m src.ai_companion.interfaces.telegram.telegram_bot
   ```

2. **Using Docker**:
   ```bash
   docker run -e INTERFACE=telegram ai-companion:latest
   ```

3. **As part of the all interfaces** mode:
   ```bash
   docker run -e INTERFACE=all ai-companion:latest
   ```

## Architecture

The Telegram interface consists of the following components:

1. **TelegramBot class**: Handles the core functionality of the bot, including:
   - Connecting to the Telegram API
   - Long polling for updates
   - Processing messages
   - Sending responses

2. **Speech processing**: The bot can handle voice messages and convert them to text, as well as generate voice responses from text.

3. **Graph integration**: Uses the LangGraph system to process messages through the AI workflow graph.

## Scheduled Messaging

The Telegram interface also supports scheduled messages through a separate service:

```bash
python -m src.ai_companion.interfaces.telegram.scheduled_message_processor
```

This service allows scheduling one-time or recurring messages to be sent to users at specified times.

## Troubleshooting

If the Telegram bot is not responding, check the following:

1. Ensure the correct `TELEGRAM_BOT_TOKEN` is set for your environment
2. Verify that all required dependencies are installed
3. Check that the bot has been started either standalone or as part of the application
4. Look for error messages in the application logs
5. Verify the bot's health status using the `/monitor/health` endpoint

## Integration with Frontend

When a patient is registered, they can optionally provide their Telegram user ID to receive messages through Telegram. This can be done through the web interface or directly through the Telegram bot.

## Security Considerations

- Bot tokens should be kept secure and not exposed in public repositories
- User communications through Telegram are subject to Telegram's encryption policies
- Sensitive patient information should be handled according to appropriate data protection regulations

