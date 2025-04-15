# AI Companion Azure Deployment Guide

## Overview

This document describes the deployment of the AI Companion application on Azure Container Apps. The deployment uses path-based routing for all interfaces in a single container app.

## Prerequisites

- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed and authenticated
- [Docker](https://www.docker.com/get-started/) installed and running
- Access to the Azure Container Registry (ACR)
- Azure subscription with permissions to deploy Container Apps

## Deployment Methods

### 1. Using the PowerShell Script (Recommended)

The `deploy.ps1` script handles all aspects of deployment in a single command:

```powershell
# From the project root directory
./deploy.ps1
```

The script supports various parameters for customization:

```powershell
./deploy.ps1 -ForceRebuild -CustomTag "v1.2.3" -SkipTelegramSetup
```

Key parameters:
- `-ForceRebuild`: Forces rebuild even if no changes detected
- `-CustomTag`: Specifies a custom version tag
- `-SkipTelegramSetup`: Skips the Telegram scheduler setup
- `-AutoIncrement`: Automatically increments version (default: true)
- `-DiagnoseOnly`: Only run diagnostics without making changes

### 2. Manual Deployment

If you prefer to deploy manually:

```bash
# Build the Docker image
docker build -t yourregistry.azurecr.io/ai-companion:latest .

# Push to registry
az acr login --name yourregistry
docker push yourregistry.azurecr.io/ai-companion:latest

# Deploy using the YAML template or Azure CLI
az containerapp update -n your-app-name -g your-resource-group --yaml container-app-template.yaml
```

## Deployment Architecture

The application is deployed as a single Container App with path-based routing:

- **Base URL**: https://your-app-name.azurecontainerapps.io
- **Chainlit Interface**: `/` (root path)
- **WhatsApp Webhook**: `/whatsapp/*`
- **Monitoring API**: `/monitor/*`

### Container App Configuration

```yaml
name: ai-companion-app
image: yourregistry.azurecr.io/ai-companion:latest
targetPort: 8000
ingress:
  external: true
  transport: auto  # Critical for WebSocket support
```

## Environment Variables

The application requires these key environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| INTERFACE | Interface types to enable (`unified` or `all`) | Yes |
| PORT | Port the application listens on (default: 8000) | Yes |
| QDRANT_URL | Qdrant vector database URL | Yes |
| AZURE_OPENAI_ENDPOINT | Azure OpenAI service endpoint | Yes |
| AZURE_OPENAI_API_KEY | Azure OpenAI API key | Yes |
| AZURE_OPENAI_API_VERSION | Azure OpenAI API version | Yes |
| AZURE_OPENAI_DEPLOYMENT | Azure OpenAI deployment name | Yes |
| AZURE_EMBEDDING_DEPLOYMENT | Azure OpenAI embedding model deployment | Yes |

Example configuration:
```bash
INTERFACE=unified
PORT=8000
QDRANT_URL=https://your-qdrant-instance.cloud.qdrant.io
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com
AZURE_EMBEDDING_DEPLOYMENT=text-embedding-3-small
OPENAI_API_TYPE=azure
OPENAI_API_VERSION=2024-08-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

## WebSocket Support

The application requires WebSocket support for the Chainlit interface. Ensure proper configuration:

1. **Set transport to `auto`**:
   ```powershell
   az containerapp ingress update --name your-app-name --resource-group your-resource-group --transport auto
   ```

2. **Configure CORS for WebSockets**:
   ```powershell
   az containerapp ingress cors update --name your-app-name --resource-group your-resource-group --allowed-origins "*" --allowed-methods "*" --allowed-headers "*" --expose-headers "*" --max-age 7200 --allow-credentials true
   ```

3. **Resource allocation**: Ensure adequate CPU (1.0) and memory (2.0Gi) for WebSocket connections:
   ```powershell
   az containerapp update --name your-app-name --resource-group your-resource-group --cpu 1.0 --memory 2.0Gi
   ```

## Monitoring and Troubleshooting

### View Logs

```bash
# View recent logs
az containerapp logs show --name your-app-name --resource-group your-resource-group --tail 100

# Follow logs in real-time
az containerapp logs show --name your-app-name --resource-group your-resource-group --follow
```

### Check Application Status

```bash
# Check running status
az containerapp show --name your-app-name --resource-group your-resource-group --query "properties.runningStatus"

# Check revision status
az containerapp revision list --name your-app-name --resource-group your-resource-group
```

### Health Checks

Health endpoints for different interfaces:

```
Chainlit Interface: /chat/status
WhatsApp Webhook: /whatsapp/health
Monitoring API: /monitor/health
```

## Common Issues

1. **WebSocket Connection Failures**: If Chainlit shows "Could not reach the server", check:
   - Transport protocol setting (`auto` not `http`)
   - CORS configuration for WebSockets
   - Container resources (CPU/memory)

2. **Resource Allocation**: If the container is crashing, increase resources:
   ```powershell
   az containerapp update --name your-app-name --resource-group your-resource-group --cpu 1.0 --memory 2.0Gi
   ```

3. **Revision Problems**: Create a new revision to apply changes:
   ```powershell
   $timestamp = Get-Date -Format "yyyyMMddHHmmss"
   az containerapp update --name your-app-name --resource-group your-resource-group --revision-suffix "restart$timestamp"
   ```

## For More Information

- [Custom Domain Setup](./custom-domains.md)
- [Scheduled Messaging Deployment](./scheduled-messaging-deployment.md)
- [Troubleshooting Guide](./troubleshooting.md) 