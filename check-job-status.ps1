# Check Telegram Scheduler Job Status
param(
    [switch]$ShowLogs,
    [switch]$TriggerExecution,
    [string]$ExecutionName
)

Write-Host "Checking Telegram Scheduler Job Status" -ForegroundColor Cyan

# Define variables
$JOB_NAME = "telegram-scheduler-app"
$RESOURCE_GROUP = "evelina-rg-20250308115110"

# List executions
if ($ExecutionName) {
    Write-Host "Checking status of execution: $ExecutionName" -ForegroundColor Yellow
    az containerapp job execution show --name $JOB_NAME --resource-group $RESOURCE_GROUP --execution-name $ExecutionName
    
    if ($ShowLogs) {
        Write-Host "Showing logs for execution: $ExecutionName" -ForegroundColor Yellow
        az containerapp job execution logs --name $JOB_NAME --resource-group $RESOURCE_GROUP --execution-name $ExecutionName
    }
} else {
    Write-Host "Listing recent executions:" -ForegroundColor Yellow
    az containerapp job execution list --name $JOB_NAME --resource-group $RESOURCE_GROUP --query "[].{name:name, startTime:properties.startTime, status:properties.status}" -o table
    
    if ($TriggerExecution) {
        Write-Host "Triggering new execution:" -ForegroundColor Yellow
        $newExecution = az containerapp job execution start --name $JOB_NAME --resource-group $RESOURCE_GROUP --query "name" -o tsv
        Write-Host "Triggered execution: $newExecution" -ForegroundColor Green
        Write-Host "To check logs later run:" -ForegroundColor Yellow
        Write-Host ".\check-job-status.ps1 -ExecutionName $newExecution -ShowLogs" -ForegroundColor White
    }
}
