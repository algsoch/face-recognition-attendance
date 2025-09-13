# Attendance Management System - Run Script
# This script helps you start and manage the attendance system

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("start", "test", "install", "setup")]
    [string]$Action = "start"
)

Write-Host "Attendance Management System" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

switch ($Action) {
    "install" {
        Write-Host "Installing dependencies..." -ForegroundColor Yellow
        
        # Check if Python is installed
        try {
            $pythonVersion = python --version 2>$null
            Write-Host "Python found: $pythonVersion" -ForegroundColor Green
        }
        catch {
            Write-Host "Python not found! Please install Python 3.8+" -ForegroundColor Red
            exit 1
        }
        
        # Install requirements
        Write-Host "Installing Python packages..."
        pip install -r requirements.txt
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Dependencies installed successfully!" -ForegroundColor Green
        } else {
            Write-Host "Failed to install dependencies" -ForegroundColor Red
            exit 1
        }
    }
    
    "setup" {
        Write-Host "Setting up the system..." -ForegroundColor Yellow
        
        # Check if .env exists
        if (-not (Test-Path ".env")) {
            Write-Host ".env file not found!" -ForegroundColor Red
            Write-Host "Please create a .env file with your database configuration." -ForegroundColor Yellow
            Write-Host "Example content:" -ForegroundColor Yellow
            Write-Host "DATABASE_URL=your_database_url_here" -ForegroundColor Gray
            Write-Host "SECRET_KEY=your_secret_key_here" -ForegroundColor Gray
            exit 1
        }
        
        Write-Host "Environment file found" -ForegroundColor Green
        
        # Run database setup
        Write-Host "Setting up database..."
        python -c "from backend.database import engine, Base; from backend import models; print('Creating database tables...'); Base.metadata.create_all(bind=engine); print('Database setup complete!')"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "System setup complete!" -ForegroundColor Green
        } else {
            Write-Host "Setup failed" -ForegroundColor Red
            exit 1
        }
    }
    
    "start" {
        Write-Host "Starting the server..." -ForegroundColor Yellow
        
        # Check if .env exists
        if (-not (Test-Path ".env")) {
            Write-Host ".env file not found! Run setup first." -ForegroundColor Red
            exit 1
        }
        
        # Start the server
        Write-Host "Starting FastAPI server on http://localhost:8000" -ForegroundColor Green
        Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Available endpoints:" -ForegroundColor Cyan
        Write-Host "  Dashboard: http://localhost:8000/" -ForegroundColor White
        Write-Host "  Login: http://localhost:8000/login" -ForegroundColor White
        Write-Host "  Student Portal: http://localhost:8000/student-portal" -ForegroundColor White
        Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
        Write-Host ""
        
        # Create faces directory if it doesn't exist
        if (-not (Test-Path "faces")) {
            New-Item -ItemType Directory -Path "faces" | Out-Null
            Write-Host "Created faces directory for facial recognition" -ForegroundColor Green
        }
        
        uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    }
    
    "test" {
        Write-Host "Running system tests..." -ForegroundColor Yellow
        
        # Check if server is running
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
            Write-Host "Server is running" -ForegroundColor Green
        }
        catch {
            Write-Host "Server is not running!" -ForegroundColor Red
            Write-Host "Please start the server first with: .\run.ps1 start" -ForegroundColor Yellow
            exit 1
        }
        
        # Run tests
        python test_system.py
    }
    
    default {
        Write-Host "Usage: .\run.ps1 [install|setup|start|test]" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Commands:" -ForegroundColor Cyan
        Write-Host "  install - Install Python dependencies" -ForegroundColor White
        Write-Host "  setup   - Set up database and configuration" -ForegroundColor White
        Write-Host "  start   - Start the application server" -ForegroundColor White
        Write-Host "  test    - Run system tests" -ForegroundColor White
        Write-Host ""
        Write-Host "Quick start:" -ForegroundColor Yellow
        Write-Host "  1. .\run.ps1 install" -ForegroundColor Gray
        Write-Host "  2. .\run.ps1 setup" -ForegroundColor Gray
        Write-Host "  3. .\run.ps1 start" -ForegroundColor Gray
    }
}
