import logging
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
from typing import Optional
from jose import jwt, JWTError
from datetime import datetime

from services.websocket_service import connection_manager, handle_websocket_error
from services.auth_service import SECRET_KEY, ALGORITHM
from services.auth_user_service import get_user_by_id
from database.connection import get_db
from schemas.websocket_schemas import (
    WebSocketStats, 
    ConnectionInfo,
    create_error_message,
    create_connection_message
)
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websockets"])

# Security scheme for WebSocket authentication
security = HTTPBearer()


@router.websocket("")
async def websocket_basic_endpoint(websocket: WebSocket):
    """
    Basic WebSocket endpoint for testing connectivity.
    
    **Authentication:** None required (public endpoint)
    
    **Usage:** 
    - Connect to `/ws` 
    - Send any text message
    - Receive echo response with "Echo: " prefix
    
    **Message Format:** Plain text
    
    **Example:**
    ```
    Client: "Hello WebSocket"
    Server: "Echo: Hello WebSocket"
    ```
    
    **Disconnect:** Connection closes cleanly when client disconnects
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        pass


async def authenticate_websocket_user(token: str, db: Session) -> tuple[int, str]:
    """Authenticate WebSocket connection using JWT token - Admin users only"""
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user_id = payload.get("user_id")
        role = payload.get("role")
        
        if username is None or user_id is None or role is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Only allow admin users to connect to WebSocket
        # Regular users don't need real-time updates from other users
        if role != "admin":
            raise HTTPException(status_code=403, detail="WebSocket access restricted to admin users only")
        
        # Get user from database to verify they still exist
        from models.auth_models import User
        user: User = get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Return the user_id and role from the token (already validated)
        return user_id, role
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.websocket("/tasks")
async def websocket_tasks_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT authentication token for WebSocket connection"),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time task updates - Admin users only.
    
    **Authentication:** Required via query parameter (Admin role required)
    
    **Connection URL:** `/ws/tasks?token=<jwt_token>`
    
    **Access Control:** Only admin users can connect to receive real-time updates.
    Regular users don't need to see updates from other users' tasks.
    
    **Features:**
    - Real-time task creation notifications
    - Task update broadcasts
    - Task deletion notifications
    - Task status change events
    - Connection management with heartbeat
    - Automatic reconnection support
    
    **Message Types Received:**
    - `ping`: Heartbeat from client
    - `subscribe`: Subscribe to specific task events
    - `unsubscribe`: Unsubscribe from task events
    
    **Message Types Sent:**
    - `connection`: Welcome message with connection details
    - `task_created`: New task was created
    - `task_updated`: Existing task was modified
    - `task_deleted`: Task was removed
    - `task_status_changed`: Task status changed
    - `heartbeat`: Server heartbeat
    - `error`: Error messages
    - `pong`: Response to ping
    
    **Example Messages:**
    ```json
    // Task Created Event
    {
        "type": "task_created",
        "timestamp": "2024-01-15T10:30:00Z",
        "data": {
            "task_id": 123,
            "title": "New Task",
            "owner_id": 1,
            "status": "TODO"
        }
    }
    
    // Error Message
    {
        "type": "error",
        "timestamp": "2024-01-15T10:30:00Z",
        "message": "Authentication failed",
        "code": 1008
    }
    ```
    
    **Error Codes:**
    - `1000`: Normal closure
    - `1003`: Invalid JSON format
    - `1008`: Authentication failure
    - `1011`: Server error
    
    **Authentication Flow:**
    1. Include JWT token in query parameter
    2. Server validates token and user permissions
    3. Connection established with user context
    4. Real-time events filtered by user permissions
    """
    connection_id = None
    
    try:
        # Authenticate user BEFORE accepting connection
        if not token:
            await handle_websocket_error(
                websocket, 
                "Authentication token required. Use ?token=<jwt_token> query parameter",
                error_code=1008,
                accept_first=True
            )
            return
        
        try:
            user_id, user_role = await authenticate_websocket_user(token, db)
        except HTTPException as e:
            await handle_websocket_error(
                websocket, 
                f"Authentication failed: {e.detail}",
                error_code=1008,
                accept_first=True
            )
            return
        
        # Establish connection
        connection_id = await connection_manager.connect(websocket, user_id, user_role)
        
        logger.info(f"WebSocket connection established for user {user_id} ({user_role}) with connection_id: {connection_id}")
        
        # Listen for messages
        while True:
            try:
                # Receive message from client with timeout to prevent hanging
                data = await websocket.receive_text()
                logger.debug(f"Received WebSocket message from {connection_id}: {data}")
                
                message = json.loads(data)
                
                # Handle different message types
                await handle_client_message(websocket, connection_id, message, user_id, user_role)
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from {connection_id}: {e}")
                # Send error for invalid JSON
                error_msg = create_error_message("Invalid JSON format", code=1003)
                await websocket.send_text(error_msg.json())
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket client {connection_id} disconnected normally")
                break
                
            except Exception as e:
                logger.error(f"Error handling WebSocket message from {connection_id}: {str(e)}")
                # Don't send error message for connection issues, just log and break
                break
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected during setup - connection_id: {connection_id}")
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
        # Don't try to send error messages if connection failed
        # if connection_id:
        #     await handle_websocket_error(
        #         websocket,
        #         f"Connection error: {str(e)}",
        #         error_code=1011,
        #         accept_first=False
        #     )
    
    finally:
        # Clean up connection
        if connection_id:
            logger.info(f"Cleaning up WebSocket connection: {connection_id}")
            connection_manager.disconnect(connection_id)


