#!/bin/bash

# MATLAB Automation Platform Setup Script
# This script sets up the development environment for the MATLAB Automation Platform

set -e

echo "🚀 Setting up MATLAB Automation Platform..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.11+ first."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_success "Python $PYTHON_VERSION is installed"
}

# Check if Node.js is installed
check_node() {
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 18+ first."
        exit 1
    fi
    
    NODE_VERSION=$(node --version)
    print_success "Node.js $NODE_VERSION is installed"
}

# Check if MATLAB is available
check_matlab() {
    if command -v matlab &> /dev/null; then
        print_success "MATLAB is available"
    else
        print_warning "MATLAB is not found in PATH. Make sure MATLAB is installed and accessible."
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p matlab/models
    mkdir -p matlab/scripts
    mkdir -p matlab/data
    mkdir -p backend/uploads
    mkdir -p backend/reports
    mkdir -p logs
    
    print_success "Directories created"
}

# Setup backend environment
setup_backend() {
    print_status "Setting up backend environment..."
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    
    # Copy environment file
    if [ ! -f ".env" ]; then
        cp env.example .env
        print_warning "Please update the .env file with your configuration"
    fi
    
    cd ..
    print_success "Backend environment setup complete"
}

# Setup frontend environment
setup_frontend() {
    print_status "Setting up frontend environment..."
    
    cd frontend
    
    # Install dependencies
    npm install
    
    # Create environment file
    if [ ! -f ".env" ]; then
        echo "REACT_APP_API_URL=http://localhost:8000/api/v1" > .env
    fi
    
    cd ..
    print_success "Frontend environment setup complete"
}

# Setup database
setup_database() {
    print_status "Setting up database..."
    
    # Start database services
    docker-compose up -d postgres redis
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    sleep 10
    
    # Run database migrations
    cd backend
    source venv/bin/activate
    alembic upgrade head
    cd ..
    
    print_success "Database setup complete"
}

# Start services
start_services() {
    print_status "Starting all services..."
    
    # Start all services
    docker-compose up -d
    
    print_success "All services started"
    print_status "Services are running on:"
    echo "  - Frontend: http://localhost:3000"
    echo "  - Backend API: http://localhost:8000"
    echo "  - Database: localhost:5432"
    echo "  - Redis: localhost:6379"
    echo "  - Grafana: http://localhost:3001"
}

# Main setup function
main() {
    echo "MATLAB Automation Platform Setup"
    echo "================================="
    
    # Check prerequisites
    check_docker
    check_python
    check_node
    check_matlab
    
    # Setup environment
    create_directories
    setup_backend
    setup_frontend
    setup_database
    
    # Start services
    start_services
    
    echo ""
    print_success "Setup complete! 🎉"
    echo ""
    echo "Next steps:"
    echo "1. Update backend/.env with your MATLAB path and other configurations"
    echo "2. Access the application at http://localhost:3000"
    echo "3. Check the health status at http://localhost:8000/health"
    echo ""
    echo "For development:"
    echo "- Backend: cd backend && source venv/bin/activate && uvicorn main:app --reload"
    echo "- Frontend: cd frontend && npm start"
    echo ""
    echo "To stop services: docker-compose down"
    echo "To view logs: docker-compose logs -f"
}

# Run main function
main "$@"
