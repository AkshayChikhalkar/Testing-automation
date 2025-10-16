"""
Test run execution records
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class TestRun(Base):
    """Test run execution record"""
    
    __tablename__ = "test_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # References
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Execution details
    status = Column(String(20), default="pending")  # pending, running, completed, failed, cancelled
    execution_time = Column(Float)  # Execution time in seconds
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    
    # Input/Output data
    input_data = Column(JSON)  # Input data used for execution
    output_data = Column(JSON)  # Output data from execution
    error_message = Column(Text)  # Error message if execution failed
    
    # Configuration
    configuration = Column(JSON)  # Test configuration and parameters
    hardware_config = Column(JSON)  # Hardware configuration if applicable
    
    # Results
    results = Column(JSON)  # Test results and metrics
    report_path = Column(String(500))  # Path to generated report
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    model = relationship("Model", back_populates="test_runs")
    user = relationship("User", back_populates="test_runs")
    data_points = relationship("DataPoint", back_populates="test_run")
    
    def __repr__(self):
        return f"<TestRun(id={self.id}, name='{self.name}', status='{self.status}')>"
