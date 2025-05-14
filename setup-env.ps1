#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Sets up the environment variables for AI Companion local development
.DESCRIPTION
    This script creates a .env.local file with the necessary environment variables
    for running the AI Companion application locally.
#>

$ENV_FILE = ".env.local"

Write-Host "Setting up environment variables for local development..." -ForegroundColor Cyan

# Check if .env.local already exists
if (Test-Path $ENV_FILE) {
    $overwrite = Read-Host "The file $ENV_FILE already exists. Do you want to overwrite it? (y/n)"
    if ($overwrite -ne "y") {
        Write-Host "Setup cancelled. Using existing .env.local file." -ForegroundColor Yellow
        exit 0
    }
}

# Create the .env.local file
@"
# Core API Configuration
PORT=8000
INTERFACE=all

# LLM Configuration
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_API_VERSION=2025-04-16
AZURE_OPENAI_DEPLOYMENT=o4-mini
AZURE_EMBEDDING_DEPLOYMENT=text-embedding-3-small
OPENAI_API_TYPE=azure
OPENAI_API_VERSION=2025-04-16
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=o4-mini

# Database Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_SUPABASE_SERVICE_KEY=your_supabase_service_key

# RAG Configuration 
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
COLLECTION_NAME=Information

# Speech Services
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=your_elevenlabs_voice_id
STT_MODEL_NAME=whisper
TTS_MODEL_NAME=eleven_flash_v2_5

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
NEXT_PUBLIC_AZURE_OPENAI_API_KEY=your_azure_openai_api_key
NEXT_PUBLIC_AZURE_OPENAI_DEPLOYMENT=o4-mini
NEXT_PUBLIC_EMBEDDING_MODEL=text-embedding-3-small
NEXT_PUBLIC_LLM_MODEL=o4-mini
NEXT_PUBLIC_COLLECTION_NAME=Information

# Chainlit Configuration
CHAINLIT_FORCE_POLLING=true
CHAINLIT_NO_WEBSOCKET=true
CHAINLIT_POLLING_MAX_WAIT=5000
"@ | Out-File -FilePath $ENV_FILE -Encoding utf8

Write-Host "Environment variables file created: $ENV_FILE" -ForegroundColor Green
Write-Host "IMPORTANT: Please update the values in $ENV_FILE with your actual API keys and endpoints" -ForegroundColor Yellow

# Provide instructions for next steps
Write-Host "`nNext steps:" -ForegroundColor Magenta
Write-Host "1. Edit $ENV_FILE and fill in your actual API keys and endpoints" -ForegroundColor White
Write-Host "2. Run ./run-local.ps1 to start the application" -ForegroundColor White

exit 0 