import logging
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
from typing import Optional
import jwt
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
    No authentication required.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        pass


async def authenticate_websocket_user(token: str, db: Session) -> tuple[int, str]:
    """Authenticate WebSocket connection using JWT token"""
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user from database
        user = get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user.id, user.role
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.websocket("/tasks")
async def websocket_tasks_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT authentication token"),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time task updates.
    
    Requires JWT authentication via query parameter.
    Sends real-time events for task creation, updates, and deletions.
    """
    connection_id = None
    
    try:
        # Authenticate user
        if not token:
            await handle_websocket_error(
                websocket, 
                "Authentication token required. Use ?token=<jwt_token> query parameter",
                error_code=1008
            )
            return
        
        try:
            user_id, user_role = await authenticate_websocket_user(token, db)
        except HTTPException as e:
            await handle_websocket_error(
                websocket, 
                f"Authentication failed: {e.detail}",
                error_code=1008
            )
            return
        
        # Establish connection
        connection_id = await connection_manager.connect(websocket, user_id, user_role)
        
        logger.info(f"WebSocket connection established for user {user_id} ({user_role})")
        
        # Listen for messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                await handle_client_message(websocket, connection_id, message, user_id, user_role)
                
            except json.JSONDecodeError:
                # Send error for invalid JSON
                error_msg = create_error_message("Invalid JSON format", code=1003)
                await websocket.send_text(error_msg.json())
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected: {connection_id}")
                break
                
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {str(e)}")
                error_msg = create_error_message(f"Message handling error: {str(e)}", code=1011)
                await websocket.send_text(error_msg.json())
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected during setup: {connection_id}")
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
        if connection_id:
            await handle_websocket_error(
                websocket,
                f"Connection error: {str(e)}",
                error_code=1011
            )
    
    finally:
        # Clean up connection
        if connection_id:
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


@router.get("/stats")
async def get_websocket_stats(
    current_user=Depends(lambda: None)  # Will be replaced with proper auth dependency
) -> WebSocketStats:
    """
    Get WebSocket connection statistics.
    
    Admin-only endpoint to monitor active connections.
    """
    # TODO: Add proper authentication dependency
    stats = connection_manager.get_stats()
    return WebSocketStats(**stats)


@router.get("/connections")
async def get_active_connections(
    current_user=Depends(lambda: None)  # Will be replaced with proper auth dependency
) -> list[ConnectionInfo]:
    """
    Get list of active WebSocket connections.
    
    Admin-only endpoint to see all active connections.
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