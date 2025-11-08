# Railway Deployment Helper Script
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Railway Deployment for Insta Agent" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Railway CLI is installed
Write-Host "Checking for Railway CLI..." -ForegroundColor Yellow
$railwayInstalled = Get-Command railway -ErrorAction SilentlyContinue

if (-not $railwayInstalled) {
    Write-Host "❌ Railway CLI not found." -ForegroundColor Red
    Write-Host ""
    Write-Host "Installing Railway CLI..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please run this command in a NEW PowerShell window (as Administrator):" -ForegroundColor Cyan
    Write-Host "iwr https://railway.app/install.ps1 | iex" -ForegroundColor White
    Write-Host ""
    Write-Host "After installation, close that window and run this script again." -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "✅ Railway CLI found!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Login to Railway: railway login" -ForegroundColor White
Write-Host "2. Initialize project: railway init" -ForegroundColor White
Write-Host "3. Link to Railway project" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to login to Railway..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

railway login
