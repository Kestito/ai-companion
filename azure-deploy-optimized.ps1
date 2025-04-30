param (
    [Parameter(Mandatory = $false)]
    [string]$ResourceGroupName = "rg-aicompanion",

    [Parameter(Mandatory = $false)]
    [string]$Location = "eastus",

    [Parameter(Mandatory = $false)]
    [string]$ImageTag = "latest",

    [Parameter(Mandatory = $false)]
    [switch]$ForceUpdate = $false,

    [Parameter(Mandatory = $false)]
    [switch]$SkipLogin = $false
)

# Set variables
$VERSION_FILE = "./.version"
$TAG = "v1.0.10"  # Default tag
$RESOURCE_GROUP = "evelina-rg"
$ACR_NAME = "evelinaacr8677"
$BACKEND_APP_NAME = "backend-app"
$FRONTEND_APP_NAME = "frontend-app"
$CONTAINER_ENV_NAME = "production-env"

# If VERSION_FILE exists, use that version instead
if (Test-Path $VERSION_FILE) {
    $TAG = Get-Content -Path $VERSION_FILE -Raw
    $TAG = $TAG.Trim()
}

# Output helper function
function Write-ColorOutput {
    param (
        [string]$Message,
        [string]$Color = "White",
        [string]$Prefix = "==>"
    )
    
    Write-Host "$Prefix $Message" -ForegroundColor $Color
}

# Check if az command is available
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-ColorOutput -Message "Azure CLI not found. Please install Azure CLI first." -Color Red -Prefix "❌"
    exit 1
}

# Login to Azure if not skipped
if (-not $SkipLogin) {
    Write-ColorOutput -Message "Logging in to Azure..." -Color Yellow
    az login
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput -Message "Failed to login to Azure" -Color Red -Prefix "❌"
        exit 1
    }
}

# Set Azure subscription
Write-ColorOutput -Message "Setting Azure subscription context..." -Color Yellow
$subscription = az account show --query id -o tsv
Write-ColorOutput -Message "Using subscription: $subscription" -Color Cyan

# Login to Azure Container Registry
Write-ColorOutput -Message "Logging in to Azure Container Registry..." -Color Yellow
az acr login --name $ACR_NAME
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput -Message "Failed to login to ACR" -Color Red -Prefix "❌"
    exit 1
}

# Build and push images using our optimized azure-deploy.sh script
Write-ColorOutput -Message "Building and pushing optimized Docker images..." -Color Yellow
bash ./azure-deploy.sh $TAG
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput -Message "Failed to build and push images" -Color Red -Prefix "❌"
    exit 1
}

# Get the backend app URL if it exists
$backendAppExists = az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP 2>$null
if ($backendAppExists) {
    $backendAppUrl = az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
    $backendAppUrl = "https://$backendAppUrl"
    Write-ColorOutput -Message "Using existing Backend App URL: $backendAppUrl" -Color Green
} else {
    Write-ColorOutput -Message "Backend app does not exist, will be created" -Color Yellow
}

# Create or update backend app
Write-ColorOutput -Message "Deploying backend app..." -Color Yellow

if (-not $backendAppExists) {
    # Create backend app
    az containerapp create `
        --name $BACKEND_APP_NAME `
        --resource-group $RESOURCE_GROUP `
        --environment $CONTAINER_ENV_NAME `
        --image "${ACR_NAME}.azurecr.io/ai-companion:${TAG}" `
        --target-port 8000 `
        --ingress external `
        --min-replicas 1 `
        --max-replicas 3 `
        --cpu 0.5 `
        --memory 1.0Gi `
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
          SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc

    # Get backend app URL after creation
    $backendAppUrl = az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
    $backendAppUrl = "https://$backendAppUrl"
    Write-ColorOutput -Message "Backend App URL: $backendAppUrl" -Color Green
} else {
    # Update backend app if ForceUpdate is enabled
    if ($ForceUpdate) {
        az containerapp update `
            --name $BACKEND_APP_NAME `
            --resource-group $RESOURCE_GROUP `
            --image "${ACR_NAME}.azurecr.io/ai-companion:${TAG}"
        Write-ColorOutput -Message "Backend app updated to version $TAG" -Color Green
    } else {
        Write-ColorOutput -Message "Skipping backend update (use -ForceUpdate to update)" -Color Yellow
    }
}

