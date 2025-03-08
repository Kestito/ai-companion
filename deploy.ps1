# Set variables
$IMAGE_NAME = "ai-companion"
$WEB_UI_IMAGE_NAME = "web-ui-companion"
$TAG = "v1.0.10"
$RESOURCE_GROUP = "evelina-rg-20250308115110"  # Use existing resource group
$ACR_NAME = "evelinaacr8677"  # Use existing ACR
$BACKEND_CONTAINER_APP_NAME = "backend-app"
$FRONTEND_CONTAINER_APP_NAME = "frontend-app"
$LOCATION = "eastus"
$SUBSCRIPTION_ID = "7bf9df5a-7a8c-42dc-ad54-81aa4bf09b3e"
$CONTAINER_ENV_NAME = "production-env-20250308115110"  # Use existing environment
$LOG_ANALYTICS_WORKSPACE = "la-evelina-rg-20250308115110-167"  # Use existing workspace
$WEB_UI_CONTAINER_APP_NAME = "web-ui-container-app"

# Create a utilities function for colored output
function Write-ColorOutput {
    param (
        [string]$Message,
        [string]$Color = "White",
        [string]$Prefix = "===",
        [string]$Suffix = "==="
    )
    
    Write-Host "$Prefix $Message $Suffix" -ForegroundColor $Color
}

# Create a function to check if a command succeeded
function Test-CommandSuccess {
    param (
        [string]$SuccessMessage,
        [string]$ErrorMessage
    )
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput -Message $SuccessMessage -Color Green -Prefix "✅"
        return $true
    } else {
        Write-ColorOutput -Message "$ErrorMessage (Exit code: $LASTEXITCODE)" -Color Red -Prefix "❌"
        return $false
    }
}

# Start deployment process
Write-ColorOutput -Message "Starting AI Companion Deployment Verification Process" -Color Cyan

# Step 1: Verify Resource Group exists (don't create or delete)
Write-ColorOutput -Message "Verifying Resource Group: $RESOURCE_GROUP" -Color Green
$rgExists = az group exists --name $RESOURCE_GROUP
if ($rgExists -eq "true") {
    Write-ColorOutput -Message "Resource group exists, proceeding with deployment" -Color Green -Prefix "✅"
} else {
    Write-ColorOutput -Message "Resource group $RESOURCE_GROUP does not exist. Please update the script with correct resource group name." -Color Red -Prefix "❌"
    exit 1
}

# Step 2: Set Azure Subscription
Write-ColorOutput -Message "Setting Azure subscription context" -Color Green
az account set --subscription $SUBSCRIPTION_ID
if (-not (Test-CommandSuccess -SuccessMessage "Subscription set successfully" -ErrorMessage "Failed to set subscription")) {
    exit 1
}

# Step 3: Verify ACR exists
Write-ColorOutput -Message "Verifying Azure Container Registry" -Color Green
$acrExists = az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP 2>$null
if ($acrExists) {
    Write-ColorOutput -Message "ACR exists, proceeding with deployment" -Color Green -Prefix "✅"
} else {
    Write-ColorOutput -Message "ACR $ACR_NAME does not exist. Please update the script with correct ACR name." -Color Red -Prefix "❌"
    exit 1
}

# Login to ACR
Write-ColorOutput -Message "Logging in to Azure Container Registry" -Color Green
az acr login --name $ACR_NAME
if (-not (Test-CommandSuccess -SuccessMessage "Logged in to ACR successfully" -ErrorMessage "Failed to login to ACR")) {
    exit 1
}

# Get ACR credentials
Write-ColorOutput -Message "Getting ACR credentials" -Color Yellow -Prefix "→"
$acrCredentials = az acr credential show --name $ACR_NAME --resource-group $RESOURCE_GROUP | ConvertFrom-Json
$ACR_USERNAME = $acrCredentials.username
$ACR_PASSWORD = $acrCredentials.passwords[0].value

