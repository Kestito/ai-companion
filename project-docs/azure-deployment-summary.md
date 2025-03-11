# Azure Container App Deployment Summary

## Deployment Information

- **Container App Name**: evelina-vnet-app
- **Resource Group**: evelina-ai-rg
- **Location**: East US
- **Environment**: evelina-env-vnet (VNET-enabled environment)
- **Image**: evelinaai247acr.azurecr.io/ai-companion:latest

## Access URLs

- **Chainlit Interface**: [https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io](https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io)
- **WhatsApp Webhook**: Port 8080 is configured but requires proper DNS configuration to be accessible
- **Monitoring API**: Port 8090 is configured but requires proper DNS configuration to be accessible

## Configuration

The Container App is configured with multiple ports:
- **Main Port (8000)**: Primary port for the Chainlit interface
- **Additional Port (8080)**: For the WhatsApp webhook
- **Additional Port (8090)**: For the Monitoring API

All ports are configured as external, which means they should be accessible from the internet. However, Azure Container Apps with additional port mappings have specific requirements for DNS and networking.

## Special Notes on Multi-Port Configuration

Azure Container Apps with multiple external ports require special DNS configuration. While the main port (8000) is accessible through the default FQDN, the additional ports require additional configuration:

1. **Custom Domain Configuration**: You may need to set up custom domains for the additional ports.
2. **DNS Configuration**: You may need to configure DNS records for the additional ports.

## Environment Variables

All necessary environment variables have been configured, including:
- QDRANT_URL
- QDRANT_API_KEY
- AZURE_OPENAI_API_KEY
- AZURE_OPENAI_ENDPOINT
- AZURE_EMBEDDING_DEPLOYMENT
- INTERFACE=all (This ensures all interfaces are running)
- And many more...

## Monitoring and Troubleshooting

- **View Logs**: `az containerapp logs show --name evelina-vnet-app --resource-group evelina-ai-rg --tail 100`
- **Check Status**: `az containerapp show --name evelina-vnet-app --resource-group evelina-ai-rg --query "properties.runningStatus"`
- **Update Image**: `az containerapp update --name evelina-vnet-app --resource-group evelina-ai-rg --image evelinaai247acr.azurecr.io/ai-companion:latest`

## Next Steps for Port Access

To make the additional ports (8080 and 8090) accessible, you may need to:

1. Set up a custom domain for the Container App
2. Configure DNS records for the additional ports
3. Consider using Azure Front Door or Application Gateway for routing traffic to different ports
4. Alternatively, expose the additional functionality through path-based routing on the main port (e.g., /whatsapp, /monitor) 