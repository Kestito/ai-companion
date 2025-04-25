#!/usr/bin/env pwsh
# Scheduled Messages Maintenance Script
# This script helps maintain the health of scheduled messages in the AI Companion application.

param (
    [switch]$CheckOnly = $false,
    [switch]$FixAll = $false,
    [switch]$FixMissingMetadata = $false,
    [switch]$ResetFailedMessages = $false,
    [switch]$FixPastDueMessages = $false,
    [switch]$Verbose = $false,
    [switch]$Help = $false
)

# Show help if requested
if ($Help) {
    Write-Host "Scheduled Messages Maintenance Script" -ForegroundColor Cyan
    Write-Host "Usage: .\maintain_scheduled_messages.ps1 [options]" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -CheckOnly             Only check for issues, don't fix anything"
    Write-Host "  -FixAll                Fix all issues found (past due, stuck processing, missing metadata, failed messages)"
    Write-Host "  -FixMissingMetadata    Only fix messages with missing metadata"
    Write-Host "  -ResetFailedMessages   Only reset failed messages to pending status"
    Write-Host "  -FixPastDueMessages    Only fix past due messages that are still in pending status"
    Write-Host "  -Verbose               Show more detailed output"
    Write-Host "  -Help                  Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\maintain_scheduled_messages.ps1 -CheckOnly                 # Just check for issues"
    Write-Host "  .\maintain_scheduled_messages.ps1 -FixAll                    # Fix all issues"
    Write-Host "  .\maintain_scheduled_messages.ps1 -ResetFailedMessages       # Only reset failed messages"
    exit 0
}

# If neither checking nor fixing is specified, default to checking
if (-not $CheckOnly -and -not $FixAll -and -not $FixMissingMetadata -and -not $ResetFailedMessages -and -not $FixPastDueMessages) {
    $CheckOnly = $true
    Write-Host "No action specified. Defaulting to checking for issues only." -ForegroundColor Yellow
}

# Function to run the check script
function Check-Messages {
    Write-Host "Checking scheduled messages for issues..." -ForegroundColor Cyan
    
    # Construct command with appropriate arguments
    $verboseArg = if ($Verbose) { "--verbose" } else { "" }
    
    # Run the Python script
    $result = python check_scheduled_messages.py $verboseArg
    
    # The exit code indicates if issues were found
    $hasIssues = $LASTEXITCODE -ne 0
    
    if ($hasIssues) {
        Write-Host "Issues were found with scheduled messages." -ForegroundColor Yellow
        if ($CheckOnly) {
            Write-Host "Run this script with -FixAll to fix all issues." -ForegroundColor Yellow
        }
    } else {
        Write-Host "No issues found with scheduled messages." -ForegroundColor Green
    }
    
    return $hasIssues
}

# Function to fix scheduled messages
function Fix-Messages {
    param(
        [bool]$FixMetadata,
        [bool]$ResetFailed,
        [bool]$FixPastDue
    )
    
    Write-Host "Fixing scheduled messages..." -ForegroundColor Cyan
    
    # Construct arguments based on what should be fixed
    $args = @()
    if ($FixMetadata) { $args += "--fix-metadata" }
    if ($ResetFailed) { $args += "--reset-failed" }
    if ($FixPastDue) { $args += "--fix-past-due" }
    $args += "--yes"  # Auto-confirm fixes
    
    # Only proceed if we have something to fix
    if ($args.Count -le 1) {
        Write-Host "No fix options specified." -ForegroundColor Yellow
        return
    }
    
    # Run the Python script with the specified arguments
    $result = python fix_scheduled_messages.py $args
    
    # Check if the fix was successful
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Successfully fixed scheduled messages." -ForegroundColor Green
    } else {
        Write-Host "Failed to fix scheduled messages." -ForegroundColor Red
    }
}

# Set environment variables with hardcoded values (failsafe)
# These will be used if the script can't find them in the environment
$env:SUPABASE_URL = "https://aubulhjfeszmsheonmpy.supabase.co"
$env:SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc"

# Make sure the Python module is installed
try {
    python -m pip install supabase --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install required Python package 'supabase'." -ForegroundColor Red
        Write-Host "Please run 'python -m pip install supabase' and try again." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Failed to install required Python package: $_" -ForegroundColor Red
    exit 1
}

# Step 1: Always check for issues
$hasIssues = Check-Messages

# Step 2: Fix issues if requested
if (-not $CheckOnly) {
    if ($FixAll) {
        # Fix all issues
        Fix-Messages -FixMetadata $true -ResetFailed $true -FixPastDue $true
    } else {
        # Fix specific issues as requested
        Fix-Messages -FixMetadata $FixMissingMetadata -ResetFailed $ResetFailedMessages -FixPastDue $FixPastDueMessages
    }
    
    # After fixing, check again to verify
    Write-Host "`nVerifying fixes..." -ForegroundColor Cyan
    $stillHasIssues = Check-Messages
    
    if ($stillHasIssues) {
        Write-Host "Some issues still remain after applying fixes." -ForegroundColor Yellow
    } else {
        Write-Host "All issues have been successfully resolved!" -ForegroundColor Green
    }
}

# Clean up environment variables
Remove-Item Env:\SUPABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:\SUPABASE_KEY -ErrorAction SilentlyContinue 