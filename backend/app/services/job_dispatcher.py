"""Dispatch test-run execution off the API process (Celery, else detached subprocess)."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import structlog

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.test_run import TestRun
from app.services.run_logs import log_path
from app.services.run_state import update_run_results

logger = structlog.get_logger()

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


def _celery_available() -> bool:
    try:
        from app.core.celery import celery_app

        conn = celery_app.connection()
        try:
            conn.ensure_connection(max_retries=0, timeout=0.5)
        finally:
            conn.close()
        return True
    except Exception:
        return False


def _spawn_detached(test_run_id: int) -> int:
    log_file = log_path(test_run_id)
    creationflags = 0
    startupinfo = None
    if sys.platform == "win32":
        # CREATE_NO_WINDOW hides python.exe. DETACHED_PROCESS would open an empty console.
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | getattr(
            subprocess, "CREATE_NO_WINDOW", 0x08000000
        )
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
    with open(log_file, "ab") as log:
        proc = subprocess.Popen(
            [sys.executable, "-m", "app.worker", str(test_run_id)],
            cwd=str(BACKEND_DIR),
            stdout=log,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
            startupinfo=startupinfo,
            close_fds=True,
            env={
                **os.environ,
                "PYTHONUNBUFFERED": "1",
                "TEST_RUN_LOG_FILE": str(log_file),
            },
        )
    return proc.pid


def enqueue_test_run(test_run_id: int) -> str:
    """Start execution outside uvicorn. Returns 'celery' or 'process'."""
    if _celery_available():
        from app.tasks.matlab_tasks import execute_test_run_task

        execute_test_run_task.delay(test_run_id)
        logger.info("Queued test run on Celery", test_run_id=test_run_id)
        return "celery"

    pid = _spawn_detached(test_run_id)
    db = SessionLocal()
    try:
        test_run = db.get(TestRun, test_run_id)
        if test_run:
            update_run_results(test_run, worker_pid=pid, dispatch="process")
            db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to store worker pid", test_run_id=test_run_id)
    finally:
        db.close()
    print(f"[TEST RUN] Started detached worker pid={pid} for test_run_id={test_run_id}", flush=True)
    logger.info("Started detached test-run worker", test_run_id=test_run_id, pid=pid)
    return "process"


def kill_worker(pid: Optional[int]) -> None:
    if not pid:
        return
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            os.kill(pid, 15)
    except Exception:
        logger.warning("Could not stop worker process", pid=pid)


def grafana_url_for(
    simulation_id: Optional[str] = None,
    *,
    from_time: str = "now-7d",
    to_time: str = "now",
) -> Optional[str]:
    if not settings.GRAFANA_DASHBOARD_URL:
        return None
    parsed = urlparse(settings.GRAFANA_DASHBOARD_URL)
    query = parse_qs(parsed.query)
    query["from"] = [from_time]
    query["to"] = [to_time]
    query["theme"] = ["light"]
    if simulation_id:
        query["var-simulation_id"] = [simulation_id]
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))
