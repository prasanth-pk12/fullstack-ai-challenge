import os
import uuid
import aiofiles
from typing import List, Optional, BinaryIO
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from models.attachment_models import Attachment
from models.task_models import Task
from models.auth_models import User, UserRole
from schemas.attachment_schemas import AttachmentCreate

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
            detail="No file selected for upload"
        )
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file_ext}' not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check content type
    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not determine file content type"
        )


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename to prevent conflicts"""
    file_ext = Path(original_filename).suffix.lower()
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{file_ext}"


async def save_file_to_disk(file: UploadFile, filename: str) -> tuple[str, int]:
    """Save uploaded file to disk and return file path and size"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    file_size = 0
    
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(8192):  # Read in 8KB chunks
                file_size += len(chunk)
                
                # Check file size limit
                if file_size > MAX_FILE_SIZE:
                    # Clean up the partial file
                    await f.close()
                    os.remove(file_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File too large. Maximum size allowed: {MAX_FILE_SIZE / (1024*1024):.1f}MB"
                    )
                
                await f.write(chunk)
    except Exception as e:
        # Clean up on error
        if os.path.exists(file_path):
            os.remove(file_path)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file"
        )
    finally:
        await file.close()
    
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
    """Create attachment record in database"""
    attachment = Attachment(
        filename=filename,
        original_filename=original_filename,
        file_path=file_path,
        file_size=file_size,
        content_type=content_type,
        task_id=task_id,
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
    is_admin = current_user.role.value == UserRole.ADMIN.value
    is_owner = task.owner_id == current_user.id
    
    if not (is_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to upload files to this task"
        )
    
    # Validate file
    validate_file(file)
    
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
        return attachment
    except Exception as e:
        # Clean up file if database operation fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save attachment record"
        )


def get_task_attachments(db: Session, task_id: int, current_user: User) -> List[Attachment]:
    """Get all attachments for a task with RBAC"""
    
    # Validate task exists and user has permission
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user has permission to view this task
    is_admin = current_user.role.value == UserRole.ADMIN.value
    is_owner = task.owner_id == current_user.id
    
    if not (is_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view attachments for this task"
        )
    
    return db.query(Attachment).filter(Attachment.task_id == task_id).all()


def delete_attachment(db: Session, attachment_id: int, current_user: User) -> bool:
    """Delete an attachment with RBAC"""
    
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        return False
    
    # Get the task to check permissions
    task = db.query(Task).filter(Task.id == attachment.task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated task not found"
        )
    
    # Check if user has permission to delete this attachment
    is_admin = current_user.role.value == UserRole.ADMIN.value
    is_task_owner = task.owner_id == current_user.id
    is_file_uploader = attachment.uploaded_by == current_user.id
    
    if not (is_admin or is_task_owner or is_file_uploader):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this attachment"
        )
    
    # Delete file from disk
    if os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)
    
    # Delete from database
    db.delete(attachment)
    db.commit()
    return True