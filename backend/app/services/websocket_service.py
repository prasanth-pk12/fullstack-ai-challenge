import json
import logging
import asyncio
from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasting"""
    
    def __init__(self):
        # Dictionary to store active connections: {connection_id: {websocket, user_id, user_role}}
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        # Set to track user IDs with active connections
        self.connected_users: Set[int] = set()
        
    async def connect(self, websocket: WebSocket, user_id: int, user_role: str) -> str:
        """Accept a new WebSocket connection and return connection ID"""
        try:
            await websocket.accept()
            logger.info(f"WebSocket accepted for user {user_id}")
            
            connection_id = str(uuid.uuid4())
            self.active_connections[connection_id] = {
                "websocket": websocket,
                "user_id": user_id,
                "user_role": user_role,
                "connected_at": datetime.utcnow()
            }
            self.connected_users.add(user_id)
            
            logger.info(f"WebSocket connection stored: {connection_id} for user {user_id}")
            
            # Send welcome message
            await self.send_personal_message(connection_id, {
                "type": "connection",
                "message": "Connected to task updates",
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            
            logger.info(f"Welcome message sent to {connection_id}")
            return connection_id
            
        except Exception as e:
            logger.error(f"Error in WebSocket connect: {str(e)}")
            raise
    
    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id in self.active_connections:
            connection_info = self.active_connections[connection_id]
            user_id = connection_info["user_id"]
            
            del self.active_connections[connection_id]
            
            # Check if user has other active connections
            user_still_connected = any(
                conn["user_id"] == user_id 
                for conn in self.active_connections.values()
            )
            
            if not user_still_connected:
                self.connected_users.discard(user_id)
            
            logger.info(f"WebSocket connection closed: {connection_id} for user {user_id}")
    
    async def send_personal_message(self, connection_id: str, message: dict):
        """Send a message to a specific connection"""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]["websocket"]
                await websocket.send_text(json.dumps(message))
                logger.debug(f"Sent message to connection {connection_id}: {message.get('type', 'unknown')}")
            except Exception as e:
                logger.error(f"Error sending message to connection {connection_id}: {str(e)}")
                # Remove broken connection
                self.disconnect(connection_id)
    
    async def send_to_user(self, user_id: int, message: dict):
        """Send a message to all connections for a specific user"""
        user_connections = [
            conn_id for conn_id, conn_info in self.active_connections.items()
            if conn_info["user_id"] == user_id
        ]
        
        for connection_id in user_connections:
            await self.send_personal_message(connection_id, message)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connected clients"""
        if not self.active_connections:
            logger.debug("No active connections to broadcast to")
            return
        
        disconnected_connections = []
        
        for connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]["websocket"]
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to connection {connection_id}: {str(e)}")
                disconnected_connections.append(connection_id)
        
        # Clean up broken connections
        for connection_id in disconnected_connections:
            self.disconnect(connection_id)
        
        logger.debug(f"Broadcast message to {len(self.active_connections)} connections")
    
    async def broadcast_to_admins(self, message: dict):
        """Broadcast a message to all admin connections"""
        admin_connections = [
            conn_id for conn_id, conn_info in self.active_connections.items()
            if conn_info["user_role"] == "admin"
        ]
        
        logger.info(f"Broadcasting to admins: Found {len(admin_connections)} admin connections out of {len(self.active_connections)} total connections")
        logger.info(f"Message type: {message.get('type')}, Task ID: {message.get('task', {}).get('id')}")
        
        for connection_id in admin_connections:
            conn_info = self.active_connections.get(connection_id)
            if conn_info:
                logger.info(f"Sending to admin connection {connection_id} (user_id: {conn_info['user_id']}, role: {conn_info['user_role']})")
                await self.send_personal_message(connection_id, message)
            else:
                logger.warning(f"Admin connection {connection_id} not found in active connections")
        
        logger.info(f"Successfully broadcast admin message to {len(admin_connections)} admin connections")
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific connection"""
        return self.active_connections.get(connection_id)
    
    def get_user_connections(self, user_id: int) -> List[str]:
        """Get all connection IDs for a specific user"""
        return [
            conn_id for conn_id, conn_info in self.active_connections.items()
            if conn_info["user_id"] == user_id
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "unique_users": len(self.connected_users),
            "admin_connections": len([
                conn for conn in self.active_connections.values()
                if conn["user_role"] == "admin"
            ]),
            "user_connections": len([
                conn for conn in self.active_connections.values()
                if conn["user_role"] == "user"
            ])
        }


# Global connection manager instance
connection_manager = ConnectionManager()


class TaskEventBroadcaster:
    """Handles broadcasting of task-related events"""
    
    def __init__(self, manager: ConnectionManager):
        self.manager = manager
    
    async def broadcast_task_created(self, task_data: dict, created_by_user_id: int, user_info: Optional[dict] = None):
        """Broadcast task creation event"""
        message = {
            "type": "task_created",
            "task": task_data,
            "user": user_info or {"id": created_by_user_id, "username": f"User {created_by_user_id}"},
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_id": str(uuid.uuid4())
        }
        
        # Send to task owner (creator)
        await self.manager.send_to_user(created_by_user_id, message)
        
        # Send to all admins (they can see all tasks)
        await self.manager.broadcast_to_admins(message)
        
        # Note: Regular users don't get notifications about other users' tasks
        # as they can't see them due to RBAC (Role-Based Access Control)
        
        logger.info(f"Broadcast task created event: task_id={task_data.get('id')} by user_id={created_by_user_id} (sent to creator + all admins)")
    
    async def broadcast_task_updated(self, task_data: dict, updated_by_user_id: int, task_owner_id: int, user_info: Optional[dict] = None):
        """Broadcast task update event"""
        message = {
            "type": "task_updated",
            "task": task_data,
            "user": user_info or {"id": updated_by_user_id, "username": f"User {updated_by_user_id}"},
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_id": str(uuid.uuid4())
        }
        
        # Send to task owner (if different from updater)
        if task_owner_id != updated_by_user_id:
            await self.manager.send_to_user(task_owner_id, message)
        
        # Send to updater
        await self.manager.send_to_user(updated_by_user_id, message)
        
        # Send to all admins (they can see all tasks)
        await self.manager.broadcast_to_admins(message)
        
        logger.info(f"Broadcast task updated event: task_id={task_data.get('id')} by user_id={updated_by_user_id} (sent to owner, updater + all admins)")
    
    async def broadcast_task_deleted(self, task_id: int, deleted_by_user_id: int, task_owner_id: int, user_info: Optional[dict] = None):
        """Broadcast task deletion event"""
        message = {
            "type": "task_deleted",
            "task_id": task_id,
            "user": user_info or {"id": deleted_by_user_id, "username": f"User {deleted_by_user_id}"},
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_id": str(uuid.uuid4())
        }
        
        # Send to task owner (if different from deleter)
        if task_owner_id != deleted_by_user_id:
            await self.manager.send_to_user(task_owner_id, message)
        
        # Send to deleter
        await self.manager.send_to_user(deleted_by_user_id, message)
        
        # Send to all admins (they can see all tasks)
        await self.manager.broadcast_to_admins(message)
        
        logger.info(f"Broadcast task deleted event: task_id={task_id} by user_id={deleted_by_user_id} (sent to owner, deleter + all admins)")
    
    async def broadcast_task_status_changed(self, task_data: dict, old_status: str, new_status: str, updated_by_user_id: int):
        """Broadcast task status change event"""
        message = {
            "type": "task_status_changed",
            "task": task_data,
            "old_status": old_status,
            "new_status": new_status,
            "updated_by": updated_by_user_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_id": str(uuid.uuid4())
        }
        
        # Send to task owner
        task_owner_id = task_data.get("user_id")
        if task_owner_id:
            await self.manager.send_to_user(task_owner_id, message)
        
        # Send to all admins
        await self.manager.broadcast_to_admins(message)
        
        logger.info(f"Broadcast task status changed: task_id={task_data.get('id')} from {old_status} to {new_status}")


# Global event broadcaster instance
task_event_broadcaster = TaskEventBroadcaster(connection_manager)


async def handle_websocket_error(websocket: WebSocket, error_message: str, error_code: int = 1000, accept_first: bool = True):
    """Handle WebSocket errors gracefully"""
    try:
        # Accept the connection first if not already accepted
        if accept_first:
            await websocket.accept()
        
        error_response = {
            "type": "error",
            "message": error_message,
            "code": error_code,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        await websocket.send_text(json.dumps(error_response))
        await websocket.close(code=error_code)
    except Exception as e:
        logger.error(f"Error handling WebSocket error: {str(e)}")


async def send_heartbeat():
    """Send periodic heartbeat to maintain connections"""
    while True:
        if connection_manager.active_connections:
            heartbeat_message = {
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "active_connections": len(connection_manager.active_connections)
            }
            await connection_manager.broadcast_to_all(heartbeat_message)
        
        await asyncio.sleep(30)  # Send heartbeat every 30 seconds


# Start heartbeat task (this will be managed by the application lifecycle)
def start_heartbeat_task():
    """Start the heartbeat background task"""
    return asyncio.create_task(send_heartbeat())