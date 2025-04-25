# PowerShell script to run integration tests with real credentials

# Check if the tests directory structure exists
$integrationDir = ".\tests\integration"
if (-not (Test-Path $integrationDir)) {
    Write-Host "Creating integration tests directory..."
    New-Item -ItemType Directory -Path $integrationDir -Force | Out-Null
}

Write-Host "============================================================"
Write-Host "Running integration tests with real credentials from settings"
Write-Host "============================================================"
Write-Host "NOTE: This test will use the credentials from settings.py by default."
Write-Host "You can override these values by setting environment variables."
Write-Host "Required environment variables:"
Write-Host "  - TEST_TELEGRAM_CHAT_ID: The Telegram chat ID to use for testing"
Write-Host "Optional environment variables to override settings.py values:"
Write-Host "  - SUPABASE_URL: Your Supabase URL"
Write-Host "  - SUPABASE_KEY: Your Supabase API key"
Write-Host "  - TELEGRAM_BOT_TOKEN: Your Telegram bot token"
Write-Host "  - RUN_TELEGRAM_TEST: Set to 'true' to run tests that send actual Telegram messages"
Write-Host "------------------------------------------------------------"

# Set the Telegram Chat ID (using the user's actual ID)
$env:TEST_TELEGRAM_CHAT_ID = "6519374243"
Write-Host "Using Telegram Chat ID: 6519374243"

# Ask if should run Telegram sending test (defaults to no)
$runTelegramTest = $false
$response = Read-Host "Do you want to run the test that actually sends a Telegram message? (y/N)"
if ($response -eq "y" -or $response -eq "Y") {
    $runTelegramTest = $true
    $env:RUN_TELEGRAM_TEST = "true"
} else {
    $env:RUN_TELEGRAM_TEST = "false"
}

# Display current settings that will be used
Write-Host "------------------------------------------------------------"
Write-Host "Test configuration:"
Write-Host "- Test Chat ID: $($env:TEST_TELEGRAM_CHAT_ID)"
Write-Host "- Run Telegram Send Test: $runTelegramTest"

# Optional: Display environment variables if they're set (these will override settings.py)
if ($env:SUPABASE_URL) {
    Write-Host "- Using custom Supabase URL (overriding settings.py)"
}
if ($env:SUPABASE_KEY) {
    Write-Host "- Using custom Supabase Key (overriding settings.py)"
}
if ($env:TELEGRAM_BOT_TOKEN) {
    Write-Host "- Using custom Telegram Bot Token (overriding settings.py)"
}
Write-Host "------------------------------------------------------------"

# Run the tests
python -m pytest tests/integration/test_scheduler_real.py -v

# No need to clear environment variables that were in settings.py anyway
# Just clear the custom ones
if ($runTelegramTest -eq $false) {
    $env:RUN_TELEGRAM_TEST = $null
} 