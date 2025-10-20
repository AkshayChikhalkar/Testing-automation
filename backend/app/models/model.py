"""
Model metadata and configuration
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Model(Base):
    """MATLAB/Simulink model metadata"""
    
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    file_path = Column(String(500), nullable=True)
    file_type = Column(String(10), nullable=True)  # .slx, .m
    version = Column(String(20), default="1.0.0")
    
    # Model configuration
    startup_script = Column(String(500))  # Path to startup script
    input_schema = Column(JSON)  # JSON schema for input validation
    output_schema = Column(JSON)  # JSON schema for output validation
    parameters = Column(JSON)  # Model parameters and default values
    
    # Metadata
    tags = Column(JSON)  # Tags for categorization
    category = Column(String(50))  # Model category
    author = Column(String(100))
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_validated = Column(Boolean, default=False)
    validation_errors = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_executed = Column(DateTime(timezone=True))
    
    # Relationships
    test_runs = relationship("TestRun", back_populates="model")
    created_by_user = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<Model(id={self.id}, name='{self.name}', type='{self.file_type}')>"
