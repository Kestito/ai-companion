n#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Sets up the development environment for AI Companion
.DESCRIPTION
    This script sets up the complete development environment for AI Companion,
    including installing dependencies, setting up environment variables,
    and ensuring all required tools are available.
#>

Write-Host "=== AI Companion Development Environment Setup ===" -ForegroundColor Magenta

# Check if Python is installed
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python is not installed or not in PATH. Please install Python 3.9+" -ForegroundColor Red
    exit 1
}

# Check Python version
$pythonVersion = (python --version).ToString().Split(" ")[1]
Write-Host "Found Python version: $pythonVersion" -ForegroundColor Cyan
if ([version]$pythonVersion -lt [version]"3.9") {
    Write-Host "Python version must be 3.9 or higher. Please upgrade Python." -ForegroundColor Red
    exit 1
}

# Create and activate virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
}

# Activate the virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& "./venv/Scripts/Activate.ps1"

# Install pip-tools or uv
Write-Host "Installing package management tools..." -ForegroundColor Cyan
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    pip install uv
}

# Install dependencies
Write-Host "Installing project dependencies..." -ForegroundColor Cyan
uv sync

# Install pre-commit hooks if .pre-commit-config.yaml exists
if (Test-Path ".pre-commit-config.yaml") {
    Write-Host "Installing pre-commit hooks..." -ForegroundColor Cyan
    pip install pre-commit
    pre-commit install
}

# Check if Node.js is installed (for frontend)
if (Test-Path "src/ai_companion/interfaces/web-ui") {
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        Write-Host "Node.js is not installed or not in PATH. Please install Node.js 18+ for frontend development." -ForegroundColor Yellow
    } else {
        $nodeVersion = (node --version).ToString().TrimStart("v")
        Write-Host "Found Node.js version: $nodeVersion" -ForegroundColor Cyan
        if ([version]$nodeVersion -lt [version]"18.0.0") {
            Write-Host "Node.js version must be 18.0.0 or higher for frontend development. Please upgrade Node.js." -ForegroundColor Yellow
        } else {
            # Install frontend dependencies
            Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
            Push-Location "src/ai_companion/interfaces/web-ui"
            npm install
            Pop-Location
        }
    }
}

# Set up environment variables
Write-Host "Setting up environment variables..." -ForegroundColor Cyan
& "./setup-env.ps1"

# Create necessary directories
Write-Host "Creating necessary directories..." -ForegroundColor Cyan
$directories = @("logs", "data")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "Created directory: $dir" -ForegroundColor Green
    }
}

# Success message and next steps
Write-Host "`n=== Setup Complete! ===" -ForegroundColor Green
Write-Host "Your development environment is now set up." -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Magenta
Write-Host "1. Edit .env.local with your actual API keys and endpoints" -ForegroundColor White
Write-Host "2. Run ./run-local.ps1 to start the application" -ForegroundColor White
Write-Host "3. For more information, see the project documentation in the project-docs directory" -ForegroundColor White

Write-Host "`nHappy coding! 🚀" -ForegroundColor Cyan 