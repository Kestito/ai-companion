# Check for command line parameters
param (
    [switch]$ForceRebuild = $false,
    [string]$CustomTag,
    [switch]$SkipChangeDetection = $false,  # Add parameter to skip change detection
    [switch]$AutoIncrement = $true,        # Auto-increment version by default
    [switch]$CleanupLocalImages = $false,    # Add parameter to clean up local images after deployment
    [switch]$ForceUpdate = $true           # Force update container apps to latest image by default
)

# Set variables
$IMAGE_NAME = "ai-companion"
$WEB_UI_IMAGE_NAME = "web-ui-companion"
$VERSION_FILE = "./.version"               # New file to store version
$TAG = "v1.0.10"                           # Default tag (will be updated if auto-increment)
$RESOURCE_GROUP = "evelina-rg-20250308115110"  # Use existing resource group
$ACR_NAME = "evelinaacr8677"  # Use existing ACR
$BACKEND_CONTAINER_APP_NAME = "backend-app"
$FRONTEND_CONTAINER_APP_NAME = "frontend-app"
$LOCATION = "eastus"
$SUBSCRIPTION_ID = "7bf9df5a-7a8c-42dc-ad54-81aa4bf09b3e"
$CONTAINER_ENV_NAME = "production-env-20250308115110"  # Use existing environment
$LOG_ANALYTICS_WORKSPACE = "la-evelina-rg-20250308115110-167"  # Use existing workspace
$BACKEND_SRC_PATH = "./src/ai_companion"  # Path to backend source
$FRONTEND_SRC_PATH = "./src/ai_companion/interfaces/web-ui"  # Path to frontend source
$BACKEND_DOCKERFILE_PATH = "./Dockerfile"  # Path to backend Dockerfile (in root directory)
$FORCE_REBUILD = $false  # Set to true to force rebuilding images even if they exist in ACR
$BACKEND_HASH_FILE = "./.backend-hash"  # File to store hash of backend code
$FRONTEND_HASH_FILE = "./.frontend-hash"  # File to store hash of frontend code
$DETECT_CHANGES = -not $SkipChangeDetection  # Flag to enable/disable change detection

# Update variables based on parameters
if ($ForceRebuild) {
    $FORCE_REBUILD = $true
    Write-Host "Force rebuild enabled: Images will be rebuilt even if they exist in ACR" -ForegroundColor Yellow
}

# By default ForceUpdate is now true, so we only need to show the message
Write-Host "Container apps will be updated to match local image versions (ForceUpdate=true by default)" -ForegroundColor Green
Write-Host "Use -ForceUpdate:$false to disable automatic updates" -ForegroundColor Green

# By default AutoIncrement is now true
Write-Host "Version will be auto-incremented on each deployment (AutoIncrement=true by default)" -ForegroundColor Green
Write-Host "Use -AutoIncrement:$false to keep the same version" -ForegroundColor Green

# Handle version auto-incrementing (now enabled by default)
if (-not $AutoIncrement) {
    # AutoIncrement is disabled, check if custom tag is provided
    if ($CustomTag) {
        $TAG = $CustomTag
        Write-Host "Using custom tag: $TAG" -ForegroundColor Yellow
        # Update the version file with the custom tag
        $TAG | Out-File -FilePath $VERSION_FILE
    } else {
        # If no auto-increment and no custom tag, use existing version if available
        if (Test-Path $VERSION_FILE) {
            $fileVersion = Get-Content -Path $VERSION_FILE -Raw
            $TAG = $fileVersion.Trim()
            Write-Host "Using existing version from file: $TAG" -ForegroundColor Yellow
        } else {
            # If no version file, create one with default tag
            $TAG | Out-File -FilePath $VERSION_FILE
            Write-Host "Created version file with default version: $TAG" -ForegroundColor Yellow
        }
    }
} else {
    # AutoIncrement is enabled (default behavior)
    # Check if version file exists
    if (Test-Path $VERSION_FILE) {
        # Read current version
        $currentVersion = Get-Content -Path $VERSION_FILE -Raw
        Write-Host "Current version: $currentVersion" -ForegroundColor Cyan
        
        # Parse version components
        if ($currentVersion -match 'v(\d+)\.(\d+)\.(\d+)') {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            $patch = [int]$Matches[3]
            
            # Increment patch version
            $patch += 1
            
            # Create new version string
            $TAG = "v$major.$minor.$patch"
            
            Write-Host "New version: $TAG" -ForegroundColor Green
        } else {
            Write-Host "Version file format not recognized. Using default version: $TAG" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Version file not found. Creating with default version: $TAG" -ForegroundColor Yellow
    }
    
    # Write new version to file
    $TAG | Out-File -FilePath $VERSION_FILE
}

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

# Create a function to check if an image exists in ACR
function Test-ImageExistsInACR {
    param (
        [string]$ImageName,
        [string]$Tag
    )
    
    $imageExists = az acr repository show --name $ACR_NAME --image "$ImageName`:$Tag" 2>$null
    if ($imageExists) {
        Write-ColorOutput -Message "Image $ImageName`:$Tag already exists in ACR" -Color Green -Prefix "✅"
        return $true
    } else {
        Write-ColorOutput -Message "Image $ImageName`:$Tag does not exist in ACR, needs to be built" -Color Yellow -Prefix "→"
        return $false
    }
}

# Create a function to check if Docker is installed and running
function Test-DockerAvailable {
    Write-ColorOutput -Message "Checking if Docker is installed and running" -Color Green
    
    # Check if docker command is available
    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $dockerCmd) {
        Write-ColorOutput -Message "Docker is not installed or not in PATH" -Color Red -Prefix "❌"
        return $false
    }
    
    # Check if docker is running by executing a simple command
    try {
        $dockerInfo = docker info 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput -Message "Docker is installed but not running" -Color Red -Prefix "❌"
            return $false
        }
    }
    catch {
        Write-ColorOutput -Message "Failed to connect to Docker: $_" -Color Red -Prefix "❌"
        return $false
    }
    
    Write-ColorOutput -Message "Docker is installed and running" -Color Green -Prefix "✅"
    return $true
}

