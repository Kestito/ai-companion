# Azure Container App Deployment Guide

This guide provides instructions for deploying the AI Companion to Azure Container Apps using the provided deployment scripts and templates.

## Prerequisites

- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed and authenticated
- [Docker](https://www.docker.com/get-started/) installed
- Access to the Azure Container Registry (ACR)
- Azure subscription with permissions to deploy Container Apps

## Deployment Methods

There are three ways to deploy the application:

1. PowerShell script (Windows)
2. Bash script (Linux/macOS)
3. YAML template (all platforms)

## 1. Using the PowerShell Script (Windows)

The `deploy.ps1` script builds and deploys the application in a single step:

```powershell
# From the project root directory
.\deploy.ps1
```

## 2. Using the Bash Script (Linux/macOS)

The `deploy.sh` script builds and deploys the application in a single step:

```bash
# From the project root directory
chmod +x ./deploy.sh
./deploy.sh
```

## 3. Using the YAML Template (All Platforms)

The YAML template provides a declarative way to configure and deploy the application:

```bash
# Build and push the Docker image first
docker build -t evelinaai247acr.azurecr.io/ai-companion:latest .
az acr login --name evelinaai247acr
docker push evelinaai247acr.azurecr.io/ai-companion:latest

# Deploy using the YAML template
az containerapp update -n evelina-vnet-app -g evelina-ai-rg --yaml container-app-template.yaml
```

## Troubleshooting

If you encounter container crashes or deployment issues, refer to the `CONTAINER-CRASH-FIX.md` guide for detailed troubleshooting steps.

### Common Issues

1. **Environment Variables Syntax**: Make sure you're using the correct syntax for environment variables:
   ```
   --set-env-vars KEY1=value1 KEY2=value2
   ```

2. **Resource Allocation**: If your container is crashing, try increasing the CPU and memory:
   ```
   az containerapp update --name evelina-vnet-app --resource-group evelina-ai-rg --cpu 0.5 --memory 1.0Gi
   ```

3. **Checking Container Logs**: Always check logs when troubleshooting:
   ```
   az containerapp logs show --name evelina-vnet-app --resource-group evelina-ai-rg --tail 100
   ```

## Environment Variables Reference

The application requires several environment variables to function correctly:

| Variable | Description | Required |
|----------|-------------|----------|
| INTERFACE | Interface types to enable (all, telegram, whatsapp) | Yes |
| PORT | Port the application listens on | Yes |
| QDRANT_URL | Qdrant vector database URL | Yes |
| AZURE_OPENAI_ENDPOINT | Azure OpenAI service endpoint | Yes |
| AZURE_OPENAI_API_KEY | Azure OpenAI API key | Yes |
| AZURE_OPENAI_API_VERSION | Azure OpenAI API version | Yes |
| AZURE_OPENAI_DEPLOYMENT | Azure OpenAI deployment name | Yes |
| AZURE_EMBEDDING_DEPLOYMENT | Azure OpenAI embedding model deployment | Yes |
| ELEVENLABS_API_KEY | ElevenLabs API key for voice generation | For voice |
| ELEVENLABS_VOICE_ID | ElevenLabs voice ID | For voice |
| STT_MODEL_NAME | Speech-to-Text model name | For voice |
| TTS_MODEL_NAME | Text-to-Speech model name | For voice |

## Additional Resources

- [Azure Container Apps Documentation](https://docs.microsoft.com/en-us/azure/container-apps/)
- [Docker Documentation](https://docs.docker.com/)
- [Azure CLI Documentation](https://docs.microsoft.com/en-us/cli/azure/) 