# Start script for Django with WebSocket support (Daphne ASGI server)
# PowerShell version for Windows/WSL

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Starting Django with WebSocket Support" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if Redis is running in WSL
Write-Host "[1/3] Checking Redis in WSL..." -ForegroundColor Yellow
$redisCheck = wsl -- redis-cli ping 2>&1
if ($redisCheck -match "PONG") {
    Write-Host "✓ Redis is running" -ForegroundColor Green
} else {
    Write-Host "⚠️  Redis is not running!" -ForegroundColor Red
    Write-Host "Starting Redis in WSL background..." -ForegroundColor Yellow
    wsl -- redis-server --daemonize yes
    Start-Sleep -Seconds 2
    
    $redisCheck2 = wsl -- redis-cli ping 2>&1
    if ($redisCheck2 -match "PONG") {
        Write-Host "✓ Redis started successfully" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to start Redis" -ForegroundColor Red
        Write-Host "Please install Redis first:" -ForegroundColor Yellow
        Write-Host "  wsl -- bash install_redis.sh" -ForegroundColor Cyan
        exit 1
    }
}

# Navigate to Django project
Set-Location "$PSScriptRoot\attendance_system"

# Set Django settings module
$env:DJANGO_SETTINGS_MODULE = "config.settings.development"

# Start Daphne ASGI server
Write-Host ""
Write-Host "[2/3] Starting Daphne ASGI server..." -ForegroundColor Yellow
Write-Host "Server will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "WebSocket endpoint: ws://localhost:8000/ws/camera/{camera_id}/" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Start Daphne
& python -m daphne -b 0.0.0.0 -p 8000 config.asgi:application
