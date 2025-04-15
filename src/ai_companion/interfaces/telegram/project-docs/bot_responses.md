# Telegram Bot Response Patterns

This document outlines the different types of responses that the Telegram bot is tested to handle correctly.

## Basic Text Response

When a user sends a simple text message, the bot responds with a conversational answer:

**User Message:**
```
Hello bot, how are you?
```

**Bot Response:**
```
Hello! I'm doing well, thank you for asking. How can I help you today?
```

This is the standard conversation flow that handles general inquiries.

## Command Response

When a user sends a command message (prefixed with `/`), the bot processes it as a specific action:

**User Message:**
```
/schedule tomorrow at 2pm Reminder for doctor appointment
```

**Bot Response:**
```
I've scheduled your reminder for tomorrow at 2:00 PM.
```

Commands trigger special workflows in the bot, such as scheduling reminders, retrieving information, or managing settings.

## Long Message Handling

The bot can handle very long responses (>4000 characters) by chunking them into multiple messages:

**User Message:**
```
Please provide a detailed health overview.
```

**Bot Response:**
Long detailed response is split into multiple messages with [Part 1/n], [Part 2/n] etc. prefixes to ensure delivery within Telegram's message size limits.

## Empty Content Handling

The bot gracefully handles messages without text content:

**User Message:**
*[Message with no text content, such as an empty message or only media]*

**Bot Response:**
*No response is generated for empty messages*

## Media Response Types

### Voice Message Response

When a user sends a voice message:

**User Message:**
*[Voice recording]*

**Bot Response:**
1. Transcription of the voice message
2. Response to the transcribed content
3. Optional voice response for accessibility

### Image Analysis Response

When a user sends an image:

**User Message:**
*[Image with optional caption]*

**Bot Response:**
```
[Image Analysis: Description of what's in the image]

Response addressing the image content and any caption provided.
```

## Error Handling Responses

### Network Error

**Bot Response:**
```
Sorry, I'm having trouble connecting. Please try again in a moment.
```

### Processing Error

**Bot Response:**
```
Sorry, I encountered an error processing your request.
```

## Response Formats by Workflow Type

The bot uses different response formats based on the workflow:

1. **Conversation workflow** - Standard text responses
2. **Audio workflow** - Voice message responses
3. **Image workflow** - Text responses with image attachments
4. **Schedule workflow** - Confirmation responses for scheduled items 