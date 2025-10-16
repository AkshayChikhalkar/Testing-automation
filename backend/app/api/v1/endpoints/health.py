"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.services.matlab_service import MATLABService
import structlog

router = APIRouter()
logger = structlog.get_logger()


@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "matlab-automation-platform",
        "version": "1.0.0"
    }


@router.get("/database")
async def database_health(db: AsyncSession = Depends(get_async_db)):
    """Database health check"""
    try:
        # Test database connection
        result = await db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


@router.get("/matlab")
async def matlab_health():
    """MATLAB Engine health check"""
    try:
        matlab_service = MATLABService()
        is_initialized = matlab_service.is_initialized
        
        if not is_initialized:
            await matlab_service.initialize()
        
        return {
            "status": "healthy",
            "matlab": "available",
            "initialized": matlab_service.is_initialized
        }
    except Exception as e:
        logger.error("MATLAB health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "matlab": "unavailable",
            "error": str(e)
        }


@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_async_db)):
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "services": {}
    }
    
    # Check database
    try:
        await db.execute("SELECT 1")
        health_status["services"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["services"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"
    
    # Check MATLAB
    try:
        matlab_service = MATLABService()
        if not matlab_service.is_initialized:
            await matlab_service.initialize()
        health_status["services"]["matlab"] = {"status": "healthy"}
    except Exception as e:
        health_status["services"]["matlab"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"
    
    return health_status
