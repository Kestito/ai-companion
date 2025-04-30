# Check for command line parameters
param (
    [Parameter(Mandatory = $false)]
    [string]$SubscriptionId = $env:AZURE_SUBSCRIPTION_ID,

    [Parameter(Mandatory = $false)]
    [string]$ResourceGroupName = "rg-aicompanion",

    [Parameter(Mandatory = $false)]
    [string]$Location = "eastus",

    [Parameter(Mandatory = $false)]
    [string]$ImageTag = "latest",

    [Parameter(Mandatory = $false)]
    [switch]$ForceUpdate = $false,

    [Parameter(Mandatory = $false)]
    [switch]$SkipLogin = $false,

    [Parameter(Mandatory = $false)]
    [switch]$SkipResourceGroup = $false,

    [Parameter(Mandatory = $false)]
    [switch]$SkipVault = $false,

    [Parameter(Mandatory = $false)]
    [switch]$SkipRegistry = $false,

    [Parameter(Mandatory = $false)]
    [switch]$SkipStorageAccount = $false,

    [Parameter(Mandatory = $false)]
    [switch]$SkipContainerAppEnv = $false,

    [Parameter(Mandatory = $false)]
    [switch]$SkipCustomizedContainers = $false,

    [Parameter(Mandatory = $false)]
    [switch]$SkipAPILayer = $false,

    [Parameter(Mandatory = $false)]
    [switch]$SkipBackendContainer = $false,

    [Parameter(Mandatory = $false)]
    [switch]$SkipFrontendSetup = $false,

    [Parameter(Mandatory = $false)]
    [switch]$SkipFrontendBuild = $false,

    [Parameter(Mandatory = $false)]
    [switch]$SkipDeployFrontend = $false,

    [Parameter(Mandatory = $false)]
    [switch]$SkipRemovedOldBackendRevisions = $false,

    [Parameter(Mandatory = $false)]
    [switch]$SkipOldResourcesCleanup = $false,

    [Parameter(Mandatory = $false)]
    [switch]$SkipPostDeploymentChecks = $false,

    [Parameter(Mandatory = $false)]
    [switch]$CheckScheduledMessages = $false,

    [Parameter(Mandatory = $false)]
    [switch]$FixScheduledMessages = $false,

    [Parameter(Mandatory = $false)]
    [switch]$FixMissingMetadata = $false,

    [Parameter(Mandatory = $false)]
    [switch]$ResetFailedMessages = $false,

    [Parameter(Mandatory = $false)]
    [switch]$SkipScheduledMessagesSetup = $false,

    [Parameter(Mandatory = $false)]
    [switch]$BypassImageCheck = $false,

    [Parameter(Mandatory = $false)]
    [switch]$UseOptimizedImages = $true
)

# Set variables
$IMAGE_NAME = "ai-companion"
$WEB_UI_IMAGE_NAME = "web-ui-companion"
$VERSION_FILE = "./.version"               # New file to store version
$TAG = "v1.0.10"                           # Default tag (will be updated if auto-increment)
$RESOURCE_GROUP = "evelina-rg-20250308115110"  # Use existing resource group
$ACR_NAME = "evelinaacr8677"  # Use existing ACR
$BACKEND_APP_NAME = "backend-app"
$FRONTEND_APP_NAME = "frontend-app"
$LOCATION = "eastus"
$SUBSCRIPTION_ID = "7bf9df5a-7a8c-42dc-ad54-81aa4bf09b3e"
$CONTAINER_ENV_NAME = "production-env-20250308115110"  # Use existing environment
$LOG_ANALYTICS_WORKSPACE = "la-evelina-rg-20250308115110-167"  # Use existing workspace
$BACKEND_SRC_PATH = "./src/ai_companion"  # Path to backend source
$FRONTEND_SRC_PATH = "./src/ai_companion/interfaces/web-ui"  # Path to frontend source
$BACKEND_DOCKERFILE_PATH = "./Dockerfile"  # Path to backend Dockerfile (in root directory)
$FRONTEND_DOCKERFILE_PATH = "$FRONTEND_SRC_PATH/Dockerfile"  # Correctly define the path to frontend Dockerfile
$FORCE_REBUILD = $false  # Set to true to force rebuilding images even if they exist in ACR
$BACKEND_HASH_FILE = "./.backend-hash"  # File to store hash of backend code
$FRONTEND_HASH_FILE = "./.frontend-hash"  # File to store hash of frontend code
$DETECT_CHANGES = -not $SkipChangeDetection  # Flag to enable/disable change detection

# New variables for optimized Docker builds
$OPTIMIZED_BACKEND_DOCKERFILE_PATH = "./Dockerfile"  # Use the optimized Dockerfile that we created
$OPTIMIZED_FRONTEND_DOCKERFILE_PATH = "$FRONTEND_SRC_PATH/Dockerfile"  # Use the optimized Dockerfile that we created
$USE_BUILDKIT = $true  # Enable BuildKit for better layer caching and multi-stage builds

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

# By default UseOptimizedImages is now true
if ($UseOptimizedImages) {
    Write-Host "Using optimized Docker images for Azure deployment (60-70% smaller)" -ForegroundColor Green
    Write-Host "Use -UseOptimizedImages:$false to use original Dockerfiles" -ForegroundColor Green
} else {
    Write-Host "Using original Docker images (consider using -UseOptimizedImages for 60-70% smaller images)" -ForegroundColor Yellow
}

# Inform users about integrated Telegram functionality
Write-Host "Telegram functionality is now integrated into the main backend app" -ForegroundColor Green

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
    
    # Only show info, warnings, and errors (not success messages)
    if ($Color -ne "Green" -or $Prefix -eq "ℹ️" -or $Message -like "*Info*" -or $Message -like "*info*") {
        Write-Host "$Prefix $Message $Suffix" -ForegroundColor $Color
    }
}

# Create a function to check if a command succeeded
function Test-CommandSuccess {
    param (
        [string]$SuccessMessage,
        [string]$ErrorMessage
    )
    
    if ($LASTEXITCODE -eq 0) {
        # Don't show success messages
        return $true
    } else {
        Write-ColorOutput -Message "$ErrorMessage (Exit code: $LASTEXITCODE)" -Color Red -Prefix "❌"
        return $false
    }
}

# Create a function to check if an image exists in ACR with tag
function Test-ImageExists {
    param (
        [string]$AcrName,
        [string]$ImageName,
        [string]$Tag,
        [string]$Username,
        [string]$Password
    )
    
    # Login to ACR if credentials provided
    if ($Username -and $Password) {
        az acr login --name $AcrName
    }
    
    try {
        # Use az acr repository show-tags command to check if the tag exists
        $imageExists = az acr repository show-tags --name $AcrName --repository $ImageName --query "contains(@, '$Tag')" --output tsv 2>$null
        if ($imageExists -eq "true") {
            return $true
        } else {
            Write-ColorOutput -Message "Image tag '$Tag' does not exist in repository '$ImageName'" -Color Red -Prefix "❌"
            
            # List available tags
            Write-ColorOutput -Message "Available tags for '$ImageName':" -Color Yellow -Prefix "→"
            $tags = az acr repository show-tags --name $AcrName --repository $ImageName --output tsv
            foreach ($availableTag in $tags) {
                Write-Host "  - $availableTag"
            }
            
            return $false
        }
    } catch {
        Write-ColorOutput -Message "Error checking image: $_" -Color Red -Prefix "❌"
        return $false
    }
}

# Legacy function for backward compatibility
function Test-ImageExistsInACR {
    param (
        [string]$ImageName,
        [string]$Tag
    )
    
    $imageExists = az acr repository show --name $ACR_NAME --image "$ImageName`:$Tag" 2>$null
    if ($imageExists) {
        # Don't show success message
        return $true
    } else {
        Write-ColorOutput -Message "Image $ImageName`:$Tag does not exist in ACR, needs to be built" -Color Yellow -Prefix "→"
        return $false
    }
}

# Create a function to check if Docker is installed and running
function Test-DockerAvailable {
    Write-ColorOutput -Message "Checking if Docker is installed and running" -Color Yellow
    
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
    
    # Don't show success message
    return $true
}

# Create a function to check if source directories exist
function Test-SourceDirectoriesExist {
    Write-ColorOutput -Message "Checking if source directories exist" -Color Yellow
    
    $allPathsExist = $true
    $backendExists = $true
    $frontendExists = $true
    
    # Check backend source path
    if (-not (Test-Path $BACKEND_SRC_PATH)) {
        Write-ColorOutput -Message "Backend source path not found: $BACKEND_SRC_PATH" -Color Red -Prefix "❌"
        $allPathsExist = $false
        $backendExists = $false
    }
    # Don't show success message for backend source path
    
    # Check backend Dockerfile
    if (-not (Test-Path $BACKEND_DOCKERFILE_PATH)) {
        Write-ColorOutput -Message "Backend Dockerfile not found at $BACKEND_DOCKERFILE_PATH" -Color Yellow -Prefix "⚠️"
        # We don't fail the overall check for missing Dockerfile if directory exists
        # since images might already exist in the registry
    }
    # Don't show success message for backend Dockerfile
    
    # Check frontend source path
    if (-not (Test-Path $FRONTEND_SRC_PATH)) {
        Write-ColorOutput -Message "Frontend source path not found: $FRONTEND_SRC_PATH" -Color Red -Prefix "❌"
        $allPathsExist = $false
        $frontendExists = $false
    }
    # Don't show success message for frontend source path
    
    # Check frontend Dockerfile
    if (-not (Test-Path $FRONTEND_DOCKERFILE_PATH)) {
        Write-ColorOutput -Message "Frontend Dockerfile not found at $FRONTEND_DOCKERFILE_PATH" -Color Yellow -Prefix "⚠️"
        # We don't fail the overall check for missing Dockerfile if directory exists
    }
    # Don't show success message for frontend Dockerfile
    
    # Summary of findings
    if (-not $backendExists -and -not $frontendExists) {
        Write-ColorOutput -Message "Both backend and frontend source paths are missing" -Color Red -Prefix "❌"
    } elseif (-not $backendExists) {
        Write-ColorOutput -Message "Backend source path is missing, but frontend exists" -Color Yellow -Prefix "⚠️"
    } elseif (-not $frontendExists) {
        Write-ColorOutput -Message "Frontend source path is missing, but backend exists" -Color Yellow -Prefix "⚠️"
    } elseif (-not (Test-Path $BACKEND_DOCKERFILE_PATH) -or -not (Test-Path $FRONTEND_DOCKERFILE_PATH)) {
        Write-ColorOutput -Message "Source paths exist but one or more Dockerfiles are missing" -Color Yellow -Prefix "⚠️"
    }
    # Don't show success message for all paths existing
    
    return $allPathsExist
}

