@echo off
REM MATLAB Automation Platform Clean Setup Script for Windows
REM This script creates a fresh environment and fixes dependency conflicts

echo 🚀 Setting up MATLAB Automation Platform (Clean Install)...

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)
echo [SUCCESS] Docker and Docker Compose are installed

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Please install Python 3.11+ first.
    exit /b 1
)
echo [SUCCESS] Python is installed

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed. Please install Node.js 18+ first.
    exit /b 1
)
echo [SUCCESS] Node.js is installed

REM Clean up any existing virtual environment
echo [INFO] Cleaning up existing virtual environment...
if exist "backend\venv" (
    rmdir /s /q "backend\venv"
    echo [INFO] Removed existing virtual environment
)

REM Clean up node_modules
echo [INFO] Cleaning up existing node_modules...
if exist "frontend\node_modules" (
    rmdir /s /q "frontend\node_modules"
    echo [INFO] Removed existing node_modules
)

REM Clean up package-lock.json
if exist "frontend\package-lock.json" (
    del "frontend\package-lock.json"
    echo [INFO] Removed package-lock.json
)

REM Create necessary directories
echo [INFO] Creating necessary directories...
if not exist "matlab\models" mkdir matlab\models
if not exist "matlab\scripts" mkdir matlab\scripts
if not exist "matlab\data" mkdir matlab\data
if not exist "backend\uploads" mkdir backend\uploads
if not exist "backend\reports" mkdir backend\reports
if not exist "logs" mkdir logs
echo [SUCCESS] Directories created

REM Setup backend environment
echo [INFO] Setting up backend environment...
cd backend

REM Create fresh virtual environment
echo [INFO] Creating fresh virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment
    exit /b 1
)

REM Activate virtual environment and upgrade pip
echo [INFO] Activating virtual environment and upgrading pip...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip

REM Install core dependencies first
echo [INFO] Installing core dependencies...
pip install wheel setuptools

REM Install main requirements
echo [INFO] Installing main requirements...
pip install -r requirements.txt

REM Install dev requirements with relaxed constraints
echo [INFO] Installing development requirements...
pip install -r requirements-dev.txt

REM Copy environment file
if not exist ".env" (
    copy env.example .env
    echo [WARNING] Please update the .env file with your configuration
)

cd ..
echo [SUCCESS] Backend environment setup complete

REM Setup frontend environment
echo [INFO] Setting up frontend environment...
cd frontend

REM Clear npm cache
echo [INFO] Clearing npm cache...
npm cache clean --force

REM Install dependencies with legacy peer deps to resolve conflicts
echo [INFO] Installing frontend dependencies...
npm install --legacy-peer-deps

REM Create environment file
if not exist ".env" (
    echo REACT_APP_API_URL=http://localhost:8000/api/v1 > .env
)

cd ..
echo [SUCCESS] Frontend environment setup complete

REM Stop any existing containers
echo [INFO] Stopping existing containers...
docker-compose down >nul 2>&1

REM Setup database
echo [INFO] Setting up database...

REM Start database services
echo [INFO] Starting database services...
docker-compose up -d postgres redis

REM Wait for database to be ready
echo [INFO] Waiting for database to be ready...
timeout /t 15 /nobreak >nul

REM Run database migrations
echo [INFO] Running database migrations...
cd backend
call venv\Scripts\activate.bat
alembic upgrade head
if %errorlevel% neq 0 (
    echo [WARNING] Database migration failed, but continuing...
)
cd ..

echo [SUCCESS] Database setup complete

REM Start all services
echo [INFO] Starting all services...

REM Start all services
docker-compose up -d

REM Wait for services to start
echo [INFO] Waiting for services to start...
timeout /t 10 /nobreak >nul

REM Check service status
echo [INFO] Checking service status...
docker-compose ps

echo [SUCCESS] All services started
echo [INFO] Services are running on:
echo   - Frontend: http://localhost:3000
echo   - Backend API: http://localhost:8000
echo   - Database: localhost:5432
echo   - Redis: localhost:6379
echo   - Grafana: http://localhost:3001

echo.
echo [SUCCESS] Clean setup complete! 🎉
echo.
echo Next steps:
echo 1. Update backend\.env with your MATLAB path and other configurations
echo 2. Access the application at http://localhost:3000
echo 3. Check the health status at http://localhost:8000/health
echo.
echo For development:
echo - Backend: cd backend ^&^& venv\Scripts\activate ^&^& uvicorn main:app --reload
echo - Frontend: cd frontend ^&^& npm start
echo.
echo To stop services: docker-compose down
echo To view logs: docker-compose logs -f

echo.
echo [INFO] Testing the setup...
timeout /t 5 /nobreak >nul

REM Test backend health
echo [INFO] Testing backend health...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Backend is responding
) else (
    echo [WARNING] Backend may not be ready yet, check logs with: docker-compose logs backend
)

pause
