from fastapi import FastAPI, Depends, HTTPException, status
from database.connection import create_tables
from routers import auth_router
from services.auth_service import get_current_user, role_required
from models.auth_models import UserRole, User
from schemas.auth_schemas import User as UserSchema

# Create FastAPI app
app = FastAPI(
    title="FastAPI Authentication API",
    description="A FastAPI application with JWT-based authentication and role management",
    version="1.0.0"
)

# Create database tables on startup
@app.on_event("startup")
async def startup():
    create_tables()

# Include routers
app.include_router(auth_router.router)

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