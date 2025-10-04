from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
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
from schemas.task_schemas import TaskCreate, TaskUpdate, Task, TaskWithOwner
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