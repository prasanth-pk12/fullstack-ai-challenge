"""
Simple test script to verify the existing attachment upload functionality
"""

import os
import sys
import asyncio
from httpx import AsyncClient

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from main import app


async def test_attachment_endpoints():
    """Test the existing attachment upload endpoints"""
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        print("🔧 Testing attachment upload functionality...")
        
        # Try to login with existing user
        print("\n1. Logging in with existing admin user...")
        login_response = await client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        print(f"   Login status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            # Try with different credentials
            print("   Trying different credentials...")
            login_response = await client.post("/auth/login", json={
                "username": "john_doe",
                "password": "securepassword"
            })
            print(f"   Login status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Get existing tasks first
            print("\n2. Getting existing tasks...")
            tasks_response = await client.get("/tasks", headers=headers)
            print(f"   Tasks status: {tasks_response.status_code}")
            
            task_id = None
            if tasks_response.status_code == 200:
                tasks = tasks_response.json()
                if tasks:
                    task_id = tasks[0]["id"]
                    print(f"   Using existing task: {task_id}")
                else:
                    print("   No existing tasks found, creating new one...")
            
            # Create a task if none exist
            if not task_id:
                print("\n3. Creating a new task...")
                task_response = await client.post("/tasks", json={
                    "title": "Test Task for Attachments",
                    "description": "Testing file uploads"
                }, headers=headers)
                print(f"   Task creation status: {task_response.status_code}")
                
                if task_response.status_code == 201:
                    task_id = task_response.json()["id"]
                else:
                    print(f"   ❌ Task creation failed: {task_response.json()}")
                    return
            
            if task_id:
                # Test file upload
                print(f"\n4. Testing file upload to task {task_id}...")
                
                # Create a test file
                test_content = b"This is a test document for attachment upload testing."
                files = {"file": ("test_document.txt", test_content, "text/plain")}
                
                upload_response = await client.post(
                    f"/tasks/{task_id}/upload",
                    files=files,
                    headers=headers
                )
                print(f"   Upload status: {upload_response.status_code}")
                
                if upload_response.status_code == 201:
                    upload_data = upload_response.json()
                    print(f"   ✅ Upload successful!")
                    print(f"   📁 File: {upload_data.get('original_filename')}")
                    print(f"   📏 Size: {upload_data.get('file_size')} bytes")
                    print(f"   🔗 URL: {upload_data.get('file_url')}")
                    
                    # Test listing attachments
                    print(f"\n5. Testing attachment listing...")
                    list_response = await client.get(
                        f"/tasks/{task_id}/attachments",
                        headers=headers
                    )
                    print(f"   List status: {list_response.status_code}")
                    
                    if list_response.status_code == 200:
                        attachments = list_response.json()
                        print(f"   ✅ Found {len(attachments)} attachment(s)")
                        for attachment in attachments:
                            print(f"      - {attachment.get('original_filename')} ({attachment.get('content_type')})")
                    else:
                        print(f"   ❌ Failed to list attachments: {list_response.json()}")
                        
                else:
                    print(f"   ❌ Upload failed: {upload_response.json()}")
        else:
            print(f"   ❌ Login failed: {login_response.json()}")


if __name__ == "__main__":
    print("🚀 Starting attachment functionality test...")
    asyncio.run(test_attachment_endpoints())
    print("\n✨ Test completed!")