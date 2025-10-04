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


@router.get(
    "/", 
    response_model=List[TaskWithOwner],
    summary="List all tasks",
    description="Get a paginated list of tasks based on user permissions",
    responses={
        200: {
            "description": "Successfully retrieved tasks",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "title": "Complete project documentation",
                            "description": "Write comprehensive API documentation",
                            "status": "TODO",
                            "due_date": "2024-12-31T23:59:59Z",
                            "attachments": ["doc1.pdf", "spec.md"],
                            "owner_id": 1,
                            "owner": {
                                "id": 1,
                                "username": "john_doe",
                                "email": "john@example.com"
                            },
                            "created_at": "2024-01-15T10:30:00Z",
                            "updated_at": "2024-01-15T10:30:00Z"
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
        }
    }
)
async def list_tasks(
    skip: int = Query(0, ge=0, description="Number of tasks to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of tasks to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a paginated list of tasks.
    
    **Authentication:** Required (JWT token)
    
    **Permissions:**
    - **ADMIN**: Can view all tasks in the system
    - **USER**: Can only view their own tasks
    
    **Query Parameters:**
    - **skip**: Number of tasks to skip (for pagination)
    - **limit**: Maximum number of tasks to return (1-1000)
    
    **Response:** Array of task objects with full details
    
    **Pagination Example:**
    - Page 1: `skip=0&limit=10`
    - Page 2: `skip=10&limit=10`
    - Page 3: `skip=20&limit=10`
    """
    tasks = get_tasks(db, current_user, skip=skip, limit=limit)
    return tasks


@router.post(
    "/", 
    response_model=TaskWithOwner, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    description="Create a new task with title, description, and optional metadata",
    responses={
        201: {
            "description": "Task successfully created",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Complete project documentation",
                        "description": "Write comprehensive API documentation",
                        "status": "TODO",
                        "due_date": "2024-12-31T23:59:59Z",
                        "attachments": [],
                        "owner_id": 1,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
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
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "title"],
                                "msg": "ensure this value has at least 1 characters",
                                "type": "value_error.any_str.min_length"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def create_new_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new task.
    
    **Authentication:** Required (JWT token)
    
    **Request Body:**
    - **title**: Task title (1-200 characters, required)
    - **description**: Detailed task description (optional)
    - **status**: Task status - "TODO", "IN_PROGRESS", or "DONE" (optional, defaults to "TODO")
    - **due_date**: ISO 8601 datetime string (optional)
    - **attachments**: List of attachment filenames (optional, typically empty on creation)
    
    **Permissions:** All authenticated users can create tasks
    
    **Ownership:** The task will be automatically assigned to the current user as the owner
    
    **Response:** Complete task object with generated ID and timestamps
    """
    task = create_task(db, task_data, current_user)
    return task


@router.get(
    "/{task_id}", 
    response_model=TaskWithOwner,
    summary="Get task by ID",
    description="Retrieve a specific task by its ID",
    responses={
        200: {
            "description": "Task found and returned",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Complete project documentation",
                        "description": "Write comprehensive API documentation",
                        "status": "IN_PROGRESS",
                        "due_date": "2024-12-31T23:59:59Z",
                        "attachments": ["requirements.pdf"],
                        "owner_id": 1,
                        "owner": {
                            "id": 1,
                            "username": "john_doe",
                            "email": "john@example.com"
                        },
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-20T14:45:00Z"
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
            "description": "Access forbidden - not task owner",
            "content": {
                "application/json": {
                    "example": {"detail": "Not enough permissions"}
                }
            }
        },
        404: {
            "description": "Task not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Task not found"}
                }
            }
        }
    }
)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a specific task by its ID.
    
    **Authentication:** Required (JWT token)
    
    **Path Parameters:**
    - **task_id**: Unique identifier for the task
    
    **Permissions:**
    - **ADMIN**: Can view any task in the system
    - **USER**: Can only view their own tasks
    
    **Response:** Complete task object with all details
    """
    task = get_task_by_id(db, task_id, current_user)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task


@router.put("/{task_id}", response_model=TaskWithOwner)
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