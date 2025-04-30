# Azure Deployment Guide

This guide explains how to deploy your AI Companion application to Azure using optimized Docker images and Azure-specific configurations.

## Prerequisites

1. Azure CLI installed and configured
2. Docker installed and running locally
3. Access to an Azure subscription with permissions to create resources
4. Access to Azure Container Registry

## Deployment Options

We now provide two deployment options:

1. **Standard deployment with original deploy.ps1 script**: Uses the main deployment script with optimizations
   ```powershell
   ./deploy.ps1
   ```

2. **Legacy deployment without optimizations**: You can still use the original build process if needed
   ```powershell
   ./deploy.ps1 -UseOptimizedImages:$false
   ```

## Optimized Docker Images for Azure

The deployment script now includes built-in optimizations for Azure deployment:

- **Multi-stage builds** - Reduces image sizes by 60-70% 
- **Azure-specific base images** - Uses Microsoft Container Registry (MCR) images
- **Layer optimization** - Better caching and smaller layers
- **BuildKit integration** - Faster builds with improved caching

### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `-UseOptimizedImages` | `$true` | Enables optimized Docker builds for Azure |
| `-ForceUpdate` | `$true` | Updates container apps even if they exist |
| `-SkipLogin` | `$false` | Skips Azure login (if already logged in) |
| `-ResourceGroupName` | `"rg-aicompanion"` | Sets the target resource group |
| `-ImageTag` | `"latest"` | Sets an explicit image tag |

### Using Optimized Deployment

The optimized Docker build process is now the default. Simply run:

```powershell
# Standard deployment with optimized Docker builds
./deploy.ps1

# Force update of existing deployments
./deploy.ps1 -ForceUpdate

# Skip Azure login (if already logged in)
./deploy.ps1 -SkipLogin

# Use a specific resource group
./deploy.ps1 -ResourceGroupName "my-resource-group"
```

## Deployment Components

The deployment process creates or updates the following Azure resources:

1. **Backend Container App**
   - Image: `ai-companion`
   - Ports: 8000
   - Health Check: `/monitor/health`
   
2. **Frontend Container App**
   - Image: `web-ui-companion`
   - Ports: 3000
   - Connected to backend via environment variables

## Manual Steps After Deployment

After deployment, you may want to:

1. Configure custom domains
2. Set up SSL certificates
3. Configure authentication
4. Set up monitoring

## Troubleshooting

If you encounter issues during deployment:

1. Check container logs in Azure Portal
2. Verify health endpoints are responding
3. Ensure Azure Container Registry access is configured
4. Check resource limits for Container Apps

## Azure Cost Optimization

The optimized images and deployment process help reduce costs in several ways:

1. Smaller images mean faster deployments and less egress bandwidth
2. Reduced resource requirements (CPU/memory)
3. Proper health checks prevent unnecessary restarts
4. Streamlined configuration reduces management overhead

## Maintenance

To update your deployment:

1. Build new optimized images
2. Push to Azure Container Registry
3. Run `deploy.ps1 -ForceUpdate` 