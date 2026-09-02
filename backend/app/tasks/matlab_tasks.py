"""
Celery tasks for MATLAB model execution
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from celery import current_task
from sqlalchemy import select, update
from datetime import datetime, timezone
import time
import asyncio
import structlog

from app.core.celery import celery_app
from app.core.config import settings
from app.core.database import AsyncSessionLocal, SessionLocal
from app.models.test_run import TestRun
from app.models.model import Model
from app.models.user import User  # noqa: F401 — TestRun.user relationship
from app.models.data_point import DataPoint  # noqa: F401
from app.services.matlab_service import MATLABService
from app.services.simulation_runner_service import SimulationRunnerService
from app.services.influxdb_service import get_simulation_ids_in_time_range
from app.services.run_logs import ensure_matlab_output_logged
from app.services.run_state import parse_progress_line, update_run_results, progress_from_run, results_dict
from app.services import simulation_ids

logger = structlog.get_logger()

# Max length for stored error messages (avoid verbose logs in DB/UI)
ERROR_MSG_MAX_LEN = 200


def _short_error(msg: str) -> str:
    """Extract concise error message (first line, max length)"""
    first = (msg.split("\n")[0] or msg).strip()
    return first[:ERROR_MSG_MAX_LEN] + ("..." if len(first) > ERROR_MSG_MAX_LEN else "")


def _error_from_result(result: Dict[str, Any]) -> str:
    """Prefer a MATLAB error line from captured output over a generic exit-code message."""
    err = result.get("error") or "Simulation failed"
    output = result.get("output") or ""
    markers = (
        "Unrecognized function or variable",
        "Unable to resolve the name",
        "[ERROR]",
        "ERROR: MATLAB",
        "Error running MATLAB",
        "Error in runBatchSimulations",
        "Error in batch processing",
        "Neither STAB1 nor STAB",
        "Invalid parameter path",
    )
    for line in output.splitlines():
        stripped = line.strip()
        if any(marker in stripped for marker in markers):
            return stripped
    return err


def _extract_simulation_id_from_output_dir(output_directory: Optional[str]) -> Optional[str]:
    """Latest simOut_YYYYMMDD_HHMMSS.csv — used as Grafana/Influx simulation_id."""
    return simulation_ids.from_output_dir(output_directory)


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
                        start_time=datetime.now(timezone.utc)
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
                        end_time=datetime.now(timezone.utc),
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
                        end_time=datetime.now(timezone.utc),
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
    return asyncio.run(_execute_model())


@celery_app.task(bind=True, name="execute_test_run", time_limit=3600, soft_time_limit=3500)
def execute_test_run_task(self, test_run_id: int):
    """Celery wrapper so MATLAB runs in a worker process, not in uvicorn."""
    run_test_run_execution(test_run_id)


def run_test_run_execution(test_run_id: int) -> None:
    """Run a test run in a worker process (Celery or `python -m app.worker`)."""
    print(f"\n{'='*60}\n[TEST RUN] Starting execution for test_run_id={test_run_id}\n{'='*60}", flush=True)
    db = SessionLocal()
    try:
        test_run = db.execute(select(TestRun).where(TestRun.id == test_run_id)).scalar_one_or_none()
        if not test_run:
            logger.error("Test run not found", test_run_id=test_run_id)
            return

        model = db.execute(select(Model).where(Model.id == test_run.model_id)).scalar_one_or_none()
        if not model:
            logger.error("Model not found", model_id=test_run.model_id)
            test_run.status = "failed"
            test_run.error_message = "Model not found"
            test_run.end_time = datetime.now(timezone.utc)
            db.commit()
            return

        if model.model_type == "directory" and model.model_directory:
            sim_runner = SimulationRunnerService()
            if not sim_runner.is_available():
                print("[TEST RUN] Simulation Runner not available - cannot execute directory model", flush=True)
            else:
                # Set running so UI shows correct status during execution (create flow doesn't set it)
                test_run.status = "running"
                if not test_run.start_time:
                    test_run.start_time = datetime.now(timezone.utc)
                update_run_results(
                    test_run,
                    worker_pid=os.getpid(),
                    heartbeat_at=datetime.now(timezone.utc).isoformat(),
                    progress=1,
                    progress_message="Queued worker started",
                )
                db.commit()
                print(f"[TEST RUN] Executing directory model via Simulation Runner: {model.model_directory}", flush=True)
                logger.info(
                    "Executing directory model via Simulation Runner",
                    test_run_id=test_run_id,
                    model_directory=model.model_directory,
                )
                params_json = None
                params_file = None
                batch_mode = False
                if test_run.configuration and isinstance(test_run.configuration, dict):
                    params_json = test_run.configuration.get("parameters")
                if test_run.input_data and isinstance(test_run.input_data, dict):
                    file_path = test_run.input_data.get("file_path")
                    if file_path:
                        path_str = str(file_path).replace("/", os.sep)
                        path_str = str(Path(path_str).resolve()) if not os.path.isabs(path_str) else path_str
                        if os.path.isfile(path_str):
                            if path_str.endswith(".json"):
                                try:
                                    with open(path_str, "r", encoding="utf-8") as f:
                                        params_json = json.load(f)
                                except Exception:
                                    pass
                            elif path_str.endswith(".csv"):
                                params_file = path_str
                                batch_mode = True

                # Enable DB export when a token is configured (backend .env / settings only)
                influx = settings.influx_connection()
                db_token = influx.get("token")
                db_mode = bool(db_token)
                db_type = "influxdb"
                db_host = influx.get("host")
                db_port = influx.get("port")
                db_org = influx.get("org")
                db_bucket = influx.get("bucket")
                if not db_mode:
                    logger.warning("INFLUXDB_TOKEN not set; skipping InfluxDB export", test_run_id=test_run_id)

                last_progress_commit = [0.0]

                def on_progress_line(line: str) -> None:
                    parsed = parse_progress_line(line)
                    now = time.time()
                    if not parsed and now - last_progress_commit[0] < 15:
                        return
                    fields = parsed or {}
                    if "progress" in fields:
                        prev = results_dict(test_run).get("progress") or 0
                        try:
                            fields["progress"] = max(int(prev), int(fields["progress"]))
                        except (TypeError, ValueError):
                            fields.pop("progress", None)
                    fields["heartbeat_at"] = datetime.now(timezone.utc).isoformat()
                    update_run_results(test_run, **fields)
                    try:
                        db.commit()
                    except Exception:
                        db.rollback()
                    last_progress_commit[0] = now

                result = sim_runner.run_simulation(
                    project_directory=model.model_directory,
                    params_file=params_file,
                    params_json=params_json,
                    batch_mode=batch_mode,
                    db_mode=db_mode,
                    db_type=db_type,
                    db_host=db_host,
                    db_port=db_port,
                    db_token=db_token,
                    db_org=db_org,
                    db_bucket=db_bucket,
                    startup_script=model.startup_script,
                    progress_callback=on_progress_line,
                )
                test_run.end_time = datetime.now(timezone.utc)
                if test_run.start_time and test_run.end_time:
                    try:
                        st = test_run.start_time
                        if st.tzinfo is None:
                            st = st.replace(tzinfo=timezone.utc)
                        delta = test_run.end_time - st
                        test_run.execution_time = delta.total_seconds()
                    except (TypeError, ValueError):
                        pass
                output_dir = result.get("output_directory")
                raw_output = result.get("output") or ""
                try:
                    ensure_matlab_output_logged(test_run_id, raw_output)
                except Exception:
                    logger.warning("Could not write MATLAB output to logs folder", test_run_id=test_run_id)
                output_data = {
                    "output_directory": output_dir,
                    "output_tail": raw_output[-4000:],
                }
                db_warning = result.get("db_export_warning") if result.get("success") else None
                csv_exported = bool(output_dir and _extract_simulation_id_from_output_dir(output_dir))
                # Prefer the ID MATLAB actually wrote to Influx, not an older CSV in the same folder
                simulation_id = simulation_ids.preferred_simulation_id(
                    output_data=output_data,
                    raw_output=raw_output,
                )
                if (
                    not simulation_id
                    and result.get("success")
                    and not db_warning
                    and db_mode
                    and (test_run.start_time or test_run.end_time)
                ):
                    start = test_run.start_time or test_run.end_time
                    end = test_run.end_time or test_run.start_time
                    if start:
                        ids = get_simulation_ids_in_time_range(start, end)
                        if len(ids) == 1:
                            simulation_id = ids[0]
                        elif len(ids) > 1 and test_run.start_time:
                            def _parse_sid(s: str):
                                try:
                                    return datetime.strptime(s, "%Y%m%d_%H%M%S")
                                except ValueError:
                                    return None
                            start_naive = test_run.start_time.replace(tzinfo=None) if test_run.start_time.tzinfo else test_run.start_time
                            best, best_delta = None, None
                            for s in ids:
                                t = _parse_sid(s)
                                if t is None:
                                    continue
                                delta = abs((t - start_naive).total_seconds())
                                if best_delta is None or delta < best_delta:
                                    best_delta, best = delta, s
                            simulation_id = best
                        elif ids:
                            simulation_id = ids[0]
                if simulation_id:
                    test_run.simulation_id = simulation_id

                influx_ok = bool(result.get("success") and db_mode and not db_warning)
                update_run_results(
                    test_run,
                    csv_exported=csv_exported or bool(output_dir),
                    influx_exported=influx_ok,
                    progress=100 if result.get("success") else progress_from_run(test_run),
                    progress_message="Complete" if result.get("success") else "Failed",
                    heartbeat_at=datetime.now(timezone.utc).isoformat(),
                )

                if result.get("success"):
                    db_warning = result.get("db_export_warning")
                    test_run.output_data = output_data
                    if db_warning:
                        print(
                            f"[TEST RUN] Simulation completed with warning for test_run_id={test_run_id}: {db_warning}",
                            flush=True,
                        )
                        test_run.status = "completed_warning"
                        test_run.error_message = _short_error(db_warning)
                        logger.warning(
                            "Simulation completed with InfluxDB export warning",
                            test_run_id=test_run_id,
                            simulation_id=simulation_id,
                            warning=db_warning,
                        )
                    else:
                        print(f"[TEST RUN] Simulation completed successfully for test_run_id={test_run_id} (exit code: {result.get('return_code', '?')})", flush=True)
                        test_run.status = "completed"
                        test_run.error_message = None
                        logger.info("Simulation completed", test_run_id=test_run_id, simulation_id=simulation_id)
                else:
                    rc = result.get("return_code", "?")
                    err = _error_from_result(result)
                    print(f"[TEST RUN] Simulation failed for test_run_id={test_run_id}: {err} (exit code: {rc})", flush=True)
                    test_run.status = "failed"
                    test_run.error_message = _short_error(err)
                    # Still store output and output_dir for debugging even when failed
                    test_run.output_data = output_data
                    logger.error(
                        "Simulation failed",
                        test_run_id=test_run_id,
                        error=err,
                        return_code=rc,
                    )
                try:
                    db.commit()
                except Exception as commit_err:
                    logger.exception("Failed to commit test run result", test_run_id=test_run_id, error=str(commit_err))
                    db.rollback()
                    # Refetch and store user-friendly message: execution succeeded but DB write failed
                    tr = db.execute(select(TestRun).where(TestRun.id == test_run_id)).scalar_one_or_none()
                    if tr:
                        tr.status = "failed"
                        tr.end_time = datetime.now(timezone.utc)
                        tr.error_message = _short_error(
                            f"Execution completed successfully but failed to save results. {commit_err!s}"
                        )
                        try:
                            db.commit()
                        except Exception:
                            db.rollback()
                    return
                return

        # File model or directory model without Simulation Runner
        error_msg = (
            "MATLAB Engine is not available for in-process execution. "
            "For directory models, ensure simulationsmodelle is a sibling directory. "
            "For file models, install: pip install matlabengine (from MATLAB)."
        )
        logger.warning("Cannot execute file model without MATLAB Engine", test_run_id=test_run_id)
        test_run.status = "failed"
        test_run.end_time = datetime.now(timezone.utc)
        test_run.error_message = error_msg
        db.commit()
    except Exception as e:
        logger.exception("Test run execution failed", test_run_id=test_run_id, error=str(e))
        try:
            test_run = db.execute(select(TestRun).where(TestRun.id == test_run_id)).scalar_one_or_none()
            if test_run:
                test_run.status = "failed"
                test_run.end_time = datetime.now(timezone.utc)
                test_run.error_message = _short_error(str(e))
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()


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
