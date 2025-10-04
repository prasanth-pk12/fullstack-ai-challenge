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


class AttachmentInfo(BaseModel):
    """Attachment information for task response"""
    id: int
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    file_url: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    """Base task schema"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = TaskStatus.TODO
    due_date: Optional[datetime] = None
    attachments: List[str] = Field(default_factory=list)  # Keep for backward compatibility


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
    attachment: Optional[AttachmentInfo] = Field(default=None, description="Single file attachment")

    class Config:
        from_attributes = True
        
    @classmethod
    def from_task_model(cls, task_model):
        """Create Task schema from SQLAlchemy model with single attachment"""
        attachment_info = None
        if task_model.attachment:
            attachment_info = AttachmentInfo(
                id=task_model.attachment.id,
                filename=task_model.attachment.filename,
                original_filename=task_model.attachment.original_filename,
                file_size=task_model.attachment.file_size,
                content_type=task_model.attachment.content_type,
                file_url=task_model.attachment.file_url,
                uploaded_at=task_model.attachment.uploaded_at
            )
        
        return cls(
            id=task_model.id,
            title=task_model.title,
            description=task_model.description,
            status=task_model.status,
            due_date=task_model.due_date,
            attachments=task_model.attachments,  # Keep for backward compatibility
            owner_id=task_model.owner_id,
            created_at=task_model.created_at,
            updated_at=task_model.updated_at,
            attachment=attachment_info
        )


class TaskWithOwner(Task):
    """Schema for task response with owner details"""
    owner: UserInfo = Field(..., description="Owner user information")

    class Config:
        from_attributes = True
        
    @classmethod
    def from_task_model(cls, task_model):
        """Create TaskWithOwner schema from SQLAlchemy model with single attachment"""
        attachment_info = None
        if task_model.attachment:
            attachment_info = AttachmentInfo(
                id=task_model.attachment.id,
                filename=task_model.attachment.filename,
                original_filename=task_model.attachment.original_filename,
                file_size=task_model.attachment.file_size,
                content_type=task_model.attachment.content_type,
                file_url=task_model.attachment.file_url,
                uploaded_at=task_model.attachment.uploaded_at
            )
        
        return cls(
            id=task_model.id,
            title=task_model.title,
            description=task_model.description,
            status=task_model.status,
            due_date=task_model.due_date,
            attachments=task_model.attachments,  # Keep for backward compatibility
            owner_id=task_model.owner_id,
            created_at=task_model.created_at,
            updated_at=task_model.updated_at,
            attachment=attachment_info,
            owner=task_model.owner
        )