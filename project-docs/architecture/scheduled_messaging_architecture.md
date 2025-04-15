# Scheduled Messaging System Architecture

## System Overview

The Scheduled Messaging System is designed to enable automated, time-based delivery of messages to patients across multiple communication platforms. The architecture follows a modular, service-oriented approach with clear separation of concerns to ensure maintainability and extensibility.

## High-Level Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│  Web Interface  │<─────│  Message Store  │<─────│ Scheduler Service│
│  (NextJS)       │─────>│  (Supabase)     │─────>│                 │
│                 │      │                 │      │                 │
└─────────────────┘      └─────────────────┘      └────────┬────────┘
                                                           │
                                                           ▼
                                             ┌─────────────────────────┐
                                             │                         │
                                             │  Platform Delivery      │
                                             │  Services               │
                                             │                         │
                                             └───┬─────────┬─────────┬─┘
                                                 │         │         │
                     ┌───────────────────────────┘         │         └───────────────────────────┐
                     │                                     │                                     │
                     ▼                                     ▼                                     ▼
          ┌────────────────────┐              ┌────────────────────┐              ┌────────────────────┐
          │                    │              │                    │              │                    │
          │  Telegram Service  │              │  WhatsApp Service  │              │   SMS Service      │
          │                    │              │                    │              │                    │
          └──────────┬─────────┘              └──────────┬─────────┘              └──────────┬─────────┘
                     │                                   │                                   │
                     ▼                                   ▼                                   ▼
          ┌────────────────────┐              ┌────────────────────┐              ┌────────────────────┐
          │                    │              │                    │              │                    │
          │  Telegram API      │              │  WhatsApp API      │              │   SMS Gateway      │
          │                    │              │                    │              │                    │
          └────────────────────┘              └────────────────────┘              └────────────────────┘
