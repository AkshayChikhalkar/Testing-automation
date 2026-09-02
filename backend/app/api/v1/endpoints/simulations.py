"""
MATLAB Simulation Runner API - Web UI for run_simulation.py (simulationsmodelle)

Allows running MATLAB models with custom parameters, batch mode, and DB export.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form

from app.core.database import get_async_db
import os
import tempfile
import structlog

from app.core.config import settings
from app.core.security import get_current_user
from app.services.simulation_runner_service import SimulationRunnerService

router = APIRouter()
logger = structlog.get_logger()


@router.get("/runner/status")
async def get_runner_status(current_user=Depends(get_current_user)):
    """Check if simulation runner (simulationsmodelle) is available"""
    service = SimulationRunnerService()
    return {
        "available": service.is_available(),
        "simulations_path": str(service.simulations_path) if service.simulations_path else None,
    }


@router.post("/runner/run")
async def run_simulation(
    project_directory: str = Form(..., description="Path to MATLAB project (simulationsmodelle root)"),
    params_file: Optional[UploadFile] = File(None, description="CSV or JSON params file"),
    params_json: Optional[str] = Form(None, description="Inline JSON params {\"param.path\": value}"),
    param_overrides: Optional[str] = Form(None, description="Comma-separated param.path=value"),
    batch_mode: bool = Form(False, description="Batch mode (CSV with multiple param sets)"),
    db_mode: bool = Form(False, description="Export results to database"),
    db_type: str = Form("influxdb", description="influxdb or timescaledb"),
    db_host: Optional[str] = Form(None),
    db_port: Optional[int] = Form(None),
    db_token: Optional[str] = Form(None),
    db_org: Optional[str] = Form(None),
    db_bucket: Optional[str] = Form(None),
    startup_script: Optional[str] = Form(None, description="Custom startup script path"),
    current_user=Depends(get_current_user),
):
    """
    Run MATLAB simulation via simulationsmodelle run_simulation.py.

    - **project_directory**: Path to simulationsmodelle repo (must contain run_simulation.py)
    - **params_file**: Upload CSV (batch) or JSON (single) - each CSV row = one simulation
    - **params_json**: Alternative - inline JSON params
    - **param_overrides**: "param.path=value,param2.path=value2"
    - **batch_mode**: Enable for CSV with multiple rows
    - **db_mode**: Export to InfluxDB/TimescaleDB
    """
    service = SimulationRunnerService()
    if not service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Simulation runner not available. Ensure simulationsmodelle project is configured (SIMULATIONS_PROJECT_PATH).",
        )

    params_file_path: Optional[str] = None
    if params_file and params_file.filename:
        # Save uploaded file to temp and pass path
        ext = os.path.splitext(params_file.filename)[1].lower()
        suffix = ".csv" if ext == ".csv" else ".json"
        content = await params_file.read()
        with tempfile.NamedTemporaryFile(mode="wb", suffix=suffix, delete=False) as f:
            f.write(content)
            params_file_path = f.name
        try:
            result = _run_with_service(
                service=service,
                project_directory=project_directory,
                params_file=params_file_path,
                params_json=params_json,
                param_overrides=param_overrides,
                batch_mode=batch_mode,
                db_mode=db_mode,
                db_type=db_type,
                db_host=db_host,
                db_port=db_port,
                db_token=db_token,
                db_org=db_org,
                db_bucket=db_bucket,
                startup_script=startup_script,
            )
            return result
        finally:
            try:
                os.unlink(params_file_path)
            except OSError:
                pass
    else:
        return _run_with_service(
            service=service,
            project_directory=project_directory,
            params_file=None,
            params_json=params_json,
            param_overrides=param_overrides,
            batch_mode=batch_mode,
            db_mode=db_mode,
            db_type=db_type,
            db_host=db_host,
            db_port=db_port,
            db_token=db_token,
            db_org=db_org,
            db_bucket=db_bucket,
            startup_script=startup_script,
        )


def _run_with_service(
    service: SimulationRunnerService,
    project_directory: str,
    params_file: Optional[str],
    params_json: Optional[str],
    param_overrides: Optional[str],
    batch_mode: bool,
    db_mode: bool,
    db_type: str,
    db_host: Optional[str],
    db_port: Optional[int],
    db_token: Optional[str],
    db_org: Optional[str],
    db_bucket: Optional[str],
    startup_script: Optional[str],
) -> Dict[str, Any]:
    """Helper to call service with parsed params"""
    import json

    parsed_params: Optional[Dict[str, Any]] = None
    if params_json:
        try:
            parsed_params = json.loads(params_json)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid params_json: {e}")

    overrides_list: Optional[List[str]] = None
    if param_overrides:
        overrides_list = [p.strip() for p in param_overrides.split(",") if p.strip()]

    influx = settings.influx_connection()
    if db_mode and not db_token:
        db_token = influx.get("token")
    if db_host is None:
        db_host = influx.get("host")
    if db_port is None:
        db_port = influx.get("port")
    if db_org is None:
        db_org = influx.get("org")
    if db_bucket is None:
        db_bucket = influx.get("bucket")

    result = service.run_simulation(
        project_directory=project_directory,
        params_file=params_file,
        params_json=parsed_params,
        param_overrides=overrides_list,
        batch_mode=batch_mode,
        db_mode=db_mode,
        db_type=db_type,
        db_host=db_host,
        db_port=db_port,
        db_token=db_token,
        db_org=db_org,
        db_bucket=db_bucket,
        startup_script=startup_script,
    )
    return result


@router.get("/runner/models")
async def list_registered_models_for_runner(
    db=Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """List models with model_directory for use in simulation runner"""
    from sqlalchemy import select
    from app.models.model import Model

    result = await db.execute(
        select(Model).where(
            Model.model_type == "directory",
            Model.model_directory.isnot(None),
            Model.is_active == True,
        )
    )
    models = result.scalars().all()
    return [
        {
            "id": m.id,
            "name": m.name,
            "model_directory": m.model_directory,
            "startup_script": m.startup_script,
        }
        for m in models
    ]
