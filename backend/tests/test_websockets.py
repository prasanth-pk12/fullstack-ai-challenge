import pytest
import asyncio
import json
import sys
import os
from typing import Dict, Any
from unittest.mock import AsyncMock, patch, MagicMock

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))


class TestWebSocketService:
    """Test WebSocket service functionality without actual connections"""
    
    def test_connection_manager_initialization(self):
        """Test that connection manager initializes properly"""
        from services.websocket_service import ConnectionManager
        
        manager = ConnectionManager()
        assert manager.active_connections == {}
        assert manager.connected_users == set()
        
        stats = manager.get_stats()
        assert stats["total_connections"] == 0
        assert stats["unique_users"] == 0
    
    @pytest.mark.asyncio
    async def test_connection_manager_connect_and_disconnect(self):
        """Test connection management"""
        from services.websocket_service import ConnectionManager
        
        manager = ConnectionManager()
        
        # Mock WebSocket
        mock_websocket = AsyncMock()
        
        # Test connection
        connection_id = await manager.connect(mock_websocket, user_id=1, user_role="user")
        
        assert connection_id in manager.active_connections
        assert 1 in manager.connected_users
        assert manager.get_stats()["total_connections"] == 1
        
        # Test disconnection
        manager.disconnect(connection_id)
        assert connection_id not in manager.active_connections
        assert 1 not in manager.connected_users
        assert manager.get_stats()["total_connections"] == 0
    
    @pytest.mark.asyncio
    async def test_task_event_broadcaster(self):
        """Test task event broadcasting"""
        from services.websocket_service import TaskEventBroadcaster, ConnectionManager
        
        manager = ConnectionManager()
        broadcaster = TaskEventBroadcaster(manager)
        
        # Mock WebSocket
        mock_websocket = AsyncMock()
        
        # Add a connection
        connection_id = await manager.connect(mock_websocket, user_id=1, user_role="user")
        
        # Test task created event
        task_data = {
            "id": 1,
            "title": "Test Task",
            "status": "todo",
            "owner_id": 1
        }
        
        await broadcaster.broadcast_task_created(task_data, created_by_user_id=1)
        
        # Verify WebSocket was called
        mock_websocket.send_text.assert_called()
        
        # Get the call arguments
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)
        
        assert message["type"] == "task_created"
        assert message["task"]["id"] == 1
        assert message["created_by"] == 1
        
        # Clean up
        manager.disconnect(connection_id)


class TestWebSocketSchemas:
    """Test WebSocket message schemas"""
    
    def test_create_task_created_message(self):
        """Test task created message creation"""
        from schemas.websocket_schemas import create_task_created_message
        
        task_data = {"id": 1, "title": "Test"}
        message = create_task_created_message(task_data, created_by=1, event_id="test-123")
        
        assert message.type == "task_created"
        assert message.task == task_data
        assert message.created_by == 1
        assert message.event_id == "test-123"
    
    def test_create_error_message(self):
        """Test error message creation"""
        from schemas.websocket_schemas import create_error_message
        
        error_msg = create_error_message("Test error", code=1008)
        
        assert error_msg.type == "error"
        assert error_msg.message == "Test error"
        assert error_msg.code == 1008
    
    def test_create_connection_message(self):
        """Test connection message creation"""
        from schemas.websocket_schemas import create_connection_message
        
        conn_msg = create_connection_message(
            message="Connected",
            connection_id="test-conn-123",
            user_id=1,
            user_role="user"
        )
        
        assert conn_msg.type == "connection"
        assert conn_msg.message == "Connected"
        assert conn_msg.connection_id == "test-conn-123"
        assert conn_msg.user_id == 1
        assert conn_msg.user_role == "user"


