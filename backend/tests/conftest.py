import pytest
import asyncio
import os
import tempfile
import sys
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Direct imports (PYTHONPATH should be set to app directory)
from main import app
from database.connection import get_db, Base
from models.auth_models import User, UserRole
from models.task_models import Task, TaskStatus
from models.attachment_models import Attachment
from services.auth_service import get_password_hash, create_access_token


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    # Drop and recreate all tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    app.dependency_overrides[get_db] = override_get_db
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(scope="function")
async def async_client(db_session):
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        role=UserRole.USER
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_admin(db_session):
    """Create a test admin user."""
    admin = User(
        username="testadmin",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass123"),
        role=UserRole.ADMIN
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture(scope="function")
def user_token(test_user):
    """Create a JWT token for test user."""
    return create_access_token(data={"sub": test_user.username})


@pytest.fixture(scope="function")
def admin_token(test_admin):
    """Create a JWT token for test admin."""
    return create_access_token(data={"sub": test_admin.username})


@pytest.fixture(scope="function")
def auth_headers_user(user_token):
    """Create authorization headers for test user."""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture(scope="function")
def auth_headers_admin(admin_token):
    """Create authorization headers for test admin."""
    return {"Authorization": f"Bearer {admin_token}"}


# Additional fixtures for testing multiple users
@pytest.fixture(scope="function")
def test_users(db_session):
    """Create multiple test users for testing RBAC"""
    # Create admin user
    admin_user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ADMIN
    )
    
    # Create regular user 1
    user1 = User(
        username="user1",
        email="user1@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.USER
    )
    
    # Create regular user 2
    user2 = User(
        username="user2", 
        email="user2@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.USER
    )
    
    db_session.add_all([admin_user, user1, user2])
    db_session.commit()
    db_session.refresh(admin_user)
    db_session.refresh(user1)
    db_session.refresh(user2)
    
    return {
        "admin": admin_user,
        "user1": user1,
        "user2": user2
    }


@pytest.fixture(scope="function")
def auth_tokens(test_users):
    """Create authentication tokens for test users"""
    return {
        "admin": f"Bearer {create_access_token(data={'sub': test_users['admin'].username})}",
        "user1": f"Bearer {create_access_token(data={'sub': test_users['user1'].username})}",
        "user2": f"Bearer {create_access_token(data={'sub': test_users['user2'].username})}"
    }


@pytest.fixture(scope="function")
def temp_file():
    """Create a temporary file for upload tests."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tf:
        tf.write(b"Test file content")
        temp_path = tf.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)