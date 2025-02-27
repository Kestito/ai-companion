# Configuration
$RESOURCE_GROUP = "evelina-ai-rg"
$CONTAINER_APP_NAME = "evelina-vnet-app"
$ACR_NAME = "evelinaai247acr"
$IMAGE_NAME = "ai-companion"
$IMAGE_TAG = "unified"

Write-Host "Building unified Docker image..." -ForegroundColor Green
docker build -t "$ACR_NAME.azurecr.io/$IMAGE_NAME`:$IMAGE_TAG" -f Dockerfile.unified .

Write-Host "Logging in to Azure Container Registry..." -ForegroundColor Green
az acr login --name $ACR_NAME

Write-Host "Pushing image to Azure Container Registry..." -ForegroundColor Green
docker push "$ACR_NAME.azurecr.io/$IMAGE_NAME`:$IMAGE_TAG"

Write-Host "Updating Container App..." -ForegroundColor Green
az containerapp update `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --image "$ACR_NAME.azurecr.io/$IMAGE_NAME`:$IMAGE_TAG" `
  --set-env-vars INTERFACE=unified PORT=8000

Write-Host "Deployment completed successfully!" -ForegroundColor Green
Write-Host "Testing endpoints..." -ForegroundColor Yellow

# Get the FQDN of the Container App
$FQDN = (az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv).Trim()

Write-Host "`nTesting health endpoint..." -ForegroundColor Cyan
Invoke-WebRequest -Uri "https://$FQDN/health" -Method HEAD

Write-Host "`nTesting WhatsApp health endpoint..." -ForegroundColor Cyan
Invoke-WebRequest -Uri "https://$FQDN/whatsapp/health" -Method HEAD

Write-Host "`nTesting Monitor health endpoint..." -ForegroundColor Cyan
Invoke-WebRequest -Uri "https://$FQDN/monitor/health" -Method HEAD

Write-Host "`nTesting Monitor metrics endpoint..." -ForegroundColor Cyan
Invoke-WebRequest -Uri "https://$FQDN/monitor/metrics" -Method HEAD

Write-Host "`nAll tests completed. Please verify the responses above." -ForegroundColor Green 