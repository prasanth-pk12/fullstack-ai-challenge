import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from main import app
from database.connection import get_db, Base
from models.auth_models import User, UserRole
from models.task_models import Task, TaskStatus
from services.auth_service import get_password_hash

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def setup_database():
    """Create database tables for each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
async def test_users(setup_database):
    """Create test users"""
    db = TestingSessionLocal()
    
    # Create admin user
    admin_user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ADMIN
    )
    
    # Create regular user
    regular_user = User(
        username="user1",
        email="user1@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.USER
    )
    
    # Create another regular user
    another_user = User(
        username="user2", 
        email="user2@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.USER
    )
    
    db.add_all([admin_user, regular_user, another_user])
    db.commit()
    db.refresh(admin_user)
    db.refresh(regular_user)
    db.refresh(another_user)
    
    db.close()
    return {
        "admin": admin_user,
        "user1": regular_user,
        "user2": another_user
    }


@pytest.fixture(scope="function")
async def auth_tokens(test_users):
    """Get authentication tokens for test users"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Login admin
        admin_response = await ac.post("/auth/login", json={
            "username": "admin",
            "password": "password123"
        })
        admin_token = admin_response.json()["access_token"]
        
        # Login user1
        user1_response = await ac.post("/auth/login", json={
            "username": "user1", 
            "password": "password123"
        })
        user1_token = user1_response.json()["access_token"]
        
        # Login user2
        user2_response = await ac.post("/auth/login", json={
            "username": "user2",
            "password": "password123"
        })
        user2_token = user2_response.json()["access_token"]
        
        return {
            "admin": f"Bearer {admin_token}",
            "user1": f"Bearer {user1_token}",
            "user2": f"Bearer {user2_token}"
        }


