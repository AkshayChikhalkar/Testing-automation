"""
Pydantic schemas for application settings
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class SettingsBody(BaseModel):
    """Structure of the settings JSON blob."""
    general: dict = Field(default_factory=dict)
    matlab: dict = Field(default_factory=dict)
    storage: dict = Field(default_factory=dict)
    security: dict = Field(default_factory=dict)
    appearance: dict = Field(default_factory=dict)


class SettingsResponse(SettingsBody):
    scope: Literal["user", "global"] = "user"

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


