# Scheduled Messaging Deployment Guide

This guide explains how to deploy the scheduled messaging system to Azure Container Apps using the provided deployment script.

## Prerequisites

- Azure CLI installed and authenticated
- Docker Desktop installed and running
- Access to Azure Container Registry (ACR)
- Azure Container Apps environment set up
- Supabase project with required schema

## Quick Deployment

The simplest way to deploy is using the provided PowerShell script with default values:

```powershell
# Run from the project root
./deploy-scheduler.ps1
```

This will:
- Build the Docker image for the scheduled messaging processor
- Push it to Azure Container Registry
- Create or update the Azure Container App
- Configure environment variables

## Customized Deployment

You can customize the deployment with parameters:

```powershell
./deploy-scheduler.ps1 `
  -ResourceGroup "your-resource-group" `
  -ContainerAppName "your-app-name" `
  -ContainerAppEnvironment "your-environment" `
  -ImageTag "v1.0.0" `
  -Registry "yourregistry.azurecr.io" `
  -SubscriptionId "your-subscription-id"
```

### Skip Build Option

If you're encountering issues with Docker or just want to update the Container App settings:

```powershell
./deploy-scheduler.ps1 -SkipBuild
```

This skips the Docker build and push steps, only updating the Container App configuration.

## Required Environment Variables

The scheduled messaging processor requires these environment variables:

| Variable | Description | Source |
|----------|-------------|--------|
| CONTAINER_APP_ENV | Environment name (prod, dev) | deploy-scheduler.ps1 |
| USE_MANAGED_IDENTITY | Whether to use Azure managed identity | deploy-scheduler.ps1 |
| SUPABASE_URL | URL of Supabase API | From backend app |
| SUPABASE_KEY | API key for Supabase | Secret from Azure |
| APPLICATIONINSIGHTS_CONNECTION_STRING | Application Insights connection string | Azure |

## Health Check Configuration

The scheduled messaging system exposes a health endpoint at `/health` on port 8080 that returns:

```json
{
  "status": "healthy",
  "last_successful_run": 1721234567.123,
  "timestamp": 1721234567.456
}
```

Configure health probes in the Azure Portal:
- **Startup probe**: HTTP GET `/health` on port 8080 (Initial delay: 10s, Period: 10s, Timeout: 5s)
- **Liveness probe**: HTTP GET `/health` on port 8080 (Initial delay: 60s, Period: 30s, Timeout: 5s)

## Monitoring

### Application Insights

The processor automatically sends logs to Application Insights if configured. You can:

1. View logs in Azure Portal
2. Create alerts based on health status  
3. Monitor performance metrics

### Azure CLI Monitoring

```bash
# View logs
az containerapp logs show --resource-group your-resource-group --name your-app-name --tail 100

# Check current status
az containerapp show --resource-group your-resource-group --name your-app-name --query "properties.runningStatus"
```

## Troubleshooting

### Common Issues

1. **Container not starting**:
   - Check health probe configuration
   - Review logs with `az containerapp logs show`
   - Verify the `/health` endpoint is properly implemented

2. **Messages not processing**:
   - Verify Supabase credentials and connection
   - Check processor logs for errors

3. **Database connection issues**:
   - Check network access to Supabase
   - Verify the SUPABASE_URL environment variable

### Docker Build Issues

If you encounter errors during Docker build:

1. **Use .dockerignore**: Ensure you have a proper .dockerignore file to exclude unnecessary files
2. **Cleanup Docker**: Run `docker system prune -f` to clean up resources
3. **Try verbose output**: Run with `-Verbose` flag for detailed build logs

### Restart the Processor

If you need to restart the processor:

```bash
az containerapp update --name your-app-name --resource-group your-resource-group
``` 