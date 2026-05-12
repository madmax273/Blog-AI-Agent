from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON
from datetime import datetime
from .connection import Base

class BlogThread(Base):
    __tablename__ = "blog_threads"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, unique=True, index=True)
    user_id = Column(String, index=True) # String ID for now since no auth
    topic = Column(String, nullable=True)
    content = Column(Text, nullable=True)  # Now stores HTML content
    markdown_content = Column(Text, nullable=True)  # Raw markdown for reference
    status = Column(String, default="processing")
    created_at = Column(DateTime, default=datetime.utcnow)
    image_urls = Column(JSON, nullable=True)  # Store Unsplash image URLs and metadata

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    verified = Column(Boolean, default=False)
    ip_address = Column(String, nullable=True)
    plan_type = Column(String, default="basic")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usage_metrics = Column(JSON, nullable=True)
