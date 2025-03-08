# WebSocket Performance Issues and Resolutions

## Problem Description

The Chainlit interface was experiencing connectivity issues in the Azure Container App deployment. Users were seeing "Could not reach the server" errors in the browser, and the console showed 502 Bad Gateway errors when trying to access the WebSocket endpoints. While health checks were passing successfully, the actual WebSocket connections from browser clients were failing.

## Root Causes

1. **Insufficient Resources**: The container was configured with limited CPU (0.5 cores) and memory (1.0 GB), which was not enough to handle WebSocket connections effectively, especially under load.

2. **CORS Configuration**: The default CORS policy was not properly configured to handle WebSocket connections from different origins.

3. **WebSocket Protocol Handling**: Even though HTTP transport protocol was set, additional configuration was needed to properly handle WebSocket connections.

## Resolution Steps

### 1. Increased Container Resources

We doubled the CPU and memory allocation for better WebSocket connection handling:

```powershell
az containerapp update --name evelina-vnet-app --resource-group evelina-ai-rg --cpu 1.0 --memory 2.0Gi
```

This increase in resources provides more processing power for handling concurrent WebSocket connections and prevents connection timeouts due to resource constraints.

### 2. Added Comprehensive CORS Policy

We implemented a permissive CORS policy to ensure WebSocket connections can be established from any origin:

```powershell
az containerapp ingress cors update --name evelina-vnet-app --resource-group evelina-ai-rg --allowed-origins "*" --allowed-methods "*" --allowed-headers "*" --expose-headers "*" --max-age 7200 --allow-credentials true
```

This configuration ensures that:
- Any origin can establish WebSocket connections
- All HTTP methods are allowed
- All headers are permitted
- Credentials can be included in cross-origin requests
- CORS responses are cached for 2 hours (7200 seconds)

### 3. Forced Container Restart with New Revision

To ensure all configuration changes were properly applied, we created a new revision with a timestamp suffix:

```powershell
az containerapp update --name evelina-vnet-app --resource-group evelina-ai-rg --revision-suffix restart-$(Get-Date -Format "yyyyMMddHHmmss")
```

This approach ensured a clean restart of the container with all the new configuration changes applied.

## Deployment Script Updates

The `deploy.ps1` script was updated to include these improvements for future deployments:

```powershell
# Setting container resources and scale settings
az containerapp update `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --min-replicas 1 `
  --max-replicas 10 `
  --cpu 1.0 `
  --memory 2.0Gi

# Configuring ingress for WebSocket support
az containerapp ingress update `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --target-port 8000 `
  --transport http

# Configuring CORS policy for WebSocket support
az containerapp ingress cors update `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --allowed-origins "*" `
  --allowed-methods "*" `
  --allowed-headers "*" `
  --expose-headers "*" `
  --max-age 7200 `
  --allow-credentials true
```

## Verification

After implementing these changes, we confirmed that:

1. WebSocket connections were successfully established with HTTP 200 OK responses in the logs
2. The health endpoint was accessible and returning a healthy status
3. The root URL and WebSocket endpoints were accessible and returning proper responses

## Monitoring

Continuous monitoring is crucial to ensure WebSocket connections remain stable. Key metrics to monitor include:

1. CPU and memory usage
2. WebSocket connection success rates
3. Response times for WebSocket connections
4. Number of concurrent WebSocket connections

## Best Practices for WebSocket Performance

1. **Resource Allocation**: Always allocate sufficient CPU and memory for WebSocket-heavy applications
2. **CORS Configuration**: Use appropriate CORS settings for your security requirements
3. **Health Probes**: Configure custom HTTP health probes for WebSocket applications
4. **Transport Protocol**: Always use HTTP transport protocol for WebSocket support
5. **Connection Timeouts**: Configure appropriate timeouts for WebSocket connections
6. **Scaling**: Set appropriate scaling parameters based on expected concurrent connections
7. **Monitoring**: Implement comprehensive monitoring to detect WebSocket performance issues

## Conclusion

The WebSocket connection issues were successfully resolved by increasing container resources, implementing proper CORS policies, and ensuring all configuration changes were properly applied through a container restart. These changes have resulted in stable WebSocket connections and a properly functioning Chainlit interface. 