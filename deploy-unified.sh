#!/bin/bash
set -e

# Configuration
RESOURCE_GROUP="evelina-ai-rg"
CONTAINER_APP_NAME="evelina-vnet-app"
ACR_NAME="evelinaai247acr"
IMAGE_NAME="ai-companion"
IMAGE_TAG="unified"

echo "Building unified Docker image..."
docker build -t $ACR_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG -f Dockerfile.unified .

echo "Logging in to Azure Container Registry..."
az acr login --name $ACR_NAME

echo "Pushing image to Azure Container Registry..."
docker push $ACR_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG

echo "Updating Container App..."
az containerapp update \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --image $ACR_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG \
  --set-env-vars INTERFACE=unified PORT=8000

echo "Deployment completed successfully!"
echo "Testing endpoints..."

# Get the FQDN of the Container App
FQDN=$(az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv)

echo "Testing health endpoint..."
curl -I https://$FQDN/health

echo "Testing WhatsApp health endpoint..."
curl -I https://$FQDN/whatsapp/health

echo "Testing Monitor health endpoint..."
curl -I https://$FQDN/monitor/health

echo "Testing Monitor metrics endpoint..."
curl -I https://$FQDN/monitor/metrics

echo "All tests completed. Please verify the responses above." 