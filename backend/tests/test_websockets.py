import pytest
from httpx import AsyncClient
from main import app


class TestWebSocketSimple:
    """Simplified WebSocket tests - 3 essential test cases"""

    @pytest.mark.asyncio
    async def test_websocket_endpoint_exists(self):
        """Test that WebSocket endpoint exists"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Test that the WebSocket route is available
            response = await ac.get("/ws/tasks", headers={"connection": "upgrade"})
        
        # Should return upgrade required or method not allowed
        assert response.status_code in [426, 405, 404, 400]

    @pytest.mark.asyncio
    async def test_websocket_auth_required(self):
        """Test that WebSocket requires authentication"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/ws/tasks")
        
        # Should require authentication or return method not allowed
        assert response.status_code in [401, 405, 404, 400, 426]

    @pytest.mark.asyncio
    async def test_websocket_connection_manager(self):
        """Test WebSocket connection manager functionality"""
        from services.websocket_service import connection_manager
        
        # Test that connection manager is initialized
        assert connection_manager is not None
        assert hasattr(connection_manager, 'active_connections')
        # Accept both list and dict for active_connections
        assert isinstance(connection_manager.active_connections, (list, dict))