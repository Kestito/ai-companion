# Fix the Telegram bot configuration by updating the backend-app environment variables
# This script adds the missing TELEGRAM_BOT_TOKEN to the backend-app container app

Write-Host "Fixing Telegram Bot configuration..." -ForegroundColor Cyan

# Get the token from the telegram-scheduler-app
$TELEGRAM_BOT_TOKEN = az containerapp show --name telegram-scheduler-app --resource-group evelina-rg-20250308115110 --query "properties.template.containers[0].env[?name=='TELEGRAM_BOT_TOKEN'].value" -o tsv

if (-not $TELEGRAM_BOT_TOKEN) {
    Write-Host "Could not find TELEGRAM_BOT_TOKEN in telegram-scheduler-app. Using hardcoded value." -ForegroundColor Yellow
    $TELEGRAM_BOT_TOKEN = "7602202107:AAH-7E6Dy6DGy1yaYQoZYFeJNpf4Z1m_Vmk"
}

Write-Host "Using Telegram Bot Token: $TELEGRAM_BOT_TOKEN" -ForegroundColor Green

# Update the backend-app with the TELEGRAM_BOT_TOKEN
Write-Host "Updating backend-app with TELEGRAM_BOT_TOKEN..." -ForegroundColor Cyan

# Add the environment variable to backend-app
$result = az containerapp update --name backend-app --resource-group evelina-rg-20250308115110 --set-env-vars TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Successfully updated backend-app with TELEGRAM_BOT_TOKEN!" -ForegroundColor Green
    Write-Host "The Telegram bot should now work for regular messages." -ForegroundColor Green
} else {
    Write-Host "❌ Failed to update backend-app. Please check the error and try again." -ForegroundColor Red
}

Write-Host "To verify the fix, check that the backend-app has the TELEGRAM_BOT_TOKEN with:" -ForegroundColor Cyan
Write-Host "az containerapp show --name backend-app --resource-group evelina-rg-20250308115110 --query ""properties.template.containers[0].env[?name=='TELEGRAM_BOT_TOKEN']""" -ForegroundColor Yellow 