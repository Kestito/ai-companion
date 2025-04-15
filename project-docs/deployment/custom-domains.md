# Custom Domain Setup for Azure Container Apps

This guide explains how to set up a custom domain for your AI Companion Azure Container App.

## Prerequisites

- An existing Azure Container App with external ingress enabled
- Access to your domain's DNS settings (through your domain registrar or DNS provider)
- Azure CLI installed and logged in (`az login`)

## Step 1: Get the Verification ID

First, you need to obtain the domain verification ID from Azure:

```powershell
# Replace with your values
$resourceGroup = "your-resource-group"
$containerAppName = "your-app-name"
$customDomain = "demo.yourdomain.com"

# Get the verification ID
$verificationId = az containerapp hostname show --resource-group $resourceGroup --name $containerAppName --hostname $customDomain --query "customDomainVerificationId" -o tsv
```

If the domain hasn't been added yet, you can get the general verification ID:

```powershell
$verificationId = az containerapp show --resource-group $resourceGroup --name $containerAppName --query "properties.customDomainVerificationId" -o tsv
```

## Step 2: Configure DNS Records

Add these DNS records at your domain provider:

1. **CNAME Record**:
   - **Name/Host**: `demo` (subdomain part only)
   - **Value/Target**: The FQDN of your Container App (e.g., `your-app.azurecontainerapps.io`)
   - **TTL**: 3600 (or as low as your provider allows)

2. **TXT Record**:
   - **Name/Host**: `asuid.demo`
   - **Value/Content**: The domain verification ID from Step 1
   - **TTL**: 3600 (or as low as your provider allows)

Example commands at your DNS provider might look like:

```
CNAME demo your-app.azurecontainerapps.io
TXT asuid.demo 05716FFDC761E20F2562DBCE353190F09F23B5F71B3602DFF5F71E78F5DC1112
```

> **Note**: DNS changes can take time to propagate (from minutes to up to 48 hours). You can check propagation using tools like [dnschecker.org](https://dnschecker.org).

## Step 3: Add the Custom Domain to Your Container App

After DNS propagation, add the custom domain:

```powershell
# Add custom domain with managed certificate
az containerapp hostname add --resource-group $resourceGroup --name $containerAppName --hostname $customDomain
```

Certificate provisioning can take 5-15 minutes to complete.

## Step 4: Verify Setup

Check that your custom domain has been successfully added:

```powershell
az containerapp hostname list --resource-group $resourceGroup --name $containerAppName
```

Visit your site at `https://demo.yourdomain.com` to confirm it's working.

## Troubleshooting

1. **DNS Not Propagated**: 
   - Wait for DNS changes to propagate
   - Verify DNS records are correctly configured

2. **Domain Validation Fails**:
   - Double-check the TXT record is correctly configured
   - Make sure the TXT record has the correct host (`asuid.demo`)
   - Ensure the TXT record value matches the verification ID exactly

3. **Certificate Not Provisioning**:
   - Certificates can take up to 15 minutes to provision
   - Verify DNS records are correctly configured

## Additional Resources

- [Microsoft Documentation: Custom domain names in Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/custom-domains-managed-certificates)
- [DNS record types and settings](https://docs.microsoft.com/en-us/azure/dns/dns-zones-records) 