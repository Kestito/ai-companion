# Custom Domain Setup for Azure Container Apps

This guide explains how to set up a custom domain (demo.evelinaai.com) for your Azure Container App.

## Prerequisites

- An existing Azure Container App with external ingress enabled
- Access to your domain's DNS settings (through your domain registrar or DNS provider)
- Azure CLI installed and logged in (`az login`)

## Step 1: Check Current Setup

First, run the provided script to check the current status of your custom domain setup:

```powershell
./check-custom-domain.ps1
```

This script will:
- Verify if your Container App exists
- Show the current FQDN of your Container App
- Provide the domain verification ID needed for DNS setup
- Check if your DNS is correctly configured
- Check if the custom domain is already set up in Azure

## Step 2: Configure DNS Records

Before you can add a custom domain to your Container App, you need to configure DNS records to prove you own the domain and to route traffic correctly.

For the subdomain `demo.evelinaai.com`, you need to add these records at your DNS provider:

1. **CNAME Record**:
   - **Name/Host**: `demo`
   - **Value/Target**: The FQDN of your Container App (e.g., `frontend-app.redstone-957fece8.eastus.azurecontainerapps.io`)
   - **TTL**: 3600 (or as low as your provider allows)

2. **TXT Record**:
   - **Name/Host**: `asuid.demo`
   - **Value/Content**: The domain verification ID from Step 1
   - **TTL**: 3600 (or as low as your provider allows)

Example commands at your DNS provider might look like:

```
CNAME demo frontend-app.redstone-957fece8.eastus.azurecontainerapps.io
TXT asuid.demo 05716FFDC761E20F2562DBCE353190F09F23B5F71B3602DFF5F71E78F5DC1112
```

> **Note**: DNS changes can take time to propagate (from minutes to up to 48 hours). You can check propagation using tools like [dnschecker.org](https://dnschecker.org).

## Step 3: Add the Custom Domain to Your Container App

Once your DNS records are configured, run the setup script:

```powershell
./setup-custom-domain.ps1
```

This script will:
1. Verify your DNS records are properly configured
2. Add the custom domain to your Container App
3. Configure a free managed TLS/SSL certificate for secure HTTPS access
4. Check the status of the custom domain binding

The certificate provisioning process can take 5-15 minutes to complete.

## Step 4: Verify the Setup

After setup is complete, verify that your custom domain is working:

```powershell
./check-custom-domain.ps1
```

You should also be able to visit your site at `https://demo.evelinaai.com` once the certificate is fully provisioned.

## Troubleshooting

### Common Issues:

1. **DNS Not Propagated**: 
   - Wait for DNS changes to propagate
   - Verify your DNS records are set correctly at your domain provider

2. **Domain Validation Fails**:
   - Double-check your TXT record is correctly configured
   - Make sure the TXT record has the correct host (`asuid.demo`)
   - Ensure the TXT record value matches the verification ID exactly

3. **Certificate Not Provisioning**:
   - Certificates can take up to 15 minutes to provision
   - Make sure your DNS records are correctly configured
   - Verify your Container App has external ingress enabled

4. **Container App Not Accessible**:
   - Check if your Container App is running properly by accessing its original FQDN
   - Verify the Container App ingress is configured correctly

### Manual Custom Domain Configuration (Azure Portal)

If you prefer using the Azure Portal instead of scripts:

1. Go to the Azure Portal (portal.azure.com)
2. Navigate to your Container App resource
3. Select "Custom domains" in the left menu
4. Click "Add custom domain"
5. Follow the prompts to add your domain and configure your certificate

## Technical Notes

- Azure Container Apps uses Azure-managed certificates, which are automatically renewed
- The certificates use the ACME protocol with Let's Encrypt as the provider
- Each certificate is valid for 90 days and is automatically renewed by Azure
- Your Container App Environment must have external ingress enabled

## Additional Resources

- [Microsoft Documentation: Custom domain names in Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/custom-domains-managed-certificates)
- [Custom domain verification in Azure](https://docs.microsoft.com/en-us/azure/app-service/app-service-web-tutorial-custom-domain)
- [DNS record types](https://docs.microsoft.com/en-us/azure/dns/dns-zones-records) 