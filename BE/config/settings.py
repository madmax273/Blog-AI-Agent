from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "Blog API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "A simple blog API built with FastAPI"
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    LANGSMITH_TRACING: Optional[str] = None
    LANGSMITH_ENDPOINT: Optional[str] = None
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: Optional[str] = None
    
    DEBUG: bool = False
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./blog.db"  # Changed to SQLite for development
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS settings
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    LOG_ROTATION_DAYS: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