async def handle_client_message(
    websocket: WebSocket, 
    connection_id: str, 
    message: dict, 
    user_id: int, 
    user_role: str
):
    """Handle messages received from WebSocket clients"""
    
    message_type = message.get("type")
    
    if message_type == "ping":
        # Respond to ping with pong
        pong_response = {
            "type": "pong",
            "data": message.get("data"),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        await websocket.send_text(json.dumps(pong_response))
        logger.debug(f"Responded to ping from connection {connection_id}")
    
    elif message_type == "stats":
        # Send connection statistics (admin only)
        if user_role == "admin":
            stats = connection_manager.get_stats()
            stats_response = {
                "type": "stats",
                "data": stats,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            await websocket.send_text(json.dumps(stats_response))
        else:
            error_msg = create_error_message("Insufficient permissions for stats", code=1008)
            await websocket.send_text(error_msg.json())
    
    elif message_type == "subscribe":
        # Handle subscription to specific events (future feature)
        subscription_response = {
            "type": "subscription_ack",
            "subscribed_to": message.get("events", []),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        await websocket.send_text(json.dumps(subscription_response))
        logger.debug(f"User {user_id} subscribed to events: {message.get('events', [])}")
    
    else:
        # Unknown message type
        error_msg = create_error_message(f"Unknown message type: {message_type}", code=1003)
        await websocket.send_text(error_msg.json())
        logger.warning(f"Unknown message type '{message_type}' from connection {connection_id}")


@router.get(
    "/stats",
    response_model=WebSocketStats,
    summary="Get WebSocket statistics",
    description="Retrieve current WebSocket connection statistics",
    responses={
        200: {
            "description": "Statistics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "total_connections": 15,
                        "active_connections": 12,
                        "total_messages_sent": 1234,
                        "total_messages_received": 987,
                        "uptime_seconds": 86400,
                        "peak_connections": 25,
                        "last_activity": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            }
        },
        403: {
            "description": "Admin access required",
            "content": {
                "application/json": {
                    "example": {"detail": "Admin role required"}
                }
            }
        }
    }
)
async def get_websocket_stats(
    current_user=Depends(lambda: None)  # Will be replaced with proper auth dependency
) -> WebSocketStats:
    """
    Get comprehensive WebSocket connection statistics.
    
    **Authentication:** Required (Admin role only)
    
    **Response:** Statistics about current WebSocket connections including:
    - Total number of active connections
    - Message counts (sent/received)
    - Peak connection counts
    - System uptime
    - Last activity timestamp
    
    **Use Cases:**
    - System monitoring and health checks
    - Performance analysis
    - Capacity planning
    - Debugging connection issues
    """
    # TODO: Add proper authentication dependency
    stats = connection_manager.get_stats()
    return WebSocketStats(**stats)


@router.get(
    "/connections",
    response_model=list[ConnectionInfo],
    summary="List active WebSocket connections",
    description="Get detailed information about all active WebSocket connections",
    responses={
        200: {
            "description": "Active connections retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "connection_id": "conn_abc123def456",
                            "user_id": 1,
                            "user_role": "ADMIN",
                            "connected_at": "2024-01-15T10:30:00Z"
                        },
                        {
                            "connection_id": "conn_xyz789uvw012", 
                            "user_id": 2,
                            "user_role": "USER",
                            "connected_at": "2024-01-15T10:45:00Z"
                        }
                    ]
                }
            }
        },
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            }
        },
        403: {
            "description": "Admin access required",
            "content": {
                "application/json": {
                    "example": {"detail": "Admin role required"}
                }
            }
        }
    }
)
async def get_active_connections(
    current_user=Depends(lambda: None)  # Will be replaced with proper auth dependency
) -> list[ConnectionInfo]:
    """
    Get detailed list of all active WebSocket connections.
    
    **Authentication:** Required (Admin role only)
    
    **Response:** Array of connection objects containing:
    - **connection_id**: Unique identifier for the connection
    - **user_id**: ID of the connected user
    - **user_role**: Role of the connected user (USER/ADMIN)
    - **connected_at**: ISO timestamp when connection was established
    
    **Use Cases:**
    - Monitor who is currently connected
    - Debug connection issues
    - Security auditing
    - User session management
    """
    # TODO: Add proper authentication dependency
    connections = []
    
    for conn_id, conn_info in connection_manager.active_connections.items():
        connection_data = ConnectionInfo(
            connection_id=conn_id,
            user_id=conn_info["user_id"],
            user_role=conn_info["user_role"],
            connected_at=conn_info["connected_at"]
        )
        connections.append(connection_data)
    
    return connections


