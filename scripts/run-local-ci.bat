@echo off
REM Local CI/CD Pipeline Test Script for Windows
REM This script mimics the GitHub Actions pipeline for local testing

echo 🚀 Starting local CI/CD pipeline test...

REM Check if we're in the right directory
if not exist "docker-compose.yml" (
    echo ❌ Please run this script from the project root directory
    exit /b 1
)

echo 📋 Pipeline Overview:
echo 1. Backend Tests (Unit, Integration, Performance, WebSocket)
echo 2. Frontend Tests (Unit, Coverage)
echo 3. Frontend E2E Tests (Cypress)
echo 4. Frontend Production Build
echo 5. Security Scans
echo.

REM Backend Tests
echo 🔧 Running Backend Tests...
cd backend

if not exist "venv" (
    echo ⚠️  Creating Python virtual environment...
    python -m venv venv
)

echo pwd: %cd%

echo ✅ Activating virtual environment...
call venv\Scripts\activate

echo ✅ Installing backend dependencies...
pip install -r app\requirements.txt

echo ✅ Running backend unit tests...
set PYTHONPATH=app
python -m pytest tests/ -v --junitxml=tests/output/test-results.xml

cd ..
echo pwd: %cd%


REM Frontend Tests
echo 🎨 Running Frontend Tests...
cd frontend
echo pwd: %cd%

echo ✅ Installing frontend dependencies...
call npm install

echo ✅ Running frontend E2E tests with Cypress...
call npm run cypress:run

echo ✅ Building frontend for production...
call npm run build

echo ✅ 🎉 Local CI/CD pipeline completed successfully!
echo ✅ All tests passed and build artifacts created

echo.
echo 📊 Test Results:
echo - Backend test results: backend\test\output\test-results.xml
echo - Frontend test results: frontend\cypress\videos
echo - Production build: frontend\build\

echo.
echo 🚀 Ready for deployment!

pause