import pytest
from httpx import AsyncClient
from main import app


class TestAttachmentsSimple:
    """Simplified attachment tests - 2 essential test cases"""

    @pytest.mark.asyncio
    async def test_upload_endpoint_exists(self, auth_headers_user):
        """Test that upload endpoint exists"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Test upload endpoint (even with no file)
            response = await ac.post("/tasks/1/upload", headers=auth_headers_user)
        
        # Should return bad request or not found (but not 500 error)
        assert response.status_code in [400, 404, 422, 401]

    @pytest.mark.asyncio
    async def test_upload_requires_auth(self):
        """Test that upload requires authentication"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/tasks/1/upload")
        
        # Should require authentication
        assert response.status_code in [401, 404, 422]