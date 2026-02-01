@echo off
REM Smart Study Planner - Quick Start Script for Windows

echo.
echo ====================================
echo 🎓 Smart Study Planner - Quick Start
echo ====================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo ✓ Python found
python --version

REM Check if MongoDB is running
tasklist /FI "IMAGENAME eq mongod.exe" 2>NUL | find /I /N "mongod.exe">NUL
if errorlevel 1 (
    echo ⚠️  MongoDB is not running. Please start MongoDB:
    echo    net start MongoDB
    echo.
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    echo ✓ Virtual environment created
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -q -r requirements.txt
echo ✓ Dependencies installed

REM Check if .env exists
if not exist ".env" (
    echo ⚠️  .env file not found. Creating from .env.example...
    copy .env.example .env
    echo ✓ .env file created. Please edit it if needed.
)

echo.
echo ====================================
echo ✅ Setup complete!
echo.
echo 🚀 Starting Smart Study Planner...
echo    Open your browser to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ====================================
echo.

REM Run the application
python app.py

pause
