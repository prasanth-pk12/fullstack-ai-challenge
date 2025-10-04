from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from models.task_models import Task, TaskStatus
from models.auth_models import User, UserRole
from schemas.task_schemas import TaskCreate, TaskUpdate


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
    """Create a new task"""
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
    db_task = db.query(Task).options(joinedload(Task.owner)).filter(Task.id == db_task.id).first()
    return db_task


def update_task(db: Session, task_id: int, task_data: TaskUpdate, current_user: User) -> Optional[Task]:
    """Update task with RBAC enforcement"""
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
    
    # Update only provided fields
    update_data = task_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    
    # Load the owner relationship
    task = db.query(Task).options(joinedload(Task.owner)).filter(Task.id == task.id).first()
    return task


def delete_task(db: Session, task_id: int, current_user: User) -> bool:
    """Delete task with RBAC enforcement"""
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
    
    db.delete(task)
    db.commit()
    return True


def get_task_count(db: Session, current_user: User) -> int:
    """Get total task count based on user permissions"""
    if current_user.role.value == UserRole.ADMIN.value:
        return db.query(Task).count()
    else:
        return db.query(Task).filter(Task.owner_id == current_user.id).count()