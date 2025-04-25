# Local Development Guide

This guide explains how to set up and run the AI Companion application locally for development.

## Prerequisites

- Python 3.9 or higher
- Node.js 18 or higher (for frontend development)
- PowerShell 7 or higher (for Windows)

## Quick Start

For a quick setup, run the following commands:

```powershell
# Clone the repository (if you haven't already)
git clone https://github.com/yourusername/ai-companion.git
cd ai-companion

# Setup development environment
./setup-dev.ps1

# Edit .env.local with your API keys and endpoints

# Run the application
./run-local.ps1
```

## Setup Details

### 1. Environment Setup

The `setup-dev.ps1` script will:

- Check for required dependencies (Python, Node.js)
- Create and activate a virtual environment
- Install package management tools (uv)
- Install project dependencies
- Set up pre-commit hooks (if configured)
- Install frontend dependencies (if applicable)
- Create a template `.env.local` file
- Create necessary directories (logs, data)

### 2. Configuration

After running `setup-dev.ps1`, you need to edit the `.env.local` file with your actual API keys and endpoints. The following services require configuration:

- Azure OpenAI or OpenAI API
- Supabase
- Qdrant (for RAG capabilities)
- ElevenLabs (for speech services)
- Telegram Bot Token (if using Telegram integration)

### 3. Running the Application

The `run-local.ps1` script provides options to run different components of the application:

- Option 1: Run all components (Backend, WhatsApp, Telegram, Frontend)
- Option 2: Run backend only
- Option 3: Run frontend only
- Option 4: Run WhatsApp webhook only
- Option 5: Run Telegram bot only

## Component Details

### Backend Services

The backend consists of several services:

- **LangGraph Studio**: Provides a visual interface for LangGraph workflows
- **FastAPI Backend**: Main API server for the application
- **WhatsApp Webhook**: Handles WhatsApp integration
- **Telegram Bot**: Handles Telegram integration

### Frontend Interfaces

The application supports multiple frontend interfaces:

- **Web UI**: Next.js web interface
- **Chainlit Interface**: Interactive chat interface

## Testing

For testing the application, refer to the testing documentation in the [project-docs/testing](../project-docs/testing) directory.

## Troubleshooting

If you encounter issues during setup or running the application:

1. Ensure all required environment variables are set in `.env.local`
2. Check logs in the `logs` directory
3. Make sure all required ports are available (8000, 3000, 8080)
4. Verify that your API keys are valid and have sufficient permissions

For more detailed troubleshooting, refer to the [project-docs/troubleshooting](../project-docs/troubleshooting) directory.

## Additional Resources

- [API Documentation](../project-docs/api)
- [RAG Documentation](../project-docs/rag)
- [Deployment Guide](../project-docs/deployment)
- [Project Architecture](../project-docs/architecture) 