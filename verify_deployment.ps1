# Container Deployment Verification Script
# This script checks the existing container apps and ensures they're correctly configured
# WITHOUT deleting the resource group or container registry

# Set variables for the existing deployment
$RESOURCE_GROUP = "evelina-rg-20250308115110"
$ACR_NAME = "evelinaacr8677"
$BACKEND_CONTAINER_APP_NAME = "backend-app"
$FRONTEND_CONTAINER_APP_NAME = "frontend-app"
$CONTAINER_ENV_NAME = "production-env-20250308115110"

# Color output function
function Write-ColorOutput {
    param (
        [string]$Message,
        [string]$Color = "White",
        [string]$Prefix = "===",
        [string]$Suffix = "==="
    )
    
    Write-Host "$Prefix $Message $Suffix" -ForegroundColor $Color
}

# Verification results
$backendCorrect = $true
$frontendCorrect = $true

Write-ColorOutput -Message "Starting Container App Verification" -Color Cyan -Prefix "🔍"

# Verify Resource Group exists
Write-ColorOutput -Message "Checking Resource Group: $RESOURCE_GROUP" -Color Yellow -Prefix "→"
$rgExists = az group exists --name $RESOURCE_GROUP
if ($rgExists -eq "true") {
    Write-ColorOutput -Message "Resource Group exists" -Color Green -Prefix "✅"
} else {
    Write-ColorOutput -Message "Resource Group does not exist. Please check the name." -Color Red -Prefix "❌"
    exit 1
}

# Verify Container Registry exists
Write-ColorOutput -Message "Checking Container Registry: $ACR_NAME" -Color Yellow -Prefix "→"
$acrExists = az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query "name" --output tsv 2>$null
if ($acrExists) {
    Write-ColorOutput -Message "Container Registry exists" -Color Green -Prefix "✅"
} else {
    Write-ColorOutput -Message "Container Registry does not exist. Please check the name." -Color Red -Prefix "❌"
    exit 1
}

# Get ACR credentials
$acrCredentials = az acr credential show --name $ACR_NAME --resource-group $RESOURCE_GROUP | ConvertFrom-Json
$ACR_USERNAME = $acrCredentials.username
$ACR_PASSWORD = $acrCredentials.passwords[0].value

# Verify Backend Container App
Write-ColorOutput -Message "Checking Backend Container App: $BACKEND_CONTAINER_APP_NAME" -Color Yellow -Prefix "→"
$backendExists = az containerapp show --name $BACKEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "name" --output tsv 2>$null
if ($backendExists) {
    Write-ColorOutput -Message "Backend Container App exists" -Color Green -Prefix "✅"
    
    # Verify backend is running Python
    Write-ColorOutput -Message "Checking Backend Container Configuration" -Color Yellow -Prefix "→"
    $backendConfig = az containerapp show --name $BACKEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP | ConvertFrom-Json
    $backendImage = $backendConfig.properties.template.containers[0].image
    
    if ($backendImage -match "ai-companion") {
        Write-ColorOutput -Message "Backend image is correct: $backendImage" -Color Green -Prefix "✅"
    } else {
        Write-ColorOutput -Message "Backend image is incorrect: $backendImage" -Color Red -Prefix "❌"
        $backendCorrect = $false
    }
    
    # Check running status
    $backendStatus = $backendConfig.properties.runningStatus
    Write-ColorOutput -Message "Backend app status: $backendStatus" -Color $(if ($backendStatus -eq "Running") { "Green" } else { "Red" }) -Prefix $(if ($backendStatus -eq "Running") { "✅" } else { "❌" })
    
    if ($backendStatus -ne "Running") {
        $backendCorrect = $false
    }
    
    # Check health endpoint
    try {
        $backendUrl = "https://$($backendConfig.properties.configuration.ingress.fqdn)"
        $healthEndpoint = "$backendUrl/monitor/health"
        Write-ColorOutput -Message "Checking backend health endpoint: $healthEndpoint" -Color Yellow -Prefix "→"
        $healthResponse = Invoke-WebRequest -Uri $healthEndpoint -UseBasicParsing -ErrorAction Stop
        $healthContent = $healthResponse.Content | ConvertFrom-Json
        
        if ($healthResponse.StatusCode -eq 200) {
            Write-ColorOutput -Message "Backend health check successful" -Color Green -Prefix "✅"
        } else {
            Write-ColorOutput -Message "Backend health check failed: Status $($healthResponse.StatusCode)" -Color Red -Prefix "❌"
            $backendCorrect = $false
        }
    } catch {
        Write-ColorOutput -Message "Backend health check error: $($_.Exception.Message)" -Color Red -Prefix "❌"
        $backendCorrect = $false
    }
} else {
    Write-ColorOutput -Message "Backend Container App does not exist" -Color Red -Prefix "❌"
    $backendCorrect = $false
}

