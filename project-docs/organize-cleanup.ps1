# PowerShell script to handle additional organization tasks

# Create business folder
$businessFolder = "business"
if (!(Test-Path $businessFolder)) {
    New-Item -ItemType Directory -Path $businessFolder
    Write-Host "Created folder: $businessFolder" -ForegroundColor Green
} else {
    Write-Host "Folder already exists: $businessFolder" -ForegroundColor Yellow
}

# Move business plan to business folder
$businessPlanFile = "5_Verslo planas Inostart .docx (Converted - 2025-02-04 13_48).md"
if (Test-Path $businessPlanFile) {
    Copy-Item -Path $businessPlanFile -Destination (Join-Path -Path $businessFolder -ChildPath $businessPlanFile) -Force
    Write-Host "Copied $businessPlanFile to $businessFolder folder" -ForegroundColor Green
} else {
    Write-Host "Business plan file not found: $businessPlanFile" -ForegroundColor Yellow
}

# Create empty versions of missing files
$missingFiles = @{
    "telegram.md" = "interfaces"
    "telegram_tests.md" = "testing"
    "architecture-diagram.mmd" = "diagrams"
}

foreach ($file in $missingFiles.Keys) {
    $folder = $missingFiles[$file]
    $filePath = $file
    $destinationPath = Join-Path -Path $folder -ChildPath $file
    
    if (!(Test-Path $filePath)) {
        # Create empty file with a basic header
        $fileName = [System.IO.Path]::GetFileNameWithoutExtension($file)
        $fileExt = [System.IO.Path]::GetExtension($file)
        
        if ($fileExt -eq ".md") {
            $content = "# $($fileName -replace '-|_', ' ' | ForEach-Object { [regex]::Replace($_, '(^[a-z]|\b[a-z])', { $args[0].Value.ToUpper() }) })`n`nThis documentation is under development.`n"
            $content | Out-File -FilePath $filePath -Encoding utf8
            Write-Host "Created empty markdown file with header: $file" -ForegroundColor Green
        } elseif ($fileExt -eq ".mmd") {
            $content = "flowchart TD`n    A[Start] --> B[End]`n    %% This is a placeholder diagram`n"
            $content | Out-File -FilePath $filePath -Encoding utf8
            Write-Host "Created empty mermaid diagram: $file" -ForegroundColor Green
        } else {
            "" | Out-File -FilePath $filePath -Encoding utf8
            Write-Host "Created empty file: $file" -ForegroundColor Green
        }
        
        # Copy to destination folder
        if (Test-Path $folder) {
            Copy-Item -Path $filePath -Destination $destinationPath -Force
            Write-Host "Copied $file to $folder folder" -ForegroundColor Green
        } else {
            Write-Host "Destination folder does not exist: $folder" -ForegroundColor Red
        }
    } else {
        Write-Host "File already exists: $file" -ForegroundColor Yellow
        
        # Copy to destination folder if it's not already there
        if (!(Test-Path $destinationPath) -and (Test-Path $folder)) {
            Copy-Item -Path $filePath -Destination $destinationPath -Force
            Write-Host "Copied existing $file to $folder folder" -ForegroundColor Green
        }
    }
}

# Check for and remove empty files
$emptyFiles = @(
    "http-polling-verification.md",
    "message_delivery_test_plan.md",
    "schema-change-document.md"
)

$processedEmptyFiles = @()

foreach ($file in $emptyFiles) {
    if (Test-Path $file) {
        $content = Get-Content -Path $file -Raw
        if ([string]::IsNullOrWhiteSpace($content)) {
            $processedEmptyFiles += $file
        }
    }
}

if ($processedEmptyFiles.Count -gt 0) {
    Write-Host "`nThe following files appear to be empty:" -ForegroundColor Yellow
    foreach ($file in $processedEmptyFiles) {
        Write-Host "- $file" -ForegroundColor Yellow
    }
    
    $confirmation = Read-Host "Do you want to remove these empty files? (Y/N)"
    if ($confirmation -eq 'Y' -or $confirmation -eq 'y') {
        foreach ($file in $processedEmptyFiles) {
            Remove-Item -Path $file -Force
            Write-Host "Removed empty file: $file" -ForegroundColor Green
        }
    } else {
        Write-Host "Empty files were not removed." -ForegroundColor Yellow
    }
} else {
    Write-Host "No empty files found." -ForegroundColor Green
}

Write-Host "`nAdditional organization tasks completed." -ForegroundColor Green 