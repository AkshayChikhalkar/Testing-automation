"""
User management endpoints (basic implementation for Phase 1)
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.database import get_async_db
from app.models.user import User
from app.schemas.user import UserResponse, UserListResponse

router = APIRouter()
logger = structlog.get_logger()


@router.get("/", response_model=List[UserListResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db)
):
    """List all users"""
    try:
        query = select(User).offset(skip).limit(limit)
        result = await db.execute(query)
        users = result.scalars().all()
        
        return users
    except Exception as e:
        logger.error("Failed to list users", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list users")


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_async_db)):
    """Get a specific user by ID"""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get user", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get user")


# Note: User creation, authentication, and other user management features
# will be implemented in Phase 5 (User Management & Security)
