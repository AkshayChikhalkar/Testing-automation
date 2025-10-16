"""
Custom exceptions for the application
"""

from typing import Optional


class CustomException(Exception):
    """Base custom exception"""
    
    def __init__(
        self,
        detail: str,
        status_code: int = 500,
        error_code: Optional[str] = None
    ):
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(detail)


class MATLABException(CustomException):
    """MATLAB-related exceptions"""
    
    def __init__(self, detail: str, error_code: Optional[str] = None):
        super().__init__(
            detail=detail,
            status_code=500,
            error_code=error_code or "MATLAB_ERROR"
        )


class ModelNotFoundException(CustomException):
    """Model not found exception"""
    
    def __init__(self, model_id: str):
        super().__init__(
            detail=f"Model with ID {model_id} not found",
            status_code=404,
            error_code="MODEL_NOT_FOUND"
        )


class TestRunException(CustomException):
    """Test run related exceptions"""
    
    def __init__(self, detail: str, error_code: Optional[str] = None):
        super().__init__(
            detail=detail,
            status_code=400,
            error_code=error_code or "TEST_RUN_ERROR"
        )


class HardwareException(CustomException):
    """Hardware integration exceptions"""
    
    def __init__(self, detail: str, error_code: Optional[str] = None):
        super().__init__(
            detail=detail,
            status_code=500,
            error_code=error_code or "HARDWARE_ERROR"
        )


class DataValidationException(CustomException):
    """Data validation exceptions"""
    
    def __init__(self, detail: str, error_code: Optional[str] = None):
        super().__init__(
            detail=detail,
            status_code=422,
            error_code=error_code or "DATA_VALIDATION_ERROR"
        )


class AuthenticationException(CustomException):
    """Authentication exceptions"""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            detail=detail,
            status_code=401,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationException(CustomException):
    """Authorization exceptions"""
    
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            detail=detail,
            status_code=403,
            error_code="AUTHORIZATION_ERROR"
        )
