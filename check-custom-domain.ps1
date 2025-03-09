# Check Custom Domain Status for Azure Container App
# This script checks the status of a custom domain configured for an Azure Container App

# Parameters with default values from main deployment
param (
    [string]$ResourceGroup = "evelina-rg-20250308115110",
    [string]$ContainerAppName = "frontend-app",
    [string]$CustomDomain = "demo.evelinaai.com"
)

Write-Host "=== Checking status of custom domain $CustomDomain for $ContainerAppName ===" -ForegroundColor Cyan

# Check if the container app exists
Write-Host "Checking if container app exists..." -ForegroundColor Yellow
$appExists = az containerapp show --name $ContainerAppName --resource-group $ResourceGroup 2>$null
if (-not $appExists) {
    Write-Host "Container App '$ContainerAppName' not found in resource group '$ResourceGroup'." -ForegroundColor Red
    exit 1
}

# Get the app FQDN
$appFqdn = az containerapp show --name $ContainerAppName --resource-group $ResourceGroup --query "properties.configuration.ingress.fqdn" -o tsv
Write-Host "Container App FQDN: $appFqdn" -ForegroundColor Cyan

# Get domain verification ID
$verificationId = az containerapp show --name $ContainerAppName --resource-group $ResourceGroup --query "properties.customDomainVerificationId" -o tsv
Write-Host "Domain Verification ID: $verificationId" -ForegroundColor Cyan

# Check DNS configuration
Write-Host "`nDNS Records that should be configured:" -ForegroundColor Yellow
Write-Host "1. CNAME record: demo points to $appFqdn" -ForegroundColor White
Write-Host "2. TXT record: asuid.demo with value $verificationId" -ForegroundColor White

Write-Host "`nAttempting to verify DNS records..." -ForegroundColor Yellow

# Check DNS resolution
try {
    $dnsResult = nslookup $CustomDomain 2>&1
    Write-Host "DNS Lookup Result:" -ForegroundColor Cyan
    Write-Host $dnsResult -ForegroundColor White

    if ($dnsResult -match $appFqdn) {
        Write-Host "✓ CNAME record appears to be correctly configured." -ForegroundColor Green
    } else {
        Write-Host "✗ CNAME record may not be correctly configured." -ForegroundColor Red
    }
} catch {
    Write-Host "Failed to check DNS resolution: $_" -ForegroundColor Red
}

# List custom domains on the container app
Write-Host "`nChecking if domain is configured in the Container App..." -ForegroundColor Yellow
$domains = az containerapp hostname list --name $ContainerAppName --resource-group $ResourceGroup | ConvertFrom-Json
$customDomain = $domains | Where-Object { $_.hostname -eq $CustomDomain }

if ($customDomain) {
    Write-Host "✓ Domain is configured in the Container App." -ForegroundColor Green
    Write-Host "Domain details:" -ForegroundColor Cyan
    Write-Host "  Hostname: $($customDomain.hostname)" -ForegroundColor White
    Write-Host "  Binding status: $($customDomain.bindingStatus)" -ForegroundColor White
    
    if ($customDomain.certificateId) {
        Write-Host "  Certificate ID: $($customDomain.certificateId)" -ForegroundColor White
        Write-Host "✓ Certificate is bound to the domain." -ForegroundColor Green
    } else {
        Write-Host "✗ No certificate bound to the domain." -ForegroundColor Red
    }
} else {
    Write-Host "✗ Domain is not configured in the Container App." -ForegroundColor Red
    Write-Host "You need to run the setup-custom-domain.ps1 script to configure the domain." -ForegroundColor Yellow
}

# Try to access the custom domain
Write-Host "`nAttempting to access custom domain..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://$CustomDomain" -UseBasicParsing -ErrorAction SilentlyContinue
    Write-Host "✓ Successfully accessed https://$CustomDomain" -ForegroundColor Green
    Write-Host "Status code: $($response.StatusCode)" -ForegroundColor White
} catch {
    Write-Host "✗ Failed to access https://$CustomDomain" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    
    # Try without HTTPS
    try {
        $response = Invoke-WebRequest -Uri "http://$CustomDomain" -UseBasicParsing -ErrorAction SilentlyContinue
        Write-Host "✓ Successfully accessed http://$CustomDomain" -ForegroundColor Yellow
        Write-Host "Status code: $($response.StatusCode)" -ForegroundColor White
        Write-Host "Certificate may still be provisioning. This can take 5-15 minutes." -ForegroundColor Yellow
    } catch {
        Write-Host "✗ Failed to access http://$CustomDomain" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`nRemember:" -ForegroundColor Yellow
Write-Host "1. DNS changes can take time to propagate (up to 48 hours in some cases)" -ForegroundColor White
Write-Host "2. Certificate provisioning can take 5-15 minutes" -ForegroundColor White
Write-Host "3. If you're still having issues, verify your DNS records and try running setup-custom-domain.ps1 again" -ForegroundColor White 