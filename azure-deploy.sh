#!/bin/bash

# Azure deployment script for AI Companion
# This script builds and deploys containers to Azure Container Registry with optimizations
# Usage: ./azure-deploy.sh [version]

set -e

# Configuration
ACR_NAME="evelinaacr8677"
VERSION=${1:-"v1.0.$(date +%Y%m%d%H%M)"}
LOCATION="westeurope"
RESOURCE_GROUP="ai-companion-rg"

# Login to Azure if needed
if ! az account show &> /dev/null; then
  echo "Logging in to Azure..."
  az login
fi

# Login to Azure Container Registry
echo "Logging in to Azure Container Registry..."
az acr login --name $ACR_NAME

# Set buildx as default builder for multi-platform support
echo "Setting up Docker buildx..."
docker buildx create --use --name azurebuilder

# Build and push backend image with optimizations
echo "Building and pushing backend image..."
docker buildx build \
  --platform linux/amd64 \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --cache-from $ACR_NAME.azurecr.io/ai-companion:cache \
  --cache-to type=inline \
  --push \
  -t $ACR_NAME.azurecr.io/ai-companion:$VERSION \
  -t $ACR_NAME.azurecr.io/ai-companion:latest \
  -t $ACR_NAME.azurecr.io/ai-companion:cache \
  -f Dockerfile .

# Build and push web-ui image with optimizations
echo "Building and pushing web-ui image..."
docker buildx build \
  --platform linux/amd64 \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --cache-from $ACR_NAME.azurecr.io/web-ui-companion:cache \
  --cache-to type=inline \
  --push \
  -t $ACR_NAME.azurecr.io/web-ui-companion:$VERSION \
  -t $ACR_NAME.azurecr.io/web-ui-companion:latest \
  -t $ACR_NAME.azurecr.io/web-ui-companion:cache \
  -f src/ai_companion/interfaces/web-ui/Dockerfile src/ai_companion/interfaces/web-ui

# Build and push scheduler image with optimizations
echo "Building and pushing scheduler image..."
docker buildx build \
  --platform linux/amd64 \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --cache-from $ACR_NAME.azurecr.io/scheduler-companion:cache \
  --cache-to type=inline \
  --push \
  -t $ACR_NAME.azurecr.io/scheduler-companion:$VERSION \
  -t $ACR_NAME.azurecr.io/scheduler-companion:latest \
  -t $ACR_NAME.azurecr.io/scheduler-companion:cache \
  -f scheduler-container.Dockerfile .

# Update docker-compose.yml with new version
echo "Updating docker-compose.yml with new version..."
sed -i.bak "s/v1.0.[0-9]\+/$VERSION/g" docker-compose.yml
rm docker-compose.yml.bak

# Update Azure Web App for Containers if available
if az webapp list --resource-group $RESOURCE_GROUP --query "[?contains(name, 'ai-companion')]" -o tsv &> /dev/null; then
  echo "Updating Azure Web App with new container versions..."
  
  # Update backend web app
  az webapp config container set \
    --name ai-companion-backend \
    --resource-group $RESOURCE_GROUP \
    --docker-custom-image-name $ACR_NAME.azurecr.io/ai-companion:$VERSION \
    --docker-registry-server-url https://$ACR_NAME.azurecr.io
  
  # Update frontend web app
  az webapp config container set \
    --name ai-companion-frontend \
    --resource-group $RESOURCE_GROUP \
    --docker-custom-image-name $ACR_NAME.azurecr.io/web-ui-companion:$VERSION \
    --docker-registry-server-url https://$ACR_NAME.azurecr.io
    
  # Update scheduler web app
  az webapp config container set \
    --name ai-companion-scheduler \
    --resource-group $RESOURCE_GROUP \
    --docker-custom-image-name $ACR_NAME.azurecr.io/scheduler-companion:$VERSION \
    --docker-registry-server-url https://$ACR_NAME.azurecr.io
fi

echo "Deployment completed successfully!"
echo "Container versions: $VERSION"
echo "To run locally with new images, use: docker-compose up -d" 