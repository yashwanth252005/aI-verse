# FocusGuard - Quick Start Script
# This script activates the virtual environment and runs Streamlit

Write-Host "Starting FocusGuard..." -ForegroundColor Green
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& ".\.venv\Scripts\Activate.ps1"

# Run Streamlit
Write-Host "Launching Streamlit dashboard..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Dashboard will open at: http://localhost:8501" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

streamlit run app.py
