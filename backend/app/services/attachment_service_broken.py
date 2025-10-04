import os
import uuid
import aiofiles
import asyncio
from typing import List, Optional, BinaryIO
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from models.attachment_models import Attachment
from models.task_models import Task
from models.auth_models import User, UserRole
from schemas.attachment_schemas import AttachmentCreate
from services.websocket_service import task_event_broadcaster
import logging

logger = logging.getLogger(__name__)

# Configuration
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.txt', '.md', '.rtf',  # Documents
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',  # Images
    '.zip', '.rar', '.7z', '.tar', '.gz',  # Archives
    '.mp3', '.mp4', '.avi', '.mov', '.wmv',  # Media
    '.xlsx', '.xls', '.csv', '.ppt', '.pptx'  # Office files
}

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file"""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a filename"
        )
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size (FastAPI doesn't automatically validate this)
    if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.1f}MB"
        )


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename to avoid conflicts"""
    file_ext = Path(original_filename).suffix
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{file_ext}"


async def save_file_to_disk(file: UploadFile, filename: str) -> tuple[str, int]:
    """Save uploaded file to disk and return (path, size)"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    file_size = 0
    
    async with aiofiles.open(file_path, 'wb') as f:
        while chunk := await file.read(8192):  # Read in 8KB chunks
            file_size += len(chunk)
            await f.write(chunk)
    
    return file_path, file_size


def create_attachment_record(
    db: Session,
    task_id: int,
    filename: str,
    original_filename: str,
    file_path: str,
    file_size: int,
    content_type: str,
    uploaded_by: int
) -> Attachment:
    """Create attachment database record"""
    attachment = Attachment(
        task_id=task_id,
        filename=filename,
        original_filename=original_filename,
        file_path=file_path,
        file_size=file_size,
        content_type=content_type,
        uploaded_by=uploaded_by
    )
    
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


async def upload_file_for_task(
    db: Session, 
    task_id: int, 
    file: UploadFile, 
    current_user: User
) -> Attachment:
    """Upload a file for a specific task with validation and RBAC"""
    
    # Validate task exists and user has permission
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user has permission to upload to this task
    # Note: We compare the enum values directly since current_user is loaded from DB
    is_admin = current_user.role.value == UserRole.ADMIN.value
    is_owner = task.owner_id == current_user.id

    if not (is_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to upload files to this task"
        )
    
    # Validate file
    validate_file(file)
    
    # Check if task already has an attachment and remove it
    existing_attachment = db.query(Attachment).filter(Attachment.task_id == task_id).first()
    if existing_attachment:
        # Remove existing file from disk
        if os.path.exists(existing_attachment.file_path):
            os.remove(existing_attachment.file_path)
        # Remove from database
        db.delete(existing_attachment)
        db.commit()
    
    # Ensure filename and content_type are not None
    if not file.filename or not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a name and content type"
        )
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)
    
    # Save file to disk
    file_path, file_size = await save_file_to_disk(file, unique_filename)
    
    try:
        # Create database record
        attachment = create_attachment_record(
            db=db,
            task_id=task_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            content_type=file.content_type,
            uploaded_by=current_user.id
        )
        
        # Emit WebSocket event for task update after attachment upload
        try:
            # Get the updated task with attachment
            updated_task = db.query(Task).options(
                joinedload(Task.owner),
                joinedload(Task.attachment)
            ).filter(Task.id == task_id).first()
            
            if updated_task:
                asyncio.create_task(_emit_task_updated_after_attachment(updated_task, current_user.id))
                
        except Exception as e:
            logger.error(f"Failed to emit task updated event after attachment upload: {str(e)}")
        
        return attachment
    except Exception as e:
        # Clean up file if database operation fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save attachment: {str(e)}"
        )


async def get_file_by_id(db: Session, attachment_id: int, current_user: User) -> Attachment:
    """Get a file by ID with permission check"""
    attachment = db.query(Attachment).options(
        joinedload(Attachment.task).joinedload(Task.owner)
    ).filter(Attachment.id == attachment_id).first()
    
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    
    # Check permissions (admin, task owner, or file uploader can access)
    is_admin = current_user.role.value == UserRole.ADMIN.value
    is_owner = attachment.task.owner_id == current_user.id

    if not (is_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this file"
        )
    
    return attachment


async def get_files_for_task(db: Session, task_id: int, current_user: User) -> List[Attachment]:
    """Get all files for a specific task with permission check"""
    # Check if task exists and user has permission
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check permissions
    is_admin = current_user.role.value == UserRole.ADMIN.value
    is_task_owner = task.owner_id == current_user.id
    is_file_uploader = current_user.id == task.owner_id  # Same as owner for now

    if not (is_admin or is_task_owner or is_file_uploader):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view files for this task"
        )
    
    # Get attachments for the task
    attachments = db.query(Attachment).filter(Attachment.task_id == task_id).all()
    return attachments


async def delete_attachment(db: Session, attachment_id: int, current_user: User) -> None:
    """Delete an attachment with permission check"""
    attachment = db.query(Attachment).options(
        joinedload(Attachment.task).joinedload(Task.owner)
    ).filter(Attachment.id == attachment_id).first()
    
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    
    # Check permissions (only admin or task owner can delete)
    is_admin = current_user.role.value == UserRole.ADMIN.value
    is_owner = attachment.task.owner_id == current_user.id

    if not (is_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this file"
        )
    
    # Delete file from disk
    if os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)
    
    # Delete from database
    db.delete(attachment)
    db.commit()


async def _emit_task_updated_after_attachment(task: Task, updated_by_user_id: int):
    """Helper function to emit task updated event after attachment operation"""
    try:
        from schemas.task_schemas import TaskWithOwner
        
        # Convert task to dict using schema
        task_schema = TaskWithOwner.from_task_model(task)
        task_dict = task_schema.dict()
        
        # Get user info
        user_info = {
            "id": task.owner.id,
            "username": task.owner.username,
            "email": task.owner.email,
            "role": task.owner.role.value
        } if task.owner else None
        
        await task_event_broadcaster.broadcast_task_updated(
            task_dict,
            updated_by_user_id,
            task.owner_id,
            user_info
        )
    except Exception as e:
        logger.error(f"Error broadcasting task updated event after attachment: {str(e)}")