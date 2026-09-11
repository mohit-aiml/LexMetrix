# LexMetrix - PowerShell Launcher
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host " LexMetrix - Legal Metrology Automated Compliance System" -ForegroundColor Green
Write-Host " Department of Consumer Affairs (DoCA), Govt. of India" -ForegroundColor Yellow
Write-Host " Problem Statement ID: 26034" -ForegroundColor White
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting Web Server at http://127.0.0.1:8000 ..." -ForegroundColor Cyan
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
