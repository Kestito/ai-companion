# Deploy Backend Update to Azure Container Apps
# This script builds and deploys backend changes to Azure

$RESOURCE_GROUP = "evelina-rg-20250308115110"
$CONTAINER_APP_NAME = "backend-app"
$IMAGE_NAME = "ai-companion-backend"
$ACR_NAME = "evelinaacr"
$TAG = "latest"

Write-Host "Building and deploying backend update..." -ForegroundColor Cyan

# Build and push the Docker image
try {
    # Login to Azure Container Registry
    Write-Host "Logging in to Azure Container Registry..." -ForegroundColor Yellow
    az acr login --name $ACR_NAME
    
    # Build the Docker image using our custom Dockerfile
    Write-Host "Building Docker image..." -ForegroundColor Yellow
    docker build -t "$ACR_NAME.azurecr.io/$IMAGE_NAME`:$TAG" -f backend.Dockerfile .
    
    # Push the image to ACR
    Write-Host "Pushing image to ACR..." -ForegroundColor Yellow
    docker push "$ACR_NAME.azurecr.io/$IMAGE_NAME`:$TAG"
    
    # Update the container app
    Write-Host "Updating container app..." -ForegroundColor Yellow
    az containerapp update `
        --name $CONTAINER_APP_NAME `
        --resource-group $RESOURCE_GROUP `
        --image "$ACR_NAME.azurecr.io/$IMAGE_NAME`:$TAG"
    
    # Restart the app
    Write-Host "Restarting container app..." -ForegroundColor Yellow
    az containerapp restart --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP
    
    Write-Host "Backend update deployed successfully!" -ForegroundColor Green
} 
catch {
    Write-Host "Error updating backend: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`nTo test the new API endpoint:" -ForegroundColor Cyan
Write-Host "1. Wait a few minutes for the container to restart" -ForegroundColor Cyan
Write-Host "2. Try sending a message with this curl command:" -ForegroundColor Cyan
Write-Host "   curl -X POST 'https://backend-app.redstone-957fece8.eastus.azurecontainerapps.io/monitor/telegram/send-message?message_id=cdc2da11-5f9e-4e01-aba5-1c2f63f24f05'" -ForegroundColor White

Write-Host "`nOr use the web UI to click the 'Send Now' button on a pending message" -ForegroundColor Cyan 