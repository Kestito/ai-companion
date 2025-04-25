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

## Scheduled Messaging System

The AI Companion includes a comprehensive message scheduling system for Telegram that enables healthcare providers to:
- Schedule one-time messages to be sent at specific dates and times
- Create recurring messages (daily, weekly, or monthly)
- Manage scheduled messages via a web interface
- Track message delivery status

### Scheduled Message Processor

The message scheduler runs as a separate service:

```bash
python -m src.ai_companion.interfaces.telegram.scheduled_message_processor
```

This service:
- Polls the database at regular intervals for pending messages
- Sends messages that are due to be delivered
- Updates message status in the database
- Processes recurring messages by creating new schedule entries

### Database Structure

Scheduled messages are stored in the `scheduled_messages` table in Supabase with the following fields:
- `id`: Unique identifier (UUID)
- `patient_id`: ID of the patient to receive the message
- `message_content`: Text content of the message
- `scheduled_time`: Timestamp when the message should be sent
- `status`: Current status ('pending', 'sent', 'failed', 'cancelled')
- `platform`: Communication platform ('telegram')
- `created_at`: Timestamp when the schedule was created
- `metadata`: JSON field for additional data (can include recurrence information)

### Web API Endpoints

The system provides several REST API endpoints for managing scheduled messages:

1. **List Scheduled Messages**
   - `GET /api/telegram-scheduler`
   - Optional query parameter: `patientId`

2. **Create Scheduled Message**
   - `POST /api/telegram-scheduler`
   - Required fields: `patientId`, `messageContent`, `scheduledTime`
   - Optional fields: `recurrence` (object with `type` and optional `days`)

3. **Cancel Scheduled Message**
   - `DELETE /api/telegram-scheduler?id={messageId}`

4. **Update Scheduled Message**
   - `PATCH /api/telegram-scheduler`
   - Required field: `id`
   - Optional fields: `messageContent`, `scheduledTime`, `status`, `recurrence`

5. **Send Message Immediately**
   - `POST /api/telegram-scheduler/send-now`
   - Required field: `id`

### Frontend Integration

The web interface provides a UI for managing scheduled messages at `/scheduled-messages`. This interface allows healthcare providers to:
- View all scheduled messages
- Filter messages by patient
- Create new scheduled messages
- Cancel pending messages
- Send messages immediately
- View message status

### Recurrence Patterns

The scheduler supports the following recurrence patterns:
- **Daily**: Message sent every day at the specified time
- **Weekly**: Message sent on specified days of the week
- **Monthly**: Message sent on the same day of each month

### Deployment

The scheduler is deployed as an Azure Container App that runs continuously to process messages. For development, it can be run locally or in a container.

## Troubleshooting

If the Telegram bot is not responding, check the following:

1. Ensure the correct `TELEGRAM_BOT_TOKEN` is set for your environment
2. Verify that all required dependencies are installed
3. Check that the bot has been started either standalone or as part of the application
4. Look for error messages in the application logs
5. Verify the bot's health status using the `/monitor/health` endpoint
6. For scheduler issues, check the `/monitor/health/telegram-scheduler-status` endpoint

## Integration with Frontend

When a patient is registered, they can optionally provide their Telegram user ID to receive messages through Telegram. This can be done through the web interface or directly through the Telegram bot.

## Security Considerations

- Bot tokens should be kept secure and not exposed in public repositories
- User communications through Telegram are subject to Telegram's encryption policies
- Sensitive patient information should be handled according to appropriate data protection regulations

