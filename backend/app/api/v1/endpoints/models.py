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
from app.services.model_project import inspect_model_project
from app.schemas.model import (
    ModelCreate,
    ModelUpdate,
    ModelResponse,
    ModelListResponse,
    DirectoryModelCreate,
    DirectoryValidateRequest,
)

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


@router.post("/validate-directory")
async def validate_model_directory(
    body: DirectoryValidateRequest,
    current_user=Depends(get_current_user),
):
    """Check that a path is a MATLAB project by layout (runner + startup), not folder name."""
    return inspect_model_project(body.directory_path)


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


@router.post("/upload-directory")
async def upload_model_directory(
    directory_path: str = Form(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    version: Optional[str] = Form("1.0.0"),
    category: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # comma-separated or JSON array
    parameters: Optional[str] = Form(None),  # JSON object as string
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user),
):
    """Register a MATLAB model project directory (any name; layout is validated)."""
    try:
        layout = inspect_model_project(directory_path)
        if not layout["valid"]:
            raise HTTPException(
                status_code=400,
                detail="; ".join(layout["errors"]) or "Invalid model directory",
            )

        startup_script = layout.get("startup_script")

        # Parse optional complex fields
        parsed_tags = None
        if tags:
            try:
                import json
                parsed_tags = json.loads(tags) if tags.startswith('[') else [tag.strip() for tag in tags.split(',')]
            except Exception:
                parsed_tags = [tag.strip() for tag in tags.split(',')]

        parsed_parameters = None
        if parameters:
            try:
                import json
                parsed_parameters = json.loads(parameters)
            except Exception:
                parsed_parameters = {}

        model = Model(
            name=name,
            description=description,
            model_directory=layout["root"] or directory_path,
            model_type="directory",
            startup_script=startup_script,
            version=version,
            category=category,
            author=author,
            tags=parsed_tags,
            parameters=parsed_parameters,
            created_by=current_user.id,
            is_active=True,
            is_validated=False
        )

        db.add(model)
        await db.commit()
        await db.refresh(model)

        logger.info("Directory model created", model_id=model.id, name=model.name, directory=layout["root"])
        return model

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create directory model", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create directory model")


@router.post("/{model_id}/launch")
async def launch_model(
    model_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user),
):
    """Launch a MATLAB model (especially directory-based models)"""
    try:
        result = await db.execute(select(Model).where(Model.id == model_id))
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Check if user has access to this model
        if not (current_user.is_superuser or model.created_by == current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Initialize MATLAB service
        matlab_service = MATLABService()
        await matlab_service.initialize()
        
        # Launch model based on type
        if model.model_type == "directory" and model.model_directory:
            # For directory-based models, run the startup script
            if model.startup_script and os.path.exists(model.startup_script):
                # Change to the startup script directory
                startup_dir = os.path.dirname(model.startup_script)
                startup_name = os.path.basename(model.startup_script).replace('.m', '')
                
                # Run the startup script
                matlab_service.engine.cd(startup_dir)
                matlab_service.engine.eval(f"run('{startup_name}')")
                
                logger.info("Directory model launched", model_id=model_id, startup_script=model.startup_script)
                return {
                    "model_id": model_id,
                    "status": "launched",
                    "message": f"Model launched successfully using startup script: {os.path.basename(model.startup_script)}",
                    "startup_script": model.startup_script
                }
            else:
                raise HTTPException(status_code=400, detail="No valid startup script found for directory model")
        
        elif model.file_path and os.path.exists(model.file_path):
            # For file-based models, execute normally
            result = await matlab_service.execute_model(
                model_path=model.file_path,
                input_data={},
                startup_script=model.startup_script
            )
            
            logger.info("File model executed", model_id=model_id, file_path=model.file_path)
            return {
                "model_id": model_id,
                "status": "executed",
                "result": result
            }
        
        else:
            raise HTTPException(status_code=400, detail="Model file or directory not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to launch model", model_id=model_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to launch model: {str(e)}")


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
