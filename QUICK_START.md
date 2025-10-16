# Quick Start Guide - MATLAB Automation Platform

## 🚀 Quick Setup (Recommended)

### Option 1: PowerShell Script (Recommended)
```powershell
# Run the PowerShell setup script
.\setup-clean.ps1
```

### Option 2: Manual Step-by-Step

## Step 1: Clean Environment
```bash
# Remove existing setup
rmdir /s /q backend\venv
rmdir /s /q frontend\node_modules
del frontend\package-lock.json
docker-compose down
```

## Step 2: Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install wheel setuptools
pip install -r requirements-minimal.txt
copy env.example .env
cd ..
```

## Step 3: Frontend Setup
```bash
cd frontend
npm cache clean --force
npm install --legacy-peer-deps
echo REACT_APP_API_URL=http://localhost:8000/api/v1 > .env
cd ..
```

## Step 4: Database Setup
```bash
docker-compose up -d postgres redis
timeout /t 20
cd backend
venv\Scripts\activate
alembic upgrade head
cd ..
```

## Step 5: Start Services
```bash
docker-compose up -d
```

## Step 6: Verify Setup
```bash
# Test backend
curl http://localhost:8000/health

# Open frontend
# Go to: http://localhost:3000
```

## 🔧 Configuration

Edit `backend\.env`:
```bash
MATLAB_PATH=C:\Program Files\MATLAB\R2023b
DATABASE_URL=postgresql://matlab_user:matlab_password@localhost:5432/matlab_automation
SECRET_KEY=your-super-secret-key-change-this
```

## 🚨 Troubleshooting

### If you get permission errors:
1. Run PowerShell as Administrator
2. Or use the manual step-by-step approach

### If you get dependency conflicts:
1. Use `requirements-minimal.txt` instead of `requirements.txt`
2. Use `--legacy-peer-deps` for npm install

### If services don't start:
```bash
docker-compose logs -f
docker-compose down
docker-compose up -d
```

## 📊 Service URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Grafana**: http://localhost:3001

## 🎯 Next Steps

1. **Configure MATLAB**: Update MATLAB path in `.env`
2. **Upload Models**: Use the web interface
3. **Create Test Run**: Execute your first test
4. **Monitor**: Check the dashboard

## 💡 Development Mode

```bash
# Backend (Terminal 1)
cd backend
venv\Scripts\activate
uvicorn main:app --reload

# Frontend (Terminal 2)
cd frontend
npm start

# Celery Worker (Terminal 3)
cd backend
venv\Scripts\activate
celery -A app.core.celery worker --loglevel=info
```

---

**Note**: The `requirements-minimal.txt` file contains only the essential dependencies to avoid conflicts during initial setup. You can install additional dependencies later as needed.
