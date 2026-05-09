from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from .connection import Base

class BlogThread(Base):
    __tablename__ = "blog_threads"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, unique=True, index=True)
    user_id = Column(String, index=True) # String ID for now since no auth
    topic = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    status = Column(String, default="processing")
    created_at = Column(DateTime, default=datetime.utcnow)
