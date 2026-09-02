"""
Test run execution endpoints
"""

import csv
import io
import json
import zipfile
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse, Response
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
from app.schemas.test_run import TestRunCreate, TestRunResponse, TestRunListResponse
from app.services.job_dispatcher import enqueue_test_run, kill_worker, grafana_url_for
from app.services.run_logs import read_log_lines, read_log_text, resolve_log_path
from app.services.run_state import progress_from_run, results_dict
from app.services.simulation_ids import from_test_run as simulation_id_for

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
                "simulation_id": simulation_id_for(test_run) or test_run.simulation_id,
                "user_id": test_run.user_id,
                "status": test_run.status,
                "execution_time": exec_time,
                "start_time": test_run.start_time,
                "end_time": test_run.end_time,
                "error_message": test_run.error_message,
                "created_at": test_run.created_at,
                "progress": progress_from_run(test_run),
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
        # simulation_id is stored directly on the TestRun row (Postgres mapping)
        resp.simulation_id = simulation_id_for(test_run) or test_run.simulation_id
        resp.progress = progress_from_run(test_run)
        extra = results_dict(test_run)
        resp.csv_exported = extra.get("csv_exported")
        resp.influx_exported = extra.get("influx_exported")
        resp.grafana_url = grafana_url_for(resp.simulation_id)
        resp.logs = read_log_lines(test_run.id, test_run.output_data)
        return resp
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get test run", test_run_id=test_run_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get test run")


@router.post("/", response_model=TestRunResponse)
async def create_test_run(
    test_run_data: TestRunCreate,
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
        
        enqueue_test_run(test_run.id)

        logger.info("Test run created", test_run_id=test_run.id, model_id=model.id)
        return test_run
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create test run", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create test run")


