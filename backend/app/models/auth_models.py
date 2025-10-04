from sqlalchemy import Column, Integer, String, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from database.connection import Base
import enum


class UserRole(enum.Enum):
    """User roles enumeration"""
    USER = "user"
    ADMIN = "admin"


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.USER, nullable=False)

    # Relationship to Task model
    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")
    
    # Relationship to Attachment model
    uploaded_files = relationship("Attachment", back_populates="uploader")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', role='{self.role.value}')>"