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

- **Backend**: Python with FastAPI
- **Frontend**: Next.js, React, TailwindCSS
- **Database**: PostgreSQL (via Supabase)
- **AI/ML**: OpenAI, Azure OpenAI models
- **Memory**: Supabase for conversation history
- **Deployment**: Docker containers on Azure Container Apps

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