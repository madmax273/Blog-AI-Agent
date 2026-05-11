from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from Model.auth_models import UserCreate, UserLogin, UserOut, Token, GoogleAuthRequest, UsageMetrics
from utils.auth_utils import hash_password, create_access_token, create_refresh_token, verify_password, decode_token
from database.connection import get_db, SessionLocal
from database.models import User
from sqlalchemy.orm import Session
from typing import Optional
import os
import httpx
from fastapi.responses import RedirectResponse, JSONResponse
from datetime import datetime, timedelta
import random
from jose import JWTError
from fastapi.encoders import jsonable_encoder
from fastapi import Body
from config.settings import settings

security = HTTPBearer()  # login endpoint issues tokens

router = APIRouter()

def get_initial_usage_metrics(plan_type: str) -> dict:
    """Get initial usage metrics based on plan type."""
    if plan_type == "basic":
        return {
            "blogs_generated": 0,
            "blogs_limit": 10,
            "words_generated": 0,
            "words_limit": 50000,
            "reset_date": datetime.utcnow().isoformat()
        }
    elif plan_type == "pro":
        return {
            "blogs_generated": 0,
            "blogs_limit": 100,
            "words_generated": 0,
            "words_limit": 500000,
            "reset_date": datetime.utcnow().isoformat()
        }
    else:
        return {
            "blogs_generated": 0,
            "blogs_limit": 10,
            "words_generated": 0,
            "words_limit": 50000,
            "reset_date": datetime.utcnow().isoformat()
        }

def check_and_reset_quota(user: User, db: Session) -> dict:
    """
    Check if quota needs to be reset and update usage metrics accordingly.
    Returns the updated usage metrics.
    """
    if not user.usage_metrics:
        # Initialize usage metrics if not present
        user.usage_metrics = get_initial_usage_metrics(user.plan_type)
        db.commit()
        return user.usage_metrics

    metrics = user.usage_metrics
    reset_date = datetime.fromisoformat(metrics.get("reset_date", datetime.utcnow().isoformat()))
    now = datetime.utcnow()

    # Reset quota if reset date has passed (monthly reset)
    if now > reset_date:
        # Reset counters
        metrics["blogs_generated"] = 0
        metrics["words_generated"] = 0
        # Set new reset date to next month
        if reset_date.month == 12:
            new_reset_date = reset_date.replace(year=reset_date.year + 1, month=1)
        else:
            new_reset_date = reset_date.replace(month=reset_date.month + 1)
        metrics["reset_date"] = new_reset_date.isoformat()
        user.usage_metrics = metrics
        db.commit()

    return metrics

def check_blog_quota(user: User, db: Session) -> bool:
    """
    Check if user has exceeded their blog generation quota.
    Returns True if quota is available, False if exceeded.
    """
    from config.logging import get_logger
    logger = get_logger("auth_utils")

    # Reload user from database to get fresh data
    db.refresh(user)

    metrics = check_and_reset_quota(user, db)
    blogs_generated = metrics.get("blogs_generated", 0)
    blogs_limit = metrics.get("blogs_limit", 10)

    logger.info(f"Quota check for user {user.id}: blogs_generated={blogs_generated}, blogs_limit={blogs_limit}, has_quota={blogs_generated < blogs_limit}")

    return blogs_generated < blogs_limit

def increment_blog_count(user: User, word_count: int = 0, db: Session = None) -> dict:
    """
    Increment blog generation count and word count for user.
    Returns updated usage metrics.
    """
    from config.logging import get_logger
    from sqlalchemy.orm.attributes import flag_modified
    logger = get_logger("auth_utils")

    if not db:
        from database.connection import SessionLocal
        db = SessionLocal()

    try:
        # Reload user from database to get fresh data
        db.refresh(user)
        metrics = check_and_reset_quota(user, db)
        logger.info(f"Current metrics before increment: {metrics}")

        # Create a new dict to ensure SQLAlchemy detects the change
        new_metrics = metrics.copy()
        new_metrics["blogs_generated"] = new_metrics.get("blogs_generated", 0) + 1
        new_metrics["words_generated"] = new_metrics.get("words_generated", 0) + word_count

        user.usage_metrics = new_metrics
        flag_modified(user, "usage_metrics")  # Mark the field as modified
        db.commit()

        logger.info(f"Metrics after increment: {new_metrics}")
        logger.info(f"User usage_metrics after commit: {user.usage_metrics}")
        return new_metrics
    except Exception as e:
        logger.log_error_with_context(e, "Error incrementing blog count")
        raise
    finally:
        if not db:
            db.close()

def get_user_quota_status(user: User, db: Session) -> dict:
    """
    Get user's current quota status.
    Returns usage metrics with remaining counts.
    """
    metrics = check_and_reset_quota(user, db)
    blogs_generated = metrics.get("blogs_generated", 0)
    blogs_limit = metrics.get("blogs_limit", 10)
    words_generated = metrics.get("words_generated", 0)
    words_limit = metrics.get("words_limit", 50000)

    return {
        "blogs_generated": blogs_generated,
        "blogs_limit": blogs_limit,
        "blogs_remaining": blogs_limit - blogs_generated,
        "words_generated": words_generated,
        "words_limit": words_limit,
        "words_remaining": words_limit - words_generated,
        "reset_date": metrics.get("reset_date"),
        "plan_type": user.plan_type
    }

@router.post("/signup", status_code=201)
async def signup(data: UserCreate, request: Request, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    try:
        # Create new user
        ip_address = request.client.host if request.client else "unknown"
        hashed_pwd = hash_password(data.password)
        usage_metrics = get_initial_usage_metrics("basic")

        new_user = User(
            name=data.name,
            email=data.email,
            password=hashed_pwd,
            verified=False,
            ip_address=ip_address,
            plan_type="basic",
            usage_metrics=usage_metrics,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # For now, auto-verify users (skip OTP for simplicity)
        # TODO: Implement OTP verification later
        new_user.verified = True
        db.commit()

        # Generate JWT
        access_token = create_access_token({"sub": str(new_user.id)})
        refresh_token = create_refresh_token({"sub": str(new_user.id)})

        content = {
            "user": UserOut.model_validate(new_user)
        }
        content = jsonable_encoder(content)
        return JSONResponse(content=content, status_code=status.HTTP_201_CREATED)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during registration: {str(e)}"
        )

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not user.verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    content = {
        "user": UserOut.model_validate(user),
        "refresh_token": refresh_token,
        "access_token": access_token,
    }
    content = jsonable_encoder(content)
    return JSONResponse(content=content, status_code=status.HTTP_200_OK)

@router.post("/refresh")
async def refresh_token(refresh_token: str = Body(..., embed=True), db: Session = Depends(get_db)):
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create a new access token
    new_access_token = create_access_token({"sub": str(user.id)})

    return JSONResponse(
        content={"access_token": new_access_token, "token_type": "bearer"},
        status_code=status.HTTP_200_OK,
        headers={"Content-Type": "application/json"}
    )

security_scheme2 = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme2),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency that returns the current user if authenticated.
    """
    if not credentials or not credentials.credentials or credentials.credentials.lower() == "undefined":
        raise HTTPException(status_code=401, detail="No valid token provided")

    token = credentials.credentials

    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user profile (protected route)"""
    user_data = UserOut.model_validate(current_user)
    quota_status = get_user_quota_status(current_user, db)
    return {
        "user": user_data,
        "quota": quota_status
    }

