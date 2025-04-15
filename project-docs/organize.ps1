# PowerShell script to organize project-docs folder

# Create folders if they don't exist
$folders = @(
    "core",
    "architecture",
    "diagrams",
    "database",
    "api",
    "deployment",
    "implementation",
    "rag",
    "features",
    "interfaces",
    "monitoring",
    "testing"
)

# Ensure we're in the project-docs directory
$currentDir = Get-Location
Write-Host "Current directory: $currentDir" -ForegroundColor Cyan

# Create all required directories first
foreach ($folder in $folders) {
    $folderPath = Join-Path -Path $currentDir -ChildPath $folder
    if (-not (Test-Path $folderPath)) {
        New-Item -Path $folderPath -ItemType Directory -Force
        Write-Host "Created folder: $folder" -ForegroundColor Green
    } else {
        Write-Host "Folder already exists: $folder" -ForegroundColor Yellow
    }
}

# Define file mappings (source -> destination folder)
$fileMappings = @{
    # Core documents
    "overview.md" = "core"
    "requirements.md" = "core"
    "tech-specs.md" = "core"
    "user-structure.md" = "core"
    "timeline.md" = "core"
    "project_summary.md" = "core"
    "requirements_finalization.md" = "core"
    "discovery_analysis_notes.md" = "core"
    
    # Architecture documents
    "scheduled_messaging_architecture.md" = "architecture"
    
    # Diagrams
    "architecture-diagram.mmd" = "diagrams"
    "deployment-architecture.mmd" = "diagrams"
    "rag-flow.mmd" = "diagrams"
    "scheduled-messaging-flow.mmd" = "diagrams"
    
    # Database documents
    "database-schema.md" = "database"
    "database-integration.md" = "database"
    "schema_updates.md" = "database"
    "schema-change-document.md" = "database"
    
    # API documents
    "api-structure.md" = "api"
    
    # Deployment documents
    "AZURE-CONTAINER-APP-DEPLOYMENT.md" = "deployment"
    "CUSTOM-DOMAIN-SETUP.md" = "deployment"
    "azure-deployment.md" = "deployment"
    "azure-deployment-summary.md" = "deployment"
    "docker-interfaces.md" = "deployment"
    "scheduled_messaging_deployment.md" = "deployment"
    "scheduled_messaging_azure.md" = "deployment"
    
    # Implementation documents
    "implementation_roadmap.md" = "implementation"
    "plan.md" = "implementation"
    "processor_enhancements.md" = "implementation"
    "scheduled_messaging_implementation.md" = "implementation"
    "websocket-performance-fixes.md" = "implementation"
    "websocket-fixes.md" = "implementation"
    "Action.md" = "implementation"
    "http-polling-verification.md" = "implementation"
    "chainlit.md" = "implementation"
    
    # RAG documents
    "rag.md" = "rag"
    "url_prioritization_guide.md" = "rag"
    
    # Feature documents
    "scheduled-messaging.md" = "features"
    "patient-registration.md" = "features"
    "evelina_personality.md" = "features"
    
    # Interface documents
    "web-ui.md" = "interfaces"
    "telegram.md" = "interfaces"
    
    # Monitoring documents
    "logging.md" = "monitoring"
    "monitoring.md" = "monitoring"
    "troubleshooting.md" = "monitoring"
    
    # Testing documents
    "telegram_tests.md" = "testing"
    "message_delivery_test_plan.md" = "testing"
}

# Copy files to their respective folders
foreach ($file in $fileMappings.Keys) {
    $destination = $fileMappings[$file]
    $sourcePath = Join-Path -Path $currentDir -ChildPath $file
    $destPath = Join-Path -Path $currentDir -ChildPath $destination
    
    if (Test-Path $sourcePath) {
        try {
            Copy-Item -Path $sourcePath -Destination $destPath -Force -ErrorAction Stop
            Write-Host "Copied $file to $destination folder" -ForegroundColor Green
        } catch {
            Write-Host "Error copying $file to $destination folder: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "File not found: $file" -ForegroundColor Yellow
    }
}

Write-Host "`nOrganization complete. Please review the files and delete duplicates as needed." -ForegroundColor Green
Write-Host "See README.md for the recommended folder structure." -ForegroundColor Green 