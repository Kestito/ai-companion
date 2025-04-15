# Process All Pending Telegram Messages
# This script manually processes all pending scheduled messages at once

Write-Host "==== Manual Telegram Message Processor ====" -ForegroundColor Cyan

# Set environment variables if needed
$env:TELEGRAM_BOT_TOKEN = "5933996374:AAGZDvHg3tYoXnGIa1wKVAsCO-iqFnCmGMw"
$env:SUPABASE_URL = "https://aubulhjfeszmsheonmpy.supabase.co"
$env:SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc"

# Make sure we're in the right directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $scriptDir))
Set-Location $rootDir

Write-Host "Current directory: $PWD" -ForegroundColor Yellow

# Check if required packages are installed
Write-Host "Checking required Python packages..." -ForegroundColor Yellow

$packagesToCheck = @("supabase", "python-telegram-bot")
$needsInstall = $false

foreach ($package in $packagesToCheck) {
    try {
        $result = python -c "import $($package.Replace('-', '_')); print('OK')"
        if ($result -ne "OK") {
            Write-Host "Package $package not found" -ForegroundColor Red
            $needsInstall = $true
        } else {
            Write-Host "Package $package is installed" -ForegroundColor Green
        }
    } catch {
        Write-Host "Package $package not found" -ForegroundColor Red
        $needsInstall = $true
    }
}

if ($needsInstall) {
    Write-Host "Installing required packages..." -ForegroundColor Yellow
    python -m pip install python-telegram-bot supabase
}

# Run the manual processor
Write-Host "Starting to process all pending Telegram messages..." -ForegroundColor Yellow
python -m src.ai_companion.interfaces.telegram.process_pending_messages

Write-Host "Process complete!" -ForegroundColor Green
Write-Host "Check manual_process.log for details" -ForegroundColor Cyan 