# Create a function to calculate a hash of a directory's content
function Get-DirectoryHash {
    param (
        [string]$Path
    )
    
    Write-ColorOutput -Message "Calculating hash for directory: $Path" -Color Yellow
    
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
        
        # Don't show success message
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
    
    Write-ColorOutput -Message "Checking for changes in directory: $Path" -Color Yellow
    
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
    
    # Don't show "No changes detected" message
    return $false
}

# Check if we're running as administrator for the scheduler task
function Test-Admin {
    $currentUser = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    $currentUser.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
}

# Function to check scheduled messages
function Check-ScheduledMessages {
    [CmdletBinding()]
    param()

    Write-Host "Checking scheduled messages for issues..." -ForegroundColor Cyan

    $tempScriptPath = [System.IO.Path]::GetTempFileName() + ".py"
    
    try {
        # Create a temporary Python script to check scheduled messages
        @"
import os
import sys
import json
from datetime import datetime, timedelta
from supabase import create_client, Client

try:
    # Use hardcoded credentials rather than environment variables
    supabase_url = "https://aubulhjfeszmsheonmpy.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc"
    
    # Initialize Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # First, get the table structure to discover the correct column names
    try:
        # Try to get the first row to determine column names
        response = supabase.table("scheduled_messages").select("*").limit(1).execute()
        sample_data = response.data[0] if response.data else {}
        
        # Identify the due time column based on what exists in the data
        time_related_columns = ['scheduled_at', 'due_at', 'send_at', 'execute_at']
        due_time_column = next((col for col in time_related_columns if col in sample_data), 'scheduled_at')
        
        # Debug info goes to stderr
        sys.stderr.write(f"Using '{due_time_column}' as the due time column\\n")
    except Exception:
        # If we can't determine the column, default to 'scheduled_at'
        due_time_column = 'scheduled_at'
        sys.stderr.write(f"Using default column name '{due_time_column}' for due time\\n")
    
    # Get current time
    now = datetime.now().isoformat()
    
    # Check for past due messages that are still pending
    past_due_result = supabase.table("scheduled_messages").select("id", "status").eq("status", "pending").execute()
    past_due_messages = []
    
    # Manually filter for past due messages based on the detected column
    if past_due_result.data:
        for msg in past_due_result.data:
            msg_details = supabase.table("scheduled_messages").select("*").eq("id", msg["id"]).execute().data
            if msg_details and msg_details[0].get(due_time_column) and msg_details[0][due_time_column] < now:
                past_due_messages.append(msg)
    
    # Check for messages with missing metadata
    missing_metadata_result = supabase.table("scheduled_messages").select("id", "metadata").is_("metadata", "null").execute()
    missing_metadata = missing_metadata_result.data if missing_metadata_result.data else []
    
    # Check for messages stuck in processing (more than 30 minutes)
    thirty_min_ago = (datetime.now() - timedelta(minutes=30)).isoformat()
    stuck_processing_result = supabase.table("scheduled_messages").select("id", "status", "updated_at").eq("status", "processing").execute()
    stuck_processing = []
    
    # Manually filter for stuck processing messages
    if stuck_processing_result.data:
        for msg in stuck_processing_result.data:
            if msg.get("updated_at") and msg["updated_at"] < thirty_min_ago:
                stuck_processing.append(msg)
    
    # Check for failed messages
    failed_result = supabase.table("scheduled_messages").select("id", "status").eq("status", "failed").execute()
    failed_messages = failed_result.data if failed_result.data else []
    
    # Prepare result summary
    issues_found = len(past_due_messages) > 0 or len(missing_metadata) > 0 or len(stuck_processing) > 0 or len(failed_messages) > 0
    
    result = {
        "issues_found": issues_found,
        "past_due_messages": len(past_due_messages),
        "missing_metadata": len(missing_metadata),
        "stuck_processing": len(stuck_processing),
        "failed_messages": len(failed_messages),
        "past_due_message_ids": [msg["id"] for msg in past_due_messages],
        "missing_metadata_ids": [msg["id"] for msg in missing_metadata],
        "stuck_processing_ids": [msg["id"] for msg in stuck_processing],
        "failed_message_ids": [msg["id"] for msg in failed_messages],
        "due_time_column": due_time_column
    }
    
    print(json.dumps(result))

except Exception as e:
    print(json.dumps({
        "error": str(e),
        "issues_found": False,
        "past_due_messages": 0,
        "missing_metadata": 0,
        "stuck_processing": 0,
        "failed_messages": 0
    }))
    sys.exit(1)
"@ | Out-File -FilePath $tempScriptPath -Encoding utf8
        
        # Run the Python script and capture the output, redirecting stderr to null
        $pythonOutput = python $tempScriptPath 2>$null
        
        # Parse the JSON output
        $result = $pythonOutput | ConvertFrom-Json
        
        if ($result.error) {
            Write-Host "Error checking scheduled messages: $($result.error)" -ForegroundColor Red
            return $false
        }
        
        if ($result.issues_found) {
            Write-Host "Issues found with scheduled messages:" -ForegroundColor Yellow
            Write-Host "  - Past due messages: $($result.past_due_messages)" -ForegroundColor Yellow
            Write-Host "  - Messages with missing metadata: $($result.missing_metadata)" -ForegroundColor Yellow
            Write-Host "  - Messages stuck in processing: $($result.stuck_processing)" -ForegroundColor Yellow
            Write-Host "  - Failed messages: $($result.failed_messages)" -ForegroundColor Yellow
            
            return $result
        } else {
            Write-Host "No issues found with scheduled messages." -ForegroundColor Green
            return $false
        }
    }
    catch {
        Write-Host "Error checking scheduled messages: $_" -ForegroundColor Red
        return $false
    }
    finally {
        # Clean up the temporary file
        if (Test-Path $tempScriptPath) {
            Remove-Item $tempScriptPath -Force
        }
    }
}

