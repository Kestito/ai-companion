# PowerShell script to manually trigger the Telegram scheduler job
# Usage: .\trigger_telegram_job.ps1

# Configuration variables - edit these to match your environment
$RESOURCE_GROUP = "evelina-rg-20250308115110"
$JOB_NAME = "telegram-scheduler-app"

# Function to display colored output
function Write-ColorOutput {
    param (
        [string]$Message,
        [string]$Color = "White",
        [string]$Prefix = "===",
        [string]$Suffix = "==="
    )
    
    Write-Host "$Prefix $Message $Suffix" -ForegroundColor $Color
}

# Function to check if Azure CLI is logged in
function Test-AzureLogin {
    try {
        $loginStatus = az account show 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput -Message "Not logged in to Azure. Please run 'az login' first." -Color Red -Prefix "❌"
            return $false
        }
        
        $account = $loginStatus | ConvertFrom-Json
        Write-ColorOutput -Message "Logged in as: $($account.user.name)" -Color Green -Prefix "✅"
        return $true
    }
    catch {
        Write-ColorOutput -Message "Error checking Azure login status: $_" -Color Red -Prefix "❌"
        return $false
    }
}

# Function to trigger the job with retry
function Invoke-JobExecution {
    param (
        [string]$JobName,
        [string]$ResourceGroup,
        [int]$MaxRetries = 3,
        [int]$RetryDelaySeconds = 5
    )
    
    Write-ColorOutput -Message "Attempting to trigger the Telegram scheduler job: $JobName" -Color Yellow -Prefix "→"
    
    for ($retryCount = 0; $retryCount -lt $MaxRetries; $retryCount++) {
        if ($retryCount -gt 0) {
            Write-ColorOutput -Message "Retrying job execution trigger (attempt $($retryCount+1) of $MaxRetries)..." -Color Yellow -Prefix "⚠️"
            Start-Sleep -Seconds $RetryDelaySeconds
        }
        
        try {
            # First check if the job exists
            $jobInfo = az containerapp job show --name $JobName --resource-group $ResourceGroup 2>&1
            
            if ($LASTEXITCODE -ne 0) {
                Write-ColorOutput -Message "Job $JobName does not exist in resource group $ResourceGroup" -Color Red -Prefix "❌"
                Write-ColorOutput -Message "Error details: $jobInfo" -Color Red -Prefix ""
                return $false
            }
            
            # Use the correct command format with explicit parameter names
            $result = az containerapp job execution start --name $JobName --resource-group $ResourceGroup 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput -Message "Job triggered successfully!" -Color Green -Prefix "✅"
                
                # Display execution ID and status if available
                try {
                    $resultObj = $result | ConvertFrom-Json
                    Write-ColorOutput -Message "Execution ID: $($resultObj.name)" -Color Cyan -Prefix "🔍"
                    Write-ColorOutput -Message "Status: $($resultObj.properties.status)" -Color Cyan -Prefix "🔍"
                } catch {
                    Write-ColorOutput -Message "Triggered successfully, but couldn't parse execution details." -Color Yellow -Prefix "⚠️"
                }
                
                return $true
            } else {
                Write-ColorOutput -Message "Error triggering job: $result" -Color Red -Prefix "❌"
            }
        }
        catch {
            Write-ColorOutput -Message "Exception triggering job: $_" -Color Red -Prefix "❌"
        }
    }
    
    Write-ColorOutput -Message "Failed to trigger job after $MaxRetries attempts" -Color Red -Prefix "❌"
    Write-ColorOutput -Message "Alternative method: Use Azure Portal or run this command directly:" -Color Yellow -Prefix "→"
    Write-ColorOutput -Message "  az containerapp job execution start --name $JobName --resource-group $ResourceGroup" -Color White -Prefix ""
    
    return $false
}

# Main script execution
Write-ColorOutput -Message "Telegram Scheduler Job Manual Trigger Script" -Color Cyan -Prefix "🤖"

# Check Azure login
if (-not (Test-AzureLogin)) {
    exit 1
}

# Check if resource group exists
$rgExists = az group exists --name $RESOURCE_GROUP
if ($rgExists -ne "true") {
    Write-ColorOutput -Message "Resource group $RESOURCE_GROUP does not exist." -Color Red -Prefix "❌"
    exit 1
}

# Confirm with user
Write-ColorOutput -Message "This will manually trigger the Telegram scheduler job" -Color Yellow -Prefix "⚠️"
Write-ColorOutput -Message "Job: $JOB_NAME" -Color Yellow -Prefix "📋"
Write-ColorOutput -Message "Resource Group: $RESOURCE_GROUP" -Color Yellow -Prefix "📋"
$confirmation = Read-Host "Do you want to continue? (y/n)"

if ($confirmation -ne "y") {
    Write-ColorOutput -Message "Operation cancelled by user" -Color Yellow -Prefix "⚠️"
    exit 0
}

# Trigger the job
$result = Invoke-JobExecution -JobName $JOB_NAME -ResourceGroup $RESOURCE_GROUP

if ($result) {
    Write-ColorOutput -Message "Job triggered successfully. Check Azure Portal for execution details." -Color Green -Prefix "✅"
} else {
    Write-ColorOutput -Message "Failed to trigger job. See above for error details." -Color Red -Prefix "❌"
    exit 1
}

# Monitor job execution status
Write-ColorOutput -Message "Would you like to monitor the job execution status? (y/n)" -Color Yellow -Prefix "?"
$monitorConfirmation = Read-Host

if ($monitorConfirmation -eq "y") {
    Write-ColorOutput -Message "Fetching recent job executions..." -Color Cyan -Prefix "🔍"
    
    # Get list of recent executions
    $executions = az containerapp job execution list --name $JOB_NAME --resource-group $RESOURCE_GROUP 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        try {
            $executionsObj = $executions | ConvertFrom-Json
            
            if ($executionsObj.Count -gt 0) {
                Write-ColorOutput -Message "Recent Job Executions:" -Color Cyan -Prefix "📋"
                
                foreach ($execution in $executionsObj) {
                    $status = $execution.properties.status
                    $statusColor = switch ($status) {
                        "Succeeded" { "Green" }
                        "Failed" { "Red" }
                        "Running" { "Yellow" }
                        default { "White" }
                    }
                    
                    $startTime = $execution.properties.startTime
                    if (-not $startTime) {
                        $startTime = "N/A"
                    }
                    
                    Write-Host "  Execution ID: " -NoNewline
                    Write-Host $execution.name -ForegroundColor Cyan -NoNewline
                    Write-Host " | Status: " -NoNewline
                    Write-Host $status -ForegroundColor $statusColor -NoNewline
                    Write-Host " | Start Time: $startTime"
                }
            } else {
                Write-ColorOutput -Message "No recent executions found" -Color Yellow -Prefix "⚠️"
            }
        } catch {
            Write-ColorOutput -Message "Error parsing executions: $_" -Color Red -Prefix "❌"
        }
    } else {
        Write-ColorOutput -Message "Failed to retrieve executions: $executions" -Color Red -Prefix "❌"
    }
}

Write-ColorOutput -Message "Script execution completed" -Color Cyan -Prefix "🚀" 