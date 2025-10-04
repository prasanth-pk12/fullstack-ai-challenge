from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from models.task_models import Task, TaskStatus
from models.auth_models import User, UserRole
from schemas.task_schemas import TaskCreate, TaskUpdate
import asyncio
import logging

logger = logging.getLogger(__name__)


def get_tasks(db: Session, current_user: User, skip: int = 0, limit: int = 100) -> List[Task]:
    """Get tasks based on user permissions"""
    if current_user.role.value == UserRole.ADMIN.value:
        # Admins can see all tasks
        return db.query(Task).options(joinedload(Task.owner)).offset(skip).limit(limit).all()
    else:
        # Users can only see their own tasks
        return db.query(Task).options(joinedload(Task.owner)).filter(
            Task.owner_id == current_user.id
        ).offset(skip).limit(limit).all()


def get_task_by_id(db: Session, task_id: int, current_user: User) -> Optional[Task]:
    """Get task by ID with RBAC check"""
    task = db.query(Task).options(joinedload(Task.owner)).filter(Task.id == task_id).first()
    
    if not task:
        return None
    
    # Check if user has permission to view this task
    is_admin = current_user.role.value == UserRole.ADMIN.value
    is_owner = task.owner_id == current_user.id
    
    if is_admin or is_owner:
        return task
    
    # User doesn't have permission
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to access this task"
    )


def create_task(db: Session, task_data: TaskCreate, current_user: User) -> Task:
    """Create a new task and emit WebSocket event"""
    db_task = Task(
        title=task_data.title,
        description=task_data.description,
        owner_id=current_user.id,
        status=task_data.status or TaskStatus.TODO,
        due_date=task_data.due_date,
        attachments=task_data.attachments or []
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # Load the owner relationship
    refreshed_task = db.query(Task).options(joinedload(Task.owner)).filter(Task.id == db_task.id).first()
    
    if refreshed_task:
        # Emit WebSocket event asynchronously
        try:
            task_dict = {
                "id": refreshed_task.id,
                "title": refreshed_task.title,
                "description": refreshed_task.description,
                "status": refreshed_task.status.value,
                "due_date": refreshed_task.due_date.isoformat() if refreshed_task.due_date is not None else None,
                "attachments": refreshed_task.attachments,
                "owner_id": refreshed_task.owner_id,
                "owner": {
                    "id": refreshed_task.owner.id,
                    "username": refreshed_task.owner.username,
                    "email": refreshed_task.owner.email,
                    "role": refreshed_task.owner.role.value
                } if refreshed_task.owner else None,
                "created_at": refreshed_task.created_at.isoformat() if refreshed_task.created_at is not None else None,
                "updated_at": refreshed_task.updated_at.isoformat() if refreshed_task.updated_at is not None else None
            }
            
            user_info = {
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "role": current_user.role.value
            }
            
            # Schedule WebSocket event emission
            asyncio.create_task(_emit_task_created_event(task_dict, int(current_user.id), user_info))
            
        except Exception as e:
            logger.error(f"Failed to emit task created event: {str(e)}")
        
        return refreshed_task
    
    return db_task


async def _emit_task_created_event(task_data: dict, created_by_user_id: int, user_info: dict):
    """Helper function to emit task created event"""
    try:
        from services.websocket_service import task_event_broadcaster
        await task_event_broadcaster.broadcast_task_created(task_data, created_by_user_id, user_info)
    except Exception as e:
        logger.error(f"Error broadcasting task created event: {str(e)}")


def update_task(db: Session, task_id: int, task_data: TaskUpdate, current_user: User) -> Optional[Task]:
    """Update task with RBAC enforcement and emit WebSocket event"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        return None
    
    # Check if user has permission to edit this task
    is_admin = current_user.role.value == UserRole.ADMIN.value
    is_owner = task.owner_id == current_user.id
    
    if not (is_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this task"
        )
    
    # Store old status for status change detection
    old_status = task.status.value if task.status else None
    
    # Update only provided fields
    update_data = task_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    
    # Load the owner relationship
    updated_task = db.query(Task).options(joinedload(Task.owner)).filter(Task.id == task.id).first()
    
    if updated_task:
        # Emit WebSocket event asynchronously
        try:
            task_dict = {
                "id": updated_task.id,
                "title": updated_task.title,
                "description": updated_task.description,
                "status": updated_task.status.value,
                "due_date": updated_task.due_date.isoformat() if updated_task.due_date is not None else None,
                "attachments": updated_task.attachments,
                "owner_id": updated_task.owner_id,
                "owner_username": updated_task.owner.username if updated_task.owner else None,
                "created_at": updated_task.created_at.isoformat() if updated_task.created_at is not None else None,
                "updated_at": updated_task.updated_at.isoformat() if updated_task.updated_at is not None else None
            }
            
            # Schedule WebSocket event emission
            asyncio.create_task(_emit_task_updated_event(
                task_dict, 
                int(current_user.id), 
                updated_task.owner_id,
                old_status,
                updated_task.status.value
            ))
            
        except Exception as e:
            logger.error(f"Failed to emit task updated event: {str(e)}")
        
        return updated_task
    
    return task


async def _emit_task_updated_event(
    task_data: dict, 
    updated_by_user_id: int, 
    task_owner_id: int,
    old_status: Optional[str],
    new_status: str
):
    """Helper function to emit task updated event"""
    try:
        from services.websocket_service import task_event_broadcaster
        
        # Emit general update event
        await task_event_broadcaster.broadcast_task_updated(task_data, updated_by_user_id, task_owner_id)
        
        # Emit status change event if status was changed
        if old_status and old_status != new_status:
            await task_event_broadcaster.broadcast_task_status_changed(
                task_data, old_status, new_status, updated_by_user_id
            )
            
    except Exception as e:
        logger.error(f"Error broadcasting task updated event: {str(e)}")


def delete_task(db: Session, task_id: int, current_user: User) -> bool:
    """Delete task with RBAC enforcement and emit WebSocket event"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        return False
    
    # Check if user has permission to delete this task
    is_admin = current_user.role.value == UserRole.ADMIN.value
    is_owner = task.owner_id == current_user.id
    
    if not (is_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this task"
        )
    
    # Store task info before deletion for WebSocket event
    task_owner_id = task.owner_id
    task_title = task.title
    
    db.delete(task)
    db.commit()
    
    # Emit WebSocket event asynchronously
    try:
        asyncio.create_task(_emit_task_deleted_event(task_id, int(current_user.id), task_owner_id, task_title))
    except Exception as e:
        logger.error(f"Failed to emit task deleted event: {str(e)}")
    
    return True


async def _emit_task_deleted_event(task_id: int, deleted_by_user_id: int, task_owner_id: int, task_title: str):
    """Helper function to emit task deleted event"""
    try:
        from services.websocket_service import task_event_broadcaster
        await task_event_broadcaster.broadcast_task_deleted(task_id, deleted_by_user_id, task_owner_id)
    except Exception as e:
        logger.error(f"Error broadcasting task deleted event: {str(e)}")


def get_task_count(db: Session, current_user: User) -> int:
    """Get total task count based on user permissions"""
    if current_user.role.value == UserRole.ADMIN.value:
        return db.query(Task).count()
    else:
        return db.query(Task).filter(Task.owner_id == current_user.id).count()