# Step 4: Check if Container Apps Environment exists
Write-ColorOutput -Message "Checking if Container App Environment exists" -Color Green
$envExists = az containerapp env show --name $CONTAINER_ENV_NAME --resource-group $RESOURCE_GROUP 2>$null
if (-not $envExists) {
    Write-ColorOutput -Message "Container App Environment does not exist. Creating new environment." -Color Yellow -Prefix "→"
    
    # Create Log Analytics workspace if it doesn't exist
    $workspaceExists = az monitor log-analytics workspace show --resource-group $RESOURCE_GROUP --workspace-name $LOG_ANALYTICS_WORKSPACE 2>$null
    if (-not $workspaceExists) {
        Write-ColorOutput -Message "Creating Log Analytics workspace" -Color Yellow -Prefix "→"
        az monitor log-analytics workspace create `
            --resource-group $RESOURCE_GROUP `
            --workspace-name $LOG_ANALYTICS_WORKSPACE `
            --location $LOCATION

        if (-not (Test-CommandSuccess -SuccessMessage "Log Analytics workspace created successfully" -ErrorMessage "Failed to create Log Analytics workspace")) {
            exit 1
        }
    }

    # Get Log Analytics workspace details
    Write-ColorOutput -Message "Getting Log Analytics workspace details" -Color Yellow -Prefix "→"
    $workspace = az monitor log-analytics workspace show `
        --resource-group $RESOURCE_GROUP `
        --workspace-name $LOG_ANALYTICS_WORKSPACE | ConvertFrom-Json

    $workspaceId = $workspace.customerId
    $workspaceKey = az monitor log-analytics workspace get-shared-keys `
        --resource-group $RESOURCE_GROUP `
        --workspace-name $LOG_ANALYTICS_WORKSPACE `
        --query primarySharedKey -o tsv

    # Create Container App Environment
    Write-ColorOutput -Message "Creating Container App Environment" -Color Yellow -Prefix "→"
    az containerapp env create `
        --name $CONTAINER_ENV_NAME `
        --resource-group $RESOURCE_GROUP `
        --location $LOCATION `
        --logs-destination log-analytics `
        --logs-workspace-id $workspaceId `
        --logs-workspace-key $workspaceKey

    if (-not (Test-CommandSuccess -SuccessMessage "Container App Environment created successfully" -ErrorMessage "Failed to create Container App Environment")) {
        exit 1
    }
}

# Step 5: Check Backend Container App
Write-ColorOutput -Message "Checking Backend Container App" -Color Green
$backendAppExists = az containerapp show --name $BACKEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP 2>$null
$backendAppNeedsUpdate = $false
$backendAppRunning = $true

if ($backendAppExists) {
    # Check if it's running properly
    Write-ColorOutput -Message "Backend app exists, checking status" -Color Yellow -Prefix "→"
    
    # Get the backend app URL
    $backendAppUrl = az containerapp show --name $BACKEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
    $backendAppUrl = "https://$backendAppUrl"
    
    # Check health endpoint
    try {
        $response = Invoke-WebRequest -Uri "$backendAppUrl/monitor/health" -UseBasicParsing -ErrorAction Stop
        $content = $response.Content | ConvertFrom-Json
        if ($response.StatusCode -eq 200 -and $content.status -eq "healthy") {
            Write-ColorOutput -Message "Backend Python app is running correctly" -Color Green -Prefix "✅"
        } else {
            Write-ColorOutput -Message "Backend app returned unexpected status. Container may need to be recreated." -Color Yellow -Prefix "⚠️"
            $backendAppNeedsUpdate = $true
        }
    } catch {
        Write-ColorOutput -Message "Failed to access backend health endpoint. Container may need to be recreated." -Color Yellow -Prefix "⚠️"
        $backendAppNeedsUpdate = $true
    }
    
    # Check if this is a Python app (look for Python-related headers or response patterns)
    try {
        $response = Invoke-WebRequest -Uri "$backendAppUrl" -UseBasicParsing -ErrorAction Stop
        # Check for Chainlit or Python indicators in the response
        if ($response.Content -match "Chainlit" -or $response.Headers["Server"] -match "Python" -or $response.Content -match "Python") {
            Write-ColorOutput -Message "Confirmed that backend is a Python application" -Color Green -Prefix "✅"
        } else {
            Write-ColorOutput -Message "Backend does not appear to be the Python app we expected" -Color Yellow -Prefix "⚠️"
            $backendAppNeedsUpdate = $true
        }
    } catch {
        Write-ColorOutput -Message "Failed to verify if backend is a Python app" -Color Yellow -Prefix "⚠️"
        $backendAppNeedsUpdate = $true
    }
} else {
    Write-ColorOutput -Message "Backend app does not exist, needs to be created" -Color Yellow -Prefix "→"
    $backendAppNeedsUpdate = $true
    $backendAppRunning = $false
}

# Step 6: Check Frontend Container App
Write-ColorOutput -Message "Checking Frontend Container App" -Color Green
$frontendAppExists = az containerapp show --name $FRONTEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP 2>$null
$frontendAppNeedsUpdate = $false
$frontendAppRunning = $true

if ($frontendAppExists) {
    # Check if it's running properly
    Write-ColorOutput -Message "Frontend app exists, checking status" -Color Yellow -Prefix "→"
    
    # Get the frontend app URL
    $frontendAppUrl = az containerapp show --name $FRONTEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
    $frontendAppUrl = "https://$frontendAppUrl"
    
    # Check if the frontend is responding
    try {
        $response = Invoke-WebRequest -Uri $frontendAppUrl -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-ColorOutput -Message "Frontend app is responding" -Color Green -Prefix "✅"
            
            # Check if this is a React/Next.js app (look for typical React patterns)
            if ($response.Content -match "react" -or $response.Content -match "next" -or $response.Content -match "_next") {
                Write-ColorOutput -Message "Confirmed that frontend is a React/Next.js application" -Color Green -Prefix "✅"
            } else {
                Write-ColorOutput -Message "Frontend does not appear to be the React/Next.js app we expected" -Color Yellow -Prefix "⚠️"
                $frontendAppNeedsUpdate = $true
            }
        } else {
            Write-ColorOutput -Message "Frontend app returned unexpected status. Container may need to be recreated." -Color Yellow -Prefix "⚠️"
            $frontendAppNeedsUpdate = $true
        }
    } catch {
        Write-ColorOutput -Message "Failed to access frontend. Container may need to be recreated." -Color Yellow -Prefix "⚠️"
        $frontendAppNeedsUpdate = $true
    }
} else {
    Write-ColorOutput -Message "Frontend app does not exist, needs to be created" -Color Yellow -Prefix "→"
    $frontendAppNeedsUpdate = $true
    $frontendAppRunning = $false
}

