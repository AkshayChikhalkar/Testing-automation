"""
Health check endpoints
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.services.simulation_runner_service import SimulationRunnerService
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
        await db.execute(text("SELECT 1"))
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
    """Simulation CLI runner health. Does not start MATLAB Engine."""
    runner = SimulationRunnerService()
    ok = runner.is_available()
    return {
        "status": "healthy" if ok else "unhealthy",
        "simulation_runner": {
            "available": ok,
            "path": str(runner.simulations_path) if runner.simulations_path else None,
        },
    }


@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_async_db)):
    """Comprehensive health check. CLI runner is required; MATLAB Engine is optional."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {}
    }

    try:
        await db.execute(text("SELECT 1"))
        health_status["services"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["services"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"

    runner = SimulationRunnerService()
    if runner.is_available():
        health_status["services"]["simulation_runner"] = {
            "status": "healthy",
            "path": str(runner.simulations_path),
        }
    else:
        health_status["services"]["simulation_runner"] = {"status": "unhealthy"}
        health_status["status"] = "unhealthy"

    return health_status
