import pytest
import asyncio
import os
import tempfile
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
from pathlib import Path
from io import BytesIO

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from main import app
from database.connection import get_db, Base
from models.auth_models import User, UserRole
from models.task_models import Task, TaskStatus
from models.attachment_models import Attachment
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
async def test_users_and_tasks(setup_database):
    """Create test users and tasks"""
    db = TestingSessionLocal()
    
    # Create users
    admin_user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ADMIN
    )
    
    user1 = User(
        username="user1",
        email="user1@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.USER
    )
    
    user2 = User(
        username="user2", 
        email="user2@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.USER
    )
    
    db.add_all([admin_user, user1, user2])
    db.commit()
    db.refresh(admin_user)
    db.refresh(user1)
    db.refresh(user2)
    
    # Create test tasks
    task1 = Task(
        title="User1 Task",
        description="Task owned by user1",
        owner_id=user1.id,
        status=TaskStatus.TODO
    )
    
    task2 = Task(
        title="User2 Task",
        description="Task owned by user2",
        owner_id=user2.id,
        status=TaskStatus.TODO
    )
    
    db.add_all([task1, task2])
    db.commit()
    db.refresh(task1)
    db.refresh(task2)
    
    db.close()
    return {
        "users": {"admin": admin_user, "user1": user1, "user2": user2},
        "tasks": {"task1": task1, "task2": task2}
    }


@pytest.fixture(scope="function")
async def auth_tokens(test_users_and_tasks):
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


def create_test_file(filename: str, content: bytes = b"test file content", content_type: str = "text/plain") -> tuple:
    """Create a test file for upload"""
    return filename, BytesIO(content), content_type


class TestFileUpload:
    """Test file upload functionality"""
    
    @pytest.mark.asyncio
    async def test_upload_file_success(self, auth_tokens, test_users_and_tasks):
        """Test successful file upload"""
        task_id = test_users_and_tasks["tasks"]["task1"].id
        
        # Create test file
        test_content = b"This is a test PDF file content"
        files = {"file": ("test_document.pdf", BytesIO(test_content), "application/pdf")}
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                f"/tasks/{task_id}/upload",
                files=files,
                headers={"Authorization": auth_tokens["user1"]}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert data["original_filename"] == "test_document.pdf"
        assert data["content_type"] == "application/pdf"
        assert data["file_size"] == len(test_content)
        assert data["file_url"].startswith("/uploads/")
        assert data["message"] == "File uploaded successfully"
    
    @pytest.mark.asyncio
    async def test_upload_file_unauthorized(self, auth_tokens, test_users_and_tasks):
        """Test file upload without authentication"""
        task_id = test_users_and_tasks["tasks"]["task1"].id
        
        files = {"file": ("test.txt", BytesIO(b"test"), "text/plain")}
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(f"/tasks/{task_id}/upload", files=files)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_upload_file_forbidden(self, auth_tokens, test_users_and_tasks):
        """Test file upload to another user's task"""
        task_id = test_users_and_tasks["tasks"]["task2"].id  # user2's task
        
        files = {"file": ("test.txt", BytesIO(b"test"), "text/plain")}
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                f"/tasks/{task_id}/upload",
                files=files,
                headers={"Authorization": auth_tokens["user1"]}  # user1 trying to upload to user2's task
            )
        
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_admin_can_upload_to_any_task(self, auth_tokens, test_users_and_tasks):
        """Test that admin can upload to any task"""
        task_id = test_users_and_tasks["tasks"]["task1"].id  # user1's task
        
        files = {"file": ("admin_file.txt", BytesIO(b"admin upload"), "text/plain")}
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                f"/tasks/{task_id}/upload",
                files=files,
                headers={"Authorization": auth_tokens["admin"]}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert data["original_filename"] == "admin_file.txt"
    
    @pytest.mark.asyncio
    async def test_upload_file_task_not_found(self, auth_tokens):
        """Test file upload to non-existent task"""
        files = {"file": ("test.txt", BytesIO(b"test"), "text/plain")}
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                "/tasks/999/upload",
                files=files,
                headers={"Authorization": auth_tokens["user1"]}
            )
        
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, auth_tokens, test_users_and_tasks):
        """Test upload of invalid file type"""
        task_id = test_users_and_tasks["tasks"]["task1"].id
        
        files = {"file": ("malicious.exe", BytesIO(b"executable"), "application/x-executable")}
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                f"/tasks/{task_id}/upload",
                files=files,
                headers={"Authorization": auth_tokens["user1"]}
            )
        
        assert response.status_code == 400
        assert "File type '.exe' not allowed" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_upload_no_file(self, auth_tokens, test_users_and_tasks):
        """Test upload without selecting a file"""
        task_id = test_users_and_tasks["tasks"]["task1"].id
        
        # Send empty file
        files = {"file": ("", BytesIO(b""), "text/plain")}
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                f"/tasks/{task_id}/upload",
                files=files,
                headers={"Authorization": auth_tokens["user1"]}
            )
        
        assert response.status_code == 400
        assert "No file selected" in response.json()["detail"]


