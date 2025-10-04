from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, UniqueConstraint
from sqlalchemy.orm import relationship
from database.connection import Base
from datetime import datetime


class Attachment(Base):
    """Attachment model for file uploads linked to tasks (one per task)"""
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # Size in bytes
    content_type = Column(String(100), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)  # Unique constraint for one-to-one
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    task = relationship("Task", back_populates="attachment")
    uploader = relationship("User", back_populates="uploaded_files")

    def __repr__(self):
        return f"<Attachment(id={self.id}, filename='{self.filename}', task_id={self.task_id})>"
    
    @property
    def file_url(self) -> str:
        """Generate the URL to access this file"""
        return f"/uploads/{self.filename}"