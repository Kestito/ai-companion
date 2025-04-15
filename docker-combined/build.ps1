# Build and run combined AI Companion container

Write-Host "Building combined AI Companion container..." -ForegroundColor Cyan
docker build -t ai-companion-combined .

Write-Host "Running combined AI Companion container..." -ForegroundColor Cyan
docker run -d `
  --name ai-companion-combined `
  -p 8000:8000 `
  -e TELEGRAM_BOT_TOKEN="'
    
    $psBuildScript += "$TelegramBotToken"
    $psBuildScript += @'" `
  -e SUPABASE_URL="https://aubulhjfeszmsheonmpy.supabase.co" `
  -e SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc" `
  -e PYTHONPATH=/app `
  -e PYTHONUNBUFFERED=1 `
  --restart always `
  ai-companion-combined

Write-Host "Container started! API available at http://localhost:8000" -ForegroundColor Green