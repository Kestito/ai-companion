# Technical Specifications

## Architecture Overview

The AI Companion application consists of the following components:

### Backend Application

The backend application is a Python-based FastAPI service that provides the core AI functionality. It now also includes:

- **Integrated Telegram Bot**: The Telegram bot now runs as part of the main backend application as a background thread, simplifying deployment and reducing the number of container instances needed.
- **Telegram Message Scheduler**: The scheduler functionality for sending recurring messages is now integrated into the main backend application.

### Features

The application supports:

- Natural language conversation with AI
- Voice message transcription
- Image-to-text conversion
- Scheduled messages and reminders
- Multi-platform support (Web, Telegram)

## Technology Stack

- **Backend**: Python with asyncio for concurrent operations
- **Frontend**: Next.js, React, TailwindCSS
- **Database**: Supabase (PostgreSQL)
- **APIs**: OpenAI (Azure), Telegram Bot API
- **Memory Management**: LangChain and Vector Store
- **Graph Processing**: LangGraph for workflow management

## Container Design

The application is now deployed as two primary containers:

1. **Combined Backend/Telegram Container**: Contains the main Python backend service and the integrated Telegram bot.
2. **Frontend Container**: Hosts the Next.js web application.

## Deployment Process

Deployment is handled via PowerShell scripts that:
1. Build Docker images for the frontend and combined backend
2. Push images to Azure Container Registry
3. Deploy or update the Azure Container Apps

The system uses a unified versioning approach where all components share the same version number.

## Environment Variables

The application requires various environment variables for configuration:
- Database connection details
- AI API keys
- Telegram bot token
- Azure service configuration

## Resource Requirements

- **Backend/Telegram Container**: Min 1.0 CPU, 2GB RAM
- **Frontend Container**: Min 0.5 CPU, 1GB RAM

## Tech Stack

### Backend
- Python 3.12
- LangChain
- Azure OpenAI
- GPT-4 models
- Supabase for database

### Frontend
- Next.js 14.1.0
- React 18
- Material UI
- TypeScript
- Supabase Auth

## Messaging & Scheduling

### Telegram Scheduler Service
The application includes a Telegram message scheduling system that allows healthcare providers to schedule and send messages to patients at specified times. 

#### Implementation Details
- **API Routes**: 
  - `/api/telegram-scheduler` - CRUD operations for scheduled messages
  - `/api/telegram-scheduler/send-now` - Endpoint to send scheduled messages immediately

- **Service Layer**: 
  - `telegramSchedulerService.ts` - Client-side service for interacting with the scheduler API
  - Functions include: `getScheduledMessages()`, `createScheduledMessage()`, `updateScheduledMessage()`, `cancelScheduledMessage()`, and `sendScheduledMessageNow()`

- **Database**: 
  - Uses Supabase to store scheduled messages in the `scheduled_messages` table
  - Scheduled messages can be one-time or recurring

- **Processor**: 
  - `scheduled_message_processor.py` - Background service that checks for and sends pending messages
  - Runs as a separate Azure Container App 

## Database Structure

### Key Tables

#### Patients Table

- Stores patient information and cross-platform identifiers
- Key fields:
  - `id`: Primary key (UUID) used for cross-platform identification  
  - `system_id`: Standardized identifier in format `platform:platform_id` (e.g., `telegram:12345678`)
  - `channel`: Platform identifier (telegram, whatsapp, web)
  - `risk`: Risk assessment level
  - `email`: JSONB field containing platform-specific data and identifiers
  - Other patient information fields (first_name, last_name, etc.)

Note: Platform-specific IDs are stored in the `email` field as a JSON object since the dedicated `platform_data` field is not available in the current schema.

#### Memories Table

- Stores conversation history and important memory points
- Patient isolation through `patient_id` field for privacy
- Vector embeddings for semantic search

#### Scheduled Messages Table

- Stores messages to be sent at future times
- Supports recurrence patterns for repeating messages
- Links to patients through `patient_id`

## Cross-Platform User Identification

The system uses a unified patient identification approach across platforms:

1. When a user interacts via any platform (Telegram, WhatsApp, Web), a standardized `system_id` is created combining platform name and ID (`platform:platform_id`)
2. The `get_patient_id_from_platform_id` function first checks for patients by `system_id` for most efficient lookups
3. If `system_id` is not available (e.g., in older database schemas), the function dynamically adapts and falls back to platform-specific ID fields
4. Patient records are automatically created with appropriate identifiers when a new user is detected
5. The system is designed to handle database schema variations and gracefully adapt to missing fields
6. All memory operations are isolated by patient_id to ensure privacy and data separation

## Memory Management Architecture

Memory operations require a `patient_id` to ensure proper isolation:

1. `memory_injection_node` retrieves relevant memories for the current conversation
2. `memory_extraction_node` extracts important details from current messages to store
3. Both use the platform ID to retrieve the appropriate patient ID

## Development Conventions

- Asynchronous code using Python's asyncio
- Error handling with proper logging
- Configuration via environment variables
- Memory isolation by patient ID 

## Memory Management

### Short-Term Memory
The application now uses Supabase exclusively for short-term memory storage. Previous versions used a combination of in-memory cache and SQLite database, but this has been updated to use only Supabase for better reliability, scalability, and to avoid local file system dependencies.

Key changes:
- Removed SQLite database file creation from `settings.py`
- Set `SHORT_TERM_MEMORY_DB_PATH` to ":memory:" by default
- Updated Telegram bot to remove checkpoint directory functionality
- Ensured `use_supabase_only: True` flag is set in LangGraph configurations

All memory operations require a `patient_id` parameter to ensure proper context isolation between different patients, even when they interact through the same platform account. The application automatically:
1. Retrieves the appropriate patient_id from the patients table using the platform ID (telegram_id, whatsapp_id, etc.)
2. Creates a new patient record if one doesn't exist for the given platform ID
3. Uses the patient_id to store and retrieve memory entries in a way that maintains separate conversation contexts

This change improves deployment flexibility and removes the dependency on local file system access for memory persistence.

## Logging Configuration

The application uses Python's built-in logging framework with customized configuration for different components:

### Main Application Logging
- Controlled by `LOGGING_LEVEL` environment variable
- Default level is INFO for most components
- Can be set to DEBUG, INFO, WARNING, ERROR, or CRITICAL
- HTTP client libraries (httpx, urllib3, httpcore) are set to WARNING level to reduce noise

### Scheduler Logging
- Controlled by `SCHEDULER_LOG_LEVEL` environment variable
- Default level is ERROR to hide most scheduler-related logs
- Can be set to DEBUG, INFO, WARNING, ERROR, or CRITICAL
- Affects scheduler worker and scheduled message service components
- Set to INFO or DEBUG only when troubleshooting scheduler issues

### Additional Logging Controls
- `DEBUG` boolean flag for enabling/disabling debug mode
- `VERBOSE` boolean flag for more verbose output in some components

## Development Methods

- **API-First Design**: APIs are designed before implementation
- **Modular Architecture**: Components are modular for better maintainability
- **Test-Driven Development**: Tests are written for critical components
- **Continuous Integration**: Code is integrated and tested continuously 

## Module Structure

### Graph System Structure
The graph system follows this module structure:
- `ai_companion.graph.graph`: Contains the main graph definition and workflow
- `ai_companion.graph.nodes`: Contains all node implementations including utility functions like get_patient_id_from_platform_id
- `ai_companion.graph.edges`: Contains edge conditions and transition logic
- `ai_companion.graph.state`: Defines the state model for the graph

Important note: All node implementations are in the `ai_companion.graph.nodes` module, **not** in a utils subfolder 