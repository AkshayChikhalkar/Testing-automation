"""
Application settings stored per-user or globally
"""

from sqlalchemy import Column, Integer, JSON, UniqueConstraint, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class AppSetting(Base):
    """Per-user or global settings. If user_id is NULL, the row is global."""

    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    # Store settings as a single JSON blob structured by sections
    settings = Column(JSON, nullable=False, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User")

    __table_args__ = (
        # Ensure one settings row per user; allow exactly one global row (user_id NULL)
        UniqueConstraint("user_id", name="uq_app_settings_user"),
    )


