from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from database.connection import create_tables
from routers import auth_router, task_router, external_router, websocket_router
from services.auth_service import get_current_user, role_required
from services.websocket_service import start_heartbeat_task
from models.auth_models import UserRole, User
from schemas.auth_schemas import User as UserSchema
import os
import asyncio

# Create FastAPI app with comprehensive metadata
app = FastAPI(
    title="Task Manager Pro API",
    description="""
# Task Manager Pro - Full-Stack Application API

A comprehensive FastAPI backend application providing:
- **JWT Authentication** with role-based access control (USER/ADMIN)
- **Task Management** with full CRUD operations and file attachments
- **External API Integration** for motivational quotes with fallback handling
- **Real-time WebSocket Updates** for live task notifications
- **File Upload & Management** for task attachments
- **RESTful API Design** with comprehensive error handling

## Authentication

All protected endpoints require a valid JWT token. Include the token in the `Authorization` header:
```
Authorization: Bearer <your_jwt_token>
```

## User Roles

- **USER**: Can manage their own tasks and access basic features
- **ADMIN**: Full access to all tasks and administrative functions

## WebSocket Connections

Real-time updates are available via WebSocket at `/ws/tasks` endpoint.
Authentication is required via query parameter: `?token=<jwt_token>`

## Error Handling

All endpoints provide consistent error responses with detailed error messages,
proper HTTP status codes, and helpful debugging information.
    """,
    version="1.0.0",
    contact={
        "name": "Task Manager Pro Support",
        "email": "support@taskmanagerpro.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    tags_metadata=[
        {
            "name": "authentication",
            "description": "User registration, login, and JWT token management",
        },
        {
            "name": "tasks",
            "description": "Task CRUD operations, file attachments, and statistics",
        },
        {
            "name": "external",
            "description": "External API integration for motivational quotes",
        },
        {
            "name": "websockets",
            "description": "Real-time WebSocket connections and management",
        },
        {
            "name": "user",
            "description": "User profile and role-based access endpoints",
        },
        {
            "name": "admin",
            "description": "Administrative endpoints (admin role required)",
        },
        {
            "name": "health",
            "description": "Application health check and monitoring",
        },
        {
            "name": "root",
            "description": "Public API information endpoints",
        },
    ],
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "https://tasks.prasanthp.dev"],  # React development server origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Create uploads directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files for uploaded attachments
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Create database tables on startup
@app.on_event("startup")
async def startup():
    create_tables()
    # Start WebSocket heartbeat task
    start_heartbeat_task()

# Include routers
app.include_router(auth_router.router)
app.include_router(task_router.router)
app.include_router(external_router.router)
app.include_router(websocket_router.router)

# Protected route examples
@app.get("/", tags=["root"])
async def read_root():
    """
    Public endpoint - no authentication required
    """
    return {"message": "Welcome to the FastAPI Authentication API"}


@app.get("/profile", response_model=UserSchema, tags=["user"])
async def get_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile - requires authentication
    """
    return current_user


@app.get("/admin", tags=["admin"])
async def admin_only(current_user: User = Depends(role_required(UserRole.ADMIN))):
    """
    Admin only endpoint - requires admin role
    """
    return {"message": f"Hello admin {current_user.username}! You have admin access."}


@app.get("/user", tags=["user"])
async def user_access(current_user: User = Depends(role_required(UserRole.USER))):
    """
    User access endpoint - requires user role (admins can also access)
    """
    return {"message": f"Hello {current_user.username}! You have user access."}


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)