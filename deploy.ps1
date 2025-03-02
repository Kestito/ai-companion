# Set variables
$IMAGE_NAME = "ai-companion"
$TAG = "v1.0.10"
$ACR_NAME = "evelinaai247acr"
$RESOURCE_GROUP = "evelina-ai-rg"
$CONTAINER_APP_NAME = "evelina-vnet-app"

Write-Host "=== Building Docker image ===" -ForegroundColor Green
docker build -t "$ACR_NAME.azurecr.io/$IMAGE_NAME`:$TAG" .

Write-Host "=== Logging in to Azure ===" -ForegroundColor Green

Write-Host "=== Logging in to Azure Container Registry ===" -ForegroundColor Green
az acr login --name $ACR_NAME

Write-Host "=== Pushing image to Azure Container Registry ===" -ForegroundColor Green
docker push "$ACR_NAME.azurecr.io/$IMAGE_NAME`:$TAG"

Write-Host "=== Updating Container App with new image and proper environment variables ===" -ForegroundColor Green
az containerapp update `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --image "$ACR_NAME.azurecr.io/$IMAGE_NAME`:$TAG" `
  --set-env-vars `
    INTERFACE=all `
    PORT=8000 `
    QDRANT_URL=https://b88198bc-6212-4390-bbac-b1930f543812.europe-west3-0.gcp.cloud.qdrant.io `
    QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwiZXhwIjoxNzQ3MDY5MzcyfQ.plLwDbnIi7ggn_d98e-OsxpF60lcNq9nzZ0EzwFAnQw `
    AZURE_OPENAI_ENDPOINT=https://ai-kestutis9429ai265477517797.openai.azure.com `
    AZURE_OPENAI_API_KEY=Ec1hyYbP5j6AokTzLWtc3Bp970VbCnpRMhNmQjxgJh1LrYzlsrrOJQQJ99ALACHYHv6XJ3w3AAAAACOG0Kyl `
    AZURE_OPENAI_API_VERSION=2024-08-01-preview `
    AZURE_OPENAI_DEPLOYMENT=gpt-4o `
    AZURE_EMBEDDING_DEPLOYMENT=text-embedding-3-small `
    OPENAI_API_TYPE=azure `
    OPENAI_API_VERSION=2024-08-01-preview `
    EMBEDDING_MODEL=text-embedding-3-small `
    LLM_MODEL=gpt-4o `
    SUPABASE_URL=https://aubulhjfeszmsheonmpy.supabase.co `
    SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc `
    COLLECTION_NAME=Information `
    ELEVENLABS_API_KEY=sk_f8aaf95ce7c9bc93c1341eded4014382cd6444e84cb5c03d `
    ELEVENLABS_VOICE_ID=qSfcmCS9tPikUrDxO8jt `
    PYTHONUNBUFFERED=1 `
    PYTHONPATH=/app `
    STT_MODEL_NAME=whisper `
    TTS_MODEL_NAME=eleven_flash_v2_5

Write-Host "=== Setting container resources and scale settings ===" -ForegroundColor Green
az containerapp update `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --min-replicas 1 `
  --max-replicas 10 `
  --cpu 1.0 `
  --memory 2.0Gi

Write-Host "=== Configuring ingress for WebSocket support ===" -ForegroundColor Green
az containerapp ingress update `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --target-port 8000 `
  --transport auto

Write-Host "=== Configuring CORS policy for WebSocket support ===" -ForegroundColor Green
az containerapp ingress cors update `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --allowed-origins "*" `
  --allowed-methods "*" `
  --allowed-headers "*" `
  --expose-headers "*" `
  --max-age 7200 `
  --allow-credentials true

Write-Host "=== Creating a new revision to apply changes ===" -ForegroundColor Green
az containerapp update `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --revision-suffix "websocket-fix-$(Get-Date -Format 'yyyyMMddHHmmss')"

Write-Host "=== Deployment completed ===" -ForegroundColor Green
Write-Host "Your application is now updated at: https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io" -ForegroundColor Cyan
Write-Host "Chainlit interface is available directly at the root URL: https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/" -ForegroundColor Cyan
Write-Host "  - Status: https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/chat/status" -ForegroundColor Cyan
Write-Host "Monitoring interface is available at: https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/health/" -ForegroundColor Cyan
Write-Host "  - Metrics: https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/health/metrics" -ForegroundColor Cyan
Write-Host "  - Report: https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/health/report" -ForegroundColor Cyan

Write-Host "=== Next Steps ===" -ForegroundColor Yellow
Write-Host "1. Check container logs: az containerapp logs show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --tail 100" -ForegroundColor White
Write-Host "2. If still experiencing issues, try creating a new revision: az containerapp update --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --revision-suffix restart-$(Get-Date -Format 'yyyyMMddHHmmss')" -ForegroundColor White
Write-Host "3. View revision history: az containerapp revision list --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP" -ForegroundColor White 