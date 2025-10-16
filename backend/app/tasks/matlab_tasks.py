"""
Celery tasks for MATLAB model execution
"""

from typing import Dict, Any, Optional
from celery import current_task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
import time
import structlog

from app.core.celery import celery_app
from app.core.database import AsyncSessionLocal
from app.models.test_run import TestRun
from app.services.matlab_service import MATLABService

logger = structlog.get_logger()


@celery_app.task(bind=True, name="execute_model")
def execute_model_task(
    self,
    test_run_id: int,
    model_path: str,
    input_data: Dict[str, Any],
    startup_script: Optional[str] = None
):
    """
    Execute a MATLAB/Simulink model in the background
    
    Args:
        test_run_id: ID of the test run
        model_path: Path to the model file
        input_data: Input data for the model
        startup_script: Optional startup script path
    """
    async def _execute_model():
        async with AsyncSessionLocal() as db:
            try:
                # Get test run
                result = await db.execute(
                    select(TestRun).where(TestRun.id == test_run_id)
                )
                test_run = result.scalar_one_or_none()
                
                if not test_run:
                    logger.error("Test run not found", test_run_id=test_run_id)
                    return {"status": "error", "message": "Test run not found"}
                
                # Update status to running
                await db.execute(
                    update(TestRun)
                    .where(TestRun.id == test_run_id)
                    .values(
                        status="running",
                        start_time=datetime.utcnow()
                    )
                )
                await db.commit()
                
                logger.info("Starting model execution", test_run_id=test_run_id, model=model_path)
                
                # Initialize MATLAB service
                matlab_service = MATLABService()
                await matlab_service.initialize()
                
                # Execute model
                start_time = time.time()
                result = await matlab_service.execute_model(
                    model_path=model_path,
                    input_data=input_data,
                    startup_script=startup_script,
                    timeout=300
                )
                execution_time = time.time() - start_time
                
                # Update test run with results
                await db.execute(
                    update(TestRun)
                    .where(TestRun.id == test_run_id)
                    .values(
                        status="completed",
                        end_time=datetime.utcnow(),
                        execution_time=execution_time,
                        output_data=result.get("output_data", {}),
                        results=result.get("results", {})
                    )
                )
                await db.commit()
                
                logger.info(
                    "Model execution completed",
                    test_run_id=test_run_id,
                    execution_time=execution_time
                )
                
                return {
                    "status": "success",
                    "test_run_id": test_run_id,
                    "execution_time": execution_time,
                    "output_data": result.get("output_data", {})
                }
                
            except Exception as e:
                logger.error(
                    "Model execution failed",
                    test_run_id=test_run_id,
                    error=str(e)
                )
                
                # Update test run with error
                await db.execute(
                    update(TestRun)
                    .where(TestRun.id == test_run_id)
                    .values(
                        status="failed",
                        end_time=datetime.utcnow(),
                        error_message=str(e)
                    )
                )
                await db.commit()
                
                return {
                    "status": "error",
                    "test_run_id": test_run_id,
                    "error": str(e)
                }
    
    # Run the async function
    import asyncio
    return asyncio.run(_execute_model())


@celery_app.task(name="validate_model")
def validate_model_task(model_id: int, model_path: str):
    """
    Validate a MATLAB/Simulink model
    
    Args:
        model_id: ID of the model
        model_path: Path to the model file
    """
    async def _validate_model():
        async with AsyncSessionLocal() as db:
            try:
                # Initialize MATLAB service
                matlab_service = MATLABService()
                await matlab_service.initialize()
                
                # Validate model
                is_valid = await matlab_service.validate_model(model_path)
                
                # Get model info if valid
                model_info = None
                if is_valid:
                    model_info = await matlab_service.get_model_info(model_path)
                
                logger.info(
                    "Model validation completed",
                    model_id=model_id,
                    is_valid=is_valid
                )
                
                return {
                    "status": "success",
                    "model_id": model_id,
                    "is_valid": is_valid,
                    "model_info": model_info
                }
                
            except Exception as e:
                logger.error(
                    "Model validation failed",
                    model_id=model_id,
                    error=str(e)
                )
                
                return {
                    "status": "error",
                    "model_id": model_id,
                    "error": str(e)
                }
    
    # Run the async function
    import asyncio
    return asyncio.run(_validate_model())


@celery_app.task(name="batch_execute_models")
def batch_execute_models_task(
    test_run_ids: list,
    model_paths: list,
    input_data_list: list,
    startup_scripts: Optional[list] = None
):
    """
    Execute multiple models in batch
    
    Args:
        test_run_ids: List of test run IDs
        model_paths: List of model paths
        input_data_list: List of input data dictionaries
        startup_scripts: Optional list of startup scripts
    """
    results = []
    
    for i, (test_run_id, model_path, input_data) in enumerate(
        zip(test_run_ids, model_paths, input_data_list)
    ):
        startup_script = startup_scripts[i] if startup_scripts else None
        
        # Execute each model
        result = execute_model_task.delay(
            test_run_id=test_run_id,
            model_path=model_path,
            input_data=input_data,
            startup_script=startup_script
        )
        
        results.append({
            "test_run_id": test_run_id,
            "task_id": result.id,
            "status": "queued"
        })
    
    logger.info("Batch model execution started", count=len(test_run_ids))
    
    return {
        "status": "success",
        "batch_id": current_task.request.id,
        "results": results
    }
