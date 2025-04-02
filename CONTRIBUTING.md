# Contributing to CloudSecOps Platform

First of all, thank you for considering contributing to the CloudSecOps Platform! Every contribution helps make the project better for everyone.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
  - [Code Contributions](#code-contributions)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
  - [Python Style Guide](#python-style-guide)
  - [JavaScript Style Guide](#javascript-style-guide)
- [Branch Naming Convention](#branch-naming-convention)
- [Commit Message Guidelines](#commit-message-guidelines)

## Code of Conduct

This project and everyone participating in it is governed by the CloudSecOps Platform Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to [maintainer_email@example.com](mailto:maintainer_email@example.com).

## How Can I Contribute?

### Reporting Bugs

- Use the issue tracker to report bugs
- Describe the bug in detail: what you expected to happen and what actually happened
- Include steps to reproduce the bug
- Add information about your environment (OS, browser, etc.)
- Include screenshots if possible

### Suggesting Features

- Use the issue tracker to suggest features
- Provide a clear description of the feature
- Explain why this feature would be useful to most users
- Consider how the feature would work with existing functionality

### Code Contributions

1. Look for open issues or create a new one to discuss your planned contribution
2. Fork the repository
3. Create a new branch for your feature or bugfix
4. Make your changes
5. Submit a pull request

## Development Setup

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/your-username/cloudsecops-platform.git
cd cloudsecops-platform

# Set up Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create a .env file with required environment variables
cp .env.example .env
# Edit .env with your configurations

# Run the backend in development mode
cd backend
uvicorn api.main:app --reload
```

### Frontend Setup

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

### Docker Development Setup

```bash
# Build and start all services
docker-compose up --build

# To run in background
docker-compose up -d
```

## Pull Request Process

1. Update the README.md and documentation with details of changes if needed
2. Make sure all tests pass
3. The PR should work for all supported environments
4. Get at least one reviewer to approve your changes
5. Maintainers will merge the PR when it's ready

## Style Guidelines

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use docstrings for all functions, classes, and modules
- Use type hints
- Run `black` and `isort` before committing

### JavaScript Style Guide

- Follow the [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- Use ES6+ features
- Use JSDoc for documentation
- Run ESLint before committing

## Branch Naming Convention

- `feature/short-description` - for new features
- `bugfix/issue-number-short-description` - for bug fixes
- `docs/short-description` - for documentation changes
- `refactor/short-description` - for code refactoring

## Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat: Add new feature`
- `fix: Fix bug`
- `docs: Update documentation`
- `style: Format code (no production code change)`
- `refactor: Refactor code (no functional change)`
- `test: Add or update tests`
- `chore: Update build tasks, package manager configs, etc.`

Thank you for contributing to the CloudSecOps Platform!