class TestAttachmentListing:
    """Test attachment listing functionality"""
    
    @pytest.mark.asyncio
    async def test_get_task_attachments_success(self, auth_tokens, test_users_and_tasks):
        """Test listing attachments for a task"""
        task_id = test_users_and_tasks["tasks"]["task1"].id
        
        # Upload a file first
        files = {"file": ("test_doc.pdf", BytesIO(b"test content"), "application/pdf")}
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Upload file
            upload_response = await ac.post(
                f"/tasks/{task_id}/upload",
                files=files,
                headers={"Authorization": auth_tokens["user1"]}
            )
            assert upload_response.status_code == 201
            
            # List attachments
            response = await ac.get(
                f"/tasks/{task_id}/attachments",
                headers={"Authorization": auth_tokens["user1"]}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["original_filename"] == "test_doc.pdf"
        assert data[0]["content_type"] == "application/pdf"
    
    @pytest.mark.asyncio
    async def test_get_attachments_forbidden(self, auth_tokens, test_users_and_tasks):
        """Test that users cannot list attachments of other users' tasks"""
        task_id = test_users_and_tasks["tasks"]["task2"].id  # user2's task
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(
                f"/tasks/{task_id}/attachments",
                headers={"Authorization": auth_tokens["user1"]}  # user1 trying to access user2's task
            )
        
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_admin_can_list_any_attachments(self, auth_tokens, test_users_and_tasks):
        """Test that admin can list attachments of any task"""
        task_id = test_users_and_tasks["tasks"]["task1"].id  # user1's task
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(
                f"/tasks/{task_id}/attachments",
                headers={"Authorization": auth_tokens["admin"]}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestAttachmentDeletion:
    """Test attachment deletion functionality"""
    
    @pytest.mark.asyncio
    async def test_delete_attachment_by_owner(self, auth_tokens, test_users_and_tasks):
        """Test that task owner can delete attachments"""
        task_id = test_users_and_tasks["tasks"]["task1"].id
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Upload file
            files = {"file": ("delete_me.txt", BytesIO(b"to be deleted"), "text/plain")}
            upload_response = await ac.post(
                f"/tasks/{task_id}/upload",
                files=files,
                headers={"Authorization": auth_tokens["user1"]}
            )
            attachment_id = upload_response.json()["id"]
            
            # Delete attachment
            response = await ac.delete(
                f"/tasks/attachments/{attachment_id}",
                headers={"Authorization": auth_tokens["user1"]}
            )
        
        assert response.status_code == 204
    
    @pytest.mark.asyncio
    async def test_delete_attachment_by_admin(self, auth_tokens, test_users_and_tasks):
        """Test that admin can delete any attachment"""
        task_id = test_users_and_tasks["tasks"]["task1"].id
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # User1 uploads file
            files = {"file": ("admin_delete.txt", BytesIO(b"admin can delete"), "text/plain")}
            upload_response = await ac.post(
                f"/tasks/{task_id}/upload",
                files=files,
                headers={"Authorization": auth_tokens["user1"]}
            )
            attachment_id = upload_response.json()["id"]
            
            # Admin deletes attachment
            response = await ac.delete(
                f"/tasks/attachments/{attachment_id}",
                headers={"Authorization": auth_tokens["admin"]}
            )
        
        assert response.status_code == 204
    
    @pytest.mark.asyncio
    async def test_delete_attachment_forbidden(self, auth_tokens, test_users_and_tasks):
        """Test that users cannot delete other users' attachments"""
        task_id = test_users_and_tasks["tasks"]["task2"].id
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # User2 uploads file
            files = {"file": ("protected.txt", BytesIO(b"protected file"), "text/plain")}
            upload_response = await ac.post(
                f"/tasks/{task_id}/upload",
                files=files,
                headers={"Authorization": auth_tokens["user2"]}
            )
            attachment_id = upload_response.json()["id"]
            
            # User1 tries to delete User2's attachment
            response = await ac.delete(
                f"/tasks/attachments/{attachment_id}",
                headers={"Authorization": auth_tokens["user1"]}
            )
        
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_attachment(self, auth_tokens):
        """Test deleting a non-existent attachment"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.delete(
                "/tasks/attachments/999",
                headers={"Authorization": auth_tokens["user1"]}
            )
        
        assert response.status_code == 404
        assert "Attachment not found" in response.json()["detail"]


class TestFileValidation:
    """Test file validation"""
    
    @pytest.mark.asyncio
    async def test_upload_allowed_file_types(self, auth_tokens, test_users_and_tasks):
        """Test uploading various allowed file types"""
        task_id = test_users_and_tasks["tasks"]["task1"].id
        
        allowed_files = [
            ("document.pdf", "application/pdf"),
            ("image.jpg", "image/jpeg"),
            ("text.txt", "text/plain"),
            ("archive.zip", "application/zip"),
            ("spreadsheet.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        ]
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            for filename, content_type in allowed_files:
                files = {"file": (filename, BytesIO(b"test content"), content_type)}
                response = await ac.post(
                    f"/tasks/{task_id}/upload",
                    files=files,
                    headers={"Authorization": auth_tokens["user1"]}
                )
                assert response.status_code == 201, f"Failed to upload {filename}"
    
    @pytest.mark.asyncio
    async def test_upload_disallowed_file_types(self, auth_tokens, test_users_and_tasks):
        """Test uploading disallowed file types"""
        task_id = test_users_and_tasks["tasks"]["task1"].id
        
        disallowed_files = [
            ("script.js", "application/javascript"),
            ("program.exe", "application/x-executable"),
            ("batch.bat", "application/x-bat"),
            ("shell.sh", "application/x-sh")
        ]
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            for filename, content_type in disallowed_files:
                files = {"file": (filename, BytesIO(b"test content"), content_type)}
                response = await ac.post(
                    f"/tasks/{task_id}/upload",
                    files=files,
                    headers={"Authorization": auth_tokens["user1"]}
                )
                assert response.status_code == 400, f"Should have rejected {filename}"
                assert "not allowed" in response.json()["detail"]