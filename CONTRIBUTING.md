# Contributing to MATLAB Automation Platform

Thank you for your interest in contributing to the MATLAB Automation Platform! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

## 🤝 Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

## 🚀 Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Git** installed and configured
- **Python 3.11+** for backend development
- **Node.js 18+** for frontend development
- **MATLAB R2020b+** (for testing MATLAB integration)
- **Docker** (optional, for containerized development)
- **PostgreSQL 13+** (or use Docker)

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/matlab-automation.git
   cd matlab-automation
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/matlab-automation.git
   ```

## 🛠️ Development Setup

### Backend Development

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Set up environment**:
   ```bash
   cp env.example .env
   # Edit .env with your local configuration
   ```

5. **Initialize database**:
   ```bash
   alembic upgrade head
   ```

6. **Start development server**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Development

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start development server**:
   ```bash
   npm start
   ```

### Docker Development

1. **Start all services**:
   ```bash
   docker-compose up -d
   ```

2. **View logs**:
   ```bash
   docker-compose logs -f
   ```

## 📝 Contributing Guidelines

### Types of Contributions

We welcome several types of contributions:

- **Bug fixes**: Fix issues and improve stability
- **New features**: Add new functionality
- **Documentation**: Improve or add documentation
- **Tests**: Add or improve test coverage
- **Performance**: Optimize existing code
- **UI/UX**: Improve user interface and experience

### Before You Start

1. **Check existing issues** to see if your contribution is already being worked on
2. **Create an issue** for significant changes to discuss the approach
3. **Fork the repository** and create a feature branch
4. **Follow the coding standards** outlined below

### Branch Naming

Use descriptive branch names:

- `feature/add-user-authentication`
- `bugfix/fix-model-upload-error`
- `docs/update-api-documentation`
- `refactor/optimize-database-queries`

## 🔄 Pull Request Process

### Before Submitting

1. **Update your fork**:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes** following the coding standards

4. **Run tests**:
   ```bash
   # Backend tests
   cd backend && pytest tests/ -v
   
   # Frontend tests
   cd frontend && npm test
   
   # Integration tests
   docker-compose -f docker-compose.test.yml up --abort-on-container-exit
   ```

5. **Update documentation** if needed

6. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add user authentication system"
   ```

### Commit Message Format

Use conventional commits format:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(auth): add JWT token authentication
fix(models): resolve model upload validation error
docs(api): update endpoint documentation
test(backend): add unit tests for user service
```

### Pull Request Template

When creating a PR, include:

1. **Description** of changes
2. **Related issues** (closes #123)
3. **Screenshots** for UI changes
4. **Testing instructions**
5. **Checklist** of completed items

### Review Process

1. **Automated checks** must pass (tests, linting, etc.)
2. **Code review** by maintainers
3. **Testing** on different environments
4. **Documentation** review
5. **Approval** and merge

## 🐛 Issue Reporting

### Bug Reports

When reporting bugs, include:

1. **Clear title** describing the issue
2. **Steps to reproduce** the problem
3. **Expected behavior** vs actual behavior
4. **Environment details**:
   - OS and version
   - Python/Node.js versions
   - MATLAB version
   - Browser (for frontend issues)
5. **Screenshots** or error messages
6. **Log files** if applicable

### Feature Requests

For new features, include:

1. **Clear description** of the feature
2. **Use case** and motivation
3. **Proposed implementation** (if you have ideas)
4. **Alternative solutions** considered

## 📏 Coding Standards

### Python (Backend)

- **Style**: Follow PEP 8
- **Type hints**: Use type annotations
- **Docstrings**: Use Google style docstrings
- **Imports**: Use absolute imports, group by standard/third-party/local
- **Line length**: Maximum 88 characters (Black formatter)

```python
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse


class UserService:
    """Service class for user operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user instance
            
        Raises:
            ValueError: If user already exists
        """
        # Implementation here
        pass
```

### TypeScript/React (Frontend)

- **Style**: Use Prettier and ESLint configurations
- **TypeScript**: Strict mode enabled
- **Components**: Functional components with hooks
- **Props**: Define interfaces for all props
- **Naming**: PascalCase for components, camelCase for functions

```typescript
import React, { useState, useEffect } from 'react';
import { Box, Typography, Button } from '@mui/material';

interface UserCardProps {
  user: User;
  onEdit: (user: User) => void;
  onDelete: (userId: number) => void;
}

const UserCard: React.FC<UserCardProps> = ({ user, onEdit, onDelete }) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleEdit = () => {
    onEdit(user);
  };

  return (
    <Box>
      <Typography variant="h6">{user.name}</Typography>
      <Button onClick={handleEdit}>Edit</Button>
    </Box>
  );
};

export default UserCard;
```

### General Guidelines

- **DRY**: Don't Repeat Yourself
- **SOLID**: Follow SOLID principles
- **Clean Code**: Write readable, maintainable code
- **Comments**: Explain why, not what
- **Error Handling**: Proper error handling and logging
- **Security**: Follow security best practices

## 🧪 Testing Guidelines

### Backend Testing

- **Unit tests**: Test individual functions and methods
- **Integration tests**: Test API endpoints and database interactions
- **Coverage**: Maintain at least 80% test coverage

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User


@pytest.fixture
def client():
    return TestClient(app)


def test_create_user(client: TestClient, db: Session):
    """Test user creation endpoint."""
    user_data = {
        "name": "John Doe",
        "email": "john@example.com"
    }
    
    response = client.post("/api/v1/users", json=user_data)
    
    assert response.status_code == 201
    assert response.json()["name"] == user_data["name"]
```

### Frontend Testing

- **Unit tests**: Test individual components and functions
- **Integration tests**: Test component interactions
- **E2E tests**: Test complete user workflows

```typescript
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { theme } from '../theme';
import UserCard from './UserCard';

const mockUser = {
  id: 1,
  name: 'John Doe',
  email: 'john@example.com'
};

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('UserCard', () => {
  it('renders user information correctly', () => {
    const mockOnEdit = jest.fn();
    const mockOnDelete = jest.fn();
    
    renderWithTheme(
      <UserCard 
        user={mockUser} 
        onEdit={mockOnEdit} 
        onDelete={mockOnDelete} 
      />
    );
    
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });
});
```

## 📚 Documentation

### Code Documentation

- **Docstrings**: Document all public functions and classes
- **Comments**: Explain complex logic and business rules
- **README**: Keep README.md updated
- **API Docs**: Use FastAPI's automatic documentation

### User Documentation

- **User Guide**: Step-by-step instructions for users
- **API Reference**: Complete API documentation
- **Troubleshooting**: Common issues and solutions
- **Examples**: Code examples and use cases

## 🏷️ Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers updated
- [ ] Release notes prepared
- [ ] Docker images built and pushed

## 🆘 Getting Help

### Resources

- **GitHub Issues**: For bug reports and feature requests
- **Discussions**: For questions and general discussion
- **Documentation**: Check existing docs first
- **Code Review**: Ask for help in PR comments

### Contact

- **Maintainers**: @maintainer1, @maintainer2
- **Email**: project@example.com
- **Discord**: [Join our community](https://discord.gg/example)

## 🙏 Recognition

Contributors will be recognized in:

- **README.md**: Contributors section
- **Release notes**: For significant contributions
- **GitHub**: Contributor statistics
- **Documentation**: Code comments and commit history

Thank you for contributing to the MATLAB Automation Platform! 🚀