# Create a function to check if source directories exist
function Test-SourceDirectoriesExist {
    Write-ColorOutput -Message "Checking if source directories exist" -Color Green
    
    $allPathsExist = $true
    $backendExists = $true
    $frontendExists = $true
    
    # Check backend source path
    if (-not (Test-Path $BACKEND_SRC_PATH)) {
        Write-ColorOutput -Message "Backend source path not found: $BACKEND_SRC_PATH" -Color Red -Prefix "❌"
        $allPathsExist = $false
        $backendExists = $false
    } else {
        Write-ColorOutput -Message "Backend source path exists: $BACKEND_SRC_PATH" -Color Green -Prefix "✅"
        
        # Check backend Dockerfile
        if (-not (Test-Path $BACKEND_DOCKERFILE_PATH)) {
            Write-ColorOutput -Message "Backend Dockerfile not found at $BACKEND_DOCKERFILE_PATH" -Color Yellow -Prefix "⚠️"
            # We don't fail the overall check for missing Dockerfile if directory exists
            # since images might already exist in the registry
        } else {
            Write-ColorOutput -Message "Backend Dockerfile exists" -Color Green -Prefix "✅"
        }
    }
    
    # Check frontend source path
    if (-not (Test-Path $FRONTEND_SRC_PATH)) {
        Write-ColorOutput -Message "Frontend source path not found: $FRONTEND_SRC_PATH" -Color Red -Prefix "❌"
        $allPathsExist = $false
        $frontendExists = $false
    } else {
        Write-ColorOutput -Message "Frontend source path exists: $FRONTEND_SRC_PATH" -Color Green -Prefix "✅"
        
        # Check frontend Dockerfile
        if (-not (Test-Path "$FRONTEND_SRC_PATH/Dockerfile")) {
            Write-ColorOutput -Message "Frontend Dockerfile not found at $FRONTEND_SRC_PATH/Dockerfile" -Color Yellow -Prefix "⚠️"
            # We don't fail the overall check for missing Dockerfile if directory exists
        } else {
            Write-ColorOutput -Message "Frontend Dockerfile exists" -Color Green -Prefix "✅"
        }
    }
    
    # Summary of findings
    if (-not $backendExists -and -not $frontendExists) {
        Write-ColorOutput -Message "Both backend and frontend source paths are missing" -Color Red -Prefix "❌"
    } elseif (-not $backendExists) {
        Write-ColorOutput -Message "Backend source path is missing, but frontend exists" -Color Yellow -Prefix "⚠️"
    } elseif (-not $frontendExists) {
        Write-ColorOutput -Message "Frontend source path is missing, but backend exists" -Color Yellow -Prefix "⚠️"
    } elseif (-not (Test-Path $BACKEND_DOCKERFILE_PATH) -or -not (Test-Path "$FRONTEND_SRC_PATH/Dockerfile")) {
        Write-ColorOutput -Message "Source paths exist but one or more Dockerfiles are missing" -Color Yellow -Prefix "⚠️"
    } else {
        Write-ColorOutput -Message "All source paths and Dockerfiles exist" -Color Green -Prefix "✅"
    }
    
    return $allPathsExist
}

