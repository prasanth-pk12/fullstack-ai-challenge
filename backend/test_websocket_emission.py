#!/usr/bin/env python3
"""
Test script to verify WebSocket emission is working properly
"""
import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.websocket_service import websocket_service
from app.models import Task, User, Attachment
from datetime import datetime

async def test_emission():
    """Test the WebSocket emission functionality"""
    
    # Create a mock task object
    mock_task = Task()
    mock_task.id = 1
    mock_task.title = "Test Task"
    mock_task.description = "Test Description"
    mock_task.status = "pending"
    mock_task.priority = "medium"
    mock_task.created_at = datetime.utcnow()
    mock_task.updated_at = datetime.utcnow()
    mock_task.user_id = 1
    
    # Create a mock user object
    mock_user = User()
    mock_user.id = 1
    mock_user.username = "testuser"
    mock_user.email = "test@example.com"
    mock_user.role = "user"
    
    # Create a mock attachment
    mock_attachment = Attachment()
    mock_attachment.id = 1
    mock_attachment.filename = "test.txt"
    mock_attachment.original_filename = "test.txt"
    mock_attachment.file_size = 1024
    mock_attachment.content_type = "text/plain"
    mock_attachment.file_url = "/uploads/test.txt"
    mock_attachment.uploaded_at = datetime.utcnow()
    mock_attachment.task_id = 1
    
    # Add attachment to task
    mock_task.attachment = mock_attachment
    
    print("Testing WebSocket emission...")
    print(f"Mock task: {mock_task.__dict__}")
    print(f"Mock user: {mock_user.__dict__}")
    print(f"Mock attachment: {mock_attachment.__dict__}")
    
    try:
        # Test the emission
        await websocket_service.emit_task_updated(mock_task, mock_user)
        print("✅ WebSocket emission completed successfully!")
    except Exception as e:
        print(f"❌ WebSocket emission failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_emission())