"""
API v1 router configuration
"""

from fastapi import APIRouter

from app.api.v1.endpoints import models, test_runs, users, health, auth, settings, simulations

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(test_runs.router, prefix="/test-runs", tags=["test-runs"])
api_router.include_router(simulations.router, prefix="/simulations", tags=["simulations"])
