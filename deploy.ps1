# Set variables
$IMAGE_NAME = "ai-companion"
$TAG = "latest"
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

Write-Host "=== Setting container scale settings ===" -ForegroundColor Green
az containerapp update `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --min-replicas 1 `
  --max-replicas 10

Write-Host "=== Deployment completed ===" -ForegroundColor Green
Write-Host "Your application is now updated at: https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io" -ForegroundColor Cyan

Write-Host "=== Next Steps ===" -ForegroundColor Yellow
Write-Host "1. Check container logs: az containerapp logs show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --tail 100" -ForegroundColor White
Write-Host "2. If still crashing, run: az containerapp update --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --cpu 0.5 --memory 1.0Gi" -ForegroundColor White
Write-Host "3. View revision history: az containerapp revision list --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP" -ForegroundColor White 