class TestWebSocketIntegration:
    """Test WebSocket integration with task service"""
    
    @pytest.mark.asyncio
    async def test_task_service_emits_websocket_events(self):
        """Test that task service operations emit WebSocket events"""
        
        # This test verifies the integration exists without testing actual WebSocket connections
        from services.task_service import _emit_task_created_event
        
        # Mock the broadcaster
        with patch('services.websocket_service.task_event_broadcaster.broadcast_task_created') as mock_broadcast:
            task_data = {"id": 1, "title": "Test Task"}
            
            await _emit_task_created_event(task_data, created_by_user_id=1)
            
            # Verify the broadcast was called
            mock_broadcast.assert_called_once_with(task_data, 1)
    
    def test_websocket_router_exists(self):
        """Test that WebSocket router is properly configured"""
        from main import app
        
        # Verify WebSocket routes exist
        has_websocket_route = False
        for route in app.routes:
            if hasattr(route, 'path') and '/ws' in str(route.path):
                has_websocket_route = True
                break
        
        assert has_websocket_route, "WebSocket routes not found in app"


class TestWebSocketErrorHandling:
    """Test WebSocket error handling"""
    
    @pytest.mark.asyncio
    async def test_handle_websocket_error(self):
        """Test WebSocket error handling function"""
        from services.websocket_service import handle_websocket_error
        
        mock_websocket = AsyncMock()
        
        await handle_websocket_error(mock_websocket, "Test error", 1008)
        
        # Verify error message was sent
        mock_websocket.send_text.assert_called()
        mock_websocket.close.assert_called_with(code=1008)
        
        # Check the error message format
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)
        
        assert message["type"] == "error"
        assert message["message"] == "Test error"
        assert message["code"] == 1008
    
    @pytest.mark.asyncio
    async def test_connection_manager_handles_broken_connections(self):
        """Test that connection manager handles broken connections"""
        from services.websocket_service import ConnectionManager
        
        manager = ConnectionManager()
        
        # Mock WebSocket that raises exception
        mock_websocket = AsyncMock()
        mock_websocket.send_text.side_effect = Exception("Connection broken")
        
        # Add connection
        connection_id = await manager.connect(mock_websocket, user_id=1, user_role="user")
        
        # Try to send message - should handle the exception
        await manager.send_personal_message(connection_id, {"type": "test"})
        
        # Connection should be automatically removed
        assert connection_id not in manager.active_connections


class TestWebSocketMessageTypes:
    """Test WebSocket message type validation"""
    
    def test_message_type_enum(self):
        """Test WebSocket message type enumeration"""
        from schemas.websocket_schemas import WebSocketMessageType
        
        assert WebSocketMessageType.CONNECTION == "connection"
        assert WebSocketMessageType.TASK_CREATED == "task_created"
        assert WebSocketMessageType.TASK_UPDATED == "task_updated"
        assert WebSocketMessageType.TASK_DELETED == "task_deleted"
        assert WebSocketMessageType.ERROR == "error"
        assert WebSocketMessageType.HEARTBEAT == "heartbeat"
    
    def test_schema_helper_functions(self):
        """Test helper functions for creating WebSocket messages"""
        from schemas.websocket_schemas import (
            create_task_created_message,
            create_task_updated_message,
            create_task_deleted_message,
            create_task_status_changed_message
        )
        
        # Test task created message
        task_data = {"id": 1, "title": "Test"}
        created_msg = create_task_created_message(task_data, 1, "event-123")
        assert created_msg.type == "task_created"
        assert created_msg.task == task_data
        assert created_msg.created_by == 1
        
        # Test task updated message
        updated_msg = create_task_updated_message(task_data, 2, "event-456")
        assert updated_msg.type == "task_updated"
        assert updated_msg.updated_by == 2
        
        # Test task deleted message
        deleted_msg = create_task_deleted_message(1, 2, "event-789", "Test Task")
        assert deleted_msg.type == "task_deleted"
        assert deleted_msg.task_id == 1
        assert deleted_msg.deleted_by == 2
        assert deleted_msg.task_title == "Test Task"
        
        # Test status changed message
        status_msg = create_task_status_changed_message(
            task_data, "todo", "done", 1, "event-101"
        )
        assert status_msg.type == "task_status_changed"
        assert status_msg.old_status == "todo"
        assert status_msg.new_status == "done"