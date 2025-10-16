# MATLAB Automation Platform Clean Setup Script for PowerShell
# This script creates a fresh environment and fixes dependency conflicts

Write-Host "🚀 Setting up MATLAB Automation Platform (Clean Install)..." -ForegroundColor Green

# Check if Docker is installed
try {
    docker --version | Out-Null
    Write-Host "[SUCCESS] Docker and Docker Compose are installed" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if Python is installed
try {
    python --version | Out-Null
    Write-Host "[SUCCESS] Python is installed" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed. Please install Python 3.11+ first." -ForegroundColor Red
    exit 1
}

# Check if Node.js is installed
try {
    node --version | Out-Null
    Write-Host "[SUCCESS] Node.js is installed" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Node.js is not installed. Please install Node.js 18+ first." -ForegroundColor Red
    exit 1
}

# Clean up any existing virtual environment
Write-Host "[INFO] Cleaning up existing virtual environment..." -ForegroundColor Yellow
if (Test-Path "backend\venv") {
    try {
        Remove-Item -Recurse -Force "backend\venv"
        Write-Host "[INFO] Removed existing virtual environment" -ForegroundColor Yellow
    } catch {
        Write-Host "[WARNING] Could not remove existing virtual environment, continuing..." -ForegroundColor Yellow
    }
}

# Clean up node_modules
Write-Host "[INFO] Cleaning up existing node_modules..." -ForegroundColor Yellow
if (Test-Path "frontend\node_modules") {
    Remove-Item -Recurse -Force "frontend\node_modules"
    Write-Host "[INFO] Removed existing node_modules" -ForegroundColor Yellow
}

# Clean up package-lock.json
if (Test-Path "frontend\package-lock.json") {
    Remove-Item "frontend\package-lock.json"
    Write-Host "[INFO] Removed package-lock.json" -ForegroundColor Yellow
}

# Create necessary directories
Write-Host "[INFO] Creating necessary directories..." -ForegroundColor Yellow
$directories = @("matlab\models", "matlab\scripts", "matlab\data", "backend\uploads", "backend\reports", "logs")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Host "[SUCCESS] Directories created" -ForegroundColor Green

# Setup backend environment
Write-Host "[INFO] Setting up backend environment..." -ForegroundColor Yellow
Set-Location backend

# Create fresh virtual environment
Write-Host "[INFO] Creating fresh virtual environment..." -ForegroundColor Yellow
try {
    python -m venv venv
    Write-Host "[SUCCESS] Virtual environment created" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to create virtual environment: $_" -ForegroundColor Red
    Set-Location ..
    exit 1
}

# Activate virtual environment and upgrade pip
Write-Host "[INFO] Activating virtual environment and upgrading pip..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip

# Install core dependencies first
Write-Host "[INFO] Installing core dependencies..." -ForegroundColor Yellow
pip install wheel setuptools

# Install all requirements
Write-Host "[INFO] Installing all requirements..." -ForegroundColor Yellow
pip install -r requirements.txt

# Copy environment file
if (!(Test-Path ".env")) {
    Copy-Item "env.example" ".env"
    Write-Host "[WARNING] Please update the .env file with your configuration" -ForegroundColor Yellow
}

Set-Location ..
Write-Host "[SUCCESS] Backend environment setup complete" -ForegroundColor Green

# Setup frontend environment
Write-Host "[INFO] Setting up frontend environment..." -ForegroundColor Yellow
Set-Location frontend

# Clear npm cache
Write-Host "[INFO] Clearing npm cache..." -ForegroundColor Yellow
npm cache clean --force

# Install dependencies with legacy peer deps to resolve conflicts
Write-Host "[INFO] Installing frontend dependencies..." -ForegroundColor Yellow
npm install --legacy-peer-deps

# Create environment file
if (!(Test-Path ".env")) {
    "REACT_APP_API_URL=http://localhost:8000/api/v1" | Out-File -FilePath ".env" -Encoding UTF8
}

Set-Location ..
Write-Host "[SUCCESS] Frontend environment setup complete" -ForegroundColor Green

# Stop any existing containers (commented out for direct code execution)
# Write-Host "[INFO] Stopping existing containers..." -ForegroundColor Yellow
# docker-compose down 2>$null

# Setup database (commented out for direct code execution)
# Write-Host "[INFO] Setting up database..." -ForegroundColor Yellow

# Start database services (commented out for direct code execution)
# Write-Host "[INFO] Starting database services..." -ForegroundColor Yellow
# docker-compose up -d postgres redis

# Wait for database to be ready (commented out for direct code execution)
# Write-Host "[INFO] Waiting for database to be ready..." -ForegroundColor Yellow
# Start-Sleep -Seconds 15

# Run database migrations (commented out for direct code execution)
# Write-Host "[INFO] Running database migrations..." -ForegroundColor Yellow
# Set-Location backend
# & ".\venv\Scripts\Activate.ps1"
# try {
#     alembic upgrade head
#     Write-Host "[SUCCESS] Database migrations completed" -ForegroundColor Green
# } catch {
#     Write-Host "[WARNING] Database migration failed, but continuing..." -ForegroundColor Yellow
# }
# Set-Location ..

# Write-Host "[SUCCESS] Database setup complete" -ForegroundColor Green

# Start all services (commented out for direct code execution)
# Write-Host "[INFO] Starting all services..." -ForegroundColor Yellow
# docker-compose up -d

# Wait for services to start (commented out for direct code execution)
# Write-Host "[INFO] Waiting for services to start..." -ForegroundColor Yellow
# Start-Sleep -Seconds 10

# Check service status (commented out for direct code execution)
# Write-Host "[INFO] Checking service status..." -ForegroundColor Yellow
# docker-compose ps

Write-Host "[SUCCESS] Environment setup complete!" -ForegroundColor Green
Write-Host "[INFO] Ready to run services manually:" -ForegroundColor Cyan
Write-Host "  - Frontend: http://localhost:3000 (when started)" -ForegroundColor White
Write-Host "  - Backend API: http://localhost:8000 (when started)" -ForegroundColor White
Write-Host "  - Database: localhost:5432 (when Docker containers are running)" -ForegroundColor White
Write-Host "  - Redis: localhost:6379 (when Docker containers are running)" -ForegroundColor White

Write-Host ""
Write-Host "[SUCCESS] Clean setup complete! 🎉" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Update backend\.env with your MATLAB path and other configurations" -ForegroundColor White
Write-Host "2. Install MATLAB Engine manually if you have MATLAB:" -ForegroundColor White
Write-Host "   cd 'C:\Program Files\MATLAB\R2023b\extern\engines\python'" -ForegroundColor White
Write-Host "   python setup.py install" -ForegroundColor White
Write-Host "3. Start backend: cd backend; .\venv\Scripts\Activate.ps1; uvicorn main:app --reload" -ForegroundColor White
Write-Host "4. Start frontend: cd frontend; npm start" -ForegroundColor White
Write-Host "5. Access the application at http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "For database setup (optional):" -ForegroundColor Cyan
Write-Host "- Start database: docker-compose up -d postgres redis" -ForegroundColor White
Write-Host "- Run migrations: cd backend; .\venv\Scripts\Activate.ps1; alembic upgrade head" -ForegroundColor White

Write-Host ""
Write-Host "[INFO] Starting backend in development mode..." -ForegroundColor Yellow
Set-Location backend
& ".\venv\Scripts\Activate.ps1"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\Activate.ps1; uvicorn main:app --reload --host 0.0.0.0 --port 8000"
Set-Location ..

Write-Host ""
Write-Host "[INFO] Starting frontend in development mode..." -ForegroundColor Yellow
Set-Location frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm start"
Set-Location ..

Write-Host ""
Write-Host "Setup completed! Press any key to continue..." -ForegroundColor Green
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
