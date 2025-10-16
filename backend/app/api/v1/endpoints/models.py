"""
Model management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.database import get_async_db
from app.models.model import Model
from app.services.matlab_service import MATLABService
from app.schemas.model import ModelCreate, ModelUpdate, ModelResponse, ModelListResponse

router = APIRouter()
logger = structlog.get_logger()


@router.get("/", response_model=List[ModelListResponse])
async def list_models(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """List all models with optional filtering"""
    try:
        query = select(Model)
        
        if category:
            query = query.where(Model.category == category)
        if is_active is not None:
            query = query.where(Model.is_active == is_active)
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        models = result.scalars().all()
        
        return models
    except Exception as e:
        logger.error("Failed to list models", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list models")


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(model_id: int, db: AsyncSession = Depends(get_async_db)):
    """Get a specific model by ID"""
    try:
        result = await db.execute(select(Model).where(Model.id == model_id))
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return model
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get model", model_id=model_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get model")


@router.post("/", response_model=ModelResponse)
async def create_model(
    model_data: ModelCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new model"""
    try:
        # Validate model file exists
        matlab_service = MATLABService()
        if not await matlab_service.validate_model(model_data.file_path):
            raise HTTPException(status_code=400, detail="Invalid model file")
        
        # Create model instance
        model = Model(**model_data.dict())
        db.add(model)
        await db.commit()
        await db.refresh(model)
        
        logger.info("Model created", model_id=model.id, name=model.name)
        return model
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create model", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create model")


@router.put("/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: int,
    model_data: ModelUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """Update an existing model"""
    try:
        result = await db.execute(select(Model).where(Model.id == model_id))
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Update model fields
        update_data = model_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(model, field, value)
        
        await db.commit()
        await db.refresh(model)
        
        logger.info("Model updated", model_id=model.id, name=model.name)
        return model
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update model", model_id=model_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update model")


@router.delete("/{model_id}")
async def delete_model(model_id: int, db: AsyncSession = Depends(get_async_db)):
    """Delete a model"""
    try:
        result = await db.execute(select(Model).where(Model.id == model_id))
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Soft delete by setting is_active to False
        model.is_active = False
        await db.commit()
        
        logger.info("Model deleted", model_id=model.id, name=model.name)
        return {"message": "Model deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete model", model_id=model_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete model")


@router.post("/{model_id}/validate")
async def validate_model(model_id: int, db: AsyncSession = Depends(get_async_db)):
    """Validate a model"""
    try:
        result = await db.execute(select(Model).where(Model.id == model_id))
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Validate model using MATLAB service
        matlab_service = MATLABService()
        is_valid = await matlab_service.validate_model(model.file_path)
        
        # Update validation status
        model.is_validated = is_valid
        if not is_valid:
            model.validation_errors = "Model validation failed"
        
        await db.commit()
        
        return {
            "model_id": model_id,
            "is_valid": is_valid,
            "validation_errors": model.validation_errors
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to validate model", model_id=model_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to validate model")


@router.get("/{model_id}/info")
async def get_model_info(model_id: int, db: AsyncSession = Depends(get_async_db)):
    """Get detailed information about a model"""
    try:
        result = await db.execute(select(Model).where(Model.id == model_id))
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Get model info from MATLAB service
        matlab_service = MATLABService()
        model_info = await matlab_service.get_model_info(model.file_path)
        
        return {
            "model": model,
            "matlab_info": model_info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get model info", model_id=model_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get model info")


@router.post("/upload")
async def upload_model_file(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_async_db)
):
    """Upload a model file"""
    try:
        # Validate file type
        if not file.filename.endswith(('.slx', '.m')):
            raise HTTPException(status_code=400, detail="Invalid file type. Only .slx and .m files are allowed")
        
        # Save file
        file_path = f"./matlab/models/{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create model record
        model_data = ModelCreate(
            name=name,
            description=description,
            file_path=file_path,
            file_type=file.filename.split('.')[-1],
            category=category
        )
        
        model = Model(**model_data.dict())
        db.add(model)
        await db.commit()
        await db.refresh(model)
        
        logger.info("Model file uploaded", model_id=model.id, filename=file.filename)
        return {"message": "File uploaded successfully", "model_id": model.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to upload model file", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to upload model file")
