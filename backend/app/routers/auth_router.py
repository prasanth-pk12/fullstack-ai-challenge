from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.connection import get_db
from models.auth_models import UserRole
from schemas.auth_schemas import UserCreate, UserLogin, User as UserSchema, Token
from services.auth_service import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from services.auth_user_service import (
    get_user_by_username,
    get_user_by_email,
    create_user
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register", 
    response_model=UserSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with username, email, and password",
    responses={
        201: {
            "description": "User successfully created",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "username": "johndoe",
                        "email": "john@example.com",
                        "role": "USER"
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - Username or email already exists",
            "content": {
                "application/json": {
                    "examples": {
                        "username_exists": {
                            "summary": "Username already registered",
                            "value": {"detail": "Username already registered"}
                        },
                        "email_exists": {
                            "summary": "Email already registered", 
                            "value": {"detail": "Email already registered"}
                        }
                    }
                }
            }
        },
        422: {
            "description": "Validation Error - Invalid input data",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "email"],
                                "msg": "field required",
                                "type": "value_error.missing"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    **Request Body:**
    - **username**: 3-50 characters, must be unique
    - **email**: Valid email address, must be unique
    - **password**: Minimum 8 characters, maximum 128 characters
    - **role**: Optional, defaults to "USER" (can be "USER" or "ADMIN")
    
    **Authentication:** None required (public endpoint)
    
    **Returns:** User object with ID, username, email, and role (password excluded)
    
    **Business Rules:**
    - Usernames must be unique across all users
    - Email addresses must be unique across all users
    - Passwords are securely hashed before storage
    - Default role is "USER" unless specified otherwise
    """
    # Check if username already exists
    existing_user = get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = create_user(
        db=db,
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role or UserRole.USER
    )
    
    return db_user


@router.post(
    "/login", 
    response_model=Token,
    summary="User login",
    description="Authenticate user and return JWT access token",
    responses={
        200: {
            "description": "Successfully authenticated",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {
            "description": "Authentication failed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Incorrect username or password"
                    }
                }
            }
        },
        422: {
            "description": "Validation Error - Missing or invalid credentials",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "username"],
                                "msg": "field required",
                                "type": "value_error.missing"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user credentials and return JWT access token.
    
    **Request Body:**
    - **username**: The user's registered username
    - **password**: The user's password
    
    **Authentication:** None required (public endpoint)
    
    **Returns:** JWT access token for subsequent API calls
    
    **Token Usage:**
    Include the returned token in subsequent requests:
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Token Expiration:** Tokens expire after a configured time period.
    When expired, you'll receive a 401 error and need to login again.
    
    **Security Features:**
    - Passwords are verified against secure hashes
    - Tokens include user ID, username, and role information
    - Failed login attempts are logged for security monitoring
    """
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value
        },
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}