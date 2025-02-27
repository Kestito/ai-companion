# Get the Container App FQDN
$FQDN = (az containerapp show --name evelina-vnet-app --resource-group evelina-ai-rg --query "properties.configuration.ingress.fqdn" -o tsv).Trim()

Write-Host "Testing URLs for Container App: $FQDN"
Write-Host "--------------------------------"

# Test the Chainlit interface
Write-Host "Testing Chainlit Interface (Port 8000)..."
try {
    $response = Invoke-WebRequest -Uri "https://$FQDN" -Method GET -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ Chainlit is accessible at: https://$FQDN"
    Write-Host "   Status: $($response.StatusCode) $($response.StatusDescription)"
} catch {
    Write-Host "❌ Failed to access Chainlit: $_"
}

# Test the WhatsApp webhook interface
Write-Host "`nTesting WhatsApp Interface (Port 8080)..."
try {
    $response = Invoke-WebRequest -Uri "https://$FQDN:8080/health" -Method GET -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ WhatsApp webhook is accessible at: https://$FQDN:8080"
    Write-Host "   Status: $($response.StatusCode) $($response.StatusDescription)"
} catch {
    Write-Host "❌ Failed to access WhatsApp webhook: $_"
}

# Test the Monitoring interface
Write-Host "`nTesting Monitoring Interface (Port 8090)..."
try {
    $response = Invoke-WebRequest -Uri "https://$FQDN:8090/monitor/health" -Method GET -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ Monitoring interface is accessible at: https://$FQDN:8090"
    Write-Host "   Status: $($response.StatusCode) $($response.StatusDescription)"
} catch {
    Write-Host "❌ Failed to access Monitoring interface: $_"
}

Write-Host "`nSummary of URLs:"
Write-Host "--------------------------------"
Write-Host "Chainlit Interface: https://$FQDN"
Write-Host "WhatsApp Webhook:   https://$FQDN:8080"
Write-Host "Monitoring API:     https://$FQDN:8090" 