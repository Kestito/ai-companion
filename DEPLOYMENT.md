# Deployment Guide for AI Companion Voice Message Feature

This guide will help you deploy the voice message feature changes to your Azure Container App.

## Prerequisites

- Docker installed on your local machine
- Azure CLI installed and configured
- Access to the Azure Container Registry (evelinaai247acr.azurecr.io)
- Proper permissions to update the Container App

## What Changed?

The following features were updated:

1. **Voice Message Handling**:
   - When users send voice messages to Telegram or WhatsApp, they now receive both:
     - A voice response (AI's response converted to speech)
     - A text response with the same content

2. **Improved Error Handling**:
   - Better fallback to text-only responses if voice synthesis fails
   - Proper caption handling for voice messages

## Deployment Steps

### Option 1: Using PowerShell (Windows)

1. Navigate to the project directory:
   ```powershell
   cd path\to\ai-companion
   ```

2. Run the deployment script:
   ```powershell
   .\deploy.ps1
   ```

3. Follow the prompts to authenticate with Azure if needed.

### Option 2: Using Bash (Linux/Mac)

1. Navigate to the project directory:
   ```bash
   cd path/to/ai-companion
   ```

2. Run the deployment script:
   ```bash
   ./deploy.sh
   ```

3. Follow the prompts to authenticate with Azure if needed.

### Manual Deployment

If you prefer to deploy manually, follow these steps:

1. Build the Docker image:
   ```bash
   docker build -t evelinaai247acr.azurecr.io/ai-companion:latest .
   ```

2. Login to Azure:
   ```bash
   az login
   ```

3. Login to Azure Container Registry:
   ```bash
   az acr login --name evelinaai247acr
   ```

4. Push the Docker image:
   ```bash
   docker push evelinaai247acr.azurecr.io/ai-companion:latest
   ```

5. Update the Container App:
   ```bash
   az containerapp update \
     --name evelina-vnet-app \
     --resource-group evelina-ai-rg \
     --image evelinaai247acr.azurecr.io/ai-companion:latest
   ```

## Verifying the Deployment

1. Check the deployment status:
   ```bash
   az containerapp show \
     --name evelina-vnet-app \
     --resource-group evelina-ai-rg \
     --query "properties.runningStatus"
   ```

2. View the logs to ensure proper startup:
   ```bash
   az containerapp logs show \
     --name evelina-vnet-app \
     --resource-group evelina-ai-rg \
     --tail 100
   ```

3. Test the voice message feature:
   - Send a voice message to your Telegram bot
   - Send a voice message to your WhatsApp number
   - Verify you receive both voice and text responses

## Rollback Procedure

If you need to rollback to a previous version:

1. Find the previous image tag:
   ```bash
   az acr repository show-tags --name evelinaai247acr --repository ai-companion
   ```

2. Update the Container App to use the previous image:
   ```bash
   az containerapp update \
     --name evelina-vnet-app \
     --resource-group evelina-ai-rg \
     --image evelinaai247acr.azurecr.io/ai-companion:previous-tag
   ```

## Troubleshooting

If you encounter issues after deployment:

1. Check the application logs:
   ```bash
   az containerapp logs show \
     --name evelina-vnet-app \
     --resource-group evelina-ai-rg \
     --follow
   ```

2. Verify environment variables are properly set:
   ```bash
   az containerapp show \
     --name evelina-vnet-app \
     --resource-group evelina-ai-rg \
     --query "properties.template.containers[0].env"
   ```

3. Check if the services are healthy:
   ```bash
   curl -I https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/whatsapp/health
   ```

## Contact

If you need further assistance, please contact the development team. 