# Step 7: Delete and recreate backend if needed
if ($backendAppNeedsUpdate) {
    if ($backendAppRunning) {
        Write-ColorOutput -Message "Deleting misconfigured backend container app" -Color Yellow -Prefix "→"
        az containerapp delete --name $BACKEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --yes
        if (-not (Test-CommandSuccess -SuccessMessage "Backend container app deleted successfully" -ErrorMessage "Failed to delete backend container app")) {
            Write-ColorOutput -Message "Continuing despite backend deletion failure" -Color Yellow -Prefix "⚠️"
        }
    }
    
    Write-ColorOutput -Message "Deploying Backend Container App" -Color Green
    az containerapp create `
        --name $BACKEND_CONTAINER_APP_NAME `
        --resource-group $RESOURCE_GROUP `
        --environment $CONTAINER_ENV_NAME `
        --image "$ACR_NAME.azurecr.io/$IMAGE_NAME`:$TAG" `
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
          AZURE_OPENAI_API_VERSION=2024-08-01-preview `
          AZURE_OPENAI_DEPLOYMENT=gpt-4o `
          AZURE_EMBEDDING_DEPLOYMENT=text-embedding-3-small `
          OPENAI_API_TYPE=azure `
          OPENAI_API_VERSION=2024-08-01-preview `
          EMBEDDING_MODEL=text-embedding-3-small `
          LLM_MODEL=gpt-4o `
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

    if (-not (Test-CommandSuccess -SuccessMessage "Backend Container App deployed successfully" -ErrorMessage "Failed to deploy Backend Container App")) {
        Write-ColorOutput -Message "Failed to deploy backend, continuing with deployment" -Color Yellow -Prefix "⚠️"
    } else {
        # Update URL and configure settings
        $backendAppUrl = az containerapp show --name $BACKEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
        $backendAppUrl = "https://$backendAppUrl"
        Write-ColorOutput -Message "Backend App URL: $backendAppUrl" -Color Cyan -Prefix "🔗"
        
        # Configure other settings
        Write-ColorOutput -Message "Configuring Backend Ingress" -Color Green
        az containerapp ingress update `
            --name $BACKEND_CONTAINER_APP_NAME `
            --resource-group $RESOURCE_GROUP `
            --target-port 8000 `
            --transport auto
            
        Write-ColorOutput -Message "Configuring CORS for Backend" -Color Green
        az containerapp ingress cors update `
            --name $BACKEND_CONTAINER_APP_NAME `
            --resource-group $RESOURCE_GROUP `
            --allowed-origins "*" `
            --allowed-methods "GET,POST,PUT,DELETE,OPTIONS" `
            --allowed-headers "*" `
            --max-age 7200 `
            --allow-credentials true
    }
} else {
    # Get existing backend URL for frontend configuration
    $backendAppUrl = az containerapp show --name $BACKEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
    $backendAppUrl = "https://$backendAppUrl"
    Write-ColorOutput -Message "Using existing Backend App URL: $backendAppUrl" -Color Cyan -Prefix "🔗"
}

# Step 8: Delete and recreate frontend if needed
if ($frontendAppNeedsUpdate) {
    # Check if frontend image exists in ACR
    Write-ColorOutput -Message "Checking if frontend image exists in ACR" -Color Yellow -Prefix "→"
    $frontendImageExists = az acr repository show --name $ACR_NAME --image "$WEB_UI_IMAGE_NAME`:$TAG" 2>$null
    
    if ($frontendImageExists) {
        if ($frontendAppRunning) {
            Write-ColorOutput -Message "Deleting misconfigured frontend container app" -Color Yellow -Prefix "→"
            az containerapp delete --name $FRONTEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --yes
            if (-not (Test-CommandSuccess -SuccessMessage "Frontend container app deleted successfully" -ErrorMessage "Failed to delete frontend container app")) {
                Write-ColorOutput -Message "Continuing despite frontend deletion failure" -Color Yellow -Prefix "⚠️"
            }
        }
        
        Write-ColorOutput -Message "Deploying Frontend Container App" -Color Green
        az containerapp create `
            --name $FRONTEND_CONTAINER_APP_NAME `
            --resource-group $RESOURCE_GROUP `
            --environment $CONTAINER_ENV_NAME `
            --image "$ACR_NAME.azurecr.io/$WEB_UI_IMAGE_NAME`:$TAG" `
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
              NEXT_PUBLIC_API_URL=$backendAppUrl `
              NODE_ENV=production

        if (-not (Test-CommandSuccess -SuccessMessage "Frontend Container App deployed successfully" -ErrorMessage "Failed to deploy Frontend Container App")) {
            Write-ColorOutput -Message "Frontend deployment failed, continuing with backend only" -Color Yellow -Prefix "⚠️"
        } else {
            $frontendAppUrl = az containerapp show --name $FRONTEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
            $frontendAppUrl = "https://$frontendAppUrl"
            Write-ColorOutput -Message "Frontend App URL: $frontendAppUrl" -Color Cyan -Prefix "🔗"
        }
    } else {
        Write-ColorOutput -Message "Frontend image does not exist in ACR. Cannot deploy frontend." -Color Yellow -Prefix "⚠️"
    }
}

# Step 9: Deployment Summary
Write-ColorOutput -Message "Deployment Summary" -Color Green -Prefix "📋"
Write-Host ""
Write-Host "Backend Application:" -ForegroundColor Cyan
Write-Host "  URL: $backendAppUrl" -ForegroundColor White
Write-Host "  Status Endpoint: $backendAppUrl/chat/status" -ForegroundColor White
Write-Host "  Health Endpoint: $backendAppUrl/monitor/health" -ForegroundColor White
Write-Host ""

# Check if frontend exists for summary
$frontendExists = az containerapp show --name $FRONTEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP 2>$null
if ($frontendExists) {
    $frontendAppUrl = az containerapp show --name $FRONTEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
    $frontendAppUrl = "https://$frontendAppUrl"
    
    Write-Host "Frontend Application:" -ForegroundColor Cyan
    Write-Host "  URL: $frontendAppUrl" -ForegroundColor White
    Write-Host ""
}

Write-Host "Resource Group: $RESOURCE_GROUP" -ForegroundColor Cyan
Write-Host "Container Registry: $ACR_NAME" -ForegroundColor Cyan
Write-Host "Container App Environment: $CONTAINER_ENV_NAME" -ForegroundColor Cyan
Write-Host ""

Write-ColorOutput -Message "Deployment Verification Complete" -Color Green -Prefix "🚀" 