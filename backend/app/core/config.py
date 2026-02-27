"""
Application configuration settings
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator, computed_field
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "MATLAB Automation Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql://matlab_user:matlab_password@193.16.126.186:5432/matlab_automation"
    REDIS_URL: str = "redis://localhost:6379"
    
    # MATLAB Configuration
    MATLAB_PATH: str = "C:\\Program Files\\MATLAB\\R2023b"
    MATLAB_LICENSE_SERVER: Optional[str] = None
    MATLAB_ENGINE_TIMEOUT: int = 300
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # File Upload
    MAX_FILE_SIZE: str = "100MB"
    UPLOAD_PATH: str = "./uploads"
    ALLOWED_EXTENSIONS: str = ".m,.slx,.mat,.csv,.xlsx,.json"
    
    # Hardware Integration
    HARDWARE_ENABLED: bool = False
    USB_DEVICE_PATH: str = "/dev/ttyUSB0"
    CAN_INTERFACE: str = "can0"
    MODBUS_PORT: int = 502
    
    # Analytics
    INFLUXDB_URL: str = "http://193.16.126.186:8086"
    INFLUXDB_TOKEN: Optional[str] = None
    INFLUXDB_ORG: str = "my-org"
    INFLUXDB_BUCKET: str = "simulations"
    
    # Simulationsmodelle project path (for MATLAB CLI execution)
    # Path to the simulationsmodelle repo containing run_simulation.py
    SIMULATIONS_PROJECT_PATH: Optional[str] = None
    
    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    CORS_CREDENTIALS: bool = True
    ALLOWED_HOSTS: str = "*"
    ALLOWED_EXTENSIONS: str = ".m,.slx,.mat,.csv,.xlsx,.json"
    
    @computed_field
    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        return [i.strip() for i in self.CORS_ORIGINS.split(",")]
    
    @computed_field
    @property
    def ALLOWED_HOSTS_LIST(self) -> List[str]:
        return [i.strip() for i in self.ALLOWED_HOSTS.split(",")]
    
    @computed_field
    @property
    def ALLOWED_EXTENSIONS_LIST(self) -> List[str]:
        return [i.strip() for i in self.ALLOWED_EXTENSIONS.split(",")]
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


# Create settings instance
settings = Settings()
