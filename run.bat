@echo off
REM Attendance Management System - Run Script for CMD
setlocal EnableDelayedExpansion

echo.
echo 🎓 Attendance Management System
echo =================================

if "%1"=="install" goto install
if "%1"=="setup" goto setup
if "%1"=="start" goto start
if "%1"=="test" goto test
goto help

:install
echo 📦 Installing dependencies...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python 3.8+
    exit /b 1
)
echo ✅ Python found
echo Installing Python packages...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    exit /b 1
)
echo ✅ Dependencies installed successfully!
goto end

:setup
echo 🔧 Setting up the system...
if not exist .env (
    echo ❌ .env file not found!
    echo Please create a .env file with your database configuration.
    echo Example content:
    echo DATABASE_URL=your_database_url_here
    echo SECRET_KEY=your_secret_key_here
    exit /b 1
)
echo ✅ Environment file found
echo Setting up database...
python -c "from backend.database import engine, Base; from backend import models; print('Creating database tables...'); Base.metadata.create_all(bind=engine); print('✅ Database setup complete!')"
if %errorlevel% neq 0 (
    echo ❌ Setup failed
    exit /b 1
)
echo ✅ System setup complete!
goto end

:start
echo 🚀 Starting the server...
if not exist .env (
    echo ❌ .env file not found! Run setup first.
    exit /b 1
)
echo Starting FastAPI server on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
echo Available endpoints:
echo   🏠 Dashboard: http://localhost:8000/
echo   🔐 Login: http://localhost:8000/login
echo   👨‍🎓 Student Portal: http://localhost:8000/student-portal
echo   📚 API Docs: http://localhost:8000/docs
echo.
if not exist faces mkdir faces >nul 2>&1
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
goto end

:test
echo 🧪 Running system tests...
python test_system.py
goto end

:help
echo Usage: run.bat [install^|setup^|start^|test]
echo.
echo Commands:
echo   install - Install Python dependencies
echo   setup   - Set up database and configuration
echo   start   - Start the application server
echo   test    - Run system tests
echo.
echo Quick start:
echo   1. run.bat install
echo   2. run.bat setup
echo   3. run.bat start

:end
echo.
pause
