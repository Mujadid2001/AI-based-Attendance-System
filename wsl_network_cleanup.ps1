# WSL Network Cleanup Script
# Removes port forwarding and firewall rules
# Run this in PowerShell as Administrator

Write-Host "Cleaning up WSL network configuration..." -ForegroundColor Yellow

$PORT = 8000

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    pause
    exit 1
}

# Remove port forwarding
Write-Host "Removing port forwarding..." -ForegroundColor Yellow
try {
    netsh interface portproxy delete v4tov4 listenport=$PORT listenaddress=0.0.0.0
    Write-Host "  Port forwarding removed" -ForegroundColor Green
} catch {
    Write-Host "  No port forwarding to remove" -ForegroundColor Gray
}

# Remove firewall rule
Write-Host "Removing firewall rule..." -ForegroundColor Yellow
try {
    Remove-NetFirewallRule -DisplayName "WSL Django Server" -ErrorAction Stop
    Write-Host "  Firewall rule removed" -ForegroundColor Green
} catch {
    Write-Host "  No firewall rule to remove" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Cleanup complete!" -ForegroundColor Green
pause
