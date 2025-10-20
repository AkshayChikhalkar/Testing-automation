"""
MATLAB Automation Platform - Main Application Entry Point
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog
import time
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.api.v1.api import api_router
from app.core.exceptions import CustomException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting MATLAB Automation Platform", version=settings.APP_VERSION)
    
    # Initialize database
    await init_db()
    logger.info("Database initialized successfully")

    # Seed default admin user if none exists
    try:
        async with AsyncSessionLocal() as session:  # type: AsyncSession
            # Ensure default admin exists
            result = await session.execute(select(User).where(User.username == "admin"))
            admin = result.scalar_one_or_none()
            if admin is None:
                admin = User(
                    username="admin",
                    email="admin@example.com",
                    full_name="Administrator",
                    hashed_password=get_password_hash("admin123"),
                    is_active=True,
                    is_superuser=True,
                    role="admin",
                )
                session.add(admin)
                await session.commit()
                logger.info("Seeded default admin user", username="admin")

            # Ensure requested dev user 'akshay' exists
            result = await session.execute(select(User).where(User.username == "akshay"))
            akshay = result.scalar_one_or_none()
            if akshay is None:
                akshay = User(
                    username="akshay",
                    email="akshay@example.com",
                    full_name="Akshay",
                    hashed_password=get_password_hash("akshay"),
                    is_active=True,
                    is_superuser=False,
                    role="user",
                )
                session.add(akshay)
                await session.commit()
                logger.info("Seeded dev user", username="akshay")
    except Exception as e:
        logger.error("Failed to seed default admin user", error=str(e))
    
    # Initialize MATLAB engine if available
    try:
        from app.services.matlab_service import MATLABService
        matlab_service = MATLABService()
        await matlab_service.initialize()
        logger.info("MATLAB engine initialized successfully")
    except Exception as e:
        logger.warning("MATLAB engine initialization failed", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("Shutting down MATLAB Automation Platform")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A comprehensive automation platform for testing MATLAB/Simulink models",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS_LIST
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    start_time = time.time()
    
    # Log request
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None
    )
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        "Request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time
    )
    
    return response


# Global exception handler
@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    """Handle custom exceptions"""
    logger.error(
        "Custom exception occurred",
        error=exc.detail,
        status_code=exc.status_code,
        url=str(request.url)
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": exc.error_code}
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": time.time()
    }


# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
