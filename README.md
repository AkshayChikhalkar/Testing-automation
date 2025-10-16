# MATLAB Automation Platform

A comprehensive web-based platform for automating MATLAB/Simulink model testing, execution, and reporting. This platform provides a modern interface for managing models, running tests, generating reports, and monitoring system performance.

## 🚀 Features

### Core Functionality
- **Model Management**: Upload, organize, and manage MATLAB/Simulink models
- **Test Execution**: Run automated tests on models with configurable parameters
- **Real-time Monitoring**: Track test progress and execution status
- **Advanced Reporting**: Generate comprehensive reports with charts and analytics
- **System Configuration**: Manage MATLAB paths, workers, and system settings

### Technical Features
- **Modern Web Interface**: Built with React, TypeScript, and Material-UI
- **RESTful API**: FastAPI backend with comprehensive endpoints
- **Real-time Updates**: WebSocket support for live test monitoring
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Docker Support**: Easy deployment with Docker containers
- **Database Integration**: PostgreSQL for data persistence
- **Authentication**: Secure user management and session handling

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   MATLAB        │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   Engine        │
│                 │    │                 │    │                 │
│ • Dashboard     │    │ • REST API      │    │ • Model Exec    │
│ • Models        │    │ • WebSockets    │    │ • Test Runner   │
│ • Test Runs     │    │ • Celery Tasks  │    │ • Report Gen    │
│ • Reports       │    │ • Database      │    │                 │
│ • Settings      │    │ • File Storage  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **MATLAB R2020b+** (with required toolboxes)
- **PostgreSQL 13+**
- **Docker** (optional, for containerized deployment)
- **Git**

## 🛠️ Installation

### Option 1: Docker Deployment (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd testing-automation
   ```

2. **Set up environment variables**
   ```bash
   cp backend/env.example backend/.env
   # Edit backend/.env with your configuration
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Option 2: Manual Installation

#### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   alembic upgrade head
   ```

6. **Start the backend**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm start
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory with the following variables:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/matlab_automation

# MATLAB Configuration
MATLAB_PATH=/usr/local/MATLAB/R2023b
MATLAB_MAX_WORKERS=4
MATLAB_TIMEOUT=300

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=104857600  # 100MB

# Celery (for background tasks)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### MATLAB Setup

1. **Install required MATLAB toolboxes**:
   - Simulink
   - Simulink Test
   - MATLAB Compiler
   - Parallel Computing Toolbox (optional)

2. **Configure MATLAB paths** in the settings panel

3. **Set up model validation scripts** in the `matlab/scripts` directory

## 📖 Usage

### Getting Started

1. **Access the Dashboard**
   - Open your browser and navigate to http://localhost:3000
   - The dashboard provides an overview of your models and recent test runs

2. **Upload Models**
   - Navigate to the Models page
   - Click "Add Model" to upload MATLAB/Simulink models
   - Configure model parameters and metadata

3. **Run Tests**
   - Go to the Test Runs page
   - Create a new test run and select a model
   - Configure test parameters and execute

4. **View Reports**
   - Access the Reports page for detailed analytics
   - Filter by date range and model
   - Export reports in PDF or Excel format

5. **Configure Settings**
   - Use the Settings page to configure MATLAB paths
   - Adjust system parameters and preferences
   - Manage user accounts and permissions

### API Usage

The platform provides a comprehensive REST API. Access the interactive documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Example API calls:

```bash
# Get all models
curl -X GET "http://localhost:8000/api/v1/models"

# Create a new test run
curl -X POST "http://localhost:8000/api/v1/test-runs" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Run 1", "model_id": 1, "parameters": {}}'

# Get test run status
curl -X GET "http://localhost:8000/api/v1/test-runs/1/status"
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Integration Tests
```bash
# Run full test suite
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 📊 Monitoring

### Health Checks
- Backend health: http://localhost:8000/api/v1/health
- Database status: http://localhost:8000/api/v1/health/database
- MATLAB status: http://localhost:8000/api/v1/health/matlab

### Logs
- Application logs: `logs/application.log`
- Test execution logs: `logs/test_runs/`
- Error logs: `logs/errors.log`

## 🚀 Deployment

### Production Deployment

1. **Build production images**
   ```bash
   docker-compose -f docker-compose.prod.yml build
   ```

2. **Deploy with Docker Swarm or Kubernetes**
   ```bash
   docker stack deploy -c docker-compose.prod.yml matlab-automation
   ```

3. **Set up reverse proxy** (nginx recommended)
4. **Configure SSL certificates**
5. **Set up monitoring and logging**

### Environment-specific Configurations

- **Development**: Use `docker-compose.yml`
- **Testing**: Use `docker-compose.test.yml`
- **Production**: Use `docker-compose.prod.yml`

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `npm test` and `pytest`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [API Documentation](http://localhost:8000/docs)
- [User Guide](docs/user-guide.md)
- [Developer Guide](docs/developer-guide.md)

### Getting Help
- Create an issue on GitHub
- Check the [FAQ](docs/faq.md)
- Join our community discussions

### Known Issues
- See [GitHub Issues](https://github.com/your-org/matlab-automation/issues)

## 🗺️ Roadmap

### Version 2.0 (Planned)
- [ ] Advanced model versioning
- [ ] CI/CD integration
- [ ] Cloud deployment support
- [ ] Advanced analytics dashboard
- [ ] Multi-user collaboration features

### Version 1.1 (In Progress)
- [ ] Enhanced reporting features
- [ ] Model comparison tools
- [ ] Performance optimization
- [ ] Additional export formats

## 🙏 Acknowledgments

- MATLAB and Simulink by MathWorks
- React and Material-UI communities
- FastAPI and Python communities
- All contributors and users

---

**Made with ❤️ for the MATLAB community**