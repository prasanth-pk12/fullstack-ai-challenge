# Task Manager App

A full-stack Task Manager application built with FastAPI (backend) and React (frontend), featuring real-time updates, file uploads, and role-based access control.

## Features

- **Authentication & Authorization**: JWT-based auth with role-based access (Admin/User)
- **Task Management**: Full CRUD operations for tasks with status tracking
- **File Attachments**: Upload and manage task attachments
- **Real-time Updates**: WebSocket integration for live task updates
- **External API Integration**: Motivational quotes from external APIs
- **Responsive UI**: Modern, clean interface built with React and TailwindCSS

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Robust relational database
- **SQLAlchemy**: ORM for database operations
- **JWT**: Secure authentication
- **WebSockets**: Real-time communication
- **Pytest**: Comprehensive testing

### Frontend
- **React**: Component-based UI library
- **TailwindCSS**: Utility-first CSS framework
- **React Router**: Client-side routing
- **Axios**: HTTP client for API communication
- **Jest & React Testing Library**: Frontend testing

## 🐳 Docker Setup (Recommended)

### Prerequisites
- Docker Desktop installed and running
- Docker Compose v3.8+

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/prasanth-pk12/fullstack-ai-challenge.git
   cd fullstack-ai-challenge
   ```

2. **Build and run the entire stack**
   ```bash
   # Build and start all services
   docker-compose up --build

   # Or run in detached mode
   docker-compose up --build -d
   ```

3. **Access the application**
   - **Frontend**: http://localhost:3000 or http://localhost
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs and http://localhost:8000/redoc
   - **Database**: localhost:5432

4. **Stop the services**
   ```bash
   # Stop and remove containers
   docker-compose down

   # Stop and remove containers + volumes (clears database)
   docker-compose down -v
   ```

### Docker Services

The `docker-compose.yml` includes three services:

1. **Database** (`database`):
   - PostgreSQL 15 Alpine
   - Port: 5432
   - Persistent volume for data
   - Health checks for service readiness

2. **Backend** (`backend`):
   - FastAPI with Python 3.11
   - Port: 8000
   - Depends on database health
   - File uploads volume mounted

3. **Frontend** (`frontend`):
   - React app served via Nginx
   - Port: 80 (and 3000 for development)
   - Proxies API calls to backend
   - Optimized production build

### Environment Variables

Key environment variables are configured in `docker-compose.yml`:

```yaml
# Backend
DATABASE_URL: postgresql://taskuser:taskpass@database:5432/taskmanager
SECRET_KEY: your-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES: 30

# Frontend
REACT_APP_API_URL: http://localhost:8000
REACT_APP_WS_URL: ws://localhost:8000
```

### Docker Commands

```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs database

# Rebuild specific service
docker-compose build backend
docker-compose up --build backend

# Execute commands in running containers
docker-compose exec backend bash
docker-compose exec database psql -U taskuser -d taskmanager

# Clean up everything
docker-compose down -v --rmi all
```

## 🔧 Local Development Setup

If you prefer to run services individually:

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r app/requirements.txt
   ```

3. **Set environment variables**
   ```bash
   export DATABASE_URL="postgresql://taskuser:taskpass@localhost:5432/taskmanager"
   export SECRET_KEY="your-secret-key"
   ```

4. **Run PostgreSQL** (using Docker)
   ```bash
   docker run --name taskmanager-db -e POSTGRES_DB=taskmanager -e POSTGRES_USER=taskuser -e POSTGRES_PASSWORD=taskpass -p 5432:5432 -d postgres:15-alpine
   ```

5. **Start the backend**
   ```bash
   export PYTHONPATH=app
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm start
   ```

## 🧪 Testing

### Backend Tests
```bash
cd backend
export PYTHONPATH=app
python -m pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

### E2E Tests
```bash
cd frontend
npm run cypress:run
```

## 🚀 Production Deployment

The Docker setup is production-ready with:

- **Multi-stage builds** for optimized image sizes
- **Health checks** for service monitoring
- **Security configurations** (non-root users, security headers)
- **Nginx optimization** (gzip, caching, SPA routing)
- **Persistent volumes** for data integrity
- **Proper networking** and service dependencies

## 📁 Project Structure

```
fullstack-ai-challenge/
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI/CD pipeline
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── requirements.txt     # Python dependencies
│   │   ├── database/            # Database configuration
│   │   ├── models/              # SQLAlchemy database models
│   │   ├── routers/             # API route handlers
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic services
│   │   └── uploads/             # File upload storage
│   ├── tests/                   # Backend test suite
│   │   ├── conftest.py          # Test configuration & fixtures
│   │   ├── test_auth.py         # Authentication tests
│   │   ├── test_tasks.py        # Task CRUD tests
│   │   ├── test_attachments.py  # File upload tests
│   │   ├── test_external.py     # External API tests
│   │   └── test_websockets.py   # WebSocket tests
│   ├── .dockerignore            # Docker build exclusions
│   ├── Dockerfile               # Backend container config
│   └── pytest.ini              # Test configuration
├── frontend/
│   ├── src/
│   │   ├── App.js               # Main React component
│   │   ├── api.js               # API client configuration
│   │   ├── components/          # Reusable UI components
│   │   ├── contexts/            # React context providers
│   │   ├── hooks/               # Custom React hooks
│   │   ├── pages/               # Page components (Login, Tasks)
│   │   ├── services/            # Frontend services
│   │   ├── tests/               # Frontend test files
│   │   └── utils/               # Utility functions
│   ├── cypress/                 # E2E test configuration
│   ├── e2e/                     # Cypress E2E tests
│   ├── public/                  # Static assets
│   ├── .dockerignore            # Docker build exclusions
│   ├── Dockerfile               # Frontend container config
│   ├── package.json             # Node.js dependencies
│   ├── tailwind.config.js       # TailwindCSS configuration
│   └── cypress.config.js        # Cypress test configuration
├── scripts/
│   ├── run-local-ci.bat         # Windows CI script
│   └── run-local-ci.sh          # Unix CI script
├── docker-compose.yml           # Multi-service orchestration
├── init.sql                     # Database initialization script
├── AI_PROMPTS.md                # AI development prompts log
└── README.md                    # This file
```

## 🛠️ Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 80, 3000, 8000, and 5432 are available
2. **Docker permission issues**: Make sure Docker daemon is running
3. **Database connection**: Wait for database health check to pass before starting backend

### Useful Commands

```bash
# Check Docker status
docker --version
docker-compose --version

# View container logs
docker-compose logs -f [service-name]

# Reset everything
docker-compose down -v
docker system prune -f
docker-compose up --build
```

## 📄 License

This project is licensed under the MIT License.
