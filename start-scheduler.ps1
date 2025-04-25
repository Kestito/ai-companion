# Start-Scheduler.ps1
# Script to start the AI Companion app with the scheduler enabled

# Define colors for console output
function Write-ColorOutput {
    param (
        [string]$Message,
        [string]$Color = "White",
        [string]$Prefix = "===",
        [string]$Suffix = "==="
    )
    
    Write-Host "$Prefix $Message $Suffix" -ForegroundColor $Color
}

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Change to the script directory
Set-Location $scriptDir

# Kill any existing Python processes (optional - uncomment if needed)
# Write-ColorOutput "Stopping any existing Python processes..." "Yellow"
# Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

# Check if Python is installed
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCommand = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCommand = "python3"
} else {
    Write-ColorOutput "Python not found. Please install Python 3.8 or later." "Red"
    exit 1
}

# Check Python version
$pythonVersion = & $pythonCommand -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$minVersion = [version]"3.8"
if ([version]$pythonVersion -lt $minVersion) {
    Write-ColorOutput "Python version $pythonVersion is too old. Please install Python 3.8 or later." "Red"
    exit 1
}

# Check if virtual environment exists
$venvPath = ".venv"
$activateScript = "$venvPath\Scripts\Activate.ps1"

if (-not (Test-Path $activateScript)) {
    Write-ColorOutput "Creating virtual environment..." "Yellow"
    & $pythonCommand -m venv $venvPath
    
    if (-not (Test-Path $activateScript)) {
        Write-ColorOutput "Failed to create virtual environment." "Red"
        exit 1
    }
}

# Activate virtual environment
Write-ColorOutput "Activating virtual environment..." "Green"
& $activateScript

# Install or update dependencies
Write-ColorOutput "Installing dependencies..." "Green"
pip install -e .

# Start the application with the scheduler enabled
Write-ColorOutput "Starting AI Companion with scheduler..." "Green"

# Set environment variables to enable the scheduler
$env:ENABLE_SCHEDULER = "true"

# Start the application
Write-ColorOutput "Running application..." "Yellow"
python -m src.ai_companion

# This part will only execute when the application exits
Write-ColorOutput "Application has stopped." "Red" 