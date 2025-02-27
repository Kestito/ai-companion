# Azure Deployment Guide

## Overview

This document describes the deployment of the AI Companion application on Azure Container Apps with path-based routing for all interfaces.

## Deployment Architecture

The application is deployed as a single Container App with path-based routing:

- **Base URL**: https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io
- **Chainlit Interface**: `/` (root path)
- **WhatsApp Webhook**: `/whatsapp/*`
- **Monitoring API**: `/monitor/*`

## Container App Configuration

### Environment Details

```bash
# Environment Name: evelina-env-vnet
# Resource Group: evelina-ai-rg
# Location: East US
```

### Container App Details

```yaml
name: evelina-vnet-app
image: evelinaai247acr.azurecr.io/ai-companion:latest
targetPort: 8000
ingress:
  external: true
  transport: auto
```

### Environment Variables

```bash
INTERFACE=unified
PORT=8000
QDRANT_URL=https://b88198bc-6212-4390-bbac-b1930f543812.europe-west3-0.gcp.cloud.qdrant.io
AZURE_OPENAI_ENDPOINT=https://ai-kestutis9429ai265477517797.openai.azure.com
AZURE_EMBEDDING_DEPLOYMENT=text-embedding-3-small
OPENAI_API_TYPE=azure
OPENAI_API_VERSION=2024-08-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

## Path-Based Routing Configuration

### WhatsApp Webhook Configuration

The WhatsApp webhook is now accessible through path-based routing:

```plaintext
Webhook URL: https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/whatsapp/webhook
Health Check: https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/whatsapp/health
```

### Monitoring API Configuration

The monitoring interface is accessible through path-based routing:

```plaintext
API Base URL: https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/monitor
Health Check: https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/monitor/health
Metrics: https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/monitor/metrics
```

## Deployment Commands

### Initial Deployment

```bash
# Create VNET and subnet
az network vnet create \
  --name evelina-vnet \
  --resource-group evelina-ai-rg \
  --location eastus \
  --address-prefix 10.0.0.0/16 \
  --subnet-name evelina-subnet \
  --subnet-prefix 10.0.0.0/23

# Create Container App Environment
az containerapp env create \
  --name evelina-env-vnet \
  --resource-group evelina-ai-rg \
  --location eastus \
  --infrastructure-subnet-resource-id /subscriptions/7bf9df5a-7a8c-42dc-ad54-81aa4bf09b3e/resourceGroups/evelina-ai-rg/providers/Microsoft.Network/virtualNetworks/evelina-vnet/subnets/evelina-subnet

# Deploy Container App
az containerapp create \
  --name evelina-vnet-app \
  --resource-group evelina-ai-rg \
  --environment evelina-env-vnet \
  --image evelinaai247acr.azurecr.io/ai-companion:latest \
  --target-port 8000 \
  --ingress external \
  --env-vars INTERFACE=unified PORT=8000
```

### Update Deployment

```bash
# Update Container App
az containerapp update \
  --name evelina-vnet-app \
  --resource-group evelina-ai-rg \
  --image evelinaai247acr.azurecr.io/ai-companion:latest \
  --set-env-vars INTERFACE=unified PORT=8000
```

## Monitoring and Troubleshooting

### View Logs

```bash
# View recent logs
az containerapp logs show \
  --name evelina-vnet-app \
  --resource-group evelina-ai-rg \
  --tail 100

# Follow logs in real-time
az containerapp logs show \
  --name evelina-vnet-app \
  --resource-group evelina-ai-rg \
  --follow
```

### Check Application Status

```bash
# Check running status
az containerapp show \
  --name evelina-vnet-app \
  --resource-group evelina-ai-rg \
  --query "properties.runningStatus"

# Check revision status
az containerapp revision list \
  --name evelina-vnet-app \
  --resource-group evelina-ai-rg
```

### Health Checks

```bash
# Test Chainlit interface
curl -I https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io

# Test WhatsApp webhook
curl -I https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/whatsapp/health

# Test Monitoring API
curl -I https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/monitor/health
```

## Security Considerations

1. **Environment Variables**: All sensitive information is stored as environment variables
2. **Network Security**: Using VNET integration for enhanced security
3. **HTTPS**: All endpoints are HTTPS-only
4. **Authentication**: WhatsApp webhook uses token verification

## Backup and Recovery

### Backup Environment Variables

```bash
# Export environment variables
az containerapp show \
  --name evelina-vnet-app \
  --resource-group evelina-ai-rg \
  --query "properties.template.containers[0].env" > env_backup.json
```

### Restore from Backup

```bash
# Restore environment variables
az containerapp update \
  --name evelina-vnet-app \
  --resource-group evelina-ai-rg \
  --set-env-vars @env_backup.json
``` 