# Verify Frontend Container App
Write-ColorOutput -Message "Checking Frontend Container App: $FRONTEND_CONTAINER_APP_NAME" -Color Yellow -Prefix "→"
$frontendExists = az containerapp show --name $FRONTEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "name" --output tsv 2>$null
if ($frontendExists) {
    Write-ColorOutput -Message "Frontend Container App exists" -Color Green -Prefix "✅"
    
    # Verify frontend is running Node.js
    Write-ColorOutput -Message "Checking Frontend Container Configuration" -Color Yellow -Prefix "→"
    $frontendConfig = az containerapp show --name $FRONTEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP | ConvertFrom-Json
    $frontendImage = $frontendConfig.properties.template.containers[0].image
    
    if ($frontendImage -match "web-ui") {
        Write-ColorOutput -Message "Frontend image is correct: $frontendImage" -Color Green -Prefix "✅"
    } else {
        Write-ColorOutput -Message "Frontend image is incorrect: $frontendImage" -Color Red -Prefix "❌"
        $frontendCorrect = $false
    }
    
    # Check running status
    $frontendStatus = $frontendConfig.properties.runningStatus
    Write-ColorOutput -Message "Frontend app status: $frontendStatus" -Color $(if ($frontendStatus -eq "Running") { "Green" } else { "Red" }) -Prefix $(if ($frontendStatus -eq "Running") { "✅" } else { "❌" })
    
    if ($frontendStatus -ne "Running") {
        $frontendCorrect = $false
    }
    
    # Check frontend URL
    try {
        $frontendUrl = "https://$($frontendConfig.properties.configuration.ingress.fqdn)"
        Write-ColorOutput -Message "Checking frontend URL: $frontendUrl" -Color Yellow -Prefix "→"
        $frontendResponse = Invoke-WebRequest -Uri $frontendUrl -UseBasicParsing -ErrorAction Stop
        
        if ($frontendResponse.StatusCode -eq 200) {
            Write-ColorOutput -Message "Frontend URL check successful" -Color Green -Prefix "✅"
        } else {
            Write-ColorOutput -Message "Frontend URL check failed: Status $($frontendResponse.StatusCode)" -Color Red -Prefix "❌"
            $frontendCorrect = $false
        }
    } catch {
        Write-ColorOutput -Message "Frontend URL check error: $($_.Exception.Message)" -Color Red -Prefix "❌"
        $frontendCorrect = $false
    }
    
    # Check API URL environment variable
    $frontendEnv = $frontendConfig.properties.template.containers[0].env
    $apiUrlEnv = $frontendEnv | Where-Object { $_.name -eq "NEXT_PUBLIC_API_URL" } | Select-Object -ExpandProperty value
    
    if ($apiUrlEnv) {
        Write-ColorOutput -Message "Frontend API URL is set: $apiUrlEnv" -Color Green -Prefix "✅"
    } else {
        Write-ColorOutput -Message "Frontend API URL environment variable is missing" -Color Red -Prefix "❌"
        $frontendCorrect = $false
    }
} else {
    Write-ColorOutput -Message "Frontend Container App does not exist" -Color Red -Prefix "❌"
    $frontendCorrect = $false
}

