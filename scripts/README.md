# Utility Scripts for AI Companion

This directory contains utility scripts for managing and maintaining the AI Companion application.

## Telegram Scheduler Scripts

### trigger_telegram_job.ps1

This script allows you to manually trigger the Telegram scheduler job in Azure Container Apps. While the job is configured to run automatically on a CRON schedule (every 5 minutes by default), there may be situations where you need to trigger it manually for testing or to process scheduled messages immediately.

#### Prerequisites

- Azure CLI installed and configured
- Appropriate permissions to access the Azure Container App Jobs in your subscription
- PowerShell

#### Usage

1. Open PowerShell
2. Navigate to the scripts directory
3. Run the script:

```powershell
.\trigger_telegram_job.ps1
```

The script will:
1. Verify your Azure login status
2. Check if the specified resource group exists
3. Ask for confirmation before proceeding
4. Attempt to trigger the Telegram scheduler job
5. Display the execution status

#### Configuration

You may need to modify the following variables at the top of the script to match your environment:

```powershell
$RESOURCE_GROUP = "evelina-rg-20250308115110"
$JOB_NAME = "telegram-scheduler-app"
```

#### Troubleshooting

If the script fails to trigger the job:

1. Ensure you have the correct permissions in Azure
2. Check that the job name and resource group are correct
3. Try running the Azure CLI command directly:

```powershell
az containerapp job execution start --name telegram-scheduler-app --resource-group evelina-rg-20250308115110
```

4. Check the Azure Portal for more detailed error information

## Notes on Scheduler Design

The Telegram scheduler is designed to run as an Azure Container App Job on a CRON schedule, making it more resource-efficient than a continuously running service. This approach:

1. Reduces resource usage since the job only runs when needed
2. Provides reliable execution through Azure's managed scheduling
3. Separates concerns between the main application and scheduled tasks

The scheduler job checks for due messages in the database and processes them each time it runs. 