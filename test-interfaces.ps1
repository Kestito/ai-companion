# Get the FQDN of the Container App
$FQDN = (az containerapp show --name evelina-vnet-app --resource-group evelina-ai-rg --query "properties.configuration.ingress.fqdn" -o tsv).Trim()

Write-Host "`nTesting interfaces for $FQDN..."

# Test Chainlit interface
Write-Host "`nTesting Chainlit interface..."
$chainlitUrl = "https://$FQDN"
try {
    $response = Invoke-WebRequest -Uri $chainlitUrl -Method GET
    Write-Host "✅ Chainlit interface is accessible at: $chainlitUrl"
    Write-Host "Status: $($response.StatusCode) $($response.StatusDescription)"
} catch {
    Write-Host "❌ Failed to access Chainlit interface at: $chainlitUrl"
    Write-Host "Error: $($_.Exception.Message)"
}

# Test WhatsApp webhook
Write-Host "`nTesting WhatsApp webhook..."
$whatsappUrl = "https://$FQDN/whatsapp/health"
try {
    $response = Invoke-WebRequest -Uri $whatsappUrl -Method GET
    Write-Host "✅ WhatsApp webhook is accessible at: $whatsappUrl"
    Write-Host "Status: $($response.StatusCode) $($response.StatusDescription)"
} catch {
    Write-Host "❌ Failed to access WhatsApp webhook at: $whatsappUrl"
    Write-Host "Error: $($_.Exception.Message)"
}

# Test Monitoring interface
Write-Host "`nTesting Monitoring interface..."
$monitorUrl = "https://$FQDN/monitor/health"
try {
    $response = Invoke-WebRequest -Uri $monitorUrl -Method GET
    Write-Host "✅ Monitoring interface is accessible at: $monitorUrl"
    Write-Host "Status: $($response.StatusCode) $($response.StatusDescription)"
} catch {
    Write-Host "❌ Failed to access Monitoring interface at: $monitorUrl"
    Write-Host "Error: $($_.Exception.Message)"
}

Write-Host "`nSummary of URLs:"
Write-Host "Chainlit: $chainlitUrl"
Write-Host "WhatsApp: $whatsappUrl"
Write-Host "Monitor:  $monitorUrl" 