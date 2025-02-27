# Get the FQDN of the Container App
$FQDN = (az containerapp show --name evelina-vnet-app --resource-group evelina-ai-rg --query "properties.configuration.ingress.fqdn" -o tsv).Trim()

Write-Host "`nTesting interfaces for $FQDN..." -ForegroundColor Green

# Test root endpoint
Write-Host "`nTesting root endpoint..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "https://$FQDN" -Method GET
    Write-Host "✅ Root endpoint is accessible at: https://$FQDN" -ForegroundColor Green
    Write-Host "Status: $($response.StatusCode) $($response.StatusDescription)"
} catch {
    Write-Host "❌ Failed to access root endpoint at: https://$FQDN" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)"
}

# Test health endpoint
Write-Host "`nTesting health endpoint..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "https://$FQDN/health" -Method GET
    Write-Host "✅ Health endpoint is accessible at: https://$FQDN/health" -ForegroundColor Green
    Write-Host "Status: $($response.StatusCode) $($response.StatusDescription)"
    Write-Host "Response: $($response.Content)"
} catch {
    Write-Host "❌ Failed to access health endpoint at: https://$FQDN/health" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)"
}

# Test WhatsApp webhook
Write-Host "`nTesting WhatsApp webhook..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "https://$FQDN/whatsapp/health" -Method GET
    Write-Host "✅ WhatsApp webhook is accessible at: https://$FQDN/whatsapp/health" -ForegroundColor Green
    Write-Host "Status: $($response.StatusCode) $($response.StatusDescription)"
    Write-Host "Response: $($response.Content)"
} catch {
    Write-Host "❌ Failed to access WhatsApp webhook at: https://$FQDN/whatsapp/health" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)"
}

# Test Monitoring health endpoint
Write-Host "`nTesting Monitoring health endpoint..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "https://$FQDN/monitor/health" -Method GET
    Write-Host "✅ Monitoring health endpoint is accessible at: https://$FQDN/monitor/health" -ForegroundColor Green
    Write-Host "Status: $($response.StatusCode) $($response.StatusDescription)"
    Write-Host "Response: $($response.Content)"
} catch {
    Write-Host "❌ Failed to access Monitoring health endpoint at: https://$FQDN/monitor/health" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)"
}

# Test Monitoring metrics endpoint
Write-Host "`nTesting Monitoring metrics endpoint..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "https://$FQDN/monitor/metrics" -Method GET
    Write-Host "✅ Monitoring metrics endpoint is accessible at: https://$FQDN/monitor/metrics" -ForegroundColor Green
    Write-Host "Status: $($response.StatusCode) $($response.StatusDescription)"
    Write-Host "Response: $($response.Content)"
} catch {
    Write-Host "❌ Failed to access Monitoring metrics endpoint at: https://$FQDN/monitor/metrics" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)"
}

Write-Host "`nSummary of URLs:" -ForegroundColor Yellow
Write-Host "Root:     https://$FQDN" -ForegroundColor Cyan
Write-Host "Health:   https://$FQDN/health" -ForegroundColor Cyan
Write-Host "WhatsApp: https://$FQDN/whatsapp/health" -ForegroundColor Cyan
Write-Host "Monitor:  https://$FQDN/monitor/health" -ForegroundColor Cyan
Write-Host "Metrics:  https://$FQDN/monitor/metrics" -ForegroundColor Cyan 