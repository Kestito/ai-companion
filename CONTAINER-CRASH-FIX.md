# Troubleshooting Container Crashes in Azure Container Apps

This guide helps you diagnose and fix container crashes in your Azure Container App deployments.

## Symptoms

Your Azure Container App is showing one of these status messages:
- "Failed - Container crashing"
- "Activation failed"
- "Container crashed"
- "Unhealthy"

## Step 1: Check Container Logs

First, retrieve the logs to understand what's causing the crashes:

```bash
# Get logs from the running container
az containerapp logs show --name evelina-vnet-app --resource-group evelina-ai-rg --tail 100

# If the above doesn't work, try this to get revision logs
az containerapp revision list --name evelina-vnet-app --resource-group evelina-ai-rg
az containerapp revision logs show --name evelina-vnet-app --resource-group evelina-ai-rg --revision YOUR_REVISION_NAME --tail 100
```

## Step 2: Common Causes and Solutions

### 1. Missing Environment Variables

**Solution:** Update your container app with all required environment variables using the correct syntax:

```bash
az containerapp update \
  --name evelina-vnet-app \
  --resource-group evelina-ai-rg \
  --set-env-vars \
    INTERFACE=all \
    PORT=8000 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    AZURE_OPENAI_API_KEY=YOUR_API_KEY \
    AZURE_OPENAI_ENDPOINT=YOUR_ENDPOINT \
    ELEVENLABS_API_KEY=YOUR_API_KEY \
    ELEVENLABS_VOICE_ID=YOUR_VOICE_ID \
    STT_MODEL_NAME=whisper \
    TTS_MODEL_NAME=eleven_flash_v2_5
```

### 2. Insufficient Resources

**Solution:** Increase CPU and memory allocation:

```bash
az containerapp update \
  --name evelina-vnet-app \
  --resource-group evelina-ai-rg \
  --cpu 0.5 \
  --memory 1.0Gi
```

### 3. Startup Command Issues

**Solution:** Specify a custom startup command:

```bash
az containerapp update \
  --name evelina-vnet-app \
  --resource-group evelina-ai-rg \
  --command "/app/start.sh"
```

### 4. Missing Dependencies in Dockerfile

**Solution:** Verify your Dockerfile includes all necessary dependencies:

- Check if all Python packages are installed
- Ensure all system dependencies are installed
- Update the OS packages before installing dependencies

Example fix for a Python application:

```dockerfile
# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    curl \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*
```

### 5. Port Configuration Issues

**Solution:** Ensure your app listens on the correct port:

```bash
az containerapp update \
  --name evelina-vnet-app \
  --resource-group evelina-ai-rg \
  --set-env-vars PORT=8000 INTERFACE=all
```

## Step 3: Try a Clean Deployment

If all else fails, try a clean deployment with minimal configuration:

```bash
az containerapp update \
  --name evelina-vnet-app \
  --resource-group evelina-ai-rg \
  --image evelinaai247acr.azurecr.io/ai-companion:latest \
  --min-replicas 1 \
  --max-replicas 1 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --set-env-vars INTERFACE=all PORT=8000 PYTHONUNBUFFERED=1
```

Then add other environment variables once the basic container is stable.

## Step 4: Health Check Troubleshooting

If your app is failing health checks:

1. Review the healthcheck in your Dockerfile:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 CMD ["/app/healthcheck.sh"]
```

2. Make sure your app implements the health endpoints correctly:
   - `/health` or `/whatsapp/health` for the main API
   - Make sure they return HTTP 200 when healthy

## Step 5: Contact Support

If none of the above solutions work, reach out to Azure support with:
- Your latest container logs
- Your Dockerfile
- The resource allocation for your container app 