@router.post("/create-with-input", response_model=TestRunResponse)
async def create_test_run_with_input(
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

        enqueue_test_run(test_run.id)

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
        
        test_run.status = "pending"
        test_run.start_time = datetime.now(timezone.utc)
        test_run.error_message = None
        await db.commit()
        
        enqueue_test_run(test_run.id)

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
        
        kill_worker(results_dict(test_run).get("worker_pid"))
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
        
        if test_run.status not in ("completed", "completed_warning"):
            raise HTTPException(status_code=400, detail="Test report can only be generated for completed test runs")
        
        extra = results_dict(test_run)
        reports_dir = os.path.join(settings.UPLOAD_PATH, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        report_path = os.path.join(reports_dir, f"test_run_{test_run.id}.html")
        grafana = grafana_url_for(simulation_id_for(test_run) or test_run.simulation_id) or ""
        csv_ok = extra.get("csv_exported")
        influx_ok = extra.get("influx_exported")
        sim_id = simulation_id_for(test_run) or test_run.simulation_id or "n/a"
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Test run {test_run.id}</title></head>
<body>
<h1>{test_run.name}</h1>
<p>Status: {test_run.status}</p>
<p>Simulation ID: {sim_id}</p>
<p>CSV exported: {csv_ok}</p>
<p>InfluxDB exported: {influx_ok}</p>
<p>Duration (s): {test_run.execution_time or "n/a"}</p>
{"<p><a href='" + grafana + "'>Open in Grafana</a></p>" if grafana else ""}
{"<p><strong>Warning:</strong> " + (test_run.error_message or "") + "</p>" if test_run.status == "completed_warning" else ""}
</body></html>
"""
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)
        test_run.report_path = report_path.replace("\\", "/")
        await db.commit()
        
        return {
            "message": "Test report generated",
            "test_run_id": test_run_id,
            "report_path": test_run.report_path,
            "grafana_url": grafana or None,
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
        
        extra = results_dict(test_run)
        pct = progress_from_run(test_run)
        return {
            "test_run_id": test_run.id,
            "status": test_run.status,
            "start_time": test_run.start_time,
            "end_time": test_run.end_time,
            "execution_time": test_run.execution_time,
            "progress": pct,
            "progress_message": extra.get("progress_message"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get test run status", test_run_id=test_run_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get test run status")


def _build_recorded_data_csv(
    test_run: TestRun,
    data_points: List[DataPoint],
    output_data: Optional[Dict[str, Any]] = None,
) -> str:
    """Build a CSV string containing recorded DB data: metadata, results, output_data (structured keys), and data points.

    Note: For directory-based simulations we also prefer the raw simOut_*.csv from the model's output directory.
    This helper is a fallback when that file is not available.
    """
    out = io.StringIO()
    writer = csv.writer(out)

    # Header for unified export (source, key, value + data point columns)
    writer.writerow([
        "source", "key", "value", "variable_name", "data_category", "value_type",
        "unit", "timestamp", "sequence_number", "quality_flag", "description"
    ])

    # Metadata rows
    meta = {
        "id": test_run.id,
        "name": test_run.name,
        "model_id": test_run.model_id,
        "status": test_run.status,
        "start_time": str(test_run.start_time) if test_run.start_time else None,
        "end_time": str(test_run.end_time) if test_run.end_time else None,
        "execution_time": test_run.execution_time,
        "error_message": test_run.error_message,
        "created_at": str(test_run.created_at) if test_run.created_at else None,
    }
    for k, v in meta.items():
        writer.writerow(["metadata", k, v if v is None else str(v), "", "", "", "", "", "", "", ""])

    # Results rows (flatten key-value)
    if test_run.results and isinstance(test_run.results, dict):
        for k, v in test_run.results.items():
            val = json.dumps(v) if isinstance(v, (dict, list)) else str(v)
            writer.writerow(["results", k, val, "", "", "", "", "", "", "", ""])

    # Output data rows (excluding verbose console text)
    if output_data and isinstance(output_data, dict):
        for k, v in output_data.items():
            # Skip raw console text, which is already in console_output.txt
            if k == "output":
                continue
            val = json.dumps(v, default=str) if isinstance(v, (dict, list)) else str(v)
            writer.writerow(["output_data", k, val, "", "", "", "", "", "", "", ""])

    # Data points rows
    for dp in data_points:
        value_str = json.dumps(dp.value) if dp.value is not None else ""
        writer.writerow([
            "data_point",
            str(dp.id),
            value_str,
            dp.variable_name or "",
            dp.data_category or "",
            dp.value_type or "",
            dp.unit or "",
            str(dp.timestamp) if dp.timestamp else "",
            str(dp.sequence_number) if dp.sequence_number is not None else "",
            dp.quality_flag or "",
            (dp.description or "")[:500] if dp.description else "",
        ])

    return out.getvalue()


@router.get("/{test_run_id}/logs/download")
async def download_test_run_logs(
    test_run_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """Download the execution log for a test run."""
    result = await db.execute(select(TestRun).where(TestRun.id == test_run_id))
    test_run = result.scalar_one_or_none()
    if not test_run:
        raise HTTPException(status_code=404, detail="Test run not found")
    if not (current_user.is_superuser or test_run.user_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to download this test run")

    log_file = resolve_log_path(test_run_id)
    if log_file:
        return FileResponse(
            path=str(log_file),
            media_type="text/plain; charset=utf-8",
            filename=f"test-run-{test_run_id}-logs.txt",
        )

    text = read_log_text(test_run_id)
    if not text and isinstance(test_run.output_data, dict):
        text = test_run.output_data.get("output_tail") or test_run.output_data.get("output") or ""
    if not text:
        raise HTTPException(status_code=404, detail="No logs found for this test run")
    return Response(
        content=text,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="test-run-{test_run_id}-logs.txt"'},
    )


@router.get("/{test_run_id}/download", response_class=StreamingResponse)
async def download_test_run_results(
    test_run_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """Download test run results as a ZIP file (results, output, metadata, recorded_data.csv)"""
    try:
        from sqlalchemy.orm import selectinload

        result = await db.execute(
            select(TestRun)
            .options(selectinload(TestRun.data_points))
            .where(TestRun.id == test_run_id)
        )
        test_run = result.scalar_one_or_none()

        if not test_run:
            raise HTTPException(status_code=404, detail="Test run not found")

        if not (current_user.is_superuser or test_run.user_id == current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to download this test run")

        data_points = list(test_run.data_points) if test_run.data_points else []

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
                "simulation_id": simulation_id_for(test_run) or test_run.simulation_id,
            }
            zf.writestr("metadata.json", json.dumps(meta, indent=2))

            # Results (structured test metrics)
            if test_run.results is not None:
                zf.writestr("results.json", json.dumps(test_run.results, indent=2))

            # Full output_data from DB; include simulation_id from Postgres when set
            output_data = dict(test_run.output_data or {})
            preferred_sid = simulation_id_for(test_run) or test_run.simulation_id
            if preferred_sid:
                output_data["simulation_id"] = preferred_sid
            if output_data:
                zf.writestr("output_data.json", json.dumps(output_data, indent=2, default=str))

            # Console output (MATLAB/simulation logs)
            console_output = read_log_text(test_run_id)
            if not console_output and isinstance(output_data, dict):
                console_output = output_data.get("output_tail") or output_data.get("output") or ""
            if console_output:
                zf.writestr("console_output.txt", console_output, zipfile.ZIP_DEFLATED)

            # Prefer raw simOut_*.csv from the simulation output directory as recorded_data.csv
            recorded_from_output = False
            output_dir = None
            if isinstance(output_data, dict):
                output_dir = output_data.get("output_directory")
            if output_dir and os.path.isdir(output_dir):
                for fname in sorted(os.listdir(output_dir)):
                    fpath = os.path.join(output_dir, fname)
                    if not os.path.isfile(fpath):
                        continue

                    lower_name = fname.lower()

                    # Use first simOut_*.csv (or any .csv) as the primary recorded data export
                    if not recorded_from_output and lower_name.endswith(".csv"):
                        try:
                            with open(fpath, "rb") as f:
                                csv_bytes = f.read()
                            zf.writestr("recorded_data.csv", csv_bytes, zipfile.ZIP_DEFLATED)
                            recorded_from_output = True
                        except Exception as e:
                            logger.warning("Could not add recorded CSV to ZIP", path=fpath, error=str(e))

                    # Always include raw simulation artifacts under simulation_output/
                    if lower_name.endswith((".mat", ".json", ".csv")):
                        try:
                            arcname = f"simulation_output/{fname}"
                            zf.write(fpath, arcname=arcname)
                        except Exception as e:
                            logger.warning("Could not add file to ZIP", path=fpath, error=str(e))

            # Fallback: build a CSV from DB data when no simOut CSV was found
            if not recorded_from_output:
                recorded_csv = _build_recorded_data_csv(test_run, data_points, output_data)
                zf.writestr("recorded_data.csv", recorded_csv.encode("utf-8-sig"), zipfile.ZIP_DEFLATED)

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