# Rebuild Container Apps if needed
if (-not $backendCorrect) {
    Write-ColorOutput -Message "Backend Container App needs to be reconfigured" -Color Red -Prefix "❌"
    $rebuildBackend = Read-Host "Do you want to delete and recreate the Backend Container App? (Y/N)"
    
    if ($rebuildBackend -eq "Y" -or $rebuildBackend -eq "y") {
        Write-ColorOutput -Message "Deleting Backend Container App..." -Color Yellow -Prefix "→"
        az containerapp delete --name $BACKEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --yes
        
        Write-ColorOutput -Message "Recreating Backend Container App..." -Color Yellow -Prefix "→"
        az containerapp create `
            --name $BACKEND_CONTAINER_APP_NAME `
            --resource-group $RESOURCE_GROUP `
            --environment $CONTAINER_ENV_NAME `
            --image "$ACR_NAME.azurecr.io/ai-companion:v1.0.10" `
            --registry-server "$ACR_NAME.azurecr.io" `
            --registry-username $ACR_USERNAME `
            --registry-password $ACR_PASSWORD `
            --target-port 8000 `
            --ingress external `
            --min-replicas 1 `
            --max-replicas 10 `
            --cpu 1.0 `
            --memory 2.0Gi `
            --env-vars `
              INTERFACE=all `
              PORT=8000 `
              QDRANT_URL=https://b88198bc-6212-4390-bbac-b1930f543812.europe-west3-0.gcp.cloud.qdrant.io `
              QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwiZXhwIjoxNzQ3MDY5MzcyfQ.plLwDbnIi7ggn_d98e-OsxpF60lcNq9nzZ0EzwFAnQw `
              AZURE_OPENAI_ENDPOINT=https://ai-kestutis9429ai265477517797.openai.azure.com `
              AZURE_OPENAI_API_KEY=Ec1hyYbP5j6AokTzLWtc3Bp970VbCnpRMhNmQjxgJh1LrYzlsrrOJQQJ99ALACHYHv6XJ3w3AAAAACOG0Kyl `
              AZURE_OPENAI_API_VERSION=2025-04-16 `
              AZURE_OPENAI_DEPLOYMENT=o4-mini `
              AZURE_EMBEDDING_DEPLOYMENT=text-embedding-3-small `
              OPENAI_API_TYPE=azure `
              OPENAI_API_VERSION=2025-04-16 `
              EMBEDDING_MODEL=text-embedding-3-small `
              LLM_MODEL=o4-mini `
              SUPABASE_URL=https://aubulhjfeszmsheonmpy.supabase.co `
              SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc `
              COLLECTION_NAME=Information `
              ELEVENLABS_API_KEY=sk_f8aaf95ce7c9bc93c1341eded4014382cd6444e84cb5c03d `
              ELEVENLABS_VOICE_ID=qSfcmCS9tPikUrDxO8jt `
              PYTHONUNBUFFERED=1 `
              PYTHONPATH=/app `
              STT_MODEL_NAME=whisper `
              TTS_MODEL_NAME=eleven_flash_v2_5 `
              CHAINLIT_FORCE_POLLING=true `
              CHAINLIT_NO_WEBSOCKET=true `
              CHAINLIT_POLLING_MAX_WAIT=5000
              
        # Configure CORS for Backend
        Write-ColorOutput -Message "Configuring CORS for Backend" -Color Yellow -Prefix "→"
        az containerapp ingress cors update `
            --name $BACKEND_CONTAINER_APP_NAME `
            --resource-group $RESOURCE_GROUP `
            --allowed-origins "*" `
            --allowed-methods "GET,POST,PUT,DELETE,OPTIONS" `
            --allowed-headers "*" `
            --max-age 7200 `
            --allow-credentials true
    }
}

if (-not $frontendCorrect) {
    Write-ColorOutput -Message "Frontend Container App needs to be reconfigured" -Color Red -Prefix "❌"
    $rebuildFrontend = Read-Host "Do you want to delete and recreate the Frontend Container App? (Y/N)"
    
    if ($rebuildFrontend -eq "Y" -or $rebuildFrontend -eq "y") {
        # Get backend URL for frontend configuration
        $backendConfig = az containerapp show --name $BACKEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP | ConvertFrom-Json
        $backendUrl = "https://$($backendConfig.properties.configuration.ingress.fqdn)"
        
        Write-ColorOutput -Message "Deleting Frontend Container App..." -Color Yellow -Prefix "→"
        az containerapp delete --name $FRONTEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --yes
        
        Write-ColorOutput -Message "Recreating Frontend Container App..." -Color Yellow -Prefix "→"
        az containerapp create `
            --name $FRONTEND_CONTAINER_APP_NAME `
            --resource-group $RESOURCE_GROUP `
            --environment $CONTAINER_ENV_NAME `
            --image "$ACR_NAME.azurecr.io/web-ui-companion:v1.0.10" `
            --registry-server "$ACR_NAME.azurecr.io" `
            --registry-username $ACR_USERNAME `
            --registry-password $ACR_PASSWORD `
            --target-port 3000 `
            --ingress external `
            --min-replicas 1 `
            --max-replicas 5 `
            --cpu 0.5 `
            --memory 1.0Gi `
            --env-vars `
              NEXT_PUBLIC_API_URL=$backendUrl `
              NODE_ENV=production
    }
}

# Final summary
Write-ColorOutput -Message "Verification Complete" -Color Cyan -Prefix "🔍"
Write-Host ""
Write-Host "Resource Group: $RESOURCE_GROUP" -ForegroundColor Cyan
Write-Host "Container Registry: $ACR_NAME" -ForegroundColor Cyan
Write-Host ""

if ($backendExists) {
    $backendConfig = az containerapp show --name $BACKEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP | ConvertFrom-Json
    $backendUrl = "https://$($backendConfig.properties.configuration.ingress.fqdn)"
    Write-Host "Backend Application:" -ForegroundColor Cyan
    Write-Host "  URL: $backendUrl" -ForegroundColor White
    Write-Host "  Status: $($backendConfig.properties.runningStatus)" -ForegroundColor White
    Write-Host "  Configuration: $(if ($backendCorrect) { "Correct ✅" } else { "Incorrect ❌" })" -ForegroundColor $(if ($backendCorrect) { "Green" } else { "Red" })
    Write-Host ""
}

if ($frontendExists) {
    $frontendConfig = az containerapp show --name $FRONTEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP | ConvertFrom-Json
    $frontendUrl = "https://$($frontendConfig.properties.configuration.ingress.fqdn)"
    Write-Host "Frontend Application:" -ForegroundColor Cyan
    Write-Host "  URL: $frontendUrl" -ForegroundColor White
    Write-Host "  Status: $($frontendConfig.properties.runningStatus)" -ForegroundColor White
    Write-Host "  Configuration: $(if ($frontendCorrect) { "Correct ✅" } else { "Incorrect ❌" })" -ForegroundColor $(if ($frontendCorrect) { "Green" } else { "Red" })
    Write-Host ""
} 