@router.post("/broadcast")
async def broadcast_message(
    message: dict,
    current_user=Depends(lambda: None)  # Will be replaced with proper auth dependency
):
    """
    Broadcast a custom message to all connected clients.
    
    Admin-only endpoint for sending system-wide notifications.
    """
    # TODO: Add proper authentication dependency
    
    broadcast_msg = {
        "type": "system_broadcast",
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "sender": "system"
    }
    
    await connection_manager.broadcast_to_all(broadcast_msg)
    
    return {"success": True, "message": "Message broadcast to all connections"}


@router.delete("/connections/{connection_id}")
async def disconnect_client(
    connection_id: str,
    current_user=Depends(lambda: None)  # Will be replaced with proper auth dependency
):
    """
    Forcefully disconnect a specific WebSocket connection.
    
    Admin-only endpoint for connection management.
    """
    # TODO: Add proper authentication dependency
    
    if connection_id in connection_manager.active_connections:
        # Send disconnection notice
        await connection_manager.send_personal_message(connection_id, {
            "type": "forced_disconnect",
            "message": "Connection terminated by administrator",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
        # Close the connection
        websocket = connection_manager.active_connections[connection_id]["websocket"]
        await websocket.close(code=1000, reason="Administrative disconnect")
        
        # Clean up
        connection_manager.disconnect(connection_id)
        
        return {"success": True, "message": f"Connection {connection_id} disconnected"}
    else:
        raise HTTPException(status_code=404, detail="Connection not found")