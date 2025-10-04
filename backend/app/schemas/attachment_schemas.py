from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AttachmentBase(BaseModel):
    """Base attachment schema"""
    filename: str
    original_filename: str
    file_size: int = Field(..., gt=0, description="File size in bytes")
    content_type: str


class AttachmentCreate(AttachmentBase):
    """Schema for attachment creation"""
    file_path: str
    task_id: int
    uploaded_by: int


class Attachment(AttachmentBase):
    """Schema for attachment response"""
    id: int
    file_path: str
    file_url: str
    task_id: int
    uploaded_by: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


class AttachmentUploadResponse(BaseModel):
    """Schema for upload response"""
    id: int
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    file_url: str
    uploaded_at: datetime
    message: str = "File uploaded successfully"

    class Config:
        from_attributes = True


class AttachmentListResponse(BaseModel):
    """Schema for listing attachments"""
    attachments: list[Attachment]
    total_count: int
    total_size: int = Field(..., description="Total size of all attachments in bytes")