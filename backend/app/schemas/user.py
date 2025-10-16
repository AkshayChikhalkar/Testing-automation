"""
Pydantic schemas for User
"""

from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    role: Optional[str] = Field(None, pattern="^(user|admin|engineer)$")
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    is_active: bool
    is_superuser: bool
    role: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class UserListResponse(BaseModel):
    """Schema for user list response (minimal data)"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    role: str
    created_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class UserInDB(UserResponse):
    """Schema for user in database (includes hashed password)"""
    hashed_password: str
