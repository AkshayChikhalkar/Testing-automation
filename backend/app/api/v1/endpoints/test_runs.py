"""
Test run execution endpoints
"""

import io
import json
import zipfile
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, timezone
import structlog

from app.core.database import get_async_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.test_run import TestRun
from app.models.model import Model
from app.models.data_point import DataPoint
from app.services.matlab_service import MATLABService
from app.schemas.test_run import TestRunCreate, TestRunResponse, TestRunListResponse
from app.tasks.matlab_tasks import execute_model_task, run_test_run_execution

router = APIRouter()
logger = structlog.get_logger()


@router.get("/", response_model=List[TestRunListResponse])
async def list_test_runs(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    model_id: Optional[int] = None,
    all: Optional[bool] = False,
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    """List all test runs with optional filtering"""
    try:
        from sqlalchemy.orm import selectinload
        
        query = select(TestRun).options(selectinload(TestRun.model))
        
        if status:
            query = query.where(TestRun.status == status)
        if model_id:
            query = query.where(TestRun.model_id == model_id)
        
        if not (current_user.is_superuser and all):
            query = query.where(TestRun.user_id == current_user.id)

        query = query.order_by(TestRun.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        test_runs = result.scalars().all()
        
        # Convert to response format with model names
        response_data = []
        for test_run in test_runs:
            exec_time = test_run.execution_time
            if exec_time is None and test_run.start_time and test_run.end_time:
                try:
                    st = test_run.start_time
                    et = test_run.end_time
                    if st.tzinfo is None:
                        st = st.replace(tzinfo=timezone.utc)
                    if et.tzinfo is None:
                        et = et.replace(tzinfo=timezone.utc)
                    exec_time = (et - st).total_seconds()
                except (TypeError, ValueError, AttributeError):
                    pass
            test_run_dict = {
                "id": test_run.id,
                "name": test_run.name,
                "model_id": test_run.model_id,
                "model_name": test_run.model.name if test_run.model else None,
                "user_id": test_run.user_id,
                "status": test_run.status,
                "execution_time": exec_time,
                "start_time": test_run.start_time,
                "end_time": test_run.end_time,
                "error_message": test_run.error_message,
                "created_at": test_run.created_at,
            }
            response_data.append(test_run_dict)
        
        return response_data
    except Exception as e:
        logger.error("Failed to list test runs", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list test runs")


@router.get("/{test_run_id}", response_model=TestRunResponse)
async def get_test_run(test_run_id: int, db: AsyncSession = Depends(get_async_db), current_user = Depends(get_current_user)):
    """Get a specific test run by ID"""
    try:
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(TestRun).where(TestRun.id == test_run_id).options(selectinload(TestRun.model))
        )
        test_run = result.scalar_one_or_none()
        
        if not test_run:
            raise HTTPException(status_code=404, detail="Test run not found")
        
        # Build response with model_name for UI
        resp = TestRunResponse.model_validate(test_run)
        if test_run.model:
            resp.model_name = test_run.model.name
        return resp
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get test run", test_run_id=test_run_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get test run")


@router.post("/", response_model=TestRunResponse)
async def create_test_run(
    test_run_data: TestRunCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    """Create and start a new test run"""
    try:
        # Verify model exists
        result = await db.execute(select(Model).where(Model.id == test_run_data.model_id))
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Create test run record
        test_run = TestRun(
            name=test_run_data.name,
            description=test_run_data.description,
            model_id=test_run_data.model_id,
            user_id=current_user.id,
            input_data=test_run_data.input_data,
            configuration=test_run_data.configuration,
            status="pending"
        )
        
        db.add(test_run)
        await db.commit()
        await db.refresh(test_run)
        
        # Start execution in background (uses Simulation Runner for directory models)
        background_tasks.add_task(run_test_run_execution, test_run.id)

        logger.info("Test run created", test_run_id=test_run.id, model_id=model.id)
        return test_run
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create test run", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create test run")


@router.post("/create-with-input", response_model=TestRunResponse)
async def create_test_run_with_input(
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    model_id: int = Form(...),
    input_file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    configuration: Optional[str] = Form(None),  # JSON string
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    """Create a test run with an uploaded input data file."""
    try:
        # Verify model exists
        result = await db.execute(select(Model).where(Model.id == model_id))
        model = result.scalar_one_or_none()
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # Save input file
        inputs_dir = os.path.join(settings.UPLOAD_PATH, "inputs")
        os.makedirs(inputs_dir, exist_ok=True)
        input_path_fs = os.path.join(inputs_dir, input_file.filename)
        content = await input_file.read()
        with open(input_path_fs, "wb") as buf:
            buf.write(content)
        input_path = input_path_fs.replace('\\', '/')

        # Build input_data payload
        file_ext = input_file.filename.split('.')[-1].lower()
        input_data = {"file_path": input_path, "format": file_ext}

        # Optional configuration JSON
        parsed_config = None
        if configuration:
            try:
                import json
                val = json.loads(configuration)
                if isinstance(val, dict):
                    parsed_config = val
            except Exception:
                parsed_config = None

        # Create test run record
        test_run = TestRun(
            name=name,
            description=description,
            model_id=model_id,
            user_id=current_user.id,
            input_data=input_data,
            configuration=parsed_config,
            status="pending",
        )
        db.add(test_run)
        await db.commit()
        await db.refresh(test_run)

        # Start background execution if requested
        if background_tasks is not None:
            background_tasks.add_task(run_test_run_execution, test_run.id)

        logger.info("Test run created with input file", test_run_id=test_run.id, model_id=model.id)
        return test_run
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create test run with input", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create test run with input")


@router.post("/{test_run_id}/execute")
async def execute_test_run(
    test_run_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db)
):
    """Execute an existing test run"""
    try:
        result = await db.execute(select(TestRun).where(TestRun.id == test_run_id))
        test_run = result.scalar_one_or_none()
        
        if not test_run:
            raise HTTPException(status_code=404, detail="Test run not found")
        
        if test_run.status not in ["pending", "failed"]:
            raise HTTPException(status_code=400, detail="Test run cannot be executed in current status")
        
        # Get model information
        result = await db.execute(select(Model).where(Model.id == test_run.model_id))
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Update status to running
        test_run.status = "running"
        test_run.start_time = datetime.now(timezone.utc)
        await db.commit()
        
        # Start execution in background (uses Simulation Runner for directory models)
        background_tasks.add_task(run_test_run_execution, test_run.id)

        logger.info("Test run execution started", test_run_id=test_run.id)
        return {"message": "Test run execution started", "test_run_id": test_run.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to execute test run", test_run_id=test_run_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to execute test run")


