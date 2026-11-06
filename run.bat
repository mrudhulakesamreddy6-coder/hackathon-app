@echo off
title DisasterSync AI - Emergency Response System
echo ====================================================================
echo  DISASTERSYNC AI
echo  AI-Powered Multi-Agent Disaster Response & Coordination System
echo  Project Code: AG-AI-01 | Bapatla Women's Engineering College
echo ====================================================================
echo.

echo Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH! Please install Python 3.10+.
    pause
    exit /b 1
)

echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

echo.
echo Initializing DisasterSync AI web server...
echo Serving at: http://127.0.0.1:5000
echo.
python app.py
pause

