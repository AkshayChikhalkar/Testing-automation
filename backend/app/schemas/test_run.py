"""
Pydantic schemas for TestRun
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class TestRunBase(BaseModel):
    """Base test run schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    model_id: int
    user_id: int
    input_data: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None
    hardware_config: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class TestRunCreate(BaseModel):
    """Schema for creating a test run"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    model_id: int
    input_data: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None
    hardware_config: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class TestRunUpdate(BaseModel):
    """Schema for updating a test run"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None
    hardware_config: Optional[Dict[str, Any]] = None


class TestRunResponse(TestRunBase):
    """Schema for test run response"""
    id: int
    status: str
    execution_time: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    report_path: Optional[str] = None
    model_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class TestRunListResponse(BaseModel):
    """Schema for test run list response (minimal data)"""
    id: int
    name: str
    model_id: int
    model_name: Optional[str] = None
    user_id: int
    status: str
    execution_time: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class TestRunStatus(BaseModel):
    """Schema for test run status"""
    test_run_id: int
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: Optional[float] = None
    progress: str = "0%"
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class TestRunResults(BaseModel):
    """Schema for test run results"""
    test_run_id: int
    status: str
    output_data: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    error_message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
