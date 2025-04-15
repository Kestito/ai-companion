# PowerShell script to remove duplicate files from root directory
# This script checks if files exist in their mapped subdirectories and removes them from the root if they do

# Files to preserve in root directory (never delete these)
$preserveFiles = @(
    "README.md",
    "organize.ps1",
    "organize.bat",
    "organize-cleanup.ps1",
    "remove-duplicates.ps1"
)

# Mapping of files to their subdirectories (same as in organize.ps1)
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
    
    # Business documents (from organize-cleanup.ps1)
    "5_Verslo planas Inostart .docx (Converted - 2025-02-04 13_48).md" = "business"
}

# Count variables for reporting
$totalFiles = 0
$removedFiles = 0
$preservedFiles = 0
$missingSubdirFiles = 0

# Process each file in the mapping
foreach ($file in $fileMappings.Keys) {
    $subdir = $fileMappings[$file]
    $rootPath = Join-Path -Path (Get-Location) -ChildPath $file
    $subdirPath = Join-Path -Path (Get-Location) -ChildPath (Join-Path -Path $subdir -ChildPath $file)
    
    # Skip if file should be preserved
    if ($preserveFiles -contains $file) {
        Write-Host "Preserving root file: $file" -ForegroundColor Cyan
        $preservedFiles++
        continue
    }
    
    # Check if file exists in root
    if (Test-Path $rootPath) {
        $totalFiles++
        
        # Check if file exists in subdirectory
        if (Test-Path $subdirPath) {
            # Verify files are identical before removing
            $rootContent = Get-Content -Path $rootPath -Raw
            $subdirContent = Get-Content -Path $subdirPath -Raw
            
            if ($rootContent -eq $subdirContent) {
                # Remove the file from root
                Remove-Item -Path $rootPath -Force
                Write-Host "Removed duplicate file from root: $file" -ForegroundColor Green
                $removedFiles++
            } else {
                # Files are different - don't remove
                Write-Host "Content mismatch between root and $subdir/$file - preserving both" -ForegroundColor Yellow
                $preservedFiles++
            }
        } else {
            # Subdirectory copy doesn't exist
            Write-Host "File $file not found in $subdir - preserving root copy" -ForegroundColor Yellow
            $missingSubdirFiles++
        }
    }
}

# Summary
Write-Host "`n===== Duplicate Removal Summary =====" -ForegroundColor Cyan
Write-Host "Total files processed: $totalFiles" -ForegroundColor White
Write-Host "Files removed from root: $removedFiles" -ForegroundColor Green
Write-Host "Files intentionally preserved: $preservedFiles" -ForegroundColor Yellow
Write-Host "Files missing from subdirectories: $missingSubdirFiles" -ForegroundColor Magenta
Write-Host "====================================" -ForegroundColor Cyan

# Create a verification list of remaining files in root directory
$remainingFiles = Get-ChildItem -Path (Get-Location) -File | Where-Object { $_.Extension -in ".md", ".mmd" }
if ($remainingFiles.Count -gt 0) {
    Write-Host "`nRemaining files in root directory:" -ForegroundColor White
    foreach ($file in $remainingFiles) {
        if ($preserveFiles -contains $file.Name) {
            Write-Host "- $($file.Name) (preserved intentionally)" -ForegroundColor Cyan
        } else {
            Write-Host "- $($file.Name)" -ForegroundColor Magenta
        }
    }
}

Write-Host "`nDuplicate removal complete." -ForegroundColor Green 