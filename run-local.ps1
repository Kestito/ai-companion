#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Runs the AI Companion application locally
.DESCRIPTION
    This script sets up and runs the AI Companion application locally, 
    including all necessary backend services and frontend components.
#>

# Variables
$ENV_FILE = ".env"
$BACKEND_PORT = 8000
$FRONTEND_PORT = 3000
$WHATSAPP_PORT = 8080

# Function to check if dependencies are installed
function Check-Dependencies {
    Write-Host "Checking dependencies..." -ForegroundColor Cyan
    
    # Check if Python is installed
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Host "Python is not installed or not in PATH. Please install Python 3.9+" -ForegroundColor Red
        exit 1
    }
    
    # Check if uv is installed
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "Installing uv..." -ForegroundColor Yellow
        pip install uv
    }
    
    # Check if Node.js is installed
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        Write-Host "Node.js is not installed or not in PATH. Please install Node.js 18+" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "All dependencies found!" -ForegroundColor Green
}

# Function to setup environment
function Setup-Environment {
    Write-Host "Setting up environment..." -ForegroundColor Cyan
    
    # Install dependencies
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    uv sync
    
    # Install Node dependencies if needed (for frontend)
    if (Test-Path "src/ai_companion/interfaces/web-ui/package.json") {
        Write-Host "Installing Node.js dependencies for frontend..." -ForegroundColor Yellow
        Push-Location "src/ai_companion/interfaces/web-ui"
        npm install
        Pop-Location
    }
    
    Write-Host "Environment setup complete!" -ForegroundColor Green
}

# Function to run backend
function Start-Backend {
    Write-Host "Starting backend services..." -ForegroundColor Cyan
    
    # Start LangGraph Studio
    Start-Process -FilePath "pwsh" -ArgumentList "-Command", "langgraph dev" -WindowStyle Normal
    
    # Start FastAPI backend
    Start-Process -FilePath "pwsh" -ArgumentList "-Command", "uvicorn src.ai_companion.interfaces.api.main:app --reload --port $BACKEND_PORT" -WindowStyle Normal
    
    Write-Host "Backend services started!" -ForegroundColor Green
}

# Function to run WhatsApp webhook
function Start-WhatsApp {
    Write-Host "Starting WhatsApp webhook..." -ForegroundColor Cyan
    Start-Process -FilePath "pwsh" -ArgumentList "-Command", "uvicorn src.ai_companion.interfaces.whatsapp.webhook_endpoint:app --reload --log-level debug --port $WHATSAPP_PORT" -WindowStyle Normal
    Write-Host "WhatsApp webhook started on port $WHATSAPP_PORT!" -ForegroundColor Green
}

# Function to run Telegram bot
function Start-Telegram {
    Write-Host "Starting Telegram bot..." -ForegroundColor Cyan
    Start-Process -FilePath "pwsh" -ArgumentList "-Command", "python src/ai_companion/interfaces/telegram/telegram_bot.py" -WindowStyle Normal
    Write-Host "Telegram bot started!" -ForegroundColor Green
}

# Function to run frontend
function Start-Frontend {
    Write-Host "Starting frontend..." -ForegroundColor Cyan
    
    # If using Next.js web-ui
    if (Test-Path "src/ai_companion/interfaces/web-ui") {
        Push-Location "src/ai_companion/interfaces/web-ui"
        Start-Process -FilePath "pwsh" -ArgumentList "-Command", "npm run dev" -WindowStyle Normal
        Pop-Location
        Write-Host "Frontend started on port $FRONTEND_PORT!" -ForegroundColor Green
    }
    
    # If using Chainlit interface
    if (Test-Path "src/ai_companion/interfaces/chainlit") {
        Write-Host "Starting Chainlit interface..." -ForegroundColor Cyan
        Start-Process -FilePath "pwsh" -ArgumentList "-Command", "chainlit run src/ai_companion/interfaces/chainlit/app.py" -WindowStyle Normal
        Write-Host "Chainlit interface started!" -ForegroundColor Green
    }
}

# Main execution
function Main {
    Write-Host "=== AI Companion Local Development ===" -ForegroundColor Magenta
    
    Check-Dependencies
    Setup-Environment
    
    $choice = Read-Host "Which components do you want to run? (1: All, 2: Backend only, 3: Frontend only, 4: WhatsApp, 5: Telegram, 6: Exit)"
    
    switch ($choice) {
        "1" {
            Start-Backend
            Start-WhatsApp
            Start-Telegram
            Start-Frontend
        }
        "2" {
            Start-Backend
        }
        "3" {
            Start-Frontend
        }
        "4" {
            Start-WhatsApp
        }
        "5" {
            Start-Telegram
        }
        "6" {
            Write-Host "Exiting..." -ForegroundColor Red
            exit 0
        }
        default {
            Write-Host "Invalid choice. Exiting..." -ForegroundColor Red
            exit 1
        }
    }
    
    Write-Host "`nAll requested services are now running!" -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
    
    # Keep script running
    try {
        Wait-Event -Timeout ([int]::MaxValue)
    } catch {
        Write-Host "Stopping all services..." -ForegroundColor Red
        exit 0
    }
}

# Run main function
Main 