# Create a function to calculate a hash of a directory's content
function Get-DirectoryHash {
    param (
        [string]$Path
    )
    
    Write-ColorOutput -Message "Calculating hash for directory: $Path" -Color Green
    
    # Check if the directory exists
    if (-not (Test-Path $Path)) {
        Write-ColorOutput -Message "Directory not found: $Path" -Color Red -Prefix "❌"
        return "DIRECTORY_NOT_FOUND"
    }
    
    try {
        # Get all files in the directory and subdirectories
        $files = Get-ChildItem -Path $Path -Recurse -File | 
                  Where-Object { -not ($_.FullName -like "*/node_modules/*") -and 
                                 -not ($_.FullName -like "*/.git/*") -and
                                 -not ($_.FullName -like "*/__pycache__/*") -and
                                 -not ($_.FullName -like "*/build/*") -and
                                 -not ($_.FullName -like "*/.next/*") -and
                                 -not ($_.Name -like "*.pyc") }
        
        # Initialize a string to hold file paths and last write times
        $contentHashData = ""
        
        # For each file, add its path and last write time to the string
        foreach ($file in $files) {
            $contentHashData += "$($file.FullName)|$($file.LastWriteTimeUtc)|$($file.Length)|"
        }
        
        # Calculate a hash of the string
        $sha = [System.Security.Cryptography.SHA256]::Create()
        $hashBytes = $sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($contentHashData))
        $hash = [System.BitConverter]::ToString($hashBytes) -replace '-', ''
        
        Write-ColorOutput -Message "Hash calculated successfully: $hash" -Color Green -Prefix "✅"
        return $hash
    }
    catch {
        Write-ColorOutput -Message "Failed to calculate hash: $_" -Color Red -Prefix "❌"
        return "HASH_CALCULATION_FAILED"
    }
}

# Create a function to check if the directory has changed since last build
function Test-DirectoryChanged {
    param (
        [string]$Path,
        [string]$HashFile
    )
    
    # If we're not detecting changes, return false (no changes)
    if (-not $DETECT_CHANGES) {
        return $false
    }
    
    Write-ColorOutput -Message "Checking for changes in directory: $Path" -Color Green
    
    # Calculate current hash
    $currentHash = Get-DirectoryHash -Path $Path
    
    # Check if hash file exists
    if (-not (Test-Path $HashFile)) {
        Write-ColorOutput -Message "No previous hash found, changes detected" -Color Yellow -Prefix "→"
        
        # Save current hash for future comparisons
        $currentHash | Out-File -FilePath $HashFile
        
        return $true
    }
    
    # Read previous hash
    $previousHash = Get-Content -Path $HashFile -Raw
    
    # Compare hashes
    if ($currentHash -ne $previousHash) {
        Write-ColorOutput -Message "Changes detected in directory" -Color Yellow -Prefix "→"
        
        # Save new hash
        $currentHash | Out-File -FilePath $HashFile
        
        return $true
    }
    
    Write-ColorOutput -Message "No changes detected in directory" -Color Green -Prefix "✅"
    return $false
}

# Start deployment process
Write-ColorOutput -Message "Starting AI Companion Deployment Process" -Color Cyan

# Pre-deployment checks
Write-ColorOutput -Message "Performing pre-deployment checks" -Color Green -Prefix "🔍"

# Check if Docker is available
if (-not (Test-DockerAvailable)) {
    Write-ColorOutput -Message "Docker is required for building images. Please install Docker and ensure it's running." -Color Red -Prefix "❌"
    Write-ColorOutput -Message "Continuing with deployment, but image build steps will fail." -Color Yellow -Prefix "⚠️"
}

# Check if source directories exist
$sourcePathsResult = Test-SourceDirectoriesExist
if (-not $sourcePathsResult) {
    Write-ColorOutput -Message "Some source files are missing, but deployment will continue with existing images." -Color Yellow -Prefix "⚠️"
    
    # We'll check image existence later in the deployment process
    if (-not (Test-Path $BACKEND_DOCKERFILE_PATH)) {
        Write-ColorOutput -Message "Backend Dockerfile is missing. Will attempt to use existing image from ACR." -Color Yellow -Prefix "⚠️"
    }
    
    if (-not (Test-Path "$FRONTEND_SRC_PATH/Dockerfile")) {
        Write-ColorOutput -Message "Frontend Dockerfile is missing. Will attempt to use existing image from ACR." -Color Yellow -Prefix "⚠️"
    }
}

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

# Step 4: Build and Push Docker Images
# Build Backend Docker Image
Write-ColorOutput -Message "Building Backend Docker Image" -Color Green

# Check if image exists in ACR
$backendImageExists = Test-ImageExistsInACR -ImageName $IMAGE_NAME -Tag $TAG

