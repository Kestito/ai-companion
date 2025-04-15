# Deploy Scheduled Messaging Processor to Azure Container Apps
param(
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = "evelina-rg-20250308115110",
    
    [Parameter(Mandatory=$false)]
    [string]$ContainerAppName = "scheduled-messaging-app",
    
    [Parameter(Mandatory=$false)]
    [string]$ContainerAppEnvironment = "production-env-20250308115110",
    
    [Parameter(Mandatory=$false)]
    [string]$ImageTag = "latest",
    
    [Parameter(Mandatory=$false)]
    [string]$Registry = "evelinaacr8677.azurecr.io",
    
    [Parameter(Mandatory=$false)]
    [string]$SubscriptionId = "7bf9df5a-7a8c-42dc-ad54-81aa4bf09b3e",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipBuild = $false,
    
    [Parameter(Mandatory=$false)]
    [string]$UseExistingImage = ""
)

function Write-ColorOutput {
    param (
        [string]$Message,
        [string]$Color = "White",
        [string]$Prefix = "===",
        [string]$Suffix = "==="
    )
    
    Write-Host "$Prefix $Message $Suffix" -ForegroundColor $Color
}

# Ensure Azure CLI is installed
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI is not installed. Please install it from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
}

# Check for yq installation
$yqAvailable = $false
if (Get-Command yq -ErrorAction SilentlyContinue) {
    $yqAvailable = $true
    Write-ColorOutput -Message "yq tool is available, will use YAML-based approach" -Color Green
} else {
    Write-ColorOutput -Message "yq tool is not available, will use JSON-based approach instead" -Color Yellow
    # We're not attempting to install yq automatically as it may require admin privileges
}

# Check if Docker is available - only if we're not skipping the build
if (-not $SkipBuild) {
    # Check if Docker is available
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker is not installed or not in PATH. Please install Docker Desktop."
        exit 1
    }
    
    # Check if docker is running
    try {
        $dockerInfo = docker info 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Docker is installed but not running. Please start Docker Desktop."
            exit 1
        }
    } catch {
        Write-Error "Failed to check Docker status: $_"
        exit 1
    }
}

# Check if logged in to Azure
$account = az account show --output json | ConvertFrom-Json
if (-not $account) {
    Write-Host "Not logged in to Azure. Running 'az login'..."
    az login
    $account = az account show --output json | ConvertFrom-Json
}

Write-ColorOutput -Message "Logged in as $($account.user.name) in subscription $($account.name)" -Color Cyan

# Set subscription if provided
if ($SubscriptionId) {
    Write-ColorOutput -Message "Setting subscription to $SubscriptionId" -Color Yellow
    az account set --subscription $SubscriptionId
}

# Extract ACR name from registry URL
$acrName = ($Registry -split '\.')[0]

# Determine the image to use
$imageRepository = "scheduled-messaging"
$fullImageName = "$Registry/$imageRepository`:$ImageTag"

if ($SkipBuild) {
    Write-ColorOutput -Message "Skipping build and push steps (-SkipBuild flag detected)" -Color Yellow
    
    # If user specified an existing image to use
    if ($UseExistingImage) {
        Write-ColorOutput -Message "Using specified existing image: $UseExistingImage" -Color Yellow
        $fullImageName = $UseExistingImage
    } else {
        # Check if the scheduled-messaging image already exists
        $repoExists = az acr repository show --name $acrName --repository $imageRepository 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput -Message "Found existing $imageRepository repository" -Color Green
        } else {
            # If scheduled-messaging doesn't exist, use the main ai-companion image instead
            Write-ColorOutput -Message "No $imageRepository repository found, using ai-companion instead" -Color Yellow
            
            # Find the latest ai-companion tag
            $latestTag = az acr repository show-tags --name $acrName --repository "ai-companion" --orderby time_desc --top 1 --query "[0]" -o tsv
            
            if ($latestTag) {
                Write-ColorOutput -Message "Using latest ai-companion image: $latestTag" -Color Green
                $fullImageName = "$Registry/ai-companion:$latestTag"
            } else {
                Write-Error "No ai-companion image found. Please build the image first or specify an existing image using -UseExistingImage."
                exit 1
            }
        }
    }
} else {
    # Build and push Docker image
    Write-ColorOutput -Message "Building Docker image: $fullImageName" -Color Green
    
    # Check if Dockerfile exists
    if (-not (Test-Path "scheduler-container.Dockerfile")) {
        Write-Error "scheduler-container.Dockerfile not found in current directory."
        exit 1
    }
    
    # Check if .dockerignore exists, create if not
    if (-not (Test-Path ".dockerignore")) {
        Write-ColorOutput -Message ".dockerignore file not found, creating a default one" -Color Yellow
        @"
# Version control
.git/
.gitignore

# Virtual environments
venv/
env/
ENV/

# Python cache files
__pycache__/
*.py[cod]
*$py.class

# Node modules and Next.js files
node_modules/
.next/

# Large data directories
data/
images/
logs/
generated_images/
.pytest_cache/
"@ | Out-File -FilePath ".dockerignore" -Encoding utf8
    }
    
    # Build Docker image with better output
    Write-ColorOutput -Message "Starting Docker build - this may take a few minutes..." -Color Yellow
    
    if ($VerbosePreference -eq 'Continue') {
        docker build -t $fullImageName -f scheduler-container.Dockerfile . --progress=plain
    } else {
        docker build -t $fullImageName -f scheduler-container.Dockerfile .
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker build failed. Please check the error messages above."
        exit 1
    }
    
    Write-ColorOutput -Message "Docker build completed successfully" -Color Green
    
    # Login to ACR and push image
    Write-ColorOutput -Message "Logging in to Azure Container Registry: $acrName" -Color Yellow
    az acr login --name $acrName
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to login to ACR. Please check your permissions."
        exit 1
    }
    
    Write-ColorOutput -Message "Pushing image to registry: $fullImageName" -Color Yellow
    docker push $fullImageName
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to push image to ACR. Please check your permissions and network connection."
        exit 1
    }
    
    Write-ColorOutput -Message "Image pushed successfully" -Color Green
}

# Deploy to Azure Container App
Write-ColorOutput -Message "Deploying to Azure Container App: $ContainerAppName" -Color Cyan
Write-ColorOutput -Message "Using image: $fullImageName" -Color Cyan

# Properly format the container command
$containerCommand = '["python", "-m", "src.ai_companion.modules.scheduled_messaging.processor"]'

# Check if container app exists
$appExists = az containerapp show --resource-group $ResourceGroup --name $ContainerAppName 2>&1
if ($LASTEXITCODE -ne 0) {
    # Create the container app
    Write-ColorOutput -Message "Creating new Container App: $ContainerAppName" -Color Yellow
    
    Write-Host "Running: az containerapp create --resource-group $ResourceGroup --name $ContainerAppName --environment $ContainerAppEnvironment..."
    
    az containerapp create `
        --resource-group $ResourceGroup `
        --name $ContainerAppName `
        --environment $ContainerAppEnvironment `
        --image $fullImageName `
        --target-port 8080 `
        --ingress 'internal' `
        --min-replicas 1 `
        --max-replicas 1 `
        --env-vars "CONTAINER_APP_ENV=prod" "USE_MANAGED_IDENTITY=true" `
        --cpu 1.0 `
        --memory 2.0 `
        --registry-server $Registry `
        --command $containerCommand
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create Container App. Please check your Azure permissions and resource group."
        exit 1
    }
} else {
    # Update existing container app
    Write-ColorOutput -Message "Updating existing Container App: $ContainerAppName" -Color Yellow
    
    az containerapp update `
        --resource-group $ResourceGroup `
        --name $ContainerAppName `
        --image $fullImageName `
        --command $containerCommand
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to update Container App. Please check your Azure permissions."
        exit 1
    }
}

# Set environment variables for Supabase connection
Write-ColorOutput -Message "Setting environment variables for Supabase connection" -Color Yellow

# Try to get backend URL
try {
    $backendAppUrl = az containerapp show --name "backend-app" --resource-group $ResourceGroup --query "properties.configuration.ingress.fqdn" -o tsv
    
    # Update environment variables (get the Supabase URL and key from the backend app environment)
    Write-Host "Setting SUPABASE_URL to backend app URL: $backendAppUrl"
    
    az containerapp update `
        --resource-group $ResourceGroup `
        --name $ContainerAppName `
        --set-env-vars "SUPABASE_URL=https://$backendAppUrl" "APPLICATIONINSIGHTS_CONNECTION_STRING=\${APPLICATIONINSIGHTS_CONNECTION_STRING}"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to set environment variables. Continuing anyway."
    }
} catch {
    Write-ColorOutput -Message "Could not get backend app URL. You may need to manually set the SUPABASE_URL environment variable." -Color Red
}

# Configure health probes
Write-ColorOutput -Message "Configuring health probes" -Color Yellow

Write-ColorOutput -Message "Health probes need to be configured manually in the Azure Portal" -Color Yellow
Write-ColorOutput -Message "Please follow these steps:" -Color Yellow
Write-ColorOutput -Message "1. Go to Azure Portal > Container Apps > $ContainerAppName" -Color Yellow
Write-ColorOutput -Message "2. Select 'Containers' under the Settings section" -Color Yellow
Write-ColorOutput -Message "3. Click on your container and add health probes:" -Color Yellow
Write-ColorOutput -Message "   - Startup probe: HTTP GET /health on port 8080 (Initial delay: 10s, Period: 10s, Timeout: 5s, Failure threshold: 3)" -Color Yellow
Write-ColorOutput -Message "   - Liveness probe: HTTP GET /health on port 8080 (Initial delay: 60s, Period: 30s, Timeout: 5s, Failure threshold: 3)" -Color Yellow

Write-ColorOutput -Message "Deployment completed successfully!" -Color Green

# Replace restart with update command 
Write-ColorOutput -Message "Restarting the Container App..." -Color Yellow

az containerapp update --resource-group $ResourceGroup --name $ContainerAppName
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput -Message "Failed to restart the Container App. Please restart it manually in the Azure Portal." -Color Red
} else {
    Write-ColorOutput -Message "Container App restarted successfully" -Color Green
}

# Add log streaming to help troubleshoot startup issues
Write-ColorOutput -Message "Checking Container App logs for startup issues..." -Color Yellow
Write-ColorOutput -Message "Streaming logs for 30 seconds. Press Ctrl+C to stop early." -Color Yellow

$logEndTime = (Get-Date).AddSeconds(30)
try {
    az containerapp logs show --resource-group $ResourceGroup --name $ContainerAppName --follow --tail 100 | ForEach-Object {
        Write-Host $_
        if ((Get-Date) -gt $logEndTime) {
            throw "TimeoutException"
        }
    }
} catch {
    if ($_.Exception.Message -ne "TimeoutException") {
        Write-ColorOutput -Message "Error accessing logs: $_" -Color Red
    }
}

# Add troubleshooting information
Write-ColorOutput -Message "Troubleshooting Information for 404 Error" -Color Yellow
Write-ColorOutput -Message "If you're seeing a 404 error, please check the following:" -Color Yellow
Write-ColorOutput -Message "1. Verify the container command is correct in the Azure Portal" -Color Yellow
Write-ColorOutput -Message "2. Check that the /health endpoint is properly implemented in your application" -Color Yellow
Write-ColorOutput -Message "3. Inspect logs in the Azure Portal for startup errors" -Color Yellow
Write-ColorOutput -Message "4. Try manually restarting the Container App in the Azure Portal" -Color Yellow
Write-ColorOutput -Message "5. Alternatively, you can use the fix-container-app.ps1 script:" -Color Green
Write-ColorOutput -Message "   .\fix-container-app.ps1 -ResourceGroup $ResourceGroup -ContainerAppName $ContainerAppName" -Color Green

# Show app URL
$appUrl = az containerapp show --resource-group $ResourceGroup --name $ContainerAppName --query "properties.configuration.ingress.fqdn" -o tsv
Write-ColorOutput -Message "Container App URL: $appUrl" -Color Cyan
Write-ColorOutput -Message "Health check URL: https://$appUrl/health" -Color Cyan

# Test endpoints to verify the container app is running properly
$healthCheckUrl = "https://$appUrl/health"
Write-ColorOutput -Message "Note: This internal URL is only accessible from within the Azure network" -Color Yellow
Write-ColorOutput -Message "Skipping direct endpoint test because Container App has internal ingress" -Color Yellow
Write-ColorOutput -Message "To test, you can:" -Color Yellow
Write-ColorOutput -Message "1. Use the Azure Portal to check Container App logs" -Color Yellow
Write-ColorOutput -Message "2. Connect to the Container App using Azure CLI's containerapp exec command" -Color Yellow
Write-ColorOutput -Message "3. Use a jumpbox or App Service in the same VNET to test connectivity" -Color Yellow

# Get current app status
Write-ColorOutput -Message "Current Container App status:" -Color Yellow
$appStatus = az containerapp show --resource-group $ResourceGroup --name $ContainerAppName --query "properties.runningStatus" -o tsv
Write-ColorOutput -Message "Status: $appStatus" -Color Cyan

if ($appStatus -ne "Running") {
    Write-ColorOutput -Message "Container App is not in 'Running' state! Please check logs in Azure Portal." -Color Red
    
    # Try to restart the app
    Write-ColorOutput -Message "Attempting to restart the Container App..." -Color Yellow
    az containerapp update --resource-group $ResourceGroup --name $ContainerAppName
}

# Check if the health endpoint exists in the source code
Write-ColorOutput -Message "Checking if the health endpoint is implemented in the source code..." -Color Yellow
$healthEndpointImplemented = $false

# Check common locations for health endpoint implementation
$healthFilePaths = @(
    "src/ai_companion/modules/scheduled_messaging/processor.py",
    "src/ai_companion/api/routes/health.py",
    "src/ai_companion/api/health.py"
)

foreach ($path in $healthFilePaths) {
    if (Test-Path $path) {
        $fileContent = Get-Content $path -Raw
        if ($fileContent -match "/health" -or $fileContent -match "health_check") {
            Write-ColorOutput -Message "Health endpoint found in $path" -Color Green
            $healthEndpointImplemented = $true
            break
        }
    }
}

if (-not $healthEndpointImplemented) {
    Write-ColorOutput -Message "WARNING: No health endpoint implementation found in the source code!" -Color Red
    Write-ColorOutput -Message "You need to implement a /health endpoint in your application." -Color Red
    Write-ColorOutput -Message "Here's a simple example to add to your main application file:" -Color Yellow
    Write-ColorOutput -Message '@app.get("/health")' -Color Yellow
    Write-ColorOutput -Message 'async def health_check():' -Color Yellow
    Write-ColorOutput -Message '    return {"status": "healthy"}' -Color Yellow
} 
