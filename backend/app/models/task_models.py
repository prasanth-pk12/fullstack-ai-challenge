from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLAlchemyEnum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database.connection import Base
from datetime import datetime
import enum


class TaskStatus(enum.Enum):
    """Task status enumeration"""
    TODO = "todo"
    IN_PROGRESS = "in-progress"
    DONE = "done"


class Task(Base):
    """Task model for task management"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(SQLAlchemyEnum(TaskStatus), default=TaskStatus.TODO, nullable=False)
    due_date = Column(DateTime, nullable=True)
    attachments = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship to User model
    owner = relationship("User", back_populates="tasks")

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status.value}', owner_id={self.owner_id})>"