# Determine if we need to build backend
$needToBuildBackend = $FORCE_REBUILD -or (-not $backendImageExists)
if (-not $needToBuildBackend) {
    Write-ColorOutput -Message "Skipping backend build as image already exists in ACR" -Color Green -Prefix "✅"
} else {
    # Check if Dockerfile exists in backend path
    if (Test-Path $BACKEND_DOCKERFILE_PATH) {
        # Build the backend image - FIXED COMMAND
        Write-ColorOutput -Message "Building backend Docker image with tag $TAG" -Color Yellow -Prefix "→"
        
        # Separate the Docker build parameters properly
        docker build -t "${IMAGE_NAME}:${TAG}" -f $BACKEND_DOCKERFILE_PATH .
        
        if (-not (Test-CommandSuccess -SuccessMessage "Backend Docker image built successfully" -ErrorMessage "Failed to build backend Docker image")) {
            Write-ColorOutput -Message "Continuing despite backend build failure" -Color Yellow -Prefix "⚠️"
        } else {
            # Tag the backend image for ACR
            Write-ColorOutput -Message "Tagging backend Docker image for ACR" -Color Yellow -Prefix "→"
            docker tag "${IMAGE_NAME}:${TAG}" "${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${TAG}"
            if (-not (Test-CommandSuccess -SuccessMessage "Backend Docker image tagged successfully" -ErrorMessage "Failed to tag backend Docker image")) {
                Write-ColorOutput -Message "Continuing despite backend tag failure" -Color Yellow -Prefix "⚠️"
            } else {
                # Push the backend image to ACR
                Write-ColorOutput -Message "Pushing backend Docker image to ACR" -Color Yellow -Prefix "→"
                docker push "${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${TAG}"
                if (-not (Test-CommandSuccess -SuccessMessage "Backend Docker image pushed to ACR successfully" -ErrorMessage "Failed to push backend Docker image to ACR")) {
                    Write-ColorOutput -Message "Continuing despite backend push failure" -Color Yellow -Prefix "⚠️"
                } else {
                    $backendImageExists = $true
                }
            }
        }
    } else {
        Write-ColorOutput -Message "Backend Dockerfile not found at $BACKEND_DOCKERFILE_PATH" -Color Yellow -Prefix "⚠️"
        Write-ColorOutput -Message "Cannot build backend Docker image" -Color Red -Prefix "❌"
    }
}

# Build Frontend Docker Image
Write-ColorOutput -Message "Building Frontend Docker Image" -Color Green

# Check if image exists in ACR
$frontendImageExists = Test-ImageExistsInACR -ImageName $WEB_UI_IMAGE_NAME -Tag $TAG

# Make sure backend URL is defined before building frontend
if (-not $backendAppUrl) {
    Write-ColorOutput -Message "Getting backend URL for frontend configuration" -Color Yellow -Prefix "→"
    $backendAppUrl = az containerapp show --name $BACKEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
    $backendAppUrl = "https://$backendAppUrl"
    Write-ColorOutput -Message "Backend App URL: $backendAppUrl" -Color Cyan -Prefix "🔗"
}

# Determine if we need to build frontend
$needToBuildFrontend = $FORCE_REBUILD -or (-not $frontendImageExists)
if (-not $needToBuildFrontend) {
    Write-ColorOutput -Message "Skipping frontend build as image already exists in ACR" -Color Green -Prefix "✅"
} else {
    # Check if Dockerfile exists in frontend path
    if (Test-Path "$FRONTEND_SRC_PATH/Dockerfile") {
        # Build the frontend image - FIXED COMMAND
        Write-ColorOutput -Message "Building frontend Docker image with tag $TAG" -Color Yellow -Prefix "→"
        
        # Create a single-line Docker build command that PowerShell can understand
        $dockerBuildCmd = "docker build --no-cache " + 
            "--build-arg NEXT_PUBLIC_SUPABASE_URL=`"https://aubulhjfeszmsheonmpy.supabase.co`" " + 
            "--build-arg NEXT_PUBLIC_SUPABASE_ANON_KEY=`"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzUyODc0MTIsImV4cCI6MjA1MDg2MzQxMn0.2u5v5XoHTHr4H0lD3W4qN3n7Z7X9jKj3Y7Q7Q7Q7Q7Q7Q7Q`" " + 
            "--build-arg NEXT_PUBLIC_AZURE_OPENAI_ENDPOINT=`"https://ai-kestutis9429ai265477517797.openai.azure.com`" " + 
            "--build-arg NEXT_PUBLIC_AZURE_OPENAI_API_KEY=`"Ec1hyYbP5j6AokTzLWtc3Bp970VbCnpRMhNmQjxgJh1LrYzlsrrOJQQJ99ALACHYHv6XJ3w3AAAAACOG0Kyl`" " + 
            "--build-arg NEXT_PUBLIC_AZURE_OPENAI_DEPLOYMENT=`"gpt-4o`" " + 
            "--build-arg NEXT_PUBLIC_EMBEDDING_MODEL=`"text-embedding-3-small`" " + 
            "--build-arg NEXT_PUBLIC_LLM_MODEL=`"gpt-4o`" " + 
            "--build-arg NEXT_PUBLIC_COLLECTION_NAME=`"Information`" " + 
            "--build-arg NEXT_PUBLIC_API_URL=`"$backendAppUrl`" " + 
            "-t `"${WEB_UI_IMAGE_NAME}:${TAG}`" " + 
            "`"$FRONTEND_SRC_PATH`""
        
        # Execute the Docker build command directly
        Write-ColorOutput -Message "Executing Docker build command" -Color Yellow -Prefix "→"
        Write-Host $dockerBuildCmd
        Invoke-Expression $dockerBuildCmd
        
        if (-not (Test-CommandSuccess -SuccessMessage "Frontend Docker image built successfully" -ErrorMessage "Failed to build frontend Docker image")) {
            Write-ColorOutput -Message "Continuing despite frontend build failure" -Color Yellow -Prefix "⚠️"
        } else {
            # Tag the frontend image for ACR
            Write-ColorOutput -Message "Tagging frontend Docker image for ACR" -Color Yellow -Prefix "→"
            docker tag "${WEB_UI_IMAGE_NAME}:${TAG}" "${ACR_NAME}.azurecr.io/${WEB_UI_IMAGE_NAME}:${TAG}"
            if (-not (Test-CommandSuccess -SuccessMessage "Frontend Docker image tagged successfully" -ErrorMessage "Failed to tag frontend Docker image")) {
                Write-ColorOutput -Message "Continuing despite frontend tag failure" -Color Yellow -Prefix "⚠️"
            } else {
                # Push the frontend image to ACR with force option
                Write-ColorOutput -Message "Pushing frontend Docker image to ACR" -Color Yellow -Prefix "→"
                docker push "${ACR_NAME}.azurecr.io/${WEB_UI_IMAGE_NAME}:${TAG}"
                if (-not (Test-CommandSuccess -SuccessMessage "Frontend Docker image pushed to ACR successfully" -ErrorMessage "Failed to push frontend Docker image to ACR")) {
                    Write-ColorOutput -Message "Continuing despite frontend push failure" -Color Yellow -Prefix "⚠️"
                } else {
                    # Set frontendImageExists to true after successful push
                    $frontendImageExists = $true
                }
            }
        }
    } else {
        Write-ColorOutput -Message "Frontend Dockerfile not found at $FRONTEND_SRC_PATH/Dockerfile" -Color Yellow -Prefix "⚠️"
        Write-ColorOutput -Message "Cannot build frontend Docker image" -Color Red -Prefix "❌"
    }
}

