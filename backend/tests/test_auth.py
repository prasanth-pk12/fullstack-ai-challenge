import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from main import app
from database.connection import get_db, Base
from models.auth_models import User, UserRole
from services.auth_service import get_password_hash

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def setup_database():
    """Create tables before each test and drop them after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user_data():
    """Sample user data for tests"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "role": "user"
    }


@pytest.fixture
def test_admin_data():
    """Sample admin data for tests"""
    return {
        "username": "adminuser",
        "email": "admin@example.com",
        "password": "adminpassword123",
        "role": "admin"
    }


class TestUserRegistration:
    """Test user registration functionality"""
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, setup_database, test_user_data):
        """Test successful user registration"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/auth/register", json=test_user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert data["role"] == test_user_data["role"]
        assert "id" in data
        assert "password" not in data  # Password should not be returned
    
    @pytest.mark.asyncio
    async def test_register_admin_success(self, setup_database, test_admin_data):
        """Test successful admin registration"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/auth/register", json=test_admin_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"
    
    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, setup_database, test_user_data):
        """Test registration with duplicate username"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Register first user
            await ac.post("/auth/register", json=test_user_data)
            
            # Try to register with same username
            duplicate_data = test_user_data.copy()
            duplicate_data["email"] = "different@example.com"
            response = await ac.post("/auth/register", json=duplicate_data)
        
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, setup_database, test_user_data):
        """Test registration with duplicate email"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Register first user
            await ac.post("/auth/register", json=test_user_data)
            
            # Try to register with same email
            duplicate_data = test_user_data.copy()
            duplicate_data["username"] = "differentuser"
            response = await ac.post("/auth/register", json=duplicate_data)
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_register_invalid_email(self, setup_database):
        """Test registration with invalid email"""
        invalid_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "testpassword123",
            "role": "user"
        }
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/auth/register", json=invalid_data)
        
        assert response.status_code == 422  # Validation error


class TestUserLogin:
    """Test user login functionality with JSON requests"""
    
    @pytest.mark.asyncio
    async def test_login_success(self, setup_database, test_user_data):
        """Test successful login with JSON"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Register user first
            await ac.post("/auth/register", json=test_user_data)
            
            # Login with JSON data
            login_data = {
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
            response = await ac.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_wrong_username(self, setup_database, test_user_data):
        """Test login with wrong username"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Register user first
            await ac.post("/auth/register", json=test_user_data)
            
            # Try login with wrong username
            login_data = {
                "username": "wronguser",
                "password": test_user_data["password"]
            }
            response = await ac.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, setup_database, test_user_data):
        """Test login with wrong password"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Register user first
            await ac.post("/auth/register", json=test_user_data)
            
            # Try login with wrong password
            login_data = {
                "username": test_user_data["username"],
                "password": "wrongpassword"
            }
            response = await ac.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]


class TestRoleBasedAccess:
    """Test role-based access control"""
    
    async def get_access_token(self, user_data):
        """Helper function to get access token"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Register user
            await ac.post("/auth/register", json=user_data)
            
            # Login with JSON data
            login_data = {
                "username": user_data["username"],
                "password": user_data["password"]
            }
            response = await ac.post("/auth/login", json=login_data)
            return response.json()["access_token"]
    
    @pytest.mark.asyncio
    async def test_profile_access_with_token(self, setup_database, test_user_data):
        """Test accessing profile with valid token"""
        token = await self.get_access_token(test_user_data)
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            headers = {"Authorization": f"Bearer {token}"}
            response = await ac.get("/profile", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user_data["username"]
    
    @pytest.mark.asyncio
    async def test_profile_access_without_token(self, setup_database):
        """Test accessing profile without token"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/profile")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_admin_access_with_admin_role(self, setup_database, test_admin_data):
        """Test admin endpoint access with admin role"""
        token = await self.get_access_token(test_admin_data)
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            headers = {"Authorization": f"Bearer {token}"}
            response = await ac.get("/admin", headers=headers)
        
        assert response.status_code == 200
        assert "admin access" in response.json()["message"]
    
    @pytest.mark.asyncio
    async def test_admin_access_with_user_role(self, setup_database, test_user_data):
        """Test admin endpoint access with user role (should fail)"""
        token = await self.get_access_token(test_user_data)
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            headers = {"Authorization": f"Bearer {token}"}
            response = await ac.get("/admin", headers=headers)
        
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_user_access_with_user_role(self, setup_database, test_user_data):
        """Test user endpoint access with user role"""
        token = await self.get_access_token(test_user_data)
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            headers = {"Authorization": f"Bearer {token}"}
            response = await ac.get("/user", headers=headers)
        
        assert response.status_code == 200
        assert "user access" in response.json()["message"]
    
    @pytest.mark.asyncio
    async def test_user_access_with_admin_role(self, setup_database, test_admin_data):
        """Test user endpoint access with admin role (admins can access user endpoints)"""
        token = await self.get_access_token(test_admin_data)
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            headers = {"Authorization": f"Bearer {token}"}
            response = await ac.get("/user", headers=headers)
        
        assert response.status_code == 200
        assert "user access" in response.json()["message"]


class TestPublicEndpoints:
    """Test public endpoints"""
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """Test root endpoint (public)"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/")
        
        assert response.status_code == 200
        assert "Welcome" in response.json()["message"]
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"