```

## Core Components

### 1. Web Interface (NextJS Application)
- **Purpose**: Provides user interface for scheduling messages and viewing status
- **Key Features**:
  - Message composition
  - Schedule configuration
  - Patient selection
  - Status monitoring
  - Manual triggering

### 2. Message Store (Supabase Database)
- **Purpose**: Stores scheduled messages and their status
- **Key Tables**:
  - `scheduled_messages`: Stores message content, recipient, timing, status
  - `message_delivery_attempts`: Tracks delivery attempts and outcomes
  - `patients`: Contains recipient contact information

### 3. Scheduler Service
- **Purpose**: Core engine that processes due messages
- **Key Components**:
  - **Message Retriever**: Fetches due messages from database
  - **Dispatcher**: Routes messages to appropriate platform service
  - **Status Manager**: Updates message status after delivery attempts

### 4. Platform Delivery Services
- **Purpose**: Platform-specific adapters for message delivery
- **Current Implementation**:
  - **Telegram Service**: Integrates with existing telegram_bot.py
- **Planned Extensions**:
  - WhatsApp Service
  - SMS Service

## Data Flow

### 1. Message Scheduling Flow
```
User → Web Interface → API Endpoint → Message Store
```

### 2. Message Delivery Flow
```
Scheduler Service → Message Store → Platform Service → External API → Recipient
```

### 3. Status Update Flow
```
Platform Service → Status Manager → Message Store → Web Interface
```

## Key Interfaces

### 1. Scheduler-Database Interface
- **API Type**: Database ORM / SQL
- **Operations**:
  - Fetch due messages
  - Update message status
  - Record delivery attempts

### 2. Scheduler-Platform Interface
- **Interface Definition**:
  ```python
  class PlatformDeliveryService(ABC):
      @abstractmethod
      async def send_message(message: ScheduledMessage) -> DeliveryResult:
          pass
          
      @abstractmethod
      async def validate_message(message: ScheduledMessage) -> ValidationResult:
          pass
  ```

### 3. Telegram Bot Integration Interface
- **Import Pattern**:
  ```python
  from ai_companion.interfaces.telegram.telegram_bot import TelegramBot
  ```
- **Key Methods**:
  - `send_message(chat_id, text, parse_mode, reply_markup)`
  - `get_chat(chat_id)`

## Database Schema

### scheduled_messages
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| patient_id | TEXT | ID of recipient patient |
| message_content | TEXT | Content of message |
| scheduled_time | TIMESTAMPTZ | When to send the message |
| status | TEXT | Current status (pending, processing, sent, failed) |
| platform | TEXT | Delivery platform (telegram, whatsapp, sms) |
| created_at | TIMESTAMPTZ | When the message was scheduled |
| updated_at | TIMESTAMPTZ | Last status update time |
| attempts | INTEGER | Number of delivery attempts |
| last_error | TEXT | Latest error message if failed |

### message_delivery_attempts
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| message_id | UUID | Foreign key to scheduled_messages |
| attempt_time | TIMESTAMPTZ | When attempt was made |
| status | TEXT | Outcome (success, failed) |
| error_message | TEXT | Error details if failed |
| response_data | JSONB | Platform-specific response data |

## Security Considerations

### Authentication
- **Bot Tokens**: Securely stored in environment variables
- **Database Access**: Service account with minimal permissions
- **API Access**: JWT-based authentication for web interface

### Data Protection
- **Message Content**: Encryption for sensitive health information
- **Credentials**: Never stored in code, always in secure environment variables
- **Audit Trail**: Logging of all scheduled message operations

## Scalability Design

### Horizontal Scaling
- **Stateless Services**: Scheduler designed to run multiple instances
- **Locking Mechanism**: Database-based locking to prevent duplicate processing
- **Worker Pools**: Configurable concurrent delivery workers

### Performance Considerations
- **Batch Processing**: Messages processed in configurable batches
- **Database Indexing**: Optimized for scheduled time queries
- **Rate Limiting**: Adaptive throttling for external API limits

## Error Handling Strategy

### Categorization
- **Temporary Failures**: Network issues, service unavailability
- **Permanent Failures**: Invalid recipient, permission issues
- **Configuration Errors**: Missing credentials, invalid settings

### Retry Strategy
- **Exponential Backoff**: Increasing delay between retry attempts
- **Maximum Attempts**: Configurable limit to prevent infinite retries
- **Dead Letter Queue**: Storage of permanently failed messages

## Monitoring and Observability

### Metrics Collection
- **Performance**: Processing time, queue depth, throughput
- **Reliability**: Success rate, error rate by category
- **Volume**: Messages per platform, time distribution

### Logging
- **Structured Logs**: JSON format with consistent fields
- **Log Levels**: INFO for normal operation, ERROR for exceptions
- **Correlation IDs**: Tracking request flow across components

## Deployment Architecture

### Containerization
- **Docker-based**: Each component in separate container
- **Environment Configuration**: Variables injected at runtime
- **Volume Mounting**: For persistent storage needs

### Service Management
- **Daemon Process**: Long-running background service
- **Health Checks**: HTTP endpoint for monitoring
- **Graceful Shutdown**: Proper cleanup of resources

## Future Extensions

### Additional Platforms
- **WhatsApp**: Business API integration
- **SMS**: Multiple gateway support
- **Email**: As alternative delivery channel

### Advanced Features
- **Message Templates**: Reusable content patterns
- **Dynamic Content**: Personalization variables
- **Attachments**: Support for media files
- **Interactive Messages**: Buttons and deep links

## Development Guidelines

### Coding Standards
- **Type Annotations**: Full Python type hinting
- **Documentation**: Docstrings for all public methods
- **Testing**: Unit and integration tests required
- **Error Handling**: Explicit exception handling

### Architecture Principles
- **Loose Coupling**: Minimal dependencies between components
- **Inversion of Control**: Dependency injection where possible
- **Single Responsibility**: Each module has a focused purpose
- **Open/Closed**: Extensions without modifying existing code 