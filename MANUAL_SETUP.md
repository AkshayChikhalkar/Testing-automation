# Manual Setup Guide - MATLAB Automation Platform

This guide provides step-by-step instructions to manually set up the MATLAB Automation Platform, avoiding the dependency conflicts encountered in the automated setup.

## Prerequisites

1. **Docker Desktop** - Download and install from [docker.com](https://www.docker.com/products/docker-desktop/)
2. **Python 3.11+** - Download from [python.org](https://www.python.org/downloads/)
3. **Node.js 18+** - Download from [nodejs.org](https://nodejs.org/)
4. **MATLAB R2020b+** - For model execution (optional for initial setup)

## Step 1: Clean Environment Setup

### 1.1 Remove Existing Setup (if any)
```bash
# Remove existing virtual environment
rmdir /s /q backend\venv

# Remove existing node_modules
rmdir /s /q frontend\node_modules

# Remove package-lock.json
del frontend\package-lock.json

# Stop any running containers
docker-compose down
```

### 1.2 Create Directories
```bash
mkdir matlab\models
mkdir matlab\scripts
mkdir matlab\data
mkdir backend\uploads
mkdir backend\reports
mkdir logs
```

## Step 2: Backend Setup

### 2.1 Create Virtual Environment
```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

### 2.2 Upgrade pip and Install Core Dependencies
```bash
python -m pip install --upgrade pip
pip install wheel setuptools
```

### 2.3 Install Requirements (Choose one approach)

#### Option A: Minimal Requirements (Recommended for initial setup)
```bash
pip install -r requirements-minimal.txt
```

#### Option B: Full Requirements (if minimal works)
```bash
pip install -r requirements.txt
```

#### Option C: Install Core Dependencies Individually
```bash
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install sqlalchemy==2.0.23
pip install alembic==1.13.1
pip install psycopg2-binary==2.9.9
pip install celery==5.3.4
pip install redis==5.0.1
pip install pydantic==2.5.0
pip install python-dotenv==1.0.0
pip install structlog==23.2.0
```

### 2.4 Configure Environment
```bash
copy env.example .env
```

Edit `.env` file with your configuration:
```bash
# Update these values
MATLAB_PATH=C:\Program Files\MATLAB\R2023b
DATABASE_URL=postgresql://matlab_user:matlab_password@localhost:5432/matlab_automation
SECRET_KEY=your-super-secret-key-change-this
```

## Step 3: Frontend Setup

### 3.1 Install Dependencies
```bash
cd ..\frontend
npm cache clean --force
npm install --legacy-peer-deps
```

### 3.2 Configure Environment
```bash
echo REACT_APP_API_URL=http://localhost:8000/api/v1 > .env
```

## Step 4: Database Setup

### 4.1 Start Database Services
```bash
cd ..
docker-compose up -d postgres redis
```

### 4.2 Wait for Database
```bash
# Wait 15-30 seconds for database to be ready
timeout /t 20
```

### 4.3 Run Migrations
```bash
cd backend
venv\Scripts\activate
alembic upgrade head
cd ..
```

## Step 5: Start Services

### 5.1 Start All Services
```bash
docker-compose up -d
```

### 5.2 Check Service Status
```bash
docker-compose ps
```

### 5.3 View Logs (if needed)
```bash
docker-compose logs -f
```

## Step 6: Verify Setup

### 6.1 Test Backend Health
```bash
curl http://localhost:8000/health
```

### 6.2 Test Frontend
Open browser and go to: http://localhost:3000

### 6.3 Test Database Connection
```bash
curl http://localhost:8000/health/database
```

## Development Mode

### Backend Development
```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm start
```

### Celery Worker (for background tasks)
```bash
cd backend
venv\Scripts\activate
celery -A app.core.celery worker --loglevel=info
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   netstat -ano | findstr :8000
   # Kill the process
   taskkill /PID <PID> /F
   ```

2. **Database Connection Failed**
   ```bash
   # Restart database
   docker-compose restart postgres
   # Check logs
   docker-compose logs postgres
   ```

3. **MATLAB Engine Not Found**
   - Ensure MATLAB is installed
   - Update MATLAB_PATH in .env file
   - Install MATLAB Engine for Python:
     ```bash
     cd "C:\Program Files\MATLAB\R2023b\extern\engines\python"
     python setup.py install
     ```

4. **Frontend Build Errors**
   ```bash
   # Clear cache and reinstall
   cd frontend
   npm cache clean --force
   rmdir /s /q node_modules
   del package-lock.json
   npm install --legacy-peer-deps
   ```

### Service URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Grafana**: http://localhost:3001

### Useful Commands

```bash
# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart backend

# Check service status
docker-compose ps

# Remove all containers and volumes
docker-compose down -v
```

## Next Steps

1. **Configure MATLAB**: Update the MATLAB path in `.env`
2. **Upload Models**: Use the web interface to upload your first model
3. **Create Test Run**: Execute your first test
4. **Monitor**: Check the dashboard for system status

## Support

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Verify health status: `curl http://localhost:8000/health`
3. Ensure all prerequisites are installed
4. Try the minimal requirements approach first

---

**Note**: This manual setup avoids the dependency conflicts by using more flexible version constraints and the `--legacy-peer-deps` flag for npm.
