from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, Union
from datetime import datetime
from enum import Enum


class WebSocketMessageType(str, Enum):
    """WebSocket message types"""
    CONNECTION = "connection"
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_DELETED = "task_deleted"
    TASK_STATUS_CHANGED = "task_status_changed"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    PING = "ping"
    PONG = "pong"


class BaseWebSocketMessage(BaseModel):
    """Base WebSocket message schema"""
    type: WebSocketMessageType
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    event_id: Optional[str] = None

    class Config:
        use_enum_values = True


class ConnectionMessage(BaseWebSocketMessage):
    """Connection establishment message"""
    type: WebSocketMessageType = WebSocketMessageType.CONNECTION
    message: str
    connection_id: str
    user_id: Optional[int] = None
    user_role: Optional[str] = None


class ErrorMessage(BaseWebSocketMessage):
    """Error message schema"""
    type: WebSocketMessageType = WebSocketMessageType.ERROR
    message: str
    code: int = 1000
    details: Optional[Dict[str, Any]] = None


class HeartbeatMessage(BaseWebSocketMessage):
    """Heartbeat message schema"""
    type: WebSocketMessageType = WebSocketMessageType.HEARTBEAT
    active_connections: int
    server_time: Optional[str] = None


class PingMessage(BaseWebSocketMessage):
    """Ping message schema"""
    type: WebSocketMessageType = WebSocketMessageType.PING
    data: Optional[str] = None


class PongMessage(BaseWebSocketMessage):
    """Pong response message schema"""
    type: WebSocketMessageType = WebSocketMessageType.PONG
    data: Optional[str] = None


class TaskEventMessage(BaseWebSocketMessage):
    """Base schema for task-related events"""
    task: Optional[Dict[str, Any]] = None
    task_id: Optional[int] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_by: Optional[int] = None


class TaskCreatedMessage(TaskEventMessage):
    """Task creation event message"""
    type: WebSocketMessageType = WebSocketMessageType.TASK_CREATED
    task: Dict[str, Any]
    created_by: int


class TaskUpdatedMessage(TaskEventMessage):
    """Task update event message"""
    type: WebSocketMessageType = WebSocketMessageType.TASK_UPDATED
    task: Dict[str, Any]
    updated_by: int
    changes: Optional[Dict[str, Any]] = None  # What fields were changed


class TaskDeletedMessage(TaskEventMessage):
    """Task deletion event message"""
    type: WebSocketMessageType = WebSocketMessageType.TASK_DELETED
    task_id: int
    deleted_by: int
    task_title: Optional[str] = None  # For reference in notifications


class TaskStatusChangedMessage(TaskEventMessage):
    """Task status change event message"""
    type: WebSocketMessageType = WebSocketMessageType.TASK_STATUS_CHANGED
    task: Dict[str, Any]
    old_status: str
    new_status: str
    updated_by: int


class WebSocketStats(BaseModel):
    """WebSocket connection statistics"""
    total_connections: int
    unique_users: int
    admin_connections: int
    user_connections: int
    uptime_seconds: Optional[float] = None


class ConnectionInfo(BaseModel):
    """Information about a WebSocket connection"""
    connection_id: str
    user_id: int
    user_role: str
    connected_at: datetime
    last_activity: Optional[datetime] = None
    ip_address: Optional[str] = None


class WebSocketResponse(BaseModel):
    """Generic WebSocket response wrapper"""
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Union type for all possible WebSocket messages
WebSocketMessage = Union[
    ConnectionMessage,
    ErrorMessage,
    HeartbeatMessage,
    PingMessage,
    PongMessage,
    TaskCreatedMessage,
    TaskUpdatedMessage,
    TaskDeletedMessage,
    TaskStatusChangedMessage
]


def create_task_created_message(task_data: Dict[str, Any], created_by: int, event_id: str) -> TaskCreatedMessage:
    """Helper function to create a task created message"""
    return TaskCreatedMessage(
        task=task_data,
        created_by=created_by,
        event_id=event_id
    )


def create_task_updated_message(
    task_data: Dict[str, Any], 
    updated_by: int, 
    event_id: str, 
    changes: Optional[Dict[str, Any]] = None
) -> TaskUpdatedMessage:
    """Helper function to create a task updated message"""
    return TaskUpdatedMessage(
        task=task_data,
        updated_by=updated_by,
        event_id=event_id,
        changes=changes
    )


def create_task_deleted_message(
    task_id: int, 
    deleted_by: int, 
    event_id: str, 
    task_title: Optional[str] = None
) -> TaskDeletedMessage:
    """Helper function to create a task deleted message"""
    return TaskDeletedMessage(
        task_id=task_id,
        deleted_by=deleted_by,
        event_id=event_id,
        task_title=task_title
    )


def create_task_status_changed_message(
    task_data: Dict[str, Any], 
    old_status: str, 
    new_status: str, 
    updated_by: int, 
    event_id: str
) -> TaskStatusChangedMessage:
    """Helper function to create a task status changed message"""
    return TaskStatusChangedMessage(
        task=task_data,
        old_status=old_status,
        new_status=new_status,
        updated_by=updated_by,
        event_id=event_id
    )


def create_error_message(message: str, code: int = 1000, details: Optional[Dict[str, Any]] = None) -> ErrorMessage:
    """Helper function to create an error message"""
    return ErrorMessage(
        message=message,
        code=code,
        details=details
    )


def create_connection_message(
    message: str, 
    connection_id: str, 
    user_id: Optional[int] = None, 
    user_role: Optional[str] = None
) -> ConnectionMessage:
    """Helper function to create a connection message"""
    return ConnectionMessage(
        message=message,
        connection_id=connection_id,
        user_id=user_id,
        user_role=user_role
    )