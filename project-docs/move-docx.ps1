# Move the DOCX file to the business folder

$sourceFile = "5_Verslo planas Inostart .docx (Converted - 2025-02-04 13_48).docx"
$targetFolder = "business"

if (Test-Path $sourceFile) {
    # Check if business folder exists, create if not
    if (!(Test-Path $targetFolder)) {
        New-Item -ItemType Directory -Path $targetFolder -Force
        Write-Host "Created folder: $targetFolder" -ForegroundColor Green
    }
    
    # Move file to business folder
    $targetPath = Join-Path -Path $targetFolder -ChildPath $sourceFile
    Move-Item -Path $sourceFile -Destination $targetPath -Force
    Write-Host "Moved $sourceFile to $targetFolder folder" -ForegroundColor Green
} else {
    Write-Host "Source file not found: $sourceFile" -ForegroundColor Yellow
}

Write-Host "Remaining files in root directory:" -ForegroundColor Cyan
Get-ChildItem -File | Where-Object { $_.Extension -ne ".ps1" -and $_.Name -ne "README.md" } | ForEach-Object {
    Write-Host "- $($_.Name)" -ForegroundColor Yellow
} 