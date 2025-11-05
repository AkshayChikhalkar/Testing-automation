"""
Pydantic schemas for Model
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class ModelBase(BaseModel):
    """Base model schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    file_path: Optional[str] = Field(None, max_length=500)
    file_type: Optional[str] = Field(None, pattern="^(slx|m)$")
    version: str = Field(default="1.0.0", max_length=20)
    startup_script: Optional[str] = Field(None, max_length=500)
    model_directory: Optional[str] = Field(None, max_length=500)
    model_type: Optional[str] = Field("file", max_length=20)
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = Field(None, max_length=50)
    author: Optional[str] = Field(None, max_length=100)
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class ModelCreate(ModelBase):
    """Schema for creating a model"""
    pass


class ModelUpdate(BaseModel):
    """Schema for updating a model"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    version: Optional[str] = Field(None, max_length=20)
    startup_script: Optional[str] = Field(None, max_length=500)
    model_directory: Optional[str] = Field(None, max_length=500)
    model_type: Optional[str] = Field("file", max_length=20)
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = Field(None, max_length=50)
    author: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class ModelResponse(ModelBase):
    """Schema for model response"""
    id: int
    is_active: bool
    is_validated: bool
    validation_errors: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_executed: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class ModelListResponse(BaseModel):
    """Schema for model list response (minimal data)"""
    id: int
    name: str
    file_type: Optional[str] = None
    version: str
    category: Optional[str] = None
    is_active: bool
    is_validated: bool
    created_at: datetime
    last_executed: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class ModelInfo(BaseModel):
    """Schema for model information from MATLAB"""
    path: str
    name: str
    type: str
    parameters: List[str] = []
    outputs: List[str] = []
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class DirectoryModelCreate(BaseModel):
    """Schema for creating a directory-based model"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    model_directory: str = Field(..., max_length=500)
    startup_script: Optional[str] = Field(None, max_length=500)
    version: str = Field(default="1.0.0", max_length=20)
    category: Optional[str] = Field(None, max_length=50)
    author: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None