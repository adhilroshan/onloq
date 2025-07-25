@echo off
REM Onloq Auto-Start Script for Windows
REM This script starts Onloq in daemon mode with auto-summarization

cd /d "%~dp0\.."
echo Starting Onloq in daemon mode...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if required dependencies are installed
python -c "import typer, psutil, watchdog, schedule" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Initialize configuration if it doesn't exist
if not exist "onloq_config.json" (
    echo Initializing Onloq configuration...
    python main.py init
)

REM Enable auto-summarization
echo Enabling auto-summarization...
python main.py auto --enable --time "20:00"

REM Start Onloq in daemon mode
echo Starting Onloq logger...
python main.py run --daemon --auto-summarize

echo Onloq is now running in the background
echo Check the system tray for notifications
pause
