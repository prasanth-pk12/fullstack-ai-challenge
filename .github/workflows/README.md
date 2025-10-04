# GitHub Actions CI/CD Pipeline for Task Manager

This directory contains the CI/CD pipeline configuration for the Task Manager application.

## Pipeline Overview

The CI/CD pipeline consists of the following jobs:

### 1. Backend Tests (`backend-tests`)
- **Matrix Strategy**: Tests against Python 3.9, 3.10, and 3.11
- **Test Categories**:
  - Unit tests (isolated component testing)
  - Integration tests (API endpoint testing)
  - Performance tests (load and benchmark testing)
  - WebSocket tests (real-time functionality testing)
- **Features**:
  - Pip dependency caching for faster builds
  - Separate test result artifacts for each test type
  - Detailed test reporting with durations

### 2. Frontend Tests (`frontend-tests`)
- **Matrix Strategy**: Tests against Node.js 18 and 20
- **Test Coverage**:
  - React unit tests with Jest and React Testing Library
  - Code coverage reporting
  - Test result artifacts
- **Features**:
  - npm dependency caching
  - Coverage reports uploaded as artifacts

### 3. Frontend E2E Tests (`frontend-e2e-tests`)
- **Dependencies**: Requires backend tests to pass first
- **Testing Framework**: Cypress
- **Test Environment**: Full-stack testing with both backend and frontend servers
- **Features**:
  - Automated server startup and health checks
  - Screenshot capture on test failures
  - Video recording of test runs
  - Artifact upload for debugging

### 4. Frontend Build (`frontend-build`)
- **Dependencies**: Requires frontend tests to pass
- **Purpose**: Production build verification
- **Features**:
  - Optimized production build
  - Build artifacts stored for 30 days
  - Build verification

### 5. Security Scan (`security-scan`)
- **Backend Security**:
  - Safety check for Python dependencies
  - Bandit security linting for code vulnerabilities
- **Frontend Security**:
  - npm audit for dependency vulnerabilities
- **Features**:
  - Security report artifacts
  - High-level vulnerability detection

### 6. Deployment Check (`deploy-check`)
- **Trigger**: Only runs on main branch
- **Dependencies**: Requires all other jobs to pass
- **Purpose**: Final verification before deployment
- **Features**:
  - Build artifact verification
  - Deployment readiness confirmation

## Pipeline Features

### Caching Strategy
- **Python Dependencies**: Cached using pip cache directory with requirements.txt hash
- **Node.js Dependencies**: Cached using npm built-in caching with package-lock.json

### Error Handling
- **Fail Fast**: Pipeline fails immediately if any critical step fails
- **Test Isolation**: Each test category runs independently
- **Detailed Logging**: Verbose output with test durations and failure details
- **Artifact Collection**: Test results, coverage, and failure artifacts always uploaded

### Optimization Features
- **Parallel Execution**: Multiple jobs run in parallel where possible
- **Matrix Strategy**: Multiple environment versions tested simultaneously
- **Smart Caching**: Dependency caching reduces build times
- **Conditional Execution**: Some jobs only run when needed

## Triggering the Pipeline

The pipeline runs on:
- **Push** to `main` or `develop` branches
- **Pull Requests** targeting `main` or `develop` branches

## Monitoring and Debugging

### Artifacts Available
- Backend test results (JUnit XML format)
- Frontend test coverage reports
- Cypress screenshots (on failure)
- Cypress videos (always)
- Security scan reports
- Production build artifacts

### Debugging Failed Builds
1. Check the specific job that failed
2. Review the detailed logs with `--tb=short` and `--durations=10` for tests
3. Download relevant artifacts for deeper analysis
4. Check security scan results for vulnerability issues

## Local Testing

To run the same tests locally:

```bash
# Backend tests
cd backend
python -m pytest tests/ -v --tb=short --durations=10

# Frontend tests
cd frontend
npm test -- --coverage --watchAll=false

# E2E tests (requires both servers running)
cd frontend
npm run cypress:run

# Production build
cd frontend
npm run build
```

## Pipeline Status

The pipeline ensures:
- ✅ All backend tests pass across multiple Python versions
- ✅ All frontend tests pass across multiple Node.js versions
- ✅ E2E tests verify full-stack functionality
- ✅ Security scans detect vulnerabilities
- ✅ Production build succeeds
- ✅ Code is ready for deployment

## Customization

To modify the pipeline:
1. Edit `.github/workflows/ci.yml`
2. Adjust matrix strategies for different versions
3. Add or remove test categories as needed
4. Update caching strategies for new dependencies
5. Modify security scan configurations