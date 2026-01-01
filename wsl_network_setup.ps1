# WSL Network Setup Script for AI Attendance System
# This script configures Windows Firewall and port forwarding for WSL2
# Run this in PowerShell as Administrator

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "WSL Network Setup for Django Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    pause
    exit 1
}

$PORT = 8000
$WSL_DISTRO = "Ubuntu"  # Change if using different distro

Write-Host "Step 1: Getting WSL IP address..." -ForegroundColor Yellow
try {
    $wslIP = (wsl -d $WSL_DISTRO hostname -I).Trim()
    Write-Host "  WSL IP: $wslIP" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Could not get WSL IP. Is WSL running?" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "Step 2: Getting Windows host IP address..." -ForegroundColor Yellow
try {
    $windowsIP = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias (Get-NetRoute -DestinationPrefix "0.0.0.0/0").InterfaceAlias | Where-Object {$_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*"} | Select-Object -First 1).IPAddress
    Write-Host "  Windows IP: $windowsIP" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Could not get Windows IP" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "Step 3: Configuring Windows Firewall..." -ForegroundColor Yellow
try {
    # Remove existing rule if it exists
    Remove-NetFirewallRule -DisplayName "WSL Django Server" -ErrorAction SilentlyContinue
    
    # Add new inbound rule for port 8000
    New-NetFirewallRule -DisplayName "WSL Django Server" -Direction Inbound -LocalPort $PORT -Protocol TCP -Action Allow -Profile Any
    Write-Host "  Firewall rule created successfully" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Could not configure firewall: $_" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "Step 4: Setting up port forwarding..." -ForegroundColor Yellow
try {
    # Remove existing port proxy if it exists
    $existingProxy = netsh interface portproxy show v4tov4 | Select-String "0.0.0.0.*$PORT"
    if ($existingProxy) {
        netsh interface portproxy delete v4tov4 listenport=$PORT listenaddress=0.0.0.0
        Write-Host "  Removed existing port proxy" -ForegroundColor Yellow
    }
    
    # Add new port proxy (forward Windows:8000 -> WSL:8000)
    netsh interface portproxy add v4tov4 listenport=$PORT listenaddress=0.0.0.0 connectport=$PORT connectaddress=$wslIP
    Write-Host "  Port forwarding configured: 0.0.0.0:${PORT} -> ${wslIP}:${PORT}" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Could not configure port forwarding: $_" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "Step 5: Verifying configuration..." -ForegroundColor Yellow
$portProxy = netsh interface portproxy show v4tov4
Write-Host $portProxy
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your Django server should now be accessible at:" -ForegroundColor Cyan
Write-Host "  http://${windowsIP}:${PORT}" -ForegroundColor White
Write-Host ""
Write-Host "Mobile devices on the same network can now connect!" -ForegroundColor Cyan
Write-Host ""
Write-Host "To verify, test from your mobile browser:" -ForegroundColor Yellow
Write-Host "  http://${windowsIP}:${PORT}/api/camera/sources/network-info/" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANT: These settings will be lost after Windows restart!" -ForegroundColor Red
Write-Host "Re-run this script after each Windows reboot." -ForegroundColor Yellow
Write-Host ""
Write-Host "To remove these settings, run:" -ForegroundColor Yellow
Write-Host "  netsh interface portproxy delete v4tov4 listenport=${PORT} listenaddress=0.0.0.0" -ForegroundColor White
Write-Host "  Remove-NetFirewallRule -DisplayName 'WSL Django Server'" -ForegroundColor White
Write-Host ""
pause
