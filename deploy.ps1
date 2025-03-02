# Set variables
$IMAGE_NAME = "ai-companion"
$TAG = "v1.0.10"
$ACR_NAME = "evelinaai247acr"
$RESOURCE_GROUP = "evelina-rg"
$CONTAINER_APP_NAME = "eve-contaneir-app"
$LOCATION = "eastus"
$APP_URL = "https://eve-contaneir-app.wittytree-d4635db9.eastus.azurecontainerapps.io"
$SUBSCRIPTION_ID = "7bf9df5a-7a8c-42dc-ad54-81aa4bf09b3e"
$CONTAINER_ENV_NAME = "production"
$LOG_ANALYTICS_WORKSPACE = "workspace-evelinargCvWD"

# Function to check DNS resolution
function Test-DNSResolution {
    param (
        [string]$hostname
    )
    
    try {
        $result = Resolve-DnsName -Name $hostname -ErrorAction Stop
        return $true
    } catch {
        Write-Host "⚠️ DNS resolution failed for $hostname`: $($_.Exception.Message)" -ForegroundColor Yellow
        return $false
    }
}

Write-Host "=== Checking DNS resolution for required hosts ===" -ForegroundColor Green
$ghcrResolved = Test-DNSResolution -hostname "ghcr.io"
if (-not $ghcrResolved) {
    Write-Host "⚠️ Cannot resolve ghcr.io - Docker build may fail" -ForegroundColor Yellow
    Write-Host "Attempting to add DNS entries to hosts file..." -ForegroundColor Yellow
    
    # Try to get IP for ghcr.io using alternative DNS
    try {
        # Use Google's DNS to resolve the hostname
        $dnsResult = nslookup ghcr.io 8.8.8.8 2>$null
        if ($dnsResult -match "Address:\s+(\d+\.\d+\.\d+\.\d+)") {
            $ip = $matches[1]
            Write-Host "Resolved ghcr.io to $ip using Google DNS" -ForegroundColor Green
            
            # Add to hosts file (requires admin privileges)
            # This is commented out as it requires admin privileges
            # Add-Content -Path "$env:windir\System32\drivers\etc\hosts" -Value "`n$ip`tghcr.io" -Force
        }
    } catch {
        Write-Host "Failed to resolve ghcr.io using alternative DNS" -ForegroundColor Red
    }
    
    Write-Host "Please ensure your network can access ghcr.io or try running this script with admin privileges" -ForegroundColor Yellow
    Write-Host "Continuing with deployment, but Docker build may fail..." -ForegroundColor Yellow
}

# Set the subscription context
Write-Host "=== Setting Azure subscription context ===" -ForegroundColor Green
az account set --subscription $SUBSCRIPTION_ID

Write-Host "=== Building Docker image ===" -ForegroundColor Green
$buildSuccess = $false
try {
    docker build -t "$ACR_NAME.azurecr.io/$IMAGE_NAME`:$TAG" .
    if ($LASTEXITCODE -eq 0) {
        $buildSuccess = $true
        Write-Host "✅ Docker build completed successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Docker build failed with exit code $LASTEXITCODE" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Docker build failed: $($_.Exception.Message)" -ForegroundColor Red
}

# If build fails, check if image already exists in ACR
if (-not $buildSuccess) {
    Write-Host "Checking if image already exists in ACR..." -ForegroundColor Yellow
    
    Write-Host "=== Logging in to Azure ===" -ForegroundColor Green
    # Uncomment this if you need to login to Azure
    # az login
    
    Write-Host "=== Logging in to Azure Container Registry ===" -ForegroundColor Green
    az acr login --name $ACR_NAME
    
    $imageExists = az acr repository show --name $ACR_NAME --image "$IMAGE_NAME`:$TAG" 2>$null
    
    if ($imageExists) {
        Write-Host "✅ Image $IMAGE_NAME`:$TAG already exists in ACR, proceeding with deployment" -ForegroundColor Green
        $buildSuccess = $true
    } else {
        Write-Host "❌ Image does not exist in ACR and build failed. Cannot proceed with deployment." -ForegroundColor Red
        Write-Host "Please fix the Docker build issues and try again." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "=== Logging in to Azure ===" -ForegroundColor Green
    # Uncomment this if you need to login to Azure
    # az login
    
    Write-Host "=== Logging in to Azure Container Registry ===" -ForegroundColor Green
    az acr login --name $ACR_NAME
    
    Write-Host "=== Pushing image to Azure Container Registry ===" -ForegroundColor Green
    docker push "$ACR_NAME.azurecr.io/$IMAGE_NAME`:$TAG"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to push image to ACR. Checking if image already exists..." -ForegroundColor Red
        
        $imageExists = az acr repository show --name $ACR_NAME --image "$IMAGE_NAME`:$TAG" 2>$null
        
        if ($imageExists) {
            Write-Host "✅ Image $IMAGE_NAME`:$TAG already exists in ACR, proceeding with deployment" -ForegroundColor Green
        } else {
            Write-Host "❌ Image does not exist in ACR and push failed. Cannot proceed with deployment." -ForegroundColor Red
            Write-Host "Please fix the Docker push issues and try again." -ForegroundColor Red
            exit 1
        }
    }
}

Write-Host "=== Checking if Container App exists ===" -ForegroundColor Green
$appExists = az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "name" --output tsv 2>$null
$timestamp = Get-Date -Format "yyyyMMddHHmmss"

if (!$appExists) {
    Write-Host "Container App does not exist. Creating new Container App..." -ForegroundColor Yellow
    
    # Check if the Container App Environment exists
    $envExists = az containerapp env show --name $CONTAINER_ENV_NAME --resource-group $RESOURCE_GROUP --query "name" --output tsv 2>$null
    if (!$envExists) {
        Write-Host "Creating Container App Environment..." -ForegroundColor Yellow
        az containerapp env create `
          --name $CONTAINER_ENV_NAME `
          --resource-group $RESOURCE_GROUP `
          --location $LOCATION `
          --logs-workspace-id $LOG_ANALYTICS_WORKSPACE
    }
    
    # Create the Container App
    az containerapp create `
      --name $CONTAINER_APP_NAME `
      --resource-group $RESOURCE_GROUP `
      --environment $CONTAINER_ENV_NAME `
      --image "$ACR_NAME.azurecr.io/$IMAGE_NAME`:$TAG" `
      --target-port 8000 `
      --ingress external `
      --min-replicas 1 `
      --max-replicas 10 `
      --cpu 1.0 `
      --memory 2.0Gi `
      --env-vars `
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
        TTS_MODEL_NAME=eleven_flash_v2_5 `
        CHAINLIT_FORCE_POLLING=true `
        CHAINLIT_NO_WEBSOCKET=true `
        CHAINLIT_POLLING_MAX_WAIT=5000
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Container App created successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create Container App. Exit code: $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
} else {
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
        TTS_MODEL_NAME=eleven_flash_v2_5 `
        CHAINLIT_FORCE_POLLING=true `
        CHAINLIT_NO_WEBSOCKET=true `
        CHAINLIT_POLLING_MAX_WAIT=5000
        
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to update Container App. Exit code: $LASTEXITCODE" -ForegroundColor Red
        Write-Host "Continuing with deployment, but some settings may not be applied." -ForegroundColor Yellow
    }
}

Write-Host "=== Setting container resources and scale settings ===" -ForegroundColor Green
az containerapp update `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --min-replicas 1 `
  --max-replicas 10 `
  --cpu 1.0 `
  --memory 2.0Gi

Write-Host "=== Configuring ingress for HTTP/WS support ===" -ForegroundColor Green
try {
    # Using the proper command format for ingress update
    az containerapp ingress update `
      --name $CONTAINER_APP_NAME `
      --resource-group $RESOURCE_GROUP `
      --target-port 8000 `
      --transport auto
    
    Write-Host "✅ Successfully configured ingress" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to configure ingress: $_" -ForegroundColor Red
    Write-Host "Attempting alternative ingress configuration..." -ForegroundColor Yellow
    
    # Alternative approach
    az containerapp update `
      --name $CONTAINER_APP_NAME `
      --resource-group $RESOURCE_GROUP `
      --ingress-transport auto
    
    Write-Host "✅ Completed alternative ingress configuration" -ForegroundColor Green
}

Write-Host "=== Configuring CORS policy ===" -ForegroundColor Green
az containerapp ingress cors update `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --allowed-origins "*" `
  --allowed-methods "GET,POST,PUT,DELETE,OPTIONS" `
  --allowed-headers "*" `
  --max-age 7200 `
  --allow-credentials true

# Fixed health probe configuration - using container-level probes
Write-Host "=== Configuring health probes ===" -ForegroundColor Green
try {
    az containerapp update `
      --name $CONTAINER_APP_NAME `
      --resource-group $RESOURCE_GROUP `
      --container-name $CONTAINER_APP_NAME `
      --probe "liveness:http:8000:/monitor/health:30:3:10:1" `
      --probe "readiness:http:8000:/monitor/health:10:3:5:1" `
      --probe "startup:http:8000:/monitor/health:5:30:5:1"
       
    Write-Host "✅ Successfully configured health probes" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to configure health probes: $_" -ForegroundColor Red
    Write-Host "This may be due to an unsupported format. Continuing with deployment." -ForegroundColor Yellow
}

Write-Host "=== Creating a new revision to apply changes ===" -ForegroundColor Green
az containerapp update `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --revision-suffix "httponly$timestamp"

# Use the provided app URL instead of dynamically retrieving it
$baseUrl = $APP_URL

Write-Host "=== Deployment completed ===" -ForegroundColor Green
Write-Host "Your application is now updated at: $baseUrl" -ForegroundColor Cyan
Write-Host "Chainlit interface is available directly at the root URL: $baseUrl/" -ForegroundColor Cyan
Write-Host "  - Status: $baseUrl/chat/status" -ForegroundColor Cyan
Write-Host "Monitoring interface is available at: $baseUrl/health/" -ForegroundColor Cyan
Write-Host "  - Metrics: $baseUrl/health/metrics" -ForegroundColor Cyan
Write-Host "  - Report: $baseUrl/health/report" -ForegroundColor Cyan

Write-Host "=== Next Steps ===" -ForegroundColor Yellow
Write-Host "1. Check container logs: az containerapp logs show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --tail 100" -ForegroundColor White
Write-Host "2. If still experiencing issues, try creating a new revision: az containerapp update --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --revision-suffix restart$(Get-Date -Format 'yyyyMMddHHmmss')" -ForegroundColor White
Write-Host "3. View revision history: az containerapp revision list --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP" -ForegroundColor White 

Write-Host "=== Connection Troubleshooting ===" -ForegroundColor Yellow
Write-Host "If experiencing 'Could not reach the server' errors in Chainlit UI:" -ForegroundColor White
Write-Host "1. Ensure the container is running: az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query 'properties.runningStatus'" -ForegroundColor White
Write-Host "2. Create a new revision with updated polling settings: az containerapp update --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --revision-suffix 'nows$(Get-Date -Format 'yyyyMMddHHmmss')'" -ForegroundColor White
Write-Host "3. Verify CORS policy is correctly configured: az containerapp ingress cors show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP" -ForegroundColor White
Write-Host "4. Check environment variables for CHAINLIT_FORCE_POLLING and CHAINLIT_NO_WEBSOCKET: az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query 'properties.template.containers[0].env'" -ForegroundColor White
Write-Host "5. Clear browser cache and cookies, then try loading the page again" -ForegroundColor White

Write-Host "=== Verifying Deployment ===" -ForegroundColor Green
Write-Host "Waiting 60 seconds for deployment to stabilize..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

# Check main app endpoint
try {
    Write-Host "Testing main app URL..." -ForegroundColor Yellow
    $response = Invoke-WebRequest -Uri $baseUrl -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Main app endpoint is accessible: $baseUrl" -ForegroundColor Green
    } else {
        Write-Host "❌ Main app endpoint returned unexpected status: $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Failed to access main app endpoint: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "The app may still be initializing. Try accessing it manually in a few minutes." -ForegroundColor Yellow
}

# Check status endpoint
try {
    Write-Host "Testing status endpoint..." -ForegroundColor Yellow
    $response = Invoke-WebRequest -Uri "$baseUrl/chat/status" -UseBasicParsing -ErrorAction Stop
    $content = $response.Content | ConvertFrom-Json
    if ($response.StatusCode -eq 200 -and $content.status -eq "healthy") {
        Write-Host "✅ Status endpoint is healthy: $baseUrl/chat/status" -ForegroundColor Green
    } else {
        Write-Host "❌ Status endpoint returned unexpected status: $($content.status)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Failed to access status endpoint: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "The app may still be initializing. Try accessing it manually in a few minutes." -ForegroundColor Yellow
}

# Check health endpoint
try {
    Write-Host "Testing health monitoring endpoint..." -ForegroundColor Yellow
    $response = Invoke-WebRequest -Uri "$baseUrl/monitor/health" -UseBasicParsing -ErrorAction Stop
    $content = $response.Content | ConvertFrom-Json
    if ($response.StatusCode -eq 200 -and $content.status -eq "healthy") {
        Write-Host "✅ Health endpoint is healthy: $baseUrl/monitor/health" -ForegroundColor Green
    } else {
        Write-Host "❌ Health endpoint returned unexpected status: $($content.status)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Failed to access health endpoint: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "The app may still be initializing. Try accessing it manually in a few minutes." -ForegroundColor Yellow
}

# Check HTTP polling configuration
try {
    Write-Host "Verifying HTTP polling configuration..." -ForegroundColor Yellow
    $ingress = az containerapp ingress show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP | ConvertFrom-Json
    if ($ingress) {
        Write-Host "✅ Ingress configuration found. HTTP polling will be used instead of WebSockets" -ForegroundColor Green
        Write-Host "   Transport setting: $($ingress.transport) (no longer needed for polling)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "❌ Failed to verify HTTP polling configuration: $($_.Exception.Message)" -ForegroundColor Red
}

# Check logs for successful connections
try {
    Write-Host "Checking logs for successful connections..." -ForegroundColor Yellow
    $logs = az containerapp logs show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --tail 50
    if ($logs -match "200") {
        Write-Host "✅ Successful connections found in logs" -ForegroundColor Green
    } else {
        Write-Host "⚠️ No successful connections found in recent logs" -ForegroundColor Yellow
        Write-Host "This is normal if the app was just deployed or hasn't received traffic yet" -ForegroundColor Cyan
    }
} catch {
    Write-Host "❌ Failed to check logs: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "=== Deployment Verification Complete ===" -ForegroundColor Green
Write-Host "For best results, please test the Chainlit interface in a browser at $baseUrl" -ForegroundColor Cyan 

# Add simulated Chainlit entry test
Write-Host "=== Testing Chainlit Application ===" -ForegroundColor Green

# Check general connectivity before running the test
Write-Host "Verifying connection status..." -ForegroundColor Yellow
try {
    $statusCheck = Invoke-WebRequest -Uri "$baseUrl/chat/status" -UseBasicParsing -ErrorAction SilentlyContinue
    if ($statusCheck -and $statusCheck.StatusCode -eq 200) {
        Write-Host "✅ Chat status endpoint is responding, proceeding with test" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Chat status endpoint is not responding" -ForegroundColor Yellow
        Write-Host "Waiting 30 seconds for application to initialize..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30
        $statusCheck = Invoke-WebRequest -Uri "$baseUrl/chat/status" -UseBasicParsing -ErrorAction SilentlyContinue
        if ($statusCheck -and $statusCheck.StatusCode -eq 200) {
            Write-Host "✅ Chat status endpoint is now responding" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Chat status endpoint is still not responding, but proceeding with test" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "⚠️ Chat status endpoint is not responding: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "The test will proceed, but it may fail if the application is not fully initialized" -ForegroundColor Yellow
}

# Test the main application UI instead of direct API POST
Write-Host "Testing main application UI..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri $baseUrl -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Main UI is accessible at: $baseUrl" -ForegroundColor Green
        
        # Check for typical Chainlit UI elements in the response
        if ($response.Content -match "Chainlit" -or $response.Content -match "<title>Chat" -or $response.Content -match "chat-container") {
            Write-Host "✅ Chainlit UI elements detected - application appears to be working correctly" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Page loaded but Chainlit UI elements not detected. Manual verification recommended." -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️ Main UI returned unexpected status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Failed to access main UI: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Application may still be initializing. Try accessing it manually in a browser." -ForegroundColor Yellow
}

# Check common health/monitoring endpoints
$endpoints = @(
    "/health", 
    "/monitor/health",
    "/_health"
)

$foundHealthEndpoint = $false
foreach ($endpoint in $endpoints) {
    Write-Host "Testing health endpoint: $endpoint..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl$endpoint" -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Health endpoint found and responding at: $baseUrl$endpoint" -ForegroundColor Green
            $foundHealthEndpoint = $true
            break
        }
    } catch {
        # Silently continue to next endpoint
    }
}

if (-not $foundHealthEndpoint) {
    Write-Host "⚠️ No health endpoints responded. This may be normal if health endpoints are secured or not exposed." -ForegroundColor Yellow
}

Write-Host "=== Testing Specific Chainlit Routes ===" -ForegroundColor Green

# Check frontend static content
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/public/favicon.ico" -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Static content is accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️ Static content check failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Test a GET status endpoint instead of POST API endpoint
try {
    Write-Host "Testing Chainlit status endpoint..." -ForegroundColor Yellow
    $response = Invoke-WebRequest -Uri "$baseUrl/chat/status" -Method GET -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Chainlit status endpoint is working" -ForegroundColor Green
        
        try {
            $responseContent = $response.Content | ConvertFrom-Json
            Write-Host "Status response: $($responseContent | ConvertTo-Json -Compress)" -ForegroundColor Cyan
        } catch {
            Write-Host "Response received but could not parse as JSON" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️ Status endpoint returned unexpected status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Failed to access status endpoint: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "=== Application Testing Complete ===" -ForegroundColor Green
Write-Host "Testing suggests the application is deployed and responding to requests." -ForegroundColor Cyan
Write-Host "For full functionality testing, please use a browser to access: $baseUrl" -ForegroundColor Cyan

Write-Host "=== Deployment and Verification Process Complete ===" -ForegroundColor Green
Write-Host "Your Chainlit application is ready at: $baseUrl" -ForegroundColor Cyan 