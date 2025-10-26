@echo off
REM Planted - Garden Management System
REM Windows startup script

echo.
echo ====================================
echo    Planted - Garden Management
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9 or higher from https://www.python.org/
    echo.
    pause
    exit /b 1
)

REM Check if pip is installed
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not installed
    echo Please reinstall Python with pip enabled
    echo.
    pause
    exit /b 1
)

REM Check if requirements are installed
echo Checking dependencies...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        echo.
        pause
        exit /b 1
    )
)

REM Check for .env file
if not exist .env (
    echo.
    echo WARNING: No .env file found
    echo The application will use mock weather data
    echo To use real weather data:
    echo   1. Copy .env.example to .env
    echo   2. Add your OpenWeatherMap API key
    echo.
)

echo Starting Planted...
echo.
echo The application will open in your browser at http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

REM Start the application
python main.py

pause