# Create or update frontend app
$frontendAppExists = az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP 2>$null
Write-ColorOutput -Message "Deploying frontend app..." -Color Yellow

if (-not $frontendAppExists) {
    # Create frontend app
    az containerapp create `
        --name $FRONTEND_APP_NAME `
        --resource-group $RESOURCE_GROUP `
        --environment $CONTAINER_ENV_NAME `
        --image "${ACR_NAME}.azurecr.io/web-ui-companion:${TAG}" `
        --target-port 3000 `
        --ingress external `
        --min-replicas 1 `
        --max-replicas 3 `
        --cpu 0.5 `
        --memory 1.0Gi `
        --env-vars `
          NEXT_PUBLIC_API_URL=$backendAppUrl `
          NEXT_PUBLIC_SUPABASE_URL=https://aubulhjfeszmsheonmpy.supabase.co `
          NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzUyODc0MTIsImV4cCI6MjA1MDg2MzQxMn0.2u5v5XoHTHr4H0lD3W4qN3n7Z7X9jKj3Y7Q7Q7Q7Q7Q7Q7Q `
          NEXT_PUBLIC_AZURE_OPENAI_ENDPOINT=https://ai-kestutis9429ai265477517797.openai.azure.com `
          NEXT_PUBLIC_AZURE_OPENAI_API_KEY=Ec1hyYbP5j6AokTzLWtc3Bp970VbCnpRMhNmQjxgJh1LrYzlsrrOJQQJ99ALACHYHv6XJ3w3AAAAACOG0Kyl `
          NEXT_PUBLIC_AZURE_OPENAI_DEPLOYMENT=gpt-4o `
          NEXT_PUBLIC_EMBEDDING_MODEL=text-embedding-3-small `
          NEXT_PUBLIC_LLM_MODEL=gpt-4o `
          NEXT_PUBLIC_COLLECTION_NAME=Information `
          NODE_ENV=production
          
    # Get frontend app URL after creation
    $frontendAppUrl = az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
    $frontendAppUrl = "https://$frontendAppUrl"
    Write-ColorOutput -Message "Frontend App URL: $frontendAppUrl" -Color Green
} else {
    # Update frontend app if ForceUpdate is enabled
    if ($ForceUpdate) {
        az containerapp update `
            --name $FRONTEND_APP_NAME `
            --resource-group $RESOURCE_GROUP `
            --image "${ACR_NAME}.azurecr.io/web-ui-companion:${TAG}" `
            --set-env-vars NEXT_PUBLIC_API_URL=$backendAppUrl
        Write-ColorOutput -Message "Frontend app updated to version $TAG" -Color Green
    } else {
        Write-ColorOutput -Message "Skipping frontend update (use -ForceUpdate to update)" -Color Yellow
    }
}

# Verify health status
Write-ColorOutput -Message "Verifying application health..." -Color Yellow
try {
    $backendHealth = Invoke-WebRequest -Uri "$backendAppUrl/monitor/health" -UseBasicParsing
    if ($backendHealth.StatusCode -eq 200) {
        Write-ColorOutput -Message "Backend app is healthy!" -Color Green -Prefix "✓"
    } else {
        Write-ColorOutput -Message "Backend app returned status code $($backendHealth.StatusCode)" -Color Yellow -Prefix "!"
    }
} catch {
    Write-ColorOutput -Message "Could not verify backend health: $_" -Color Red -Prefix "!"
}

# Print deployment summary
Write-ColorOutput -Message "Deployment Summary" -Color Cyan -Prefix "📋"
Write-Host "Resource Group: $RESOURCE_GROUP"
Write-Host "Container App Environment: $CONTAINER_ENV_NAME"
Write-Host "Version: $TAG"
Write-Host "Backend App URL: $backendAppUrl"
if ($frontendAppUrl) {
    Write-Host "Frontend App URL: $frontendAppUrl"
}

Write-ColorOutput -Message "Deployment Complete" -Color Green -Prefix "✓" 