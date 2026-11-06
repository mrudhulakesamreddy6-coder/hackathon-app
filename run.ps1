Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host " DISASTERSYNC AI" -ForegroundColor Green
Write-Host " AI-Powered Multi-Agent Disaster Response & Coordination System" -ForegroundColor White
Write-Host " Project Code: AG-AI-01 | Bapatla Women's Engineering College" -ForegroundColor Yellow
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

try {
    $pythonVersion = python --version
    Write-Host "[OK] Detected: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

Write-Host "Installing required Python packages..." -ForegroundColor Gray
pip install -r requirements.txt

Write-Host ""
Write-Host "Starting DisasterSync AI on http://127.0.0.1:5000 ..." -ForegroundColor Cyan
python app.py

