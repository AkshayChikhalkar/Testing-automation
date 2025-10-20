"""
Settings endpoints (per-user by default; admins can update global with ?scope=global)
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_async_db
from app.core.security import get_current_user, require_admin
from app.models.user import User
from app.models.app_setting import AppSetting
from app.schemas.settings import SettingsResponse, SettingsBody


router = APIRouter()


@router.get("/", response_model=SettingsResponse)
async def get_settings(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    scope: Optional[str] = Query(None, description="If 'global', fetch global settings (admin only)"),
):
    # If admin requests global scope, fetch that; else fetch user-specific and fallback to global
    if scope == "global":
        result = await db.execute(select(AppSetting).where(AppSetting.user_id == None))  # noqa: E711
        global_row = result.scalar_one_or_none()
        return SettingsResponse(scope="global", **(global_row.settings if global_row and global_row.settings else {}))

    # User scope
    result = await db.execute(select(AppSetting).where(AppSetting.user_id == current_user.id))
    user_row = result.scalar_one_or_none()
    if user_row and user_row.settings:
        return SettingsResponse(scope="user", **user_row.settings)

    # Fallback to global if user-specific not present
    result = await db.execute(select(AppSetting).where(AppSetting.user_id == None))  # noqa: E711
    global_row = result.scalar_one_or_none()
    return SettingsResponse(scope="user", **(global_row.settings if global_row and global_row.settings else {}))


@router.put("/", response_model=SettingsResponse)
async def put_settings(
    body: SettingsBody,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    scope: Optional[str] = Query(None, description="If 'global', update global settings (admin only)"),
):
    # Admin-only global updates
    if scope == "global":
        if not current_user.is_superuser or current_user.role not in ("admin", "superuser", "owner"):
            raise HTTPException(status_code=403, detail="Admin privileges required")
        result = await db.execute(select(AppSetting).where(AppSetting.user_id == None))  # noqa: E711
        row = result.scalar_one_or_none()
        if row is None:
            row = AppSetting(user_id=None, settings=body.model_dump())
            db.add(row)
        else:
            row.settings = body.model_dump()
        await db.commit()
        await db.refresh(row)
        return SettingsResponse(scope="global", **row.settings)

    # Per-user update
    result = await db.execute(select(AppSetting).where(AppSetting.user_id == current_user.id))
    row = result.scalar_one_or_none()
    if row is None:
        row = AppSetting(user_id=current_user.id, settings=body.model_dump())
        db.add(row)
    else:
        row.settings = body.model_dump()
    await db.commit()
    await db.refresh(row)
    return SettingsResponse(scope="user", **row.settings)


