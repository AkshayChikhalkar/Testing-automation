"""
Dynamic data points for flexible data storage
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class DataPoint(Base):
    """Dynamic data point for storing varying model data"""
    
    __tablename__ = "data_points"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    test_run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=False)
    
    # Data identification
    data_type = Column(String(20), nullable=False)  # input, output, intermediate
    variable_name = Column(String(100), nullable=False)
    data_category = Column(String(50))  # sensor, control, measurement, etc.
    
    # Data values
    value = Column(JSON)  # Flexible JSON storage for any data type
    value_type = Column(String(20))  # scalar, vector, matrix, timeseries
    unit = Column(String(20))  # Data unit (V, A, Hz, etc.)
    
    # Metadata
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    sequence_number = Column(Integer)  # For ordered data points
    quality_flag = Column(String(10))  # good, bad, uncertain
    
    # Additional metadata
    additional_metadata = Column(JSON)  # Additional metadata for the data point
    description = Column(Text)  # Human-readable description
    
    # Relationships
    test_run = relationship("TestRun", back_populates="data_points")
    
    def __repr__(self):
        return f"<DataPoint(id={self.id}, type='{self.data_type}', variable='{self.variable_name}')>"


class DataFile(Base):
    """Data file metadata and storage"""
    
    __tablename__ = "data_files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # File size in bytes
    file_type = Column(String(20))  # .csv, .mat, .xlsx, .json
    
    # Data description
    description = Column(Text)
    data_format = Column(String(50))  # timeseries, tabular, structured
    columns = Column(JSON)  # Column definitions for structured data
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<DataFile(id={self.id}, filename='{self.filename}', type='{self.file_type}')>"
