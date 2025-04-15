# Azure Deployment Troubleshooting Guide

This guide provides solutions to common issues encountered when deploying the AI Companion to Azure Container Apps.

## WebSocket Connection Issues

### Symptoms
- Chainlit interface shows "Could not reach the server" error
- Browser console shows 502 Bad Gateway for WebSocket connections:
  ```
  GET https://your-app-name.azurecontainerapps.io/ws/socket.io/ 502 (Bad Gateway)
  ```
- Health checks pass but WebSocket connections fail

### Root Causes
1. **Incorrect Transport Setting**: Using `--transport http` instead of `--transport auto`
2. **Insufficient Resources**: Limited CPU/memory for handling WebSocket connections
3. **CORS Configuration**: Missing CORS settings for WebSocket connections
4. **Missing Revision Update**: Configuration changes not properly applied

### Solutions

#### 1. Change Transport Protocol to Auto
```powershell
az containerapp ingress update --name your-app-name --resource-group your-resource-group --transport auto
```

#### 2. Increase Container Resources
```powershell
az containerapp update --name your-app-name --resource-group your-resource-group --cpu 1.0 --memory 2.0Gi
```

#### 3. Configure CORS for WebSockets
```powershell
az containerapp ingress cors update --name your-app-name --resource-group your-resource-group --allowed-origins "*" --allowed-methods "*" --allowed-headers "*" --expose-headers "*" --max-age 7200 --allow-credentials true
```

#### 4. Create a New Revision to Apply Changes
```powershell
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
az containerapp update --name your-app-name --resource-group your-resource-group --revision-suffix "restart$timestamp"
```

> **Important**: Azure Container App revision suffixes must consist of lowercase alphanumeric characters or '-', start with a letter or number, end with an alphanumeric character, and cannot have '--'.

## Deployment Issues

### Docker Issues

#### Docker Not Running
- **Symptom**: Error "Docker is installed but not running"
- **Solution**: 
  1. Start Docker Desktop
  2. Wait until the whale icon stops animating
  3. Verify with `docker info`

#### Docker Build Failures
- **Symptom**: Build fails with error messages
- **Solutions**:
  1. **Clean Docker resources**: `docker system prune -f`
  2. **Create proper .dockerignore file**:
     ```
     .git/
     __pycache__/
     node_modules/
     .next/
     ```
  3. **Run build with verbose output**: Add `--progress=plain` flag

### Azure Container App Issues

#### 404 Not Found for Service Endpoints
- **Symptom**: Health check endpoints return 404
- **Solutions**:
  1. **Verify ingress configuration**: Check that the correct target port is configured
  2. **Check health endpoints**: Ensure your code implements the expected health endpoints
  3. **Inspect logs**: `az containerapp logs show --name your-app-name --resource-group your-resource-group --tail 100`

#### Container App Not Starting
- **Symptom**: Container App shows as "Failed" or constantly restarts
- **Solutions**:
  1. **Check resource allocation**: Increase CPU/memory if needed
  2. **Review environment variables**: Ensure all required variables are set
  3. **Examine startup logs**: Look for errors during initialization

## Database Connection Issues

### Supabase Connection Failures
- **Symptom**: Logs show "Failed to connect to database" or similar errors
- **Solutions**:
  1. **Check environment variables**: Verify SUPABASE_URL and SUPABASE_KEY
  2. **Test connectivity**: Verify network access to Supabase
  3. **Check VNet integration**: If using VNet, ensure proper configuration

## Health Check Configuration

### Health Check Failures
- **Symptom**: Container App shows as unhealthy or frequently restarts
- **Solutions**:
  1. **Check health probe configuration**: Ensure correct path, port, and timing
  2. **Verify health endpoint implementation**: Confirm your code properly implements health endpoints
  3. **Adjust timing parameters**: Increase initial delay if container needs more startup time

## Environment Variable Issues

### Missing or Incorrect Variables
- **Symptom**: Application behaves incorrectly or fails to start
- **Solutions**:
  1. **Export existing variables**: `az containerapp show --name your-app-name --resource-group your-resource-group --query "properties.template.containers[0].env"`
  2. **Update variables**: `az containerapp update --name your-app-name --resource-group your-resource-group --set-env-vars KEY1=value1 KEY2=value2`
  3. **Check for typos**: Ensure variable names match exactly what the application expects

## Best Practices for Troubleshooting

1. **Check Logs First**: Always check container logs for errors
2. **Verify Health Endpoints**: Ensure health endpoints return 200 OK
3. **Incrementally Apply Changes**: Make one change at a time to isolate issues
4. **Create New Revisions**: When changing configuration, create a new revision
5. **Increase Resources**: If experiencing performance issues, try increasing CPU/memory
6. **Monitor Performance**: Watch for CPU or memory pressure in Azure Monitor

## Diagnostic Commands

```bash
# View detailed container logs
az containerapp logs show --name your-app-name --resource-group your-resource-group --follow

# Check container revisions
az containerapp revision list --name your-app-name --resource-group your-resource-group

# Get container configuration
az containerapp show --name your-app-name --resource-group your-resource-group

# Test health endpoint
curl -I https://your-app-name.azurecontainerapps.io/health
``` 