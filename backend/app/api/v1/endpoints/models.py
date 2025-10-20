"""
Model management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.database import get_async_db
from app.core.security import get_current_user
from app.core.config import settings
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
    is_active: Optional[bool] = True,
    all: Optional[bool] = False,
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user),
):
    """List all models with optional filtering"""
    try:
        query = select(Model)
        
        if category:
            query = query.where(Model.category == category)
        # By default, hide inactive (soft-deleted) models
        if is_active is None:
            query = query.where(Model.is_active == True)  # noqa: E712
        else:
            query = query.where(Model.is_active == is_active)
        
        # Scope: if not admin or all!=true, restrict to created_by=current_user
        if not (current_user.is_superuser and all):
            query = query.where(Model.created_by == current_user.id)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        models = result.scalars().all()
        
        return models
    except Exception as e:
        logger.error("Failed to list models", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list models")


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(model_id: int, db: AsyncSession = Depends(get_async_db), current_user = Depends(get_current_user)):
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
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user),
):
    """Create a new model"""
    try:
        # If file_path is provided, validate the model file
        if model_data.file_path:
            matlab_service = MATLABService()
            if not await matlab_service.validate_model(model_data.file_path):
                raise HTTPException(status_code=400, detail="Invalid model file")
        
        # Create model instance. Allow creating metadata-only models by
        # providing safe defaults when file info is absent.
        payload = model_data.dict()
        if payload.get("file_path") is None:
            payload["file_path"] = ""
        if payload.get("file_type") is None:
            payload["file_type"] = ""

        payload["created_by"] = current_user.id
        model = Model(**payload)
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
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user),
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

        # Attempt to remove stored files (best-effort)
        try:
            import os
            if model.file_path:
                try:
                    os.remove(model.file_path)
                except FileNotFoundError:
                    pass
            if model.startup_script:
                try:
                    os.remove(model.startup_script)
                except FileNotFoundError:
                    pass
        except Exception:
            # Do not block deletion on file removal failures
            pass
        
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
    version: Optional[str] = Form("1.0.0"),
    author: Optional[str] = Form(None),
    startup_script: Optional[str] = Form(None),
    startup_script_file: Optional[UploadFile] = File(None),
    tags: Optional[str] = Form(None),  # comma-separated or JSON array
    parameters: Optional[str] = Form(None),  # JSON object as string
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user),
):
    """Upload a model file"""
    try:
        # Validate file type
        if not file.filename.endswith(('.slx', '.m')):
            raise HTTPException(status_code=400, detail="Invalid file type. Only .slx and .m files are allowed")
        
        # Determine and ensure upload directory
        upload_dir = os.path.join(settings.UPLOAD_PATH, "models")
        os.makedirs(upload_dir, exist_ok=True)

        # Save model file
        file_path_fs = os.path.join(upload_dir, file.filename)
        content = await file.read()
        with open(file_path_fs, "wb") as buffer:
            buffer.write(content)
        # Normalize to forward slashes for DB/UI consistency
        file_path = file_path_fs.replace('\\', '/')

        # Optionally save startup script file
        startup_path = startup_script
        if startup_script_file is not None:
            scripts_dir = os.path.join(settings.UPLOAD_PATH, "scripts")
            os.makedirs(scripts_dir, exist_ok=True)
            startup_path_fs = os.path.join(scripts_dir, startup_script_file.filename)
            scontent = await startup_script_file.read()
            with open(startup_path_fs, "wb") as sbuf:
                sbuf.write(scontent)
            startup_path = startup_path_fs.replace('\\', '/')
        
        # Parse optional complex fields
        parsed_tags = None
        if tags:
            try:
                import json
                parsed = json.loads(tags)
                if isinstance(parsed, list):
                    parsed_tags = parsed
            except Exception:
                # fallback: comma separated
                parsed_tags = [t.strip() for t in tags.split(',') if t.strip()]

        parsed_parameters = None
        if parameters:
            try:
                import json
                parsed = json.loads(parameters)
                if isinstance(parsed, dict):
                    parsed_parameters = parsed
            except Exception:
                parsed_parameters = None

        # Create model record
        model_data = ModelCreate(
            name=name,
            description=description,
            file_path=file_path,
            file_type=file.filename.split('.')[-1],
            version=version or "1.0.0",
            startup_script=startup_path,
            parameters=parsed_parameters,
            tags=parsed_tags,
            category=category,
            author=author,
        )
        
        payload = model_data.dict()
        payload["created_by"] = current_user.id
        model = Model(**payload)
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
