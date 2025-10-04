from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from models.task_models import TaskStatus


class UserInfo(BaseModel):
    """User information schema for task ownership"""
    id: int
    username: str
    email: str
    role: str

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    """Base task schema"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = TaskStatus.TODO
    due_date: Optional[datetime] = None
    attachments: List[str] = Field(default_factory=list)


class TaskCreate(TaskBase):
    """Schema for task creation"""
    pass


class TaskUpdate(BaseModel):
    """Schema for task updates - all fields optional"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None
    attachments: Optional[List[str]] = None


class Task(TaskBase):
    """Schema for task response"""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskWithOwner(Task):
    """Schema for task response with owner details"""
    owner: UserInfo = Field(..., description="Owner user information")

    class Config:
        from_attributes = True