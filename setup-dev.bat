@echo off
REM MATLAB Automation Platform Development Setup Script for Windows
REM This script sets up the platform for development without Docker builds

echo 🚀 Setting up MATLAB Automation Platform (Development Mode)...

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

REM Clean up node_modules and package-lock.json
echo [INFO] Cleaning up existing node_modules...
if exist "frontend\node_modules" (
    rmdir /s /q "frontend\node_modules"
    echo [INFO] Removed existing node_modules
)
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

REM Install minimal requirements to avoid conflicts
echo [INFO] Installing minimal requirements...
pip install -r requirements-minimal.txt

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

echo [SUCCESS] Development setup complete! 🎉
echo.
echo Next steps:
echo 1. Update backend\.env with your MATLAB path and other configurations
echo 2. Start the backend: cd backend ^&^& venv\Scripts\activate ^&^& uvicorn main:app --reload
echo 3. Start the frontend: cd frontend ^&^& npm start
echo 4. Access the application at http://localhost:3000
echo.
echo For database setup (optional):
echo - Install PostgreSQL locally or use Docker: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres
echo - Update DATABASE_URL in backend\.env
echo - Run migrations: cd backend ^&^& venv\Scripts\activate ^&^& alembic upgrade head

echo.
echo [INFO] Starting backend in development mode...
cd backend
call venv\Scripts\activate.bat
start "Backend" cmd /k "uvicorn main:app --reload --host 0.0.0.0 --port 8000"
cd ..

echo.
echo [INFO] Starting frontend in development mode...
cd frontend
start "Frontend" cmd /k "npm start"
cd ..

echo.
echo [SUCCESS] Development environment started! 🎉
echo.
echo Services are starting in separate windows:
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:3000
echo - API Docs: http://localhost:8000/docs
echo.
echo Press any key to continue...
pause