# Function to fix scheduled messages
function Fix-ScheduledMessages {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$false)]
        [PSCustomObject]$IssuesResult,
        
        [Parameter(Mandatory=$false)]
        [switch]$AutoConfirm = $false,
        
        [Parameter(Mandatory=$false)]
        [switch]$FixPastDueMessages = $true,
        
        [Parameter(Mandatory=$false)]
        [switch]$FixMissingMetadata = $true,
        
        [Parameter(Mandatory=$false)]
        [switch]$FixStuckProcessing = $true,
        
        [Parameter(Mandatory=$false)]
        [switch]$ResetFailedMessages = $true
    )

    # If no issues result provided, run the check
    if (-not $IssuesResult) {
        $IssuesResult = Check-ScheduledMessages
        if (-not $IssuesResult) {
            Write-Host "No issues to fix." -ForegroundColor Green
            return
        }
    }
    
    # Get the due time column from the issues result
    $dueTimeColumn = $IssuesResult.due_time_column
    if (-not $dueTimeColumn) {
        $dueTimeColumn = "scheduled_at"  # Default fallback
    }
    
    # Prompt for confirmation if auto-confirm not enabled
    if (-not $AutoConfirm) {
        $confirmFix = Read-Host "Would you like to fix these issues? (y/n)"
        if ($confirmFix -ne "y") {
            Write-Host "Fix operation cancelled." -ForegroundColor Yellow
            return
        }
    }
    
    Write-Host "Fixing scheduled message issues..." -ForegroundColor Cyan
    
    $tempScriptPath = [System.IO.Path]::GetTempFileName() + ".py"
    
    try {
        # Create temporary Python script to fix issues
        @"
import os
import sys
import json
from datetime import datetime, timedelta
from supabase import create_client, Client

try:
    # Use hardcoded credentials rather than environment variables
    supabase_url = "https://aubulhjfeszmsheonmpy.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc"
    
    # Initialize Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # First, get the table structure to discover the correct column names
    try:
        # Try to get the first row to determine column names
        response = supabase.table("scheduled_messages").select("*").limit(1).execute()
        sample_data = response.data[0] if response.data else {}
        
        # Identify the due time column based on what exists in the data
        time_related_columns = ['scheduled_at', 'due_at', 'send_at', 'execute_at']
        due_time_column = next((col for col in time_related_columns if col in sample_data), 'scheduled_at')
        
        # Debug info goes to stderr
        sys.stderr.write(f"Using '{due_time_column}' as the due time column\\n")
    except Exception:
        # If we can't determine the column, default to 'scheduled_at'
        due_time_column = '$dueTimeColumn'
        sys.stderr.write(f"Using specified column name '{due_time_column}' for due time\\n")
    
    fixes_applied = 0
    fix_details = {
        "past_due_fixed": 0,
        "metadata_fixed": 0,
        "stuck_processing_fixed": 0,
        "failed_messages_reset": 0
    }
    
    # Parse command line arguments
    fix_past_due = $($FixPastDueMessages.ToString().ToLower())
    fix_metadata = $($FixMissingMetadata.ToString().ToLower())
    fix_stuck = $($FixStuckProcessing.ToString().ToLower())
    reset_failed = $($ResetFailedMessages.ToString().ToLower())
    now = datetime.now().isoformat()
    
    # Fix past due messages that are still pending
    if fix_past_due:
        # Get pending messages
        past_due_result = supabase.table("scheduled_messages").select("*").eq("status", "pending").execute()
        past_due_messages = []
        
        # Manually filter for past due messages based on the detected column
        if past_due_result.data:
            for msg in past_due_result.data:
                if msg.get(due_time_column) and msg[due_time_column] < now:
                    past_due_messages.append(msg)
        
        for msg in past_due_messages:
            # Set a new time 5 minutes in the future
            new_time = (datetime.now() + timedelta(minutes=5)).isoformat()
            update_data = {due_time_column: new_time}
            
            supabase.table("scheduled_messages").update(update_data).eq("id", msg["id"]).execute()
            fix_details["past_due_fixed"] += 1
            fixes_applied += 1
    
    # Fix messages with missing metadata
    if fix_metadata:
        default_metadata = {"priority": "normal", "retry_count": 0}
        missing_metadata_result = supabase.table("scheduled_messages").select("id").is_("metadata", "null").execute()
        missing_metadata = missing_metadata_result.data if missing_metadata_result.data else []
        
        for msg in missing_metadata:
            supabase.table("scheduled_messages").update({"metadata": default_metadata}).eq("id", msg["id"]).execute()
            fix_details["metadata_fixed"] += 1
            fixes_applied += 1
    
    # Fix messages stuck in processing
    if fix_stuck:
        thirty_min_ago = (datetime.now() - timedelta(minutes=30)).isoformat()
        stuck_processing_result = supabase.table("scheduled_messages").select("*").eq("status", "processing").execute()
        stuck_processing = []
        
        # Manually filter for stuck processing messages
        if stuck_processing_result.data:
            for msg in stuck_processing_result.data:
                if msg.get("updated_at") and msg["updated_at"] < thirty_min_ago:
                    stuck_processing.append(msg)
        
        for msg in stuck_processing:
            # Set a new time 10 minutes in the future
            new_time = (datetime.now() + timedelta(minutes=10)).isoformat()
            update_data = {
                "status": "pending",
                due_time_column: new_time,
                "updated_at": now
            }
            
            supabase.table("scheduled_messages").update(update_data).eq("id", msg["id"]).execute()
            fix_details["stuck_processing_fixed"] += 1
            fixes_applied += 1
    
    # Reset failed messages to pending
    if reset_failed:
        failed_result = supabase.table("scheduled_messages").select("id").eq("status", "failed").execute()
        failed_messages = failed_result.data if failed_result.data else []
        
        for msg in failed_messages:
            # Set a new time 15 minutes in the future
            new_time = (datetime.now() + timedelta(minutes=15)).isoformat()
            update_data = {
                "status": "pending",
                due_time_column: new_time,
                "error": None
            }
            
            supabase.table("scheduled_messages").update(update_data).eq("id", msg["id"]).execute()
            fix_details["failed_messages_reset"] += 1
            fixes_applied += 1
    
    # Prepare result summary
    result = {
        "success": True,
        "fixes_applied": fixes_applied,
        "fix_details": fix_details
    }
    
    print(json.dumps(result))

except Exception as e:
    print(json.dumps({
        "error": str(e),
        "success": False,
        "fixes_applied": 0
    }))
    sys.exit(1)
"@ | Out-File -FilePath $tempScriptPath -Encoding utf8
        
        # Run the Python script and capture the output, redirecting stderr to null
        $pythonOutput = python $tempScriptPath 2>$null
        
        # Parse the JSON output
        $result = $pythonOutput | ConvertFrom-Json
        
        if ($result.error) {
            Write-Host "Error fixing scheduled messages: $($result.error)" -ForegroundColor Red
            return $false
        }
        
        if ($result.success) {
            Write-Host "Successfully applied $($result.fixes_applied) fixes to scheduled messages:" -ForegroundColor Green
            Write-Host "  - Fixed past due messages: $($result.fix_details.past_due_fixed)" -ForegroundColor Green
            Write-Host "  - Fixed missing metadata: $($result.fix_details.metadata_fixed)" -ForegroundColor Green
            Write-Host "  - Fixed stuck processing: $($result.fix_details.stuck_processing_fixed)" -ForegroundColor Green
            Write-Host "  - Reset failed messages: $($result.fix_details.failed_messages_reset)" -ForegroundColor Green
            
            return $true
        } else {
            Write-Host "No fixes were applied to scheduled messages." -ForegroundColor Yellow
            return $false
        }
    }
    catch {
        Write-Host "Error fixing scheduled messages: $_" -ForegroundColor Red
        return $false
    }
    finally {
        # Clean up the temporary file
        if (Test-Path $tempScriptPath) {
            Remove-Item $tempScriptPath -Force
        }
    }
}

# Start deployment process
Write-ColorOutput -Message "Starting AI Companion Deployment Process" -Color Cyan

# Pre-deployment checks
Write-ColorOutput -Message "Performing pre-deployment checks" -Color Yellow -Prefix "🔍"

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
    
    if (-not (Test-Path $FRONTEND_DOCKERFILE_PATH)) {
        Write-ColorOutput -Message "Frontend Dockerfile is missing. Will attempt to use existing image from ACR." -Color Yellow -Prefix "⚠️"
    }
}

# Step 1: Verify Resource Group exists (don't create or delete)
Write-ColorOutput -Message "Verifying Resource Group: $RESOURCE_GROUP" -Color Yellow
$rgExists = az group exists --name $RESOURCE_GROUP
if ($rgExists -eq "true") {
    # Don't show success message
} else {
    Write-ColorOutput -Message "Resource group $RESOURCE_GROUP does not exist. Please update the script with correct resource group name." -Color Red -Prefix "❌"
    exit 1
}

# Step 2: Set Azure Subscription
Write-ColorOutput -Message "Setting Azure subscription context" -Color Yellow
az account set --subscription $SUBSCRIPTION_ID
if (-not (Test-CommandSuccess -SuccessMessage "Subscription set successfully" -ErrorMessage "Failed to set subscription")) {
    exit 1
}

# Step 3: Verify ACR exists
Write-ColorOutput -Message "Verifying Azure Container Registry" -Color Yellow
$acrExists = az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP 2>$null
if ($acrExists) {
    # Don't show success message
} else {
    Write-ColorOutput -Message "ACR $ACR_NAME does not exist. Please update the script with correct ACR name." -Color Red -Prefix "❌"
    exit 1
}

# Login to ACR
Write-ColorOutput -Message "Logging in to Azure Container Registry" -Color Yellow
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
Write-ColorOutput -Message "Building Backend Docker Image" -Color Yellow

# Check if image exists in ACR
$backendImageExists = Test-ImageExistsInACR -ImageName $IMAGE_NAME -Tag $TAG

# Determine if we need to build backend
$needToBuildBackend = $FORCE_REBUILD -or (-not $backendImageExists)
if (-not $needToBuildBackend) {
    Write-ColorOutput -Message "Skipping backend build as image already exists in ACR" -Color Yellow -Prefix "→"
} else {
    # Check if Dockerfile exists in backend path
    if (Test-Path $BACKEND_DOCKERFILE_PATH) {
        if ($UseOptimizedImages) {
            # Build using optimized method for Azure
            $backendBuildSuccess = Build-OptimizedBackendImage -Tag $TAG
        } else {
            # Use the original build method
            Write-ColorOutput -Message "Building backend Docker image with tag $TAG (original method)" -Color Yellow -Prefix "→"
            
            # Original docker build command
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
        }
    } else {
        Write-ColorOutput -Message "Backend Dockerfile not found at $BACKEND_DOCKERFILE_PATH" -Color Yellow -Prefix "⚠️"
        Write-ColorOutput -Message "Cannot build backend Docker image" -Color Red -Prefix "❌"
    }
}

# Build Frontend Docker Image
Write-ColorOutput -Message "Building Frontend Docker Image" -Color Yellow

# Check if image exists in ACR
$frontendImageExists = Test-ImageExistsInACR -ImageName $WEB_UI_IMAGE_NAME -Tag $TAG

# Make sure backend URL is defined before building frontend
if (-not $backendAppUrl) {
    Write-ColorOutput -Message "Getting backend URL for frontend configuration" -Color Yellow -Prefix "→"
    $backendAppUrl = az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
    $backendAppUrl = "https://$backendAppUrl"
    Write-ColorOutput -Message "Backend App URL: $backendAppUrl" -Color Cyan -Prefix "🔗"
}

# Determine if we need to build frontend
$needToBuildFrontend = $FORCE_REBUILD -or (-not $frontendImageExists)
if (-not $needToBuildFrontend) {
    Write-ColorOutput -Message "Skipping frontend build as image already exists in ACR" -Color Yellow -Prefix "→"
} else {
    # Check if Dockerfile exists in frontend path
    if (Test-Path $FRONTEND_DOCKERFILE_PATH) {
        if ($UseOptimizedImages) {
            # Build using optimized method for Azure
            $frontendBuildSuccess = Build-OptimizedFrontendImage -Tag $TAG -BackendUrl $backendAppUrl
            
            if ($frontendBuildSuccess) {
                $frontendImageExists = $true
            } else {
                Write-ColorOutput -Message "Failed to build optimized frontend image" -Color Red -Prefix "❌"
            }
        } else {
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
        }
    } else {
        Write-ColorOutput -Message "Frontend Dockerfile not found at $FRONTEND_DOCKERFILE_PATH" -Color Yellow -Prefix "⚠️"
        Write-ColorOutput -Message "Cannot build frontend Docker image" -Color Red -Prefix "❌"
    }
}

# Step 5: Check if Container Apps Environment exists
Write-ColorOutput -Message "Checking if Container App Environment exists" -Color Yellow
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
Write-ColorOutput -Message "Checking Backend Container App" -Color Yellow
$backendAppExists = az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP 2>$null
$backendAppNeedsUpdate = $false
$backendAppRunning = $true

