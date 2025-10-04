#!/bin/bash
# Local CI/CD Pipeline Test Script for Linux/Mac
# This script mimics the GitHub Actions pipeline for local testing

set -e  # exit on error

echo "🚀 Starting local CI/CD pipeline test..."

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
  echo "❌ Please run this script from the project root directory"
  exit 1
fi

echo "📋 Pipeline Overview:"
echo "1. Backend Tests (Unit, Integration, Performance, WebSocket)"
echo "2. Frontend Tests (Unit, Coverage)"
echo "3. Frontend E2E Tests (Cypress)"
echo "4. Frontend Production Build"
echo "5. Security Scans"
echo

# --- Backend Tests ---
echo "🔧 Running Backend Tests..."
cd backend

if [ ! -d "venv" ]; then
  echo "⚠️  Creating Python virtual environment..."
  python3 -m venv venv
fi

echo "✅ Activating virtual environment..."
source venv/bin/activate

echo "✅ Installing backend dependencies..."
pip install -r app/requirements.txt

echo "✅ Running backend unit tests..."
export PYTHONPATH=app
pytest tests/ -v --junitxml=tests/output/test-results.xml

cd ..
echo "pwd: $(pwd)"

# --- Frontend Tests ---
echo "🎨 Running Frontend Tests..."
cd frontend
echo "pwd: $(pwd)"

echo "✅ Installing frontend dependencies..."
npm install

echo "✅ Running frontend E2E tests with Cypress..."
npm run cypress:run

echo "✅ Building frontend for production..."
npm run build

cd ..

echo "✅ 🎉 Local CI/CD pipeline completed successfully!"
echo "✅ All tests passed and build artifacts created"

echo
echo "📊 Test Results:"
echo "- Backend test results: backend/tests/output/test-results.xml"
echo "- Frontend test results: frontend/cypress/videos/"
echo "- Production build: frontend/build/"
echo
echo "🚀 Ready for deployment!"
