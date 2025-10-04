from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from models.auth_models import UserRole


class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8, max_length=128)
    role: Optional[UserRole] = UserRole.USER


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str


class User(UserBase):
    """Schema for user response"""
    id: int
    role: UserRole

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token data"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[UserRole] = None