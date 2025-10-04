from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from database.connection import create_tables
from routers import auth_router, task_router, external_router
from services.auth_service import get_current_user, role_required
from models.auth_models import UserRole, User
from schemas.auth_schemas import User as UserSchema
import os

# Create FastAPI app
app = FastAPI(
    title="FastAPI Authentication, Task & External API",
    description="A FastAPI application with JWT authentication, task management, file uploads, and external data fetching",
    version="1.0.0"
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

# Include routers
app.include_router(auth_router.router)
app.include_router(task_router.router)
app.include_router(external_router.router)

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