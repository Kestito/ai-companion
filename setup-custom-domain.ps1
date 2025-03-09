# Custom Domain Configuration Script for Azure Container App
# This script adds a custom domain to an existing Azure Container App and configures a managed certificate

# Parameters with default values from main deployment
param (
    [string]$ResourceGroup = "evelina-rg-20250308115110",
    [string]$ContainerAppName = "frontend-app",
    [string]$CustomDomain = "demo.evelinaai.com",
    [string]$ContainerEnvName = "production-env-20250308115110"
)

Write-Host "=== Setting up custom domain $CustomDomain for $ContainerAppName ===" -ForegroundColor Cyan

# Get the domain verification ID
Write-Host "Getting domain verification ID..." -ForegroundColor Yellow
$verificationId = az containerapp show --name $ContainerAppName --resource-group $ResourceGroup --query "properties.customDomainVerificationId" -o tsv

if (-not $verificationId) {
    Write-Host "Failed to get domain verification ID. Make sure the Container App exists." -ForegroundColor Red
    exit 1
}

# Get the app FQDN
$appFqdn = az containerapp show --name $ContainerAppName --resource-group $ResourceGroup --query "properties.configuration.ingress.fqdn" -o tsv

Write-Host "`nBefore continuing, please ensure these DNS records are set up:" -ForegroundColor Yellow
Write-Host "1. CNAME record: $CustomDomain points to $appFqdn" -ForegroundColor White
Write-Host "2. TXT record: asuid.$CustomDomain with value $verificationId" -ForegroundColor White
Write-Host "`nFor subdomain demo.evelinaai.com, you need:" -ForegroundColor Yellow
Write-Host "1. CNAME record: demo points to $appFqdn" -ForegroundColor White
Write-Host "2. TXT record: asuid.demo with value $verificationId" -ForegroundColor White

$confirm = Read-Host "`nHave you configured these DNS records? (y/n)"
if ($confirm.ToLower() -ne "y") {
    Write-Host "Setup cancelled. Please configure the DNS records and run the script again." -ForegroundColor Yellow
    exit 0
}

# Add the custom domain to the frontend container app
Write-Host "`nAdding custom domain to container app..." -ForegroundColor Yellow
$addResult = az containerapp hostname add --hostname $CustomDomain --resource-group $ResourceGroup --name $ContainerAppName

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to add custom domain. Error: $addResult" -ForegroundColor Red
    Write-Host "Please check your DNS records and try again." -ForegroundColor Red
    exit 1
}

Write-Host "Custom domain added successfully!" -ForegroundColor Green

# Bind a managed certificate to the custom domain
Write-Host "`nBinding managed certificate to custom domain..." -ForegroundColor Yellow
$bindResult = az containerapp hostname bind --hostname $CustomDomain --resource-group $ResourceGroup --name $ContainerAppName --environment $ContainerEnvName --validation-method CNAME

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to bind managed certificate. Error: $bindResult" -ForegroundColor Red
    Write-Host "The domain may still be added but without HTTPS." -ForegroundColor Yellow
    exit 1
}

Write-Host "Managed certificate bound successfully!" -ForegroundColor Green
Write-Host "`nCertificate provisioning is in progress - this may take 5-15 minutes to complete." -ForegroundColor Yellow
Write-Host "You can check the status in Azure Portal while waiting." -ForegroundColor Yellow

Write-Host "`nSetup complete! Once the certificate is provisioned, your app will be available at:" -ForegroundColor Green
Write-Host "https://$CustomDomain" -ForegroundColor Cyan

# Check custom domain status
Write-Host "`nChecking custom domain status..." -ForegroundColor Yellow
$domains = az containerapp hostname list --name $ContainerAppName --resource-group $ResourceGroup | ConvertFrom-Json
$customDomain = $domains | Where-Object { $_.hostname -eq $CustomDomain }

if ($customDomain) {
    Write-Host "Domain found in configuration:" -ForegroundColor Green
    Write-Host "Hostname: $($customDomain.hostname)" -ForegroundColor Cyan
    Write-Host "Binding status: $($customDomain.bindingStatus)" -ForegroundColor Cyan
    Write-Host "Certificate: $($customDomain.certificateId)" -ForegroundColor Cyan
} else {
    Write-Host "Domain not found in container app configuration." -ForegroundColor Red
} 