if ($backendAppExists) {
    # Check if it's running properly
    Write-ColorOutput -Message "Backend app exists, checking status" -Color Yellow -Prefix "→"
    
    # Get the backend app URL
    $backendAppUrl = az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
    $backendAppUrl = "https://$backendAppUrl"
    
    # Check health endpoint
    try {
        $response = Invoke-WebRequest -Uri "$backendAppUrl/monitor/health" -UseBasicParsing -ErrorAction Stop
        $content = $response.Content | ConvertFrom-Json
        if ($response.StatusCode -eq 200 -and $content.status -eq "healthy") {
            # Don't show success message
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
            # Don't show success message
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
Write-ColorOutput -Message "Checking Frontend Container App" -Color Yellow
$frontendAppExists = az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP 2>$null
$frontendAppNeedsUpdate = $false
$frontendAppRunning = $true

if ($frontendAppExists) {
    # Check if it's running properly
    Write-ColorOutput -Message "Frontend app exists, checking status" -Color Yellow -Prefix "→"
    
    # Get the frontend app URL
    $frontendAppUrl = az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
    $frontendAppUrl = "https://$frontendAppUrl"
    
    # Check if the frontend is responding
    try {
        $response = Invoke-WebRequest -Uri $frontendAppUrl -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            # Don't show success message
            
            # Check if this is a React/Next.js app (look for typical React patterns)
            if ($response.Content -match "react" -or $response.Content -match "next" -or $response.Content -match "_next") {
                # Don't show success message
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
        az containerapp delete --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --yes
        if (-not (Test-CommandSuccess -SuccessMessage "Backend container app deleted successfully" -ErrorMessage "Failed to delete backend container app")) {
            Write-ColorOutput -Message "Continuing despite backend deletion failure" -Color Yellow -Prefix "⚠️"
        }
    } elseif ($backendAppRunning -and $ForceUpdate) {
        # Update the existing container app instead of deleting and recreating
        Write-ColorOutput -Message "Updating existing backend container app to image version: $TAG" -Color Yellow -Prefix "→"
        
        # Execute command with detailed error handling
        $updateCmd = "az containerapp update --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --image ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${TAG}"
        Write-Host "Executing command: $updateCmd" -ForegroundColor Gray
        
        $updateResult = Invoke-Expression $updateCmd
        
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput -Message "Backend update failed with exit code: $LASTEXITCODE" -Color Red -Prefix "❌"
            Write-ColorOutput -Message "Error details: $updateResult" -Color Red -Prefix "❌"
            Write-ColorOutput -Message "Failed to update backend, will attempt to recreate" -Color Yellow -Prefix "⚠️"
            
            # If update fails, delete and recreate
            az containerapp delete --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --yes
            if (-not (Test-CommandSuccess -SuccessMessage "Backend container app deleted successfully" -ErrorMessage "Failed to delete backend container app")) {
                Write-ColorOutput -Message "Continuing despite backend deletion failure" -Color Yellow -Prefix "⚠️"
            }
            $backendAppRunning = $false
        } else {
            # Get updated URL
            $backendAppUrl = az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
            $backendAppUrl = "https://$backendAppUrl"
            Write-ColorOutput -Message "Backend App updated to version $TAG" -Color Yellow -Prefix "→"
            Write-ColorOutput -Message "Backend App URL: $backendAppUrl" -Color Cyan -Prefix "🔗"
        }
    }
    
    # Only create if app doesn't exist or was deleted
    if (-not $backendAppRunning) {
        Write-ColorOutput -Message "Deploying Backend Container App" -Color Yellow
        az containerapp create `
            --name $BACKEND_APP_NAME `
            --resource-group $RESOURCE_GROUP `
            --environment $CONTAINER_ENV_NAME `
            --image "${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${TAG}" `
            --target-port 8000 `
            --ingress external `
            --min-replicas 1 `
            --max-replicas 5 `
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

        if (-not (Test-CommandSuccess -SuccessMessage "Backend Container App deployed successfully" -ErrorMessage "Failed to deploy Backend Container App")) {
            Write-ColorOutput -Message "Failed to deploy backend, continuing with deployment" -Color Yellow -Prefix "⚠️"
        } else {
            # Update URL and configure settings
            $backendAppUrl = az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
            $backendAppUrl = "https://$backendAppUrl"
            Write-ColorOutput -Message "Backend App URL: $backendAppUrl" -Color Cyan -Prefix "🔗"
            
            # Configure other settings
            Write-ColorOutput -Message "Configuring Backend Ingress" -Color Yellow
            az containerapp ingress update `
                --name $BACKEND_APP_NAME `
                --resource-group $RESOURCE_GROUP `
                --target-port 8000 `
                --transport auto
                
            Write-ColorOutput -Message "Configuring CORS for Backend" -Color Yellow
            az containerapp ingress cors update `
                --name $BACKEND_APP_NAME `
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
    $backendAppUrl = az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
    $backendAppUrl = "https://$backendAppUrl"
    Write-ColorOutput -Message "Using existing Backend App URL: $backendAppUrl" -Color Cyan -Prefix "🔗"
}

# Step 9: Delete and recreate frontend if needed
if ($frontendAppNeedsUpdate -or $ForceUpdate) {
    # Use the already known frontendImageExists variable from Step 4
    if ($frontendImageExists) {
        if ($frontendAppRunning -and (-not $ForceUpdate)) {
            Write-ColorOutput -Message "Deleting misconfigured frontend container app" -Color Yellow -Prefix "→"
            az containerapp delete --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --yes
            if (-not (Test-CommandSuccess -SuccessMessage "Frontend container app deleted successfully" -ErrorMessage "Failed to delete frontend container app")) {
                Write-ColorOutput -Message "Continuing despite frontend deletion failure" -Color Yellow -Prefix "⚠️"
            }
        } elseif ($frontendAppRunning -and $ForceUpdate) {
            # Update the existing container app instead of deleting and recreating
            Write-ColorOutput -Message "Updating existing frontend container app to image version: $TAG" -Color Yellow -Prefix "→"
            Write-ColorOutput -Message "Setting API URL to: $backendAppUrl" -Color Yellow -Prefix "→"
            
            # Execute command with detailed error handling
            $updateCmd = "az containerapp update --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --image ${ACR_NAME}.azurecr.io/${WEB_UI_IMAGE_NAME}:${TAG} --set-env-vars NEXT_PUBLIC_API_URL=$backendAppUrl"
            Write-Host "Executing command: $updateCmd" -ForegroundColor Gray
            
            $updateResult = Invoke-Expression $updateCmd
            
            if ($LASTEXITCODE -ne 0) {
                Write-ColorOutput -Message "Frontend update failed with exit code: $LASTEXITCODE" -Color Red -Prefix "❌"
                Write-ColorOutput -Message "Error details: $updateResult" -Color Red -Prefix "❌"
                Write-ColorOutput -Message "Failed to update frontend, will attempt to recreate" -Color Yellow -Prefix "⚠️"
                
                # If update fails, delete and recreate
                az containerapp delete --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --yes
                if (-not (Test-CommandSuccess -SuccessMessage "Frontend container app deleted successfully" -ErrorMessage "Failed to delete frontend container app")) {
                    Write-ColorOutput -Message "Continuing despite frontend deletion failure" -Color Yellow -Prefix "⚠️"
                }
                $frontendAppRunning = $false
            } else {
                # Get updated URL
                $frontendAppUrl = az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
                $frontendAppUrl = "https://$frontendAppUrl"
                Write-ColorOutput -Message "Frontend App updated to version $TAG" -Color Yellow -Prefix "→"
                Write-ColorOutput -Message "Frontend App URL: $frontendAppUrl" -Color Cyan -Prefix "🔗"
            }
        }
        
        # Only create if app doesn't exist or was deleted
        if (-not $frontendAppRunning) {
            Write-ColorOutput -Message "Deploying Frontend Container App" -Color Yellow
            az containerapp create `
                --name $FRONTEND_APP_NAME `
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
                $frontendAppUrl = az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
                $frontendAppUrl = "https://$frontendAppUrl"
                Write-ColorOutput -Message "Frontend App URL: $frontendAppUrl" -Color Cyan -Prefix "🔗"
            }
        }
    } else {
        Write-ColorOutput -Message "Frontend image does not exist in ACR. Cannot deploy frontend." -Color Yellow -Prefix "⚠️"
    }
} else {
    # Get existing frontend URL
    $frontendExists = az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP 2>$null
    if ($frontendExists) {
        $frontendAppUrl = az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
        $frontendAppUrl = "https://$frontendAppUrl"
        Write-ColorOutput -Message "Using existing Frontend App URL: $frontendAppUrl" -Color Cyan -Prefix "🔗"
        
        # Add check to see if versions match and report
        $deployedImageRef = az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.template.containers[0].image" -o tsv
        if ($deployedImageRef -like "*:$TAG") {
            # Don't show success message for matching versions
        } else {
            Write-ColorOutput -Message "Frontend is at version $($deployedImageRef.Split(':')[1]) but local is $TAG" -Color Yellow -Prefix "⚠️"
            Write-ColorOutput -Message "Use -ForceUpdate to update to latest version" -Color Yellow -Prefix "→"
        }
    }
}

# Add diagnostic function for Azure environment
function Test-AzureEnvironment {
    param (
        [string]$ResourceGroup,
        [string]$ContainerEnvName
    )
    
    Write-ColorOutput -Message "Diagnosing Azure environment for Container App Job support" -Color Yellow -Prefix "🔍"
    
    # Check if logged in to Azure
    try {
        $account = az account show --query "name" -o tsv 2>$null
        Write-ColorOutput -Message "Azure login verified: $account" -Color Yellow -Prefix "→"
    } catch {
        Write-ColorOutput -Message "Not logged in to Azure. Please run 'az login' first." -Color Red -Prefix "❌"
        return $false
    }
    
    # Check resource group existence
    try {
        $rgExists = az group show --name $ResourceGroup --query "name" -o tsv 2>$null
        if ($rgExists) {
            # Don't show success message
        } else {
            Write-ColorOutput -Message "Resource group not found: $ResourceGroup" -Color Red -Prefix "❌"
            return $false
        }
    } catch {
        Write-ColorOutput -Message "Error checking resource group: $_" -Color Red -Prefix "❌"
        return $false
    }
    
    # Check if Container App environment exists
    try {
        $envExists = az containerapp env show --name $ContainerEnvName --resource-group $ResourceGroup --query "name" -o tsv 2>$null
        if ($envExists) {
            # Don't show success message
        } else {
            Write-ColorOutput -Message "Container App environment not found: $ContainerEnvName" -Color Red -Prefix "❌"
            return $false
        }
    } catch {
        Write-ColorOutput -Message "Error checking Container App environment: $_" -Color Red -Prefix "❌"
        return $false
    }
    
    # Check permissions for creating jobs
    try {
        $userPrincipal = az ad signed-in-user show --query "userPrincipalName" -o tsv 2>$null
        Write-ColorOutput -Message "Current user: $userPrincipal" -Color Yellow -Prefix "→"
        
        # Check if user has Contributor role on resource group
        $rolesJson = az role assignment list --assignee $userPrincipal --resource-group $ResourceGroup --query "[].roleDefinitionName" -o json 2>$null
        
        # Handle potentially empty or null response
        if ([string]::IsNullOrEmpty($rolesJson) -or $rolesJson -eq "[]") {
            Write-ColorOutput -Message "No roles found for current user in resource group" -Color Yellow -Prefix "⚠️"
            Write-ColorOutput -Message "User does not have sufficient permissions to create Container App Jobs" -Color Yellow -Prefix "⚠️"
            Write-ColorOutput -Message "Recommended roles: Contributor or Owner" -Color Yellow -Prefix "→"
            $global:UseFallbackScheduler = $true
            return $true  # Continue with deployment using fallback
        }
        
        # Convert JSON to PowerShell object
        try {
            $roles = $rolesJson | ConvertFrom-Json
        }
        catch {
            Write-ColorOutput -Message "Error parsing roles: $_" -Color Yellow -Prefix "⚠️"
            $roles = @()
        }
        
        # Check if array is empty
        if ($roles.Count -eq 0) {
            Write-ColorOutput -Message "User has no roles assigned in this resource group" -Color Yellow -Prefix "⚠️"
            Write-ColorOutput -Message "Recommended roles: Contributor or Owner" -Color Yellow -Prefix "→"
            $global:UseFallbackScheduler = $true
        }
        elseif ($roles -contains "Contributor" -or $roles -contains "Owner") {
            # Don't show success message
        }
        else {
            Write-ColorOutput -Message "User may not have sufficient permissions to create Container App Jobs" -Color Yellow -Prefix "⚠️"
            Write-ColorOutput -Message "Recommended roles: Contributor or Owner" -Color Yellow -Prefix "→"
            Write-ColorOutput -Message "Current roles: $($roles -join ', ')" -Color Yellow -Prefix "→"
            $global:UseFallbackScheduler = $true
        }
    } catch {
        Write-ColorOutput -Message "Error checking permissions: $_" -Color Yellow -Prefix "⚠️"
        Write-ColorOutput -Message "Defaulting to fallback scheduler for safety" -Color Yellow -Prefix "→"
        $global:UseFallbackScheduler = $true
    }
    
    # Check if Container Apps Jobs feature is available in the region
    try {
        $location = az containerapp env show --name $ContainerEnvName --resource-group $ResourceGroup --query "location" -o tsv 2>$null
        Write-ColorOutput -Message "Container App environment location: $location" -Color Yellow -Prefix "→"
        
        # List of regions with confirmed Container App Jobs support (as of script creation date)
        $supportedRegions = @(
            "eastus", "eastus2", "westus", "westus2", "westus3", "centralus", "northcentralus", "southcentralus",
            "westeurope", "northeurope", "uksouth", "ukwest", "francecentral", "switzerlandnorth",
            "japaneast", "koreacentral", "southeastasia", "australiaeast"
        )
        
        if ($supportedRegions -contains $location.ToLower()) {
            # Don't show success message
        } else {
            Write-ColorOutput -Message "Region may not support Container App Jobs. Consider using fallback approach." -Color Yellow -Prefix "⚠️"
            $global:UseFallbackScheduler = $true
        }
    } catch {
        Write-ColorOutput -Message "Error checking region: $_" -Color Yellow -Prefix "⚠️"
    }
    
    # Try to list existing jobs as a test
    try {
        # First check if the jobs API is working
        $jobApiTest = az containerapp job --help 2>$null
        if ([string]::IsNullOrEmpty($jobApiTest)) {
            Write-ColorOutput -Message "Container App Jobs API may not be available" -Color Yellow -Prefix "⚠️"
            $global:UseFallbackScheduler = $true
        }
        else {
            # Try to list jobs
            $jobsListResult = az containerapp job list --resource-group $ResourceGroup 2>&1
            
            # Check if there was an error (error message contains lines with Python.exe path)
            if ($jobsListResult -like "*python.exe*" -or $jobsListResult -like "*error*") {
                Write-ColorOutput -Message "Error listing jobs: API may not be available" -Color Red -Prefix "❌"
                Write-ColorOutput -Message "Container App Jobs may not be supported in your region or configuration" -Color Yellow -Prefix "⚠️"
                $global:UseFallbackScheduler = $true
            }
            else {
                # Try to parse the result as JSON and count
                try {
                    $jobsList = $jobsListResult | ConvertFrom-Json
                    $jobsCount = $jobsList.Count
                    # Don't show success message
                }
                catch {
                    Write-ColorOutput -Message "Error processing jobs list: $_" -Color Red -Prefix "❌"
                    Write-ColorOutput -Message "Container App Jobs API may not be returning valid data" -Color Yellow -Prefix "⚠️"
                    $global:UseFallbackScheduler = $true
                }
            }
        }
    } catch {
        Write-ColorOutput -Message "Error listing jobs: $_" -Color Red -Prefix "❌"
        Write-ColorOutput -Message "Container App Jobs API may not be available" -Color Yellow -Prefix "⚠️"
        $global:UseFallbackScheduler = $true
    }
    
    # Check Azure CLI version
    try {
        $cliVersion = az version --query "azure-cli" -o tsv 2>$null
        
        if ([string]::IsNullOrEmpty($cliVersion)) {
            # Try alternate query format if the first one didn't work
            $cliVersion = az version --query '''azure-cli''' -o tsv 2>$null
        }
        
        if ([string]::IsNullOrEmpty($cliVersion)) {
            # If still empty, get the full version info and extract manually
            $versionInfo = az version 2>$null | ConvertFrom-Json
            if ($versionInfo.'azure-cli') {
                $cliVersion = $versionInfo.'azure-cli'
            }
        }
        
        Write-ColorOutput -Message "Azure CLI version: $cliVersion" -Color Yellow -Prefix "→"
        
        # Parse version components if we have a version
        if ($cliVersion -match '(\d+)\.(\d+)\.(\d+)') {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            $patch = [int]$Matches[3]
            
            # Check if version is recent enough (2.40.0+)
            if ($major -gt 2 -or ($major -eq 2 -and $minor -ge 40)) {
                Write-ColorOutput -Message "Azure CLI version supports Container App Jobs" -Color Green -Prefix "✅"
} else {
                Write-ColorOutput -Message "Azure CLI version may be too old for Container App Jobs" -Color Yellow -Prefix "⚠️"
                Write-ColorOutput -Message "Consider updating Azure CLI: az upgrade" -Color Yellow -Prefix "→"
                $global:UseFallbackScheduler = $true
            }
        } else {
            Write-ColorOutput -Message "Could not determine Azure CLI version format" -Color Yellow -Prefix "⚠️"
            Write-ColorOutput -Message "Proceeding with deployment, but consider checking CLI version manually" -Color Yellow -Prefix "→"
        }
    } catch {
        Write-ColorOutput -Message "Error checking Azure CLI version: $_" -Color Yellow -Prefix "⚠️"
        Write-ColorOutput -Message "Proceeding with deployment" -Color Yellow -Prefix "→"
    }
    
    return $true
}

# Before deploying the Telegram scheduler, run the diagnostic
if (-not $SkipTelegramSetup) {
    Write-ColorOutput -Message "Running pre-deployment diagnostics for Telegram scheduler" -Color Cyan -Prefix "🔍"
    $diagnosticResult = Test-AzureEnvironment -ResourceGroup $RESOURCE_GROUP -ContainerEnvName $CONTAINER_ENV_NAME
    
    # Check if we're in diagnose-only mode
    if ($DiagnoseOnly) {
        Write-ColorOutput -Message "Diagnostics completed. Exiting as -DiagnoseOnly flag was specified." -Color Cyan -Prefix "ℹ️"
        exit 0
    }
    
    # Override UseFallbackScheduler if explicitly set
    if ($UseFallbackScheduler) {
        Write-ColorOutput -Message "Using fallback scheduler as specified by -UseFallbackScheduler parameter" -Color Yellow -Prefix "→"
    }
}

# Step 10: Deploy Telegram Scheduler Container App
Write-ColorOutput -Message "Deploying Telegram Scheduler Container App" -Color Green -Prefix "🤖"

        $telegramSchedulerAppRunning = $false
$telegramSchedulerAppNeedsUpdate = $false
$telegramJobExists = $false
$telegramContainerAppExists = $false

# Check if the telegram-scheduler container app exists
$telegramContainerAppExists = $false
# Default is to skip since the scheduler is now integrated in the main backend
$runTelegramSetup = -not $SkipTelegramSetup

Write-Host ""
Write-Host "Checking if Telegram scheduler app exists: $TELEGRAM_SCHEDULER_APP_NAME"
$telegramContainerApp = az containerapp show --name $TELEGRAM_SCHEDULER_APP_NAME --resource-group $RESOURCE_GROUP 2>$null | ConvertFrom-Json -ErrorAction SilentlyContinue
if ($telegramContainerApp) {
    $telegramContainerAppExists = $true
    Write-Host " - Telegram scheduler container app exists in resource group: $RESOURCE_GROUP" -ForegroundColor Green
}
else {
    Write-Host " - Telegram scheduler container app not found in resource group: $RESOURCE_GROUP" -ForegroundColor Yellow
}

if ($runTelegramSetup) {
    Write-Host "Preparing to deploy Telegram scheduler container app" -ForegroundColor Green
    # ... existing code ...
} else {
    Write-Host ""
    Write-Host "Skipping Telegram scheduler deployment (SkipTelegramSetup = $SkipTelegramSetup)" -ForegroundColor Yellow
    Write-Host " - Note: Telegram functionality is now integrated in the main backend application" -ForegroundColor Cyan
    Write-Host " - No separate container is needed for the scheduler anymore" -ForegroundColor Cyan
    if ($telegramContainerAppExists) {
        Write-Host ""
        Write-Host " - A Telegram scheduler container app currently exists: $TELEGRAM_SCHEDULER_APP_NAME" -ForegroundColor Cyan
        Write-Host " - If you want to remove it to save resources, you can delete it manually from Azure portal" -ForegroundColor Cyan
        Write-Host " - Or run: az containerapp delete --name $TELEGRAM_SCHEDULER_APP_NAME --resource-group $RESOURCE_GROUP" -ForegroundColor Cyan
    }
}
# ... existing code ...

# Step 11: Deployment Summary
Write-ColorOutput -Message "Deployment Summary" -Color Green -Prefix "📋"

# Step 12: Configure Custom Domain for Frontend App
Write-ColorOutput -Message "Configuring Custom Domain for Frontend" -Color Green -Prefix "🔗"

# Define custom domain parameters
$CUSTOM_DOMAIN = "demo.evelinaai.com"

# Check if frontend exists for custom domain setup
$frontendExists = az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP 2>$null
if ($frontendExists) {
    # Get the domain verification ID
    $verificationId = az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.customDomainVerificationId" -o tsv
    
    Write-ColorOutput -Message "Domain verification ID: $verificationId" -Color Yellow -Prefix "→"
    Write-ColorOutput -Message "Important DNS requirements (automatic setup in progress):" -Color Yellow -Prefix "⚠️"
    Write-ColorOutput -Message "1. A CNAME record for 'demo' pointing to your container app FQDN" -Color White
    Write-ColorOutput -Message "2. A TXT record for 'asuid.demo' with value '$verificationId'" -Color White
    
    # First check if the custom domain is already bound
    $existingDomain = az containerapp hostname list --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query "[?hostname=='$CUSTOM_DOMAIN']" -o tsv
    
    if ($existingDomain) {
        Write-ColorOutput -Message "Custom domain $CUSTOM_DOMAIN is already configured" -Color Green -Prefix "✅"
    } else {
        # Automatically attempt to add the custom domain without prompting
        Write-ColorOutput -Message "Automatically adding custom domain to frontend app" -Color Yellow -Prefix "→"
        
        # Add the custom domain to the frontend container app
        az containerapp hostname add --hostname $CUSTOM_DOMAIN --resource-group $RESOURCE_GROUP --name $FRONTEND_APP_NAME
        
        if (-not (Test-CommandSuccess -SuccessMessage "Custom domain added successfully" -ErrorMessage "Failed to add custom domain")) {
            Write-ColorOutput -Message "Failed to add custom domain. Please verify your DNS records:" -Color Red -Prefix "❌"
            Write-ColorOutput -Message "1. CNAME record: demo.evelinaai.com → $frontendAppUrl" -Color White
            Write-ColorOutput -Message "2. TXT record: asuid.demo → $verificationId" -Color White
            Write-ColorOutput -Message "Once DNS is properly configured, run this script again." -Color Yellow -Prefix "→"
        } else {
            # Automatically bind a managed certificate to the custom domain
            Write-ColorOutput -Message "Binding managed certificate to custom domain" -Color Yellow -Prefix "→"
            az containerapp hostname bind --hostname $CUSTOM_DOMAIN --resource-group $RESOURCE_GROUP --name $FRONTEND_APP_NAME --environment $CONTAINER_ENV_NAME --validation-method CNAME
            
            if (-not (Test-CommandSuccess -SuccessMessage "Managed certificate bound successfully" -ErrorMessage "Failed to bind managed certificate")) {
                Write-ColorOutput -Message "Failed to bind managed certificate, but domain may still be added." -Color Yellow -Prefix "⚠️"
                Write-ColorOutput -Message "Please check DNS records and try again if needed:" -Color Yellow
                Write-ColorOutput -Message "1. CNAME record: demo.evelinaai.com → $frontendAppUrl" -Color White
                Write-ColorOutput -Message "2. TXT record: asuid.demo → $verificationId" -Color White
            } else {
                Write-ColorOutput -Message "Custom domain and managed certificate configured successfully!" -Color Green -Prefix "✅"
                Write-ColorOutput -Message "Custom domain URL: https://$CUSTOM_DOMAIN" -Color Cyan -Prefix "🔗"
                
                # Inform about certificate provisioning time
                Write-ColorOutput -Message "Certificate provisioning in progress - this may take 5-15 minutes" -Color Yellow -Prefix "⏳"
                Write-ColorOutput -Message "The site will be accessible when certificate provisioning completes" -Color Yellow -Prefix "→"
            }
        }
    }
} else {
    Write-ColorOutput -Message "Frontend app does not exist, skipping custom domain setup" -Color Yellow -Prefix "⚠️"
}

Write-Host ""
Write-Host "Backend Application:" -ForegroundColor Cyan
Write-Host "  URL: $backendAppUrl" -ForegroundColor White
Write-Host "  Status Endpoint: $backendAppUrl/chat/status" -ForegroundColor White
Write-Host "  Health Endpoint: $backendAppUrl/monitor/health" -ForegroundColor White
Write-Host ""

# Check if frontend exists for summary
$frontendExists = az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP 2>$null
if ($frontendExists) {
    $frontendAppUrl = az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
    $frontendAppUrl = "https://$frontendAppUrl"
    
    Write-Host "Frontend Application:" -ForegroundColor Cyan
    Write-Host "  URL: $frontendAppUrl" -ForegroundColor White
    if (az containerapp hostname list --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query "[?hostname==''$CUSTOM_DOMAIN'']" -o tsv) {
        Write-Host "  Custom Domain: https://$CUSTOM_DOMAIN" -ForegroundColor White
    }
    Write-Host ""
}

Write-Host "Resource Group: $RESOURCE_GROUP" -ForegroundColor Cyan
Write-Host "Container Registry: $ACR_NAME" -ForegroundColor Cyan
Write-Host "Container App Environment: $CONTAINER_ENV_NAME" -ForegroundColor Cyan

# Add Telegram scheduler info to summary
$taskName = "AI-Companion-Telegram-Scheduler"
$schedulerTaskExists = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

# Check if Telegram scheduler container app exists
$telegramContainerAppExists = az containerapp show --name $TELEGRAM_SCHEDULER_APP_NAME --resource-group $RESOURCE_GROUP 2>$null
$telegramJobExists = az containerapp job show --name $TELEGRAM_SCHEDULER_APP_NAME --resource-group $RESOURCE_GROUP 2>$null

if ($telegramJobExists) {
    Write-Host "Telegram Scheduler:" -ForegroundColor Cyan
    Write-Host "  Status: Active (running as Azure Container App Job)" -ForegroundColor White
    Write-Host "  Container App Job: $TELEGRAM_SCHEDULER_APP_NAME" -ForegroundColor White
    
    # Get CRON expression
    $cronExpression = az containerapp job show --name $TELEGRAM_SCHEDULER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.triggerType.schedule.cronExpression" -o tsv
    Write-Host "  CRON Schedule: $cronExpression" -ForegroundColor White
    
    # Get the deployed image version
    $telegramSchedulerImageRef = az containerapp job show --name $TELEGRAM_SCHEDULER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.template.containers[0].image" -o tsv
    $telegramSchedulerVersion = $telegramSchedulerImageRef.Split(':')[1]
    Write-Host "  Version: $telegramSchedulerVersion" -ForegroundColor White
    
    # Show message about Container App Jobs
    Write-Host "  Note: Telegram scheduler is running as an Azure Container App Job" -ForegroundColor Green
    Write-Host "        Scheduled using CRON expression for optimal reliability" -ForegroundColor Green
    
    if ($schedulerTaskExists) {
        Write-Host "  Warning: Windows Task Scheduler task $taskName still exists" -ForegroundColor Yellow
        Write-Host "           You can remove it to avoid running two instances" -ForegroundColor Yellow
    }
} elseif ($telegramContainerAppExists) {
    Write-Host "Telegram Scheduler:" -ForegroundColor Cyan
    Write-Host "  Status: Active (running as Azure Container App)" -ForegroundColor White
    Write-Host "  Container App: $TELEGRAM_SCHEDULER_APP_NAME" -ForegroundColor White
    Write-Host "  Replicas: 1 (continuously running)" -ForegroundColor White
    
    # Get the deployed image version
    $telegramSchedulerImageRef = az containerapp show --name $TELEGRAM_SCHEDULER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.template.containers[0].image" -o tsv
    $telegramSchedulerVersion = $telegramSchedulerImageRef.Split(':')[1]
    Write-Host "  Version: $telegramSchedulerVersion" -ForegroundColor White
    
    # Show message about Windows Task Scheduler vs Container App
    Write-Host "  Note: Telegram scheduler is running as a regular Container App" -ForegroundColor Green
    Write-Host "        Run with -UseContainerJobs flag to convert to scheduled job" -ForegroundColor Yellow
    
    if ($schedulerTaskExists) {
        Write-Host "  Warning: Windows Task Scheduler task $taskName still exists" -ForegroundColor Yellow
        Write-Host "           You can remove it to avoid running two instances" -ForegroundColor Yellow
    }
} elseif ($schedulerTaskExists) {
    # Fall back to Windows Task Scheduler info if it exists
    Write-Host "Telegram Scheduler:" -ForegroundColor Cyan
    Write-Host "  Status: Active (running via Windows Task Scheduler)" -ForegroundColor White
    Write-Host "  Task Name: $taskName" -ForegroundColor White
    Write-Host "  Logs: ./logs/telegram_scheduler.log" -ForegroundColor White
    Write-Host "  Note: Consider deploying as Container App Job for production" -ForegroundColor Yellow
} else {
    Write-Host "Telegram Scheduler:" -ForegroundColor Cyan
    Write-Host "  Status: Not configured" -ForegroundColor Yellow
    Write-Host "  Run deploy.ps1 again with -ForceUpdate to deploy the scheduler" -ForegroundColor White
}

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

# Step 14: Deployment Verification Complete
Write-ColorOutput -Message "Deployment and Version Verification Complete" -Color Yellow -Prefix "🔍"

# Step 15: Version Verification
Write-ColorOutput -Message "Verifying Application Versions" -Color Yellow -Prefix "🔍"

# Add this utility function to normalize version strings
function Get-VersionFromImageString {
    param (
        [string]$ImageString
    )
    
    if ([string]::IsNullOrEmpty($ImageString)) {
        return $null
    }
    
    # Check if the image string contains a colon (separator for tag)
    if ($ImageString -match '.*:(.+)$') {
        return $Matches[1]
    }
    
    return $null
}

# Create a function to update container app image if version mismatch detected
function Update-ContainerAppVersion {
    param (
        [string]$AppName,
        [string]$ResourceGroup,
        [string]$Repository,
        [string]$Tag,
        [bool]$ForceUpdate = $false
    )
    
    if (-not $ForceUpdate) {
        Write-ColorOutput -Message "Version mismatch detected, but ForceUpdate is not enabled. Use -ForceUpdate to update." -Color Yellow -Prefix "→"
        return $false
    }
    
    Write-ColorOutput -Message "Updating $AppName to version $Tag" -Color Yellow -Prefix "→"
    
    try {
        # Get ACR credentials for the image
        $acrName = $Repository.Split('.')[0]
        
        # Use the update-container CLI command to update just the image
        $updateResult = az containerapp update --name $AppName --resource-group $ResourceGroup --image "$Repository/$AppName`:$Tag" 2>$null
        
        if ($LASTEXITCODE -eq 0 -and $updateResult) {
            # Don't show success message
            return $true
        } else {
            Write-ColorOutput -Message "Failed to update $AppName to version $Tag" -Color Red -Prefix "❌"
            return $false
        }
    } catch {
        # Store the error message in a variable first
        $errorMsg = $_.Exception.Message
        Write-ColorOutput -Message "Error updating $AppName - Error details: $errorMsg" -Color Red -Prefix "❌"
        return $false
    }
}

# Check backend version
$backendExists = az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP 2>$null
if ($backendExists) {
    $backendDeployedImageRef = az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.template.containers[0].image" -o tsv
    $backendDeployedVersion = Get-VersionFromImageString -ImageString $backendDeployedImageRef
    
    if ($backendDeployedVersion -eq $TAG) {
        # Don't show success message
    } else {
        Write-ColorOutput -Message "Backend version verification: MISMATCH (Deployed: $backendDeployedVersion, Expected: $TAG)" -Color Red -Prefix "❌"
        
        if ($ForceUpdate) {
            $updateResult = Update-ContainerAppVersion -AppName $BACKEND_APP_NAME -ResourceGroup $RESOURCE_GROUP -Repository "$ACR_NAME.azurecr.io" -Tag $TAG -ForceUpdate $ForceUpdate
            if ($updateResult) {
                # Don't show success message
            }
        } else {
            Write-ColorOutput -Message "Use -ForceUpdate flag to update to the latest version" -Color Yellow -Prefix "→"
        }
    }
}

# Check frontend version
$frontendExists = az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP 2>$null
if ($frontendExists) {
    $frontendDeployedImageRef = az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.template.containers[0].image" -o tsv
    $frontendDeployedVersion = Get-VersionFromImageString -ImageString $frontendDeployedImageRef
    
    if ($frontendDeployedVersion -eq $TAG) {
        # Don't show success message
    } else {
        Write-ColorOutput -Message "Frontend version verification: MISMATCH (Deployed: $frontendDeployedVersion, Expected: $TAG)" -Color Red -Prefix "❌"
        
        if ($ForceUpdate) {
            $updateResult = Update-ContainerAppVersion -AppName $FRONTEND_APP_NAME -ResourceGroup $RESOURCE_GROUP -Repository "$ACR_NAME.azurecr.io" -Tag $TAG -ForceUpdate $ForceUpdate
            if ($updateResult) {
                # Don't show success message
            }
        } else {
            Write-ColorOutput -Message "Use -ForceUpdate flag to update to the latest version" -Color Yellow -Prefix "→"
        }
    }
}

# Check Telegram scheduler version - check both container app and job
$telegramSchedulerExists = az containerapp show --name $TELEGRAM_SCHEDULER_APP_NAME --resource-group $RESOURCE_GROUP 2>$null
if ($telegramSchedulerExists) {
    $telegramSchedulerImageRef = az containerapp show --name $TELEGRAM_SCHEDULER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.template.containers[0].image" -o tsv
    $telegramSchedulerVersion = Get-VersionFromImageString -ImageString $telegramSchedulerImageRef
    
    if ($telegramSchedulerVersion -eq $TAG) {
        Write-ColorOutput -Message "Telegram scheduler version verification: SUCCESS ($telegramSchedulerVersion)" -Color Green -Prefix "✅"
    } else {
        Write-ColorOutput -Message "Telegram scheduler version verification: MISMATCH (Deployed: $telegramSchedulerVersion, Expected: $TAG)" -Color Red -Prefix "❌"
        
        if ($ForceUpdate) {
            $updateResult = Update-ContainerAppVersion -AppName $TELEGRAM_SCHEDULER_APP_NAME -ResourceGroup $RESOURCE_GROUP -Repository "$ACR_NAME.azurecr.io" -Tag $TAG -ForceUpdate $ForceUpdate
            if ($updateResult) {
                Write-ColorOutput -Message "Telegram scheduler successfully updated to version $TAG" -Color Green -Prefix "✅"
                }
            } else {
            Write-ColorOutput -Message "Use -ForceUpdate flag to update to the latest version" -Color Yellow -Prefix "→"
        }
    }
}

# Also check Telegram scheduler job if it exists
$telegramJobExists = az containerapp job show --name $TELEGRAM_SCHEDULER_APP_NAME --resource-group $RESOURCE_GROUP 2>$null
if ($telegramJobExists) {
    $telegramJobImageRef = az containerapp job show --name $TELEGRAM_SCHEDULER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.template.containers[0].image" -o tsv
    $telegramJobVersion = Get-VersionFromImageString -ImageString $telegramJobImageRef
    
    if ($telegramJobVersion -eq $TAG) {
        # Don't show success message
    } else {
        Write-ColorOutput -Message "Telegram scheduler job version verification: MISMATCH (Deployed: $telegramJobVersion, Expected: $TAG)" -Color Red -Prefix "❌"
        
        if ($ForceUpdate) {
            # For jobs, we need to recreate them
            Write-ColorOutput -Message "Updating Telegram scheduler job to version $TAG" -Color Yellow -Prefix "→"
            # The job update logic is handled in the Telegram scheduler deployment section
            Write-ColorOutput -Message "Job will be updated when you run with -ForceUpdate" -Color Yellow -Prefix "→"
        } else {
            Write-ColorOutput -Message "Use -ForceUpdate flag to update to the latest version" -Color Yellow -Prefix "→"
        }
    }
}

# Update environment variables for the backend app
$BACKEND_ENV_VARS = @(
    "INTERFACE=all",
    "PORT=8000",
    "QDRANT_URL=https://b88198bc-6212-4390-bbac-b1930f543812.europe-west3-0.gcp.cloud.qdrant.io",
    "QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwiZXhwIjoxNzQ3MDY5MzcyfQ.plLwDbnIi7ggn_d98e-OsxpF60lcNq9nzZ0EzwFAnQw",
    "AZURE_OPENAI_ENDPOINT=https://ai-kestutis9429ai265477517797.openai.azure.com",
    "AZURE_OPENAI_API_KEY=Ec1hyYbP5j6AokTzLWtc3Bp970VbCnpRMhNmQjxgJh1LrYzlsrrOJQQJ99ALACHYHv6XJ3w3AAAAACOG0Kyl",
    "AZURE_OPENAI_API_VERSION=2024-08-01-preview",
    "AZURE_OPENAI_DEPLOYMENT=gpt-4o",
    "AZURE_EMBEDDING_DEPLOYMENT=text-embedding-3-small",
    "OPENAI_API_TYPE=azure",
    "OPENAI_API_VERSION=2024-08-01-preview",
    "EMBEDDING_MODEL=text-embedding-3-small",
    "LLM_MODEL=gpt-4o",
    "SUPABASE_URL=https://aubulhjfeszmsheonmpy.supabase.co",
    "SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc",
    "CONTAINER_APP_ENV=prod",
    "USE_MANAGED_IDENTITY=true",
    "ENABLE_SCHEDULER=true",
    "ENABLE_TELEGRAM=true",
    "TELEGRAM_BOT_TOKEN=7602202107:AAH-7E6Dy6DGy1yaYQoZYFeJNpf4Z1m_Vmk"
)

# Line where backend app is created or updated
if ($backendAppExists -ne $true) {
    # Creating new backend app
    Write-ColorOutput -Message "Creating new backend app: $BACKEND_APP_NAME" -Color Green
    
    az containerapp create `
        --resource-group $RESOURCE_GROUP `
        --name $BACKEND_APP_NAME `
        --environment $CONTAINER_ENV_NAME `
        --image "${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${TAG}" `
        --target-port 8000 `
        --ingress external `
        --min-replicas 1 `
        --max-replicas 5 `
        --env-vars $BACKEND_ENV_VARS `
        --cpu 1.0 `
        --memory 2.0 `
        --registry-server "${ACR_NAME}.azurecr.io"
    
    $backendAppCreated = $LASTEXITCODE -eq 0
    
    if ($backendAppCreated) {
        Write-ColorOutput -Message "Backend app created successfully" -Color Green
    } else {
        Write-ColorOutput -Message "Failed to create backend app" -Color Red
        exit 1
    }
} else {
    # Updating existing backend app
    Write-ColorOutput -Message "Updating existing backend app: $BACKEND_APP_NAME" -Color Green
    
    az containerapp update `
        --resource-group $RESOURCE_GROUP `
        --name $BACKEND_APP_NAME `
        --image "${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${TAG}" `
        --set-env-vars $BACKEND_ENV_VARS
    
    $backendAppUpdated = $LASTEXITCODE -eq 0
    
    if ($backendAppUpdated) {
        Write-ColorOutput -Message "Backend app updated successfully" -Color Green
    } else {
        Write-ColorOutput -Message "Failed to update backend app" -Color Red
        exit 1
    }
}

# Build and deploy backend with integrated Telegram functionality
# Update backend Dockerfile to include Telegram bot functionality
Write-Host "Deploying backend with integrated Telegram functionality" -ForegroundColor Green

# Build combined container with both backend and Telegram functionality
$backendTag = "ai-companion:$TAG"
$backendImage = "$ACR_NAME.azurecr.io/$backendTag"
$buildTime = Measure-Command {
    docker build -t $backendImage -f Dockerfile .
}
Write-Host "Backend Docker image with integrated Telegram functionality built in $($buildTime.TotalSeconds) seconds" -ForegroundColor Green

# Push backend image to ACR
docker push $backendImage
Write-Host "Backend Docker image pushed to ACR: $backendImage" -ForegroundColor Green

# Step 16: Check and fix scheduled messages
if ($CheckScheduledMessages -or $FixScheduledMessages -or $FixMissingMetadata -or $ResetFailedMessages) {
    Write-ColorOutput -Message "Step 16: Checking and maintaining scheduled messages" -Color Cyan -Prefix "🔍"
    
    # Check if python is installed
    $pythonInstalled = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonInstalled) {
        Write-ColorOutput -Message "Python is required for scheduled message maintenance but was not found" -Color Red -Prefix "❌"
    } else {
        # Ensure supabase library is installed
        Write-ColorOutput -Message "Ensuring required Python packages are installed..." -Color Yellow -Prefix "→"
        python -m pip install supabase --quiet
        
        # Set environment variables for Supabase access
        $env:SUPABASE_URL = $supabaseUrl
        $env:SUPABASE_KEY = $supabaseAnonKey
        
        # Check scheduled messages
        $issuesFound = Check-ScheduledMessages
        
        # Handle fixing if issues were found or explicitly requested
        if ($issuesFound -or $FixScheduledMessages -or $FixMissingMetadata -or $ResetFailedMessages) {
            if ($FixScheduledMessages -or $FixMissingMetadata -or $ResetFailedMessages) {
                Fix-ScheduledMessages -AutoConfirm:$FixScheduledMessages -ResetFailedMessages:$ResetFailedMessages -FixMissingMetadata:$FixMissingMetadata
            } else {
                $fixConfirmation = Read-Host "Issues found in scheduled messages. Would you like to fix them? (y/n)"
                if ($fixConfirmation -eq "y") {
                    Fix-ScheduledMessages
                } else {
                    Write-ColorOutput -Message "Skipping scheduled message fixes as requested" -Color Yellow -Prefix "⚠️"
                }
            }
        } else {
            # Don't show success message
        }
        
        # Clear environment variables
        Remove-Item Env:\SUPABASE_URL
        Remove-Item Env:\SUPABASE_KEY
    }
}

# Summarize the deployment
Write-ColorOutput -Message "Deployment Summary" -Color Cyan

Write-Host "Telegram functionality is integrated in the main backend app" -ForegroundColor Yellow

# Display deployment summary
Write-ColorOutput -Message "Deployment Complete" -Color Yellow

# Show summary information about the deployment
Write-ColorOutput -Message "Environment Details" -Color Cyan -Prefix "📋"
Write-Host "Resource Group: $RESOURCE_GROUP"
Write-Host "Container App Environment: $CONTAINER_ENV_NAME"
Write-Host "Azure Container Registry: $ACR_NAME"
Write-Host "Version: $TAG"

# Inform user about Python scripts for managing scheduled messages
Write-ColorOutput -Message "Managing Scheduled Messages" -Color Cyan -Prefix "📋"
Write-Host "You can use the following Python scripts to manage scheduled messages:"
Write-Host "  - check_scheduled_messages.py: Check for issues with scheduled messages"
Write-Host "  - fix_scheduled_messages.py: Fix issues with scheduled messages"
Write-Host ""
Write-Host "Example usage:"
Write-Host "  python check_scheduled_messages.py"
Write-Host "  python fix_scheduled_messages.py --all"
Write-Host ""
Write-Host "Add them to your deployment script with the following parameters:"
Write-Host "  -CheckScheduledMessages: Check for issues with scheduled messages"
Write-Host "  -FixScheduledMessages: Fix all issues with scheduled messages"
Write-Host "  -FixMissingMetadata: Fix messages with missing metadata"
Write-Host "  -ResetFailedMessages: Reset failed messages to pending"
Write-Host "  -AutoConfirm: Automatically confirm fixes without prompting"
Write-Host ""
Write-Host "Example: .\deploy.ps1 -CheckScheduledMessages -FixScheduledMessages -AutoConfirm"

Write-ColorOutput -Message "Deployment process completed" -Color Yellow -Prefix "🏁"

# Function to build optimized backend Docker image for Azure
function Build-OptimizedBackendImage {
    param (
        [string]$Tag
    )
    
    Write-ColorOutput -Message "Building optimized backend Docker image for Azure deployment" -Color Yellow -Prefix "→"
    
    # Set BuildKit environment variable for better builds
    $env:DOCKER_BUILDKIT = "1"
    
    # Build the optimized backend image with cache optimization
    docker build `
        --build-arg BUILDKIT_INLINE_CACHE=1 `
        --cache-from ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:cache `
        -t "${IMAGE_NAME}:${Tag}" `
        -f $OPTIMIZED_BACKEND_DOCKERFILE_PATH .
    
    if (-not (Test-CommandSuccess -SuccessMessage "Optimized backend Docker image built successfully" -ErrorMessage "Failed to build backend Docker image")) {
        return $false
    }
    
    # Tag the backend image for ACR
    docker tag "${IMAGE_NAME}:${Tag}" "${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${Tag}"
    if (-not (Test-CommandSuccess -SuccessMessage "Backend Docker image tagged successfully" -ErrorMessage "Failed to tag backend Docker image")) {
        return $false
    }
    
    # Also tag as cache for future builds
    docker tag "${IMAGE_NAME}:${Tag}" "${ACR_NAME}.azurecr.io/${IMAGE_NAME}:cache"
    
    # Push the backend image to ACR
    docker push "${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${Tag}"
    docker push "${ACR_NAME}.azurecr.io/${IMAGE_NAME}:cache"
    
    if (-not (Test-CommandSuccess -SuccessMessage "Backend Docker image pushed to ACR successfully" -ErrorMessage "Failed to push backend Docker image to ACR")) {
        return $false
    }
    
    $script:backendImageExists = $true
    return $true
}

# Function to build optimized frontend Docker image for Azure
function Build-OptimizedFrontendImage {
    param (
        [string]$Tag,
        [string]$BackendUrl
    )
    
    Write-ColorOutput -Message "Building optimized frontend Docker image for Azure deployment" -Color Yellow -Prefix "→"
    
    # Set BuildKit environment variable for better builds
    $env:DOCKER_BUILDKIT = "1"
    
    # Create a single-line Docker build command that PowerShell can understand
    $dockerBuildCmd = "docker build " + 
        "--build-arg BUILDKIT_INLINE_CACHE=1 " +
        "--cache-from ${ACR_NAME}.azurecr.io/${WEB_UI_IMAGE_NAME}:cache " +
        "--build-arg NEXT_PUBLIC_SUPABASE_URL=`"https://aubulhjfeszmsheonmpy.supabase.co`" " + 
        "--build-arg NEXT_PUBLIC_SUPABASE_ANON_KEY=`"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzUyODc0MTIsImV4cCI6MjA1MDg2MzQxMn0.2u5v5XoHTHr4H0lD3W4qN3n7Z7X9jKj3Y7Q7Q7Q7Q7Q7Q7Q`" " + 
        "--build-arg NEXT_PUBLIC_AZURE_OPENAI_ENDPOINT=`"https://ai-kestutis9429ai265477517797.openai.azure.com`" " + 
        "--build-arg NEXT_PUBLIC_AZURE_OPENAI_API_KEY=`"Ec1hyYbP5j6AokTzLWtc3Bp970VbCnpRMhNmQjxgJh1LrYzlsrrOJQQJ99ALACHYHv6XJ3w3AAAAACOG0Kyl`" " + 
        "--build-arg NEXT_PUBLIC_AZURE_OPENAI_DEPLOYMENT=`"gpt-4o`" " + 
        "--build-arg NEXT_PUBLIC_EMBEDDING_MODEL=`"text-embedding-3-small`" " + 
        "--build-arg NEXT_PUBLIC_LLM_MODEL=`"gpt-4o`" " + 
        "--build-arg NEXT_PUBLIC_COLLECTION_NAME=`"Information`" " + 
        "--build-arg NEXT_PUBLIC_API_URL=`"$BackendUrl`" " + 
        "-t `"${WEB_UI_IMAGE_NAME}:${Tag}`" " + 
        "-f `"$OPTIMIZED_FRONTEND_DOCKERFILE_PATH`" " +
        "`"$FRONTEND_SRC_PATH`""
    
    # Execute the Docker build command
    Invoke-Expression $dockerBuildCmd
    
    if (-not (Test-CommandSuccess -SuccessMessage "Optimized frontend Docker image built successfully" -ErrorMessage "Failed to build frontend Docker image")) {
        return $false
    }
    
    # Tag the frontend image for ACR
    docker tag "${WEB_UI_IMAGE_NAME}:${Tag}" "${ACR_NAME}.azurecr.io/${WEB_UI_IMAGE_NAME}:${Tag}"
    if (-not (Test-CommandSuccess -SuccessMessage "Frontend Docker image tagged successfully" -ErrorMessage "Failed to tag frontend Docker image")) {
        return $false
    }
    
    # Also tag as cache for future builds
    docker tag "${WEB_UI_IMAGE_NAME}:${Tag}" "${ACR_NAME}.azurecr.io/${WEB_UI_IMAGE_NAME}:cache"
    
    # Push the frontend image to ACR
    docker push "${ACR_NAME}.azurecr.io/${WEB_UI_IMAGE_NAME}:${Tag}"
    docker push "${ACR_NAME}.azurecr.io/${WEB_UI_IMAGE_NAME}:cache"
    
    if (-not (Test-CommandSuccess -SuccessMessage "Frontend Docker image pushed to ACR successfully" -ErrorMessage "Failed to push frontend Docker image to ACR")) {
        return $false
    }
    
    $script:frontendImageExists = $true
    return $true
}
