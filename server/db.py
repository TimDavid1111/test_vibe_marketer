"""Database models and configuration."""
from sqlmodel import SQLModel, Field, create_engine
from typing import Optional
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    instagram_user_id: str = Field(unique=True)
    access_token: str
    token_expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GenerationJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    prompt: str
    media_type: MediaType
    caption: str
    hashtags: str
    media_url: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: JobStatus = Field(default=JobStatus.PENDING)
    instagram_post_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Create database
engine = create_engine("sqlite:///data/app.db", echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
