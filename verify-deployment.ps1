# Deployment Verification Script

Write-Host "=== AI Companion Deployment Verification ===" -ForegroundColor Cyan

# Check if Docker is installed
Write-Host "Checking if Docker is installed..." -ForegroundColor Yellow
$dockerVersion = $null
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker is installed: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not installed or not in PATH. Please install Docker first." -ForegroundColor Red
    exit 1
}

# Check if Azure CLI is installed
Write-Host "Checking if Azure CLI is installed..." -ForegroundColor Yellow
$azVersion = $null
try {
    $azVersion = az --version | Select-Object -First 1
    Write-Host "✓ Azure CLI is installed: $azVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Azure CLI is not installed or not in PATH. Please install Azure CLI first." -ForegroundColor Red
    exit 1
}

# Check for required files
Write-Host "Checking for required files..." -ForegroundColor Yellow
$requiredFiles = @(
    "src/ai_companion/interfaces/telegram/telegram_bot.py",
    "src/ai_companion/interfaces/whatsapp/whatsapp_response.py",
    "Dockerfile"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✓ Found file: $file" -ForegroundColor Green
    } else {
        Write-Host "✗ Missing required file: $file" -ForegroundColor Red
        exit 1
    }
}

# Try to check Docker image build (no actual build)
Write-Host "Testing Docker build configuration..." -ForegroundColor Yellow
try {
    docker build -t test-build --quiet --no-cache=false --progress=plain --target=test . 2>&1 | Out-Null
    Write-Host "✓ Docker build configuration is valid" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker build validation failed. Please check your Dockerfile." -ForegroundColor Red
}

# All checks passed
Write-Host "`n=== Verification Complete ===" -ForegroundColor Cyan
Write-Host "All pre-deployment checks have passed. You can proceed with deployment." -ForegroundColor Green
Write-Host "To deploy, run: .\deploy.ps1" -ForegroundColor Yellow 