# Step 5: Check if Container Apps Environment exists
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

# Step 6: Check Backend Container App
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

# Step 7: Check Frontend Container App
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

# Step 8: Delete and recreate backend if needed
if ($backendAppNeedsUpdate -or $ForceUpdate) {
    if ($backendAppRunning -and (-not $ForceUpdate)) {
        Write-ColorOutput -Message "Deleting misconfigured backend container app" -Color Yellow -Prefix "→"
        az containerapp delete --name $BACKEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --yes
        if (-not (Test-CommandSuccess -SuccessMessage "Backend container app deleted successfully" -ErrorMessage "Failed to delete backend container app")) {
            Write-ColorOutput -Message "Continuing despite backend deletion failure" -Color Yellow -Prefix "⚠️"
        }
    } elseif ($backendAppRunning -and $ForceUpdate) {
        # Update the existing container app instead of deleting and recreating
        Write-ColorOutput -Message "Updating existing backend container app to image version: $TAG" -Color Yellow -Prefix "→"
        az containerapp update `
            --name $BACKEND_CONTAINER_APP_NAME `
            --resource-group $RESOURCE_GROUP `
            --image "${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${TAG}"
        
        if (-not (Test-CommandSuccess -SuccessMessage "Backend container app updated successfully" -ErrorMessage "Failed to update backend container app")) {
            Write-ColorOutput -Message "Failed to update backend, will attempt to recreate" -Color Yellow -Prefix "⚠️"
            
            # If update fails, delete and recreate
            az containerapp delete --name $BACKEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --yes
            if (-not (Test-CommandSuccess -SuccessMessage "Backend container app deleted successfully" -ErrorMessage "Failed to delete backend container app")) {
                Write-ColorOutput -Message "Continuing despite backend deletion failure" -Color Yellow -Prefix "⚠️"
            }
            $backendAppRunning = $false
        } else {
            # Get updated URL
            $backendAppUrl = az containerapp show --name $BACKEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
            $backendAppUrl = "https://$backendAppUrl"
            Write-ColorOutput -Message "Backend App updated to version $TAG" -Color Green -Prefix "✅"
            Write-ColorOutput -Message "Backend App URL: $backendAppUrl" -Color Cyan -Prefix "🔗"
        }
    }
    
    # Only create if app doesn't exist or was deleted
    if (-not $backendAppRunning) {
        Write-ColorOutput -Message "Deploying Backend Container App" -Color Green
        az containerapp create `
            --name $BACKEND_CONTAINER_APP_NAME `
            --resource-group $RESOURCE_GROUP `
            --environment $CONTAINER_ENV_NAME `
            --image "${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${TAG}" `
            --registry-server "${ACR_NAME}.azurecr.io" `
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
    }
} else {
    # Get existing backend URL for frontend configuration
    $backendAppUrl = az containerapp show --name $BACKEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
    $backendAppUrl = "https://$backendAppUrl"
    Write-ColorOutput -Message "Using existing Backend App URL: $backendAppUrl" -Color Cyan -Prefix "🔗"
}

# Step 9: Delete and recreate frontend if needed
if ($frontendAppNeedsUpdate -or $ForceUpdate) {
    # Use the already known frontendImageExists variable from Step 4
    if ($frontendImageExists) {
        if ($frontendAppRunning -and (-not $ForceUpdate)) {
            Write-ColorOutput -Message "Deleting misconfigured frontend container app" -Color Yellow -Prefix "→"
            az containerapp delete --name $FRONTEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --yes
            if (-not (Test-CommandSuccess -SuccessMessage "Frontend container app deleted successfully" -ErrorMessage "Failed to delete frontend container app")) {
                Write-ColorOutput -Message "Continuing despite frontend deletion failure" -Color Yellow -Prefix "⚠️"
            }
        } elseif ($frontendAppRunning -and $ForceUpdate) {
            # Update the existing container app instead of deleting and recreating
            Write-ColorOutput -Message "Updating existing frontend container app to image version: $TAG" -Color Yellow -Prefix "→"
            az containerapp update `
                --name $FRONTEND_CONTAINER_APP_NAME `
                --resource-group $RESOURCE_GROUP `
                --image "${ACR_NAME}.azurecr.io/${WEB_UI_IMAGE_NAME}:${TAG}" `
                --env-vars NEXT_PUBLIC_API_URL=$backendAppUrl

            if (-not (Test-CommandSuccess -SuccessMessage "Frontend container app updated successfully" -ErrorMessage "Failed to update frontend container app")) {
                Write-ColorOutput -Message "Failed to update frontend, will attempt to recreate" -Color Yellow -Prefix "⚠️"
                
                # If update fails, delete and recreate
                az containerapp delete --name $FRONTEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --yes
                if (-not (Test-CommandSuccess -SuccessMessage "Frontend container app deleted successfully" -ErrorMessage "Failed to delete frontend container app")) {
                    Write-ColorOutput -Message "Continuing despite frontend deletion failure" -Color Yellow -Prefix "⚠️"
                }
                $frontendAppRunning = $false
            } else {
                # Get URL of updated app
                $frontendAppUrl = az containerapp show --name $FRONTEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
                $frontendAppUrl = "https://$frontendAppUrl"
                Write-ColorOutput -Message "Frontend App updated to version $TAG" -Color Green -Prefix "✅"
                Write-ColorOutput -Message "Frontend App URL: $frontendAppUrl" -Color Cyan -Prefix "🔗"
            }
        }
        
        # Only create if app doesn't exist or was deleted
        if (-not $frontendAppRunning) {
            Write-ColorOutput -Message "Deploying Frontend Container App" -Color Green
            az containerapp create `
                --name $FRONTEND_CONTAINER_APP_NAME `
                --resource-group $RESOURCE_GROUP `
                --environment $CONTAINER_ENV_NAME `
                --image "${ACR_NAME}.azurecr.io/${WEB_UI_IMAGE_NAME}:${TAG}" `
                --registry-server "${ACR_NAME}.azurecr.io" `
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
                  NEXT_PUBLIC_SUPABASE_URL=https://aubulhjfeszmsheonmpy.supabase.co `
                  NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzUyODc0MTIsImV4cCI6MjA1MDg2MzQxMn0.2u5v5XoHTHr4H0lD3W4qN3n7Z7X9jKj3Y7Q7Q7Q7Q7Q7Q7Q `
                  SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc `
                  NEXT_PUBLIC_AZURE_OPENAI_ENDPOINT=https://ai-kestutis9429ai265477517797.openai.azure.com `
                  NEXT_PUBLIC_AZURE_OPENAI_API_KEY=Ec1hyYbP5j6AokTzLWtc3Bp970VbCnpRMhNmQjxgJh1LrYzlsrrOJQQJ99ALACHYHv6XJ3w3AAAAACOG0Kyl `
                  NEXT_PUBLIC_AZURE_OPENAI_DEPLOYMENT=gpt-4o `
                  NEXT_PUBLIC_EMBEDDING_MODEL=text-embedding-3-small `
                  NEXT_PUBLIC_LLM_MODEL=gpt-4o `
                  NEXT_PUBLIC_COLLECTION_NAME=Information `
                  NODE_ENV=production

            if (-not (Test-CommandSuccess -SuccessMessage "Frontend Container App deployed successfully" -ErrorMessage "Failed to deploy Frontend Container App")) {
                Write-ColorOutput -Message "Frontend deployment failed, continuing with backend only" -Color Yellow -Prefix "⚠️"
            } else {
                $frontendAppUrl = az containerapp show --name $FRONTEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
                $frontendAppUrl = "https://$frontendAppUrl"
                Write-ColorOutput -Message "Frontend App URL: $frontendAppUrl" -Color Cyan -Prefix "🔗"
            }
        }
    } else {
        Write-ColorOutput -Message "Frontend image does not exist in ACR. Cannot deploy frontend." -Color Yellow -Prefix "⚠️"
    }
} else {
    # Get existing frontend URL
    $frontendExists = az containerapp show --name $FRONTEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP 2>$null
    if ($frontendExists) {
        $frontendAppUrl = az containerapp show --name $FRONTEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
        $frontendAppUrl = "https://$frontendAppUrl"
        Write-ColorOutput -Message "Using existing Frontend App URL: $frontendAppUrl" -Color Cyan -Prefix "🔗"
        
        # Add check to see if versions match and report
        $deployedImageRef = az containerapp show --name $FRONTEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.template.containers[0].image" -o tsv
        if ($deployedImageRef -like "*:$TAG") {
            Write-ColorOutput -Message "Frontend is already at version $TAG" -Color Green -Prefix "✅"
        } else {
            Write-ColorOutput -Message "Frontend is at version $($deployedImageRef.Split(':')[1]) but local is $TAG" -Color Yellow -Prefix "⚠️"
            Write-ColorOutput -Message "Use -ForceUpdate to update to latest version" -Color Yellow -Prefix "→"
        }
    }
}

# Step 10: Deployment Summary
Write-ColorOutput -Message "Deployment Summary" -Color Green -Prefix "📋"

# Step 11: Configure Custom Domain for Frontend App
Write-ColorOutput -Message "Configuring Custom Domain for Frontend" -Color Green -Prefix "🔗"

# Define custom domain parameters
$CUSTOM_DOMAIN = "demo.evelinaai.com"

# Check if frontend exists for custom domain setup
$frontendExists = az containerapp show --name $FRONTEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP 2>$null
if ($frontendExists) {
    # Get the domain verification ID
    $verificationId = az containerapp show --name $FRONTEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.customDomainVerificationId" -o tsv
    
    Write-ColorOutput -Message "Domain verification ID: $verificationId" -Color Yellow -Prefix "→"
    Write-ColorOutput -Message "Before proceeding, ensure these DNS records are set up:" -Color Yellow -Prefix "⚠️"
    Write-ColorOutput -Message "1. A CNAME record for 'demo' pointing to your container app FQDN" -Color White
    Write-ColorOutput -Message "2. A TXT record for 'asuid.demo' with value '$verificationId'" -Color White
    
    # Prompt user to confirm DNS records are set up
    $confirmDNS = Read-Host -Prompt "Have you configured the required DNS records? (Y/N)"
    
    if ($confirmDNS.ToLower() -eq "y") {
        # Add the custom domain to the frontend container app
        Write-ColorOutput -Message "Adding custom domain to frontend app" -Color Yellow -Prefix "→"
        az containerapp hostname add --hostname $CUSTOM_DOMAIN --resource-group $RESOURCE_GROUP --name $FRONTEND_CONTAINER_APP_NAME
        
        if (-not (Test-CommandSuccess -SuccessMessage "Custom domain added successfully" -ErrorMessage "Failed to add custom domain")) {
            Write-ColorOutput -Message "Failed to add custom domain, check DNS records and try again" -Color Red -Prefix "❌"
        } else {
            # Bind a managed certificate to the custom domain
            Write-ColorOutput -Message "Binding managed certificate to custom domain" -Color Yellow -Prefix "→"
            az containerapp hostname bind --hostname $CUSTOM_DOMAIN --resource-group $RESOURCE_GROUP --name $FRONTEND_CONTAINER_APP_NAME --environment $CONTAINER_ENV_NAME --validation-method CNAME
            
            if (-not (Test-CommandSuccess -SuccessMessage "Managed certificate bound successfully" -ErrorMessage "Failed to bind managed certificate")) {
                Write-ColorOutput -Message "Failed to bind managed certificate, but domain may still be added" -Color Yellow -Prefix "⚠️"
            } else {
                Write-ColorOutput -Message "Custom domain and managed certificate configured successfully!" -Color Green -Prefix "✅"
                Write-ColorOutput -Message "Custom domain URL: https://$CUSTOM_DOMAIN" -Color Cyan -Prefix "🔗"
                
                # Wait for certificate provisioning (this can take some time)
                Write-ColorOutput -Message "Certificate provisioning in progress - this may take 5-15 minutes" -Color Yellow -Prefix "⏳"
                Write-ColorOutput -Message "You can check status in Azure Portal while waiting" -Color Yellow -Prefix "→"
            }
        }
    } else {
        Write-ColorOutput -Message "Custom domain setup skipped. Configure DNS records and run script again." -Color Yellow -Prefix "⚠️"
        Write-ColorOutput -Message "Required DNS records:" -Color White
        Write-ColorOutput -Message "1. CNAME record: demo.evelinaai.com → $frontendAppUrl" -Color White
        Write-ColorOutput -Message "2. TXT record: asuid.demo → $verificationId" -Color White
    }
} else {
    Write-ColorOutput -Message "Frontend app does not exist, skipping custom domain setup" -Color Yellow -Prefix "⚠️"
}

# Step 12: Deployment Summary
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
    if (az containerapp hostname list --name $FRONTEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "[?hostname==''$CUSTOM_DOMAIN'']" -o tsv) {
        Write-Host "  Custom Domain: https://$CUSTOM_DOMAIN" -ForegroundColor White
    }
    Write-Host ""
}

Write-Host "Resource Group: $RESOURCE_GROUP" -ForegroundColor Cyan
Write-Host "Container Registry: $ACR_NAME" -ForegroundColor Cyan
Write-Host "Container App Environment: $CONTAINER_ENV_NAME" -ForegroundColor Cyan
Write-Host ""

# Add cleanup step if requested
if ($CleanupLocalImages) {
    Write-ColorOutput -Message "Cleaning up local Docker images" -Color Green -Prefix "🧹"
    docker rmi "${IMAGE_NAME}:${TAG}" "${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${TAG}" -f
    docker rmi "${WEB_UI_IMAGE_NAME}:${TAG}" "${ACR_NAME}.azurecr.io/${WEB_UI_IMAGE_NAME}:${TAG}" -f
    Write-ColorOutput -Message "Local Docker images cleanup complete" -Color Green -Prefix "✅"
}

# Step 13: Deployment Verification
Write-ColorOutput -Message "Verifying Application Deployment" -Color Green -Prefix "🔍"

# Verify Backend Deployment
Write-ColorOutput -Message "Verifying Backend Health" -Color Yellow -Prefix "→"
try {
    $backendHealthResponse = Invoke-WebRequest -Uri "$backendAppUrl/monitor/health" -UseBasicParsing -ErrorAction Stop
    $backendStatusCode = $backendHealthResponse.StatusCode
    
    if ($backendStatusCode -eq 200) {
        $backendContent = $backendHealthResponse.Content | ConvertFrom-Json
        if ($backendContent.status -eq "healthy") {
            Write-ColorOutput -Message "Backend Application is healthy and responding correctly!" -Color Green -Prefix "✅"
        } else {
            Write-ColorOutput -Message "Backend Application responded with status code 200 but health check indicates non-healthy status: $($backendContent.status)" -Color Yellow -Prefix "⚠️"
        }
    } else {
        Write-ColorOutput -Message "Backend Application responded with unexpected status code: $backendStatusCode" -Color Yellow -Prefix "⚠️"
    }
} catch {
    Write-ColorOutput -Message "Failed to verify backend health: $_" -Color Red -Prefix "❌"
}

# Verify Frontend Deployment (if it exists)
if ($frontendExists) {
    Write-ColorOutput -Message "Verifying Frontend Accessibility" -Color Yellow -Prefix "→"
    try {
        $frontendResponse = Invoke-WebRequest -Uri $frontendAppUrl -UseBasicParsing -ErrorAction Stop
        $frontendStatusCode = $frontendResponse.StatusCode
        
        if ($frontendStatusCode -eq 200) {
            Write-ColorOutput -Message "Frontend Application is accessible and responding correctly!" -Color Green -Prefix "✅"
            
            # Verify backend connection from frontend
            Write-ColorOutput -Message "Verifying Backend connection from Frontend" -Color Yellow -Prefix "→"
            if ($frontendResponse.Content -match "api|backend|$backendAppUrl") {
                Write-ColorOutput -Message "Frontend appears to be correctly configured to connect to backend" -Color Green -Prefix "✅"
            } else {
                Write-ColorOutput -Message "Frontend may not be correctly configured to connect to backend. Check NEXT_PUBLIC_API_URL environment variable." -Color Yellow -Prefix "⚠️"
            }
        } else {
            Write-ColorOutput -Message "Frontend Application responded with unexpected status code: $frontendStatusCode" -Color Yellow -Prefix "⚠️"
        }
    } catch {
        Write-ColorOutput -Message "Failed to verify frontend accessibility: $_" -Color Red -Prefix "❌"
    }
}

# Step 13: Version Verification
Write-ColorOutput -Message "Verifying Application Versions" -Color Green -Prefix "🔍"

# Check backend version
$backendExists = az containerapp show --name $BACKEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP 2>$null
if ($backendExists) {
    $backendDeployedImageRef = az containerapp show --name $BACKEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.template.containers[0].image" -o tsv
    $backendDeployedVersion = $backendDeployedImageRef.Split(':')[1]
    
    if ($backendDeployedVersion -eq $TAG) {
        Write-ColorOutput -Message "Backend version verification: SUCCESS ($backendDeployedVersion)" -Color Green -Prefix "✅"
    } else {
        Write-ColorOutput -Message "Backend version verification: MISMATCH (Deployed: $backendDeployedVersion, Expected: $TAG)" -Color Red -Prefix "❌"
        Write-ColorOutput -Message "Use -ForceUpdate flag to update to the latest version" -Color Yellow -Prefix "→"
    }
}

# Check frontend version
$frontendExists = az containerapp show --name $FRONTEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP 2>$null
if ($frontendExists) {
    $frontendDeployedImageRef = az containerapp show --name $FRONTEND_CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.template.containers[0].image" -o tsv
    $frontendDeployedVersion = $frontendDeployedImageRef.Split(':')[1]
    
    if ($frontendDeployedVersion -eq $TAG) {
        Write-ColorOutput -Message "Frontend version verification: SUCCESS ($frontendDeployedVersion)" -Color Green -Prefix "✅"
    } else {
        Write-ColorOutput -Message "Frontend version verification: MISMATCH (Deployed: $frontendDeployedVersion, Expected: $TAG)" -Color Red -Prefix "❌"
        Write-ColorOutput -Message "Use -ForceUpdate flag to update to the latest version" -Color Yellow -Prefix "→"
    }
}

# Step 14: Deployment Verification Complete
Write-ColorOutput -Message "Deployment and Version Verification Complete" -Color Green -Prefix "🚀" 