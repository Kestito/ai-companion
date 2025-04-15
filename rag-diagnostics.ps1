# RAG System Diagnostics Script

Write-Host "Starting RAG System Diagnostics" -ForegroundColor Cyan

# Check environment variables
Write-Host "1. Checking Environment Variables..." -ForegroundColor Yellow
$envVars = @(
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "QDRANT_URL",
    "QDRANT_API_KEY",
    "AZURE_OPENAI_DEPLOYMENT",
    "LLM_MODEL",
    "AZURE_EMBEDDING_DEPLOYMENT",
    "EMBEDDING_MODEL"
)

$missingVars = @()
foreach ($var in $envVars) {
    $value = [Environment]::GetEnvironmentVariable($var)
    if ([string]::IsNullOrEmpty($value)) {
        $missingVars += $var
        Write-Host "  - Missing: $var" -ForegroundColor Red
    } else {
        Write-Host "  - Found: $var" -ForegroundColor Green
    }
}

# Test Qdrant Connection
Write-Host "`n2. Testing Qdrant Connection..." -ForegroundColor Yellow
$qdrantUrl = [Environment]::GetEnvironmentVariable("QDRANT_URL")
if (-not [string]::IsNullOrEmpty($qdrantUrl)) {
    try {
        $qdrantResponse = Invoke-RestMethod -Uri "$qdrantUrl/collections" -Method GET -Headers @{
            "api-key" = [Environment]::GetEnvironmentVariable("QDRANT_API_KEY")
        } -ErrorAction Stop
        
        Write-Host "  - Qdrant connection successful" -ForegroundColor Green
        Write-Host "  - Found collections: $($qdrantResponse.result.collections.name -join ', ')" -ForegroundColor Green
        
        # Check if Information collection exists
        $infoCollection = $qdrantResponse.result.collections | Where-Object { $_.name -eq "Information" }
        if (-not $infoCollection) {
            Write-Host "  - WARNING: 'Information' collection not found!" -ForegroundColor Red
        }
    } catch {
        Write-Host "  - Qdrant connection failed: $_" -ForegroundColor Red
    }
} else {
    Write-Host "  - Skipping Qdrant test (URL not configured)" -ForegroundColor Yellow
}

# Test Supabase Connection
Write-Host "`n3. Testing Supabase Connection..." -ForegroundColor Yellow
$supabaseUrl = [Environment]::GetEnvironmentVariable("SUPABASE_URL")
$supabaseKey = [Environment]::GetEnvironmentVariable("SUPABASE_KEY")

if (-not [string]::IsNullOrEmpty($supabaseUrl) -and -not [string]::IsNullOrEmpty($supabaseKey)) {
    try {
        $supabaseResponse = Invoke-RestMethod -Uri "$supabaseUrl/rest/v1/" -Method GET -Headers @{
            "apikey" = $supabaseKey
            "Authorization" = "Bearer $supabaseKey"
        } -ErrorAction Stop
        
        Write-Host "  - Supabase connection successful" -ForegroundColor Green
    } catch {
        Write-Host "  - Supabase connection failed: $_" -ForegroundColor Red
    }
} else {
    Write-Host "  - Skipping Supabase test (URL or key not configured)" -ForegroundColor Yellow
}

# Summary
Write-Host "`nRAG System Diagnostics Summary:" -ForegroundColor Cyan
if ($missingVars.Count -gt 0) {
    Write-Host "Missing environment variables: $($missingVars -join ', ')" -ForegroundColor Red
    Write-Host "Fix: Add these variables to your environment or .env file" -ForegroundColor Yellow
}

Write-Host "`nRecommended fixes:" -ForegroundColor Cyan
Write-Host "1. Ensure all environment variables are set correctly" -ForegroundColor Yellow
Write-Host "2. Verify that the 'Information' collection exists in Qdrant" -ForegroundColor Yellow
Write-Host "3. Check if documents are properly indexed in both Qdrant and Supabase" -ForegroundColor Yellow
Write-Host "4. Validate Azure OpenAI API key and endpoint configuration" -ForegroundColor Yellow
Write-Host "5. Try restarting the application after fixing these issues" -ForegroundColor Yellow

Write-Host "`nTo apply fixes and test RAG with a sample query, run:" -ForegroundColor Green
Write-Host "python -c 'from ai_companion.modules.rag.core.rag_chain import get_rag_chain; import asyncio; print(asyncio.run(get_rag_chain().query(\"Test query\")))'" -ForegroundColor Cyan 