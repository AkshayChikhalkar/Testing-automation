@echo off
REM MATLAB Automation Platform Setup Script for Windows
REM This script sets up the development environment for the MATLAB Automation Platform

echo 🚀 Setting up MATLAB Automation Platform...

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

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    python -m venv venv
)

REM Activate virtual environment and install dependencies
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
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

REM Install dependencies
npm install

REM Create environment file
if not exist ".env" (
    echo REACT_APP_API_URL=http://localhost:8000/api/v1 > .env
)

cd ..
echo [SUCCESS] Frontend environment setup complete

REM Setup database
echo [INFO] Setting up database...

REM Start database services
docker-compose up -d postgres redis

REM Wait for database to be ready
echo [INFO] Waiting for database to be ready...
timeout /t 10 /nobreak >nul

REM Run database migrations
cd backend
call venv\Scripts\activate.bat
alembic upgrade head
cd ..

echo [SUCCESS] Database setup complete

REM Start services
echo [INFO] Starting all services...

REM Start all services
docker-compose up -d

echo [SUCCESS] All services started
echo [INFO] Services are running on:
echo   - Frontend: http://localhost:3000
echo   - Backend API: http://localhost:8000
echo   - Database: localhost:5432
echo   - Redis: localhost:6379
echo   - Grafana: http://localhost:3001

echo.
echo [SUCCESS] Setup complete! 🎉
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

pause