@router.delete("/{test_run_id}")
async def delete_test_run(
    test_run_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """Delete a test run and its data points"""
    try:
        result = await db.execute(select(TestRun).where(TestRun.id == test_run_id))
        test_run = result.scalar_one_or_none()

        if not test_run:
            raise HTTPException(status_code=404, detail="Test run not found")

        if not (current_user.is_superuser or test_run.user_id == current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to delete this test run")

        await db.execute(delete(DataPoint).where(DataPoint.test_run_id == test_run_id))
        await db.delete(test_run)
        await db.commit()

        logger.info("Test run deleted", test_run_id=test_run_id)
        return {"message": "Test run deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete test run", test_run_id=test_run_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete test run")


@router.post("/{test_run_id}/cancel")
async def cancel_test_run(test_run_id: int, db: AsyncSession = Depends(get_async_db)):
    """Cancel a running test run"""
    try:
        result = await db.execute(select(TestRun).where(TestRun.id == test_run_id))
        test_run = result.scalar_one_or_none()
        
        if not test_run:
            raise HTTPException(status_code=404, detail="Test run not found")
        
        if test_run.status not in ["pending", "running"]:
            raise HTTPException(status_code=400, detail="Test run cannot be cancelled in current status")
        
        # Update status to cancelled
        test_run.status = "cancelled"
        test_run.end_time = datetime.now(timezone.utc)
        await db.commit()
        
        logger.info("Test run cancelled", test_run_id=test_run.id)
        return {"message": "Test run cancelled", "test_run_id": test_run.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel test run", test_run_id=test_run_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to cancel test run")


@router.get("/{test_run_id}/results")
async def get_test_run_results(test_run_id: int, db: AsyncSession = Depends(get_async_db)):
    """Get test run results and output data"""
    try:
        result = await db.execute(select(TestRun).where(TestRun.id == test_run_id))
        test_run = result.scalar_one_or_none()
        
        if not test_run:
            raise HTTPException(status_code=404, detail="Test run not found")
        
        return {
            "test_run_id": test_run.id,
            "status": test_run.status,
            "output_data": test_run.output_data,
            "results": test_run.results,
            "execution_time": test_run.execution_time,
            "error_message": test_run.error_message
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get test run results", test_run_id=test_run_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get test run results")


@router.post("/{test_run_id}/report")
async def generate_test_report(test_run_id: int, db: AsyncSession = Depends(get_async_db)):
    """Generate a test report for a completed test run"""
    try:
        result = await db.execute(select(TestRun).where(TestRun.id == test_run_id))
        test_run = result.scalar_one_or_none()
        
        if not test_run:
            raise HTTPException(status_code=404, detail="Test run not found")
        
        if test_run.status != "completed":
            raise HTTPException(status_code=400, detail="Test report can only be generated for completed test runs")
        
        # TODO: Implement report generation
        # This would typically generate a PDF or HTML report
        
        return {
            "message": "Test report generation started",
            "test_run_id": test_run_id,
            "report_path": test_run.report_path
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate test report", test_run_id=test_run_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate test report")


@router.get("/{test_run_id}/status")
async def get_test_run_status(test_run_id: int, db: AsyncSession = Depends(get_async_db)):
    """Get the current status of a test run"""
    try:
        result = await db.execute(select(TestRun).where(TestRun.id == test_run_id))
        test_run = result.scalar_one_or_none()
        
        if not test_run:
            raise HTTPException(status_code=404, detail="Test run not found")
        
        return {
            "test_run_id": test_run.id,
            "status": test_run.status,
            "start_time": test_run.start_time,
            "end_time": test_run.end_time,
            "execution_time": test_run.execution_time,
            "progress": "0%"  # TODO: Implement progress tracking
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get test run status", test_run_id=test_run_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get test run status")


@router.get("/{test_run_id}/download", response_class=StreamingResponse)
async def download_test_run_results(
    test_run_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """Download test run results as a ZIP file (results, output, metadata)"""
    try:
        result = await db.execute(select(TestRun).where(TestRun.id == test_run_id))
        test_run = result.scalar_one_or_none()

        if not test_run:
            raise HTTPException(status_code=404, detail="Test run not found")

        if not (current_user.is_superuser or test_run.user_id == current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to download this test run")

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # Metadata
            meta = {
                "id": test_run.id,
                "name": test_run.name,
                "model_id": test_run.model_id,
                "status": test_run.status,
                "start_time": str(test_run.start_time) if test_run.start_time else None,
                "end_time": str(test_run.end_time) if test_run.end_time else None,
                "execution_time": test_run.execution_time,
                "error_message": test_run.error_message,
            }
            zf.writestr("metadata.json", json.dumps(meta, indent=2))

            # Results (structured test metrics)
            if test_run.results is not None:
                zf.writestr("results.json", json.dumps(test_run.results, indent=2))

            # Console output (MATLAB/simulation logs)
            output_data = test_run.output_data or {}
            console_output = output_data.get("output", "") if isinstance(output_data, dict) else ""
            if console_output:
                zf.writestr("console_output.txt", console_output, zipfile.ZIP_DEFLATED)

            # Output data summary (paths, structure - without huge output text)
            output_meta = {k: v for k, v in (output_data or {}).items() if k != "output"}
            if output_meta:
                zf.writestr("output_info.json", json.dumps(output_meta, indent=2))

            # Add .mat and .json files from simulation output directory
            output_dir = None
            if isinstance(output_data, dict):
                output_dir = output_data.get("output_directory")
            if output_dir and os.path.isdir(output_dir):
                for fname in sorted(os.listdir(output_dir)):
                    if fname.endswith((".mat", ".json")):
                        fpath = os.path.join(output_dir, fname)
                        if os.path.isfile(fpath):
                            try:
                                arcname = f"simulation_output/{fname}"
                                zf.write(fpath, arcname=arcname)
                            except Exception as e:
                                logger.warning("Could not add file to ZIP", path=fpath, error=str(e))

        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="test-run-{test_run_id}-results.zip"',
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to download test run results", test_run_id=test_run_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to download test run results")
