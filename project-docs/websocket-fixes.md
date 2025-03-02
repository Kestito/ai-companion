# WebSocket Connection Fixes for Chainlit

## Problem Description

The Chainlit interface was showing "Could not reach the server" errors, even though the application health checks were reporting as healthy (200 OK). The browser console revealed the root cause:

```
GET https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/ws/socket.io/ 502 (Bad Gateway)
```

This indicated that while the HTTP health checks were passing, the WebSocket connections were failing with 502 errors.

## Root Cause Analysis

After investigating the Azure Container App configuration, we discovered two issues:

1. **Transport Protocol**: The ingress was configured with the `--transport http` setting, which doesn't properly handle WebSocket connections.

2. **Missing Force Restart**: Configuration changes require a new revision to fully take effect, especially for WebSocket-related settings.

## Solution Implemented

We fixed the issue with the following steps:

1. **Changed Transport Protocol to Auto**:
   ```powershell
   az containerapp ingress update --name evelina-vnet-app --resource-group evelina-ai-rg --transport auto
   ```
   
   The `auto` setting allows Azure to automatically detect and handle different protocols, including WebSockets, whereas the `http` setting is more restrictive.

2. **Created a New Revision to Apply Changes**:
   ```powershell
   $timestamp = Get-Date -Format "yyyyMMddHHmmss"
   az containerapp update --name evelina-vnet-app --resource-group evelina-ai-rg --revision-suffix "websocket$timestamp"
   ```
   
   This forces Azure to create a new container instance with the updated configuration, ensuring all changes take effect.

   > **Important**: Azure Container App revision suffixes must consist of lowercase alphanumeric characters or '-', start with a letter or number, end with an alphanumeric character, and cannot have '--'. Avoid using complex patterns with special characters.

3. **Updated Deployment Script**:
   We modified the `deploy.ps1` script to:
   - Use `--transport auto` instead of `--transport http`
   - Add a step to create a new revision after configuration changes
   - Fix the restart command (Azure doesn't have a direct restart command)
   - Use a properly formatted revision suffix pattern

## Verifying the Fix

After implementing these changes, the WebSocket connections should work properly, allowing the Chainlit interface to connect to the server. You can verify this by:

1. Refreshing the browser at `https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/`
2. Checking the browser console for any WebSocket-related errors
3. Verifying that the "Could not reach the server" error is gone

## Best Practices for WebSocket Support in Azure Container Apps

1. **Always use `--transport auto` for WebSocket applications**
2. **Create a new revision after making configuration changes** using the revision-suffix parameter
3. **Use valid revision suffix formats** (alphanumeric characters, no special characters)
4. **Implement proper CORS settings** to allow WebSocket connections from necessary origins
5. **Configure appropriate health check endpoints** that return 200 OK responses
6. **Allocate sufficient resources** (CPU/memory) for handling concurrent WebSocket connections
7. **Monitor WebSocket connection errors** in your application logs

## Troubleshooting WebSocket Issues

If WebSocket issues persist:

1. Check browser console for specific error messages
2. Verify CORS configuration is allowing WebSocket connections
3. Confirm the application is listening on the correct port (8000)
4. Consider increasing request timeout settings if connections time out
5. Create a new revision to force a clean restart of the container

## References

- [Azure Container Apps - Configure ingress](https://docs.microsoft.com/en-us/azure/container-apps/ingress-overview)
- [WebSocket Protocol - RFC 6455](https://datatracker.ietf.org/doc/html/rfc6455)
- [Chainlit WebSocket Requirements](https://docs.chainlit.io/get-started/installation)
- [Azure Container App Naming Requirements](https://learn.microsoft.com/en-us/azure/container-apps/containers) 