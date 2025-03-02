# Chainlit WebSocket Connection Issues in Azure Container Apps

## Problem Description

Users may encounter "Could not reach the server" errors when attempting to access the Chainlit interface deployed on Azure Container Apps. This error appears as a red notification banner in the Chainlit UI and prevents users from interacting with the chat interface.

![Error Screenshot](https://i.imgur.com/YOUR_IMAGE_HERE.png)

The issue occurs because Chainlit relies heavily on WebSocket connections for real-time communication, and the default Azure Container App configuration may interfere with these connections.

## Current Status

**✅ RESOLVED**: As of March 2, 2025, we have successfully resolved the WebSocket connection issues. The current logs show multiple successful WebSocket connections:

```
INFO:ai_companion.main:Proxying WebSocket request to Chainlit: GET /ws/socket.io/
INFO:ai_companion.main:Chainlit WebSocket response: 200
```

All WebSocket connections are now returning status code 200, indicating proper functioning.

## Known Issues and Solutions

### JSON Parsing Error in Deployment Script

When running the deployment script, you might encounter a JSON parsing error during the ingress configuration step:

```
=== Configuring ingress for WebSocket support ===
The command failed with an unexpected error. Here is the traceback:
Unterminated string starting at: line 1 column 3097 (char 3096)
```

**Solution**: The updated `deploy.ps1` script includes error handling for this scenario. The script will:
1. Try the primary approach using the standard Azure CLI command
2. If that fails, execute an alternative approach using separate commands
3. Log the results of both attempts

This ensures the deployment completes successfully even if the JSON parsing error occurs.

## Root Causes

1. **TCP-based Health Probes**: Default TCP health probes can interrupt WebSocket connections.
2. **Incorrect Transport Protocol**: Azure Container Apps needs to be configured with the proper transport mode to handle WebSocket connections.
3. **CORS Configuration**: Insufficient CORS settings can block WebSocket connections from browsers.
4. **Browser Caching**: Sometimes browser cache can interfere with establishing new WebSocket connections after configuration changes.

## Solution Steps

### 1. Configure Proper Transport Mode

Ensure the transport mode is set to "Auto" to support both HTTP and WebSocket traffic:

```powershell
az containerapp ingress update \
  --name YOUR_CONTAINER_APP_NAME \
  --resource-group YOUR_RESOURCE_GROUP \
  --target-port 8000 \
  --transport auto
```

### 2. Configure HTTP Health Probes

Replace the default TCP health probes with HTTP probes that check a specific health endpoint:

```powershell
az containerapp ingress update \
  --name YOUR_CONTAINER_APP_NAME \
  --resource-group YOUR_RESOURCE_GROUP \
  --probe-path "/monitor/health" \
  --probe-protocol http \
  --probe-interval 30 \
  --probe-timeout 10 \
  --probe-retries 3
```

### 3. Configure Comprehensive CORS Policy

Allow WebSocket connections from any origin:

```powershell
az containerapp ingress cors update \
  --name YOUR_CONTAINER_APP_NAME \
  --resource-group YOUR_RESOURCE_GROUP \
  --allowed-origins "*" \
  --allowed-methods "*" \
  --allowed-headers "*" \
  --expose-headers "*" \
  --max-age 7200 \
  --allow-credentials true
```

### 4. Force a Revision Update

Create a new revision to apply all the changes:

```powershell
az containerapp update \
  --name YOUR_CONTAINER_APP_NAME \
  --resource-group YOUR_RESOURCE_GROUP \
  --revision-suffix "websocket$(Get-Date -Format 'yyyyMMddHHmmss')"
```

### 5. Clear Browser Cache

Instruct users to clear their browser cache and cookies before attempting to access the application again.

## Verification

After implementing these changes, you can verify that WebSocket connections are working by:

1. Checking the container logs for successful WebSocket connections:
```powershell
az containerapp logs show --name YOUR_CONTAINER_APP_NAME --resource-group YOUR_RESOURCE_GROUP --tail 50
```

2. Looking for entries like "WebSocket connection established" or "proxying WebSocket request" in the logs.

3. Opening the Chainlit UI in a browser and confirming that no "Could not reach the server" errors appear.

## Prevention

To prevent these issues in future deployments, incorporate these configurations into your deployment scripts or ARM/Bicep templates.

Our `deploy.ps1` script now includes all of these settings by default to ensure WebSocket connections work properly with every deployment.

## Troubleshooting Further Issues

If you're still experiencing WebSocket connection issues after implementing these fixes:

1. **Check Container Status**: Ensure the container is running properly.
2. **Review Resource Allocation**: WebSocket connections may require more memory/CPU.
3. **Check Network Policies**: Ensure no network policies are blocking WebSocket traffic.
4. **Browser Console**: Check browser developer tools for specific error messages.
5. **Try a Different Browser**: Some browsers handle WebSocket connections differently.

## Related Documentation

- [Azure Container Apps WebSocket Support](https://learn.microsoft.com/en-us/azure/container-apps/websockets)
- [Chainlit Documentation](https://docs.chainlit.io/deployment)
- [CORS in Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/cors) 