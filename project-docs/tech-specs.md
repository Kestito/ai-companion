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
  - `id`: Primary key
  - `telegram_id`: Telegram user ID 
  - `whatsapp_id`: WhatsApp user ID
  - `web_id`: Web platform user ID
  - `platform_data`: JSONB field for additional platform data
  - Other patient information fields (name, date_of_birth, etc.)

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

1. When a user interacts via any platform (Telegram, WhatsApp, Web), their platform-specific ID is stored in the corresponding field in the patients table
2. The `get_patient_id_from_platform_id` function in `nodes.py` retrieves or creates patient records based on platform identifiers
3. All memory operations are isolated by patient_id to ensure privacy and data separation

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