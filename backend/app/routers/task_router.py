from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from database.connection import get_db
from services.auth_service import get_current_user
from services.task_service import (
    get_tasks,
    get_task_by_id,
    create_task,
    update_task,
    delete_task,
    get_task_count
)
from services.attachment_service import (
    upload_file_for_task,
    get_task_attachments,
    delete_attachment
)
from schemas.task_schemas import TaskCreate, TaskUpdate, Task, TaskWithOwner
from schemas.attachment_schemas import AttachmentUploadResponse, Attachment as AttachmentSchema
from models.auth_models import User

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=List[Task])
async def list_tasks(
    skip: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of tasks to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all tasks with pagination.
    
    - **Admins**: Can see all tasks
    - **Users**: Can only see their own tasks
    """
    tasks = get_tasks(db, current_user, skip=skip, limit=limit)
    return tasks


@router.post("/", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_new_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new task.
    
    The task will be automatically assigned to the current user as the owner.
    """
    task = create_task(db, task_data, current_user)
    return task


@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific task by ID.
    
    - **Admins**: Can view any task
    - **Users**: Can only view their own tasks
    """
    task = get_task_by_id(db, task_id, current_user)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task


@router.put("/{task_id}", response_model=Task)
async def update_existing_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a specific task by ID.
    
    - **Admins**: Can update any task
    - **Users**: Can only update their own tasks
    """
    task = update_task(db, task_id, task_data, current_user)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a specific task by ID.
    
    - **Admins**: Can delete any task
    - **Users**: Can only delete their own tasks
    """
    success = delete_task(db, task_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return None


@router.get("/stats/count")
async def get_task_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get task count statistics.
    
    - **Admins**: Get total count of all tasks
    - **Users**: Get count of their own tasks
    """
    count = get_task_count(db, current_user)
    return {"total_tasks": count}


@router.post("/{task_id}/upload", response_model=AttachmentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file_to_task(
    task_id: int,
    file: UploadFile = File(..., description="File to upload"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a file attachment to a specific task.
    
    - **File Requirements**: 
      - Max size: 10MB
      - Allowed types: PDF, DOC, DOCX, TXT, MD, RTF, JPG, JPEG, PNG, GIF, BMP, SVG, ZIP, RAR, 7Z, TAR, GZ, MP3, MP4, AVI, MOV, WMV, XLSX, XLS, CSV, PPT, PPTX
    
    - **Permissions**:
      - **Task Owner**: Can upload files to their own tasks
      - **Admin**: Can upload files to any task
    
    Returns the uploaded file metadata and access URL.
    """
    attachment = await upload_file_for_task(db, task_id, file, current_user)
    
    return AttachmentUploadResponse(
        id=attachment.id,
        filename=attachment.filename,
        original_filename=attachment.original_filename,
        file_size=attachment.file_size,
        content_type=attachment.content_type,
        file_url=attachment.file_url,
        uploaded_at=attachment.uploaded_at
    )


@router.get("/{task_id}/attachments", response_model=List[AttachmentSchema])
async def get_task_attachments_list(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all attachments for a specific task.
    
    - **Permissions**:
      - **Task Owner**: Can view attachments of their own tasks
      - **Admin**: Can view attachments of any task
    """
    attachments = get_task_attachments(db, task_id, current_user)
    return attachments


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a specific attachment.
    
    - **Permissions**:
      - **Task Owner**: Can delete attachments from their own tasks
      - **File Uploader**: Can delete files they uploaded
      - **Admin**: Can delete any attachment
    """
    success = delete_attachment(db, attachment_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    return None