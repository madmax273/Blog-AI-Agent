from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings
from typing import List, Optional


DEFAULT_SECRET_VALUES = {
    "your-secret-key-here-change-in-production",
    "your-jwt-secret-key-here-change-in-production",
    "your-secret-key-change-this-in-production",
}


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
    JWT_SECRET: str = "your-jwt-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 300
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS settings
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    LOG_ROTATION_DAYS: int = 10

    # Unsplash settings
    UNSPLASH_ACCESS_KEY: Optional[str] = None
    UNSPLASH_SECRET_KEY: Optional[str] = None

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, value):
        if isinstance(value, str):
            return [host.strip() for host in value.split(",") if host.strip()]
        return value

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.ENVIRONMENT.lower() in {"production", "prod"}:
            missing = []
            if not self.GROQ_API_KEY:
                missing.append("GROQ_API_KEY")
            if not self.JWT_SECRET or self.JWT_SECRET in DEFAULT_SECRET_VALUES:
                missing.append("JWT_SECRET")
            if not self.SECRET_KEY or self.SECRET_KEY in DEFAULT_SECRET_VALUES:
                missing.append("SECRET_KEY")
            if self.DATABASE_URL.startswith("sqlite"):
                missing.append("DATABASE_URL (use a persistent production database)")

            if missing:
                raise ValueError(
                    "Invalid production configuration. Set: " + ", ".join(missing)
                )

        return self
    
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
