from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime

class UsageMetrics(BaseModel):
    blogs_generated: int = 0
    blogs_limit: int = 10
    words_generated: int = 0
    words_limit: int = 50000
    reset_date: Optional[datetime] = None

class UserBase(BaseModel):
    name: str
    email: EmailStr
    plan_type: str = "basic"

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    verified: bool
    plan_type: str
    created_at: datetime
    usage_metrics: Optional[UsageMetrics] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    sub: Optional[str] = None
    email: Optional[str] = None

class GoogleAuthRequest(BaseModel):
    token: str

class EmailVerificationRequest(BaseModel):
    email: EmailStr

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