class TestTaskCRUD:
    """Test task CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_task_success(self, auth_tokens):
        """Test successful task creation"""
        task_data = {
            "title": "Test Task",
            "description": "This is a test task",
            "status": "todo",
            "due_date": "2025-12-31T23:59:59",
            "attachments": ["file1.pdf", "file2.txt"]
        }
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                "/tasks/",
                json=task_data,
                headers={"Authorization": auth_tokens["user1"]}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["description"] == task_data["description"]
        assert data["status"] == task_data["status"]
        assert data["owner_id"] == 2  # user1 ID
        assert data["attachments"] == task_data["attachments"]
    
    @pytest.mark.asyncio
    async def test_create_task_unauthorized(self):
        """Test task creation without authentication"""
        task_data = {
            "title": "Test Task",
            "description": "This is a test task"
        }
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/tasks/", json=task_data)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_tasks_user_sees_own_only(self, auth_tokens):
        """Test that users only see their own tasks"""
        # Create tasks for different users
        task1_data = {"title": "User1 Task", "description": "Task by user1"}
        task2_data = {"title": "User2 Task", "description": "Task by user2"}
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # User1 creates a task
            await ac.post(
                "/tasks/",
                json=task1_data,
                headers={"Authorization": auth_tokens["user1"]}
            )
            
            # User2 creates a task
            await ac.post(
                "/tasks/",
                json=task2_data,
                headers={"Authorization": auth_tokens["user2"]}
            )
            
            # User1 gets tasks - should only see their own
            response = await ac.get(
                "/tasks/",
                headers={"Authorization": auth_tokens["user1"]}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "User1 Task"
        assert data[0]["owner_id"] == 2  # user1 ID
    
    @pytest.mark.asyncio
    async def test_get_tasks_admin_sees_all(self, auth_tokens):
        """Test that admins see all tasks"""
        # Create tasks for different users
        task1_data = {"title": "User1 Task", "description": "Task by user1"}
        task2_data = {"title": "User2 Task", "description": "Task by user2"}
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Users create tasks
            await ac.post(
                "/tasks/",
                json=task1_data,
                headers={"Authorization": auth_tokens["user1"]}
            )
            
            await ac.post(
                "/tasks/",
                json=task2_data,
                headers={"Authorization": auth_tokens["user2"]}
            )
            
            # Admin gets tasks - should see all
            response = await ac.get(
                "/tasks/",
                headers={"Authorization": auth_tokens["admin"]}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        titles = [task["title"] for task in data]
        assert "User1 Task" in titles
        assert "User2 Task" in titles
    
    @pytest.mark.asyncio
    async def test_get_task_by_id_success(self, auth_tokens):
        """Test getting a specific task by ID"""
        task_data = {"title": "Test Task", "description": "Test description"}
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create task
            create_response = await ac.post(
                "/tasks/",
                json=task_data,
                headers={"Authorization": auth_tokens["user1"]}
            )
            task_id = create_response.json()["id"]
            
            # Get task by ID
            response = await ac.get(
                f"/tasks/{task_id}",
                headers={"Authorization": auth_tokens["user1"]}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == task_data["title"]
    
    @pytest.mark.asyncio
    async def test_get_task_by_id_not_found(self, auth_tokens):
        """Test getting a non-existent task"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(
                "/tasks/999",
                headers={"Authorization": auth_tokens["user1"]}
            )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_task_success(self, auth_tokens):
        """Test successful task update"""
        task_data = {"title": "Original Task", "description": "Original description"}
        update_data = {
            "title": "Updated Task",
            "status": "in-progress",
            "description": "Updated description"
        }
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create task
            create_response = await ac.post(
                "/tasks/",
                json=task_data,
                headers={"Authorization": auth_tokens["user1"]}
            )
            task_id = create_response.json()["id"]
            
            # Update task
            response = await ac.put(
                f"/tasks/{task_id}",
                json=update_data,
                headers={"Authorization": auth_tokens["user1"]}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["status"] == update_data["status"]
        assert data["description"] == update_data["description"]
    
    @pytest.mark.asyncio
    async def test_delete_task_success(self, auth_tokens):
        """Test successful task deletion"""
        task_data = {"title": "Task to Delete", "description": "Will be deleted"}
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create task
            create_response = await ac.post(
                "/tasks/",
                json=task_data,
                headers={"Authorization": auth_tokens["user1"]}
            )
            task_id = create_response.json()["id"]
            
            # Delete task
            response = await ac.delete(
                f"/tasks/{task_id}",
                headers={"Authorization": auth_tokens["user1"]}
            )
        
        assert response.status_code == 204
        
        # Verify task is deleted
        async with AsyncClient(app=app, base_url="http://test") as ac:
            get_response = await ac.get(
                f"/tasks/{task_id}",
                headers={"Authorization": auth_tokens["user1"]}
            )
        assert get_response.status_code == 404


class TestTaskRBAC:
    """Test Role-Based Access Control for tasks"""
    
    @pytest.mark.asyncio
    async def test_user_cannot_access_other_user_task(self, auth_tokens):
        """Test that users cannot access other users' tasks"""
        task_data = {"title": "User2 Private Task", "description": "Only user2 should see this"}
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # User2 creates a task
            create_response = await ac.post(
                "/tasks/",
                json=task_data,
                headers={"Authorization": auth_tokens["user2"]}
            )
            task_id = create_response.json()["id"]
            
            # User1 tries to access User2's task
            response = await ac.get(
                f"/tasks/{task_id}",
                headers={"Authorization": auth_tokens["user1"]}
            )
        
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_admin_can_access_any_task(self, auth_tokens):
        """Test that admins can access any user's tasks"""
        task_data = {"title": "User Task", "description": "Admin should see this"}
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # User creates a task
            create_response = await ac.post(
                "/tasks/",
                json=task_data,
                headers={"Authorization": auth_tokens["user1"]}
            )
            task_id = create_response.json()["id"]
            
            # Admin accesses user's task
            response = await ac.get(
                f"/tasks/{task_id}",
                headers={"Authorization": auth_tokens["admin"]}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == task_data["title"]
    
    @pytest.mark.asyncio
    async def test_user_cannot_edit_other_user_task(self, auth_tokens):
        """Test that users cannot edit other users' tasks"""
        task_data = {"title": "User2 Task", "description": "User2's task"}
        update_data = {"title": "Hacked Task"}
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # User2 creates a task
            create_response = await ac.post(
                "/tasks/",
                json=task_data,
                headers={"Authorization": auth_tokens["user2"]}
            )
            task_id = create_response.json()["id"]
            
            # User1 tries to edit User2's task
            response = await ac.put(
                f"/tasks/{task_id}",
                json=update_data,
                headers={"Authorization": auth_tokens["user1"]}
            )
        
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_admin_can_edit_any_task(self, auth_tokens):
        """Test that admins can edit any user's tasks"""
        task_data = {"title": "User Task", "description": "User's task"}
        update_data = {"title": "Admin Updated Task"}
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # User creates a task
            create_response = await ac.post(
                "/tasks/",
                json=task_data,
                headers={"Authorization": auth_tokens["user1"]}
            )
            task_id = create_response.json()["id"]
            
            # Admin edits user's task
            response = await ac.put(
                f"/tasks/{task_id}",
                json=update_data,
                headers={"Authorization": auth_tokens["admin"]}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
    
    @pytest.mark.asyncio
    async def test_user_cannot_delete_other_user_task(self, auth_tokens):
        """Test that users cannot delete other users' tasks"""
        task_data = {"title": "User2 Task", "description": "User2's task"}
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # User2 creates a task
            create_response = await ac.post(
                "/tasks/",
                json=task_data,
                headers={"Authorization": auth_tokens["user2"]}
            )
            task_id = create_response.json()["id"]
            
            # User1 tries to delete User2's task
            response = await ac.delete(
                f"/tasks/{task_id}",
                headers={"Authorization": auth_tokens["user1"]}
            )
        
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_admin_can_delete_any_task(self, auth_tokens):
        """Test that admins can delete any user's tasks"""
        task_data = {"title": "User Task", "description": "User's task"}
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # User creates a task
            create_response = await ac.post(
                "/tasks/",
                json=task_data,
                headers={"Authorization": auth_tokens["user1"]}
            )
            task_id = create_response.json()["id"]
            
            # Admin deletes user's task
            response = await ac.delete(
                f"/tasks/{task_id}",
                headers={"Authorization": auth_tokens["admin"]}
            )
        
        assert response.status_code == 204


class TestTaskStats:
    """Test task statistics endpoint"""
    
    @pytest.mark.asyncio
    async def test_task_count_for_user(self, auth_tokens):
        """Test task count for regular user"""
        # Create multiple tasks for user1
        for i in range(3):
            task_data = {"title": f"Task {i+1}", "description": f"Description {i+1}"}
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                await ac.post(
                    "/tasks/",
                    json=task_data,
                    headers={"Authorization": auth_tokens["user1"]}
                )
        
        # Get task count
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(
                "/tasks/stats/count",
                headers={"Authorization": auth_tokens["user1"]}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_tasks"] == 3
    
    @pytest.mark.asyncio
    async def test_task_count_for_admin(self, auth_tokens):
        """Test task count for admin (should see all tasks)"""
        # Create tasks for different users
        for user in ["user1", "user2"]:
            for i in range(2):
                task_data = {"title": f"{user} Task {i+1}", "description": f"Description {i+1}"}
                
                async with AsyncClient(app=app, base_url="http://test") as ac:
                    await ac.post(
                        "/tasks/",
                        json=task_data,
                        headers={"Authorization": auth_tokens[user]}
                    )
        
        # Admin gets task count
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(
                "/tasks/stats/count",
                headers={"Authorization": auth_tokens["admin"]}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_tasks"] == 4  # 2 tasks per user * 2 users
