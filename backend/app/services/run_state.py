"""Helpers to store progress / heartbeat / worker pid on TestRun.results."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm.attributes import flag_modified

from app.models.test_run import TestRun


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def results_dict(test_run: TestRun) -> Dict[str, Any]:
    data = test_run.results
    return dict(data) if isinstance(data, dict) else {}


def update_run_results(test_run: TestRun, **fields: Any) -> None:
    merged = results_dict(test_run)
    merged.update({k: v for k, v in fields.items() if v is not None})
    test_run.results = merged
    flag_modified(test_run, "results")


def progress_from_run(test_run: TestRun) -> Optional[int]:
    data = results_dict(test_run)
    value = data.get("progress")
    if isinstance(value, (int, float)):
        return max(0, min(100, int(value)))
    if test_run.status in ("completed", "completed_warning"):
        return 100
    if test_run.status == "running":
        return 0
    return None


def parse_progress_line(line: str) -> Optional[Dict[str, Any]]:
    """Map runner/MATLAB logs to a monotonic phase-based percent.

    Do not treat incidental figures like ``Config 3/3 (100.0%)`` as overall
    completion — that is only config prep, before the long sim batch.
    """
    import re

    stripped = (line or "").strip()
    if not stripped:
        return None
    lower = stripped.lower()

    if "starting matlab" in lower:
        return {"progress": 5, "progress_message": "Starting MATLAB"}

    if "parameter sweep complete" in lower:
        return {"progress": 100, "progress_message": "Complete"}
    if "[success] simulation completed successfully" in lower:
        return {"progress": 100, "progress_message": "Complete"}

    cfg = re.search(r"\[progress\]\s*config\s+(\d+)\s*/\s*(\d+)", lower)
    if cfg:
        cur, tot = int(cfg.group(1)), max(int(cfg.group(2)), 1)
        return {
            "progress": 5 + int(10 * cur / tot),
            "progress_message": f"Preparing configurations {cur}/{tot}",
        }

    if "running all" in lower and "simulation" in lower:
        return {"progress": 18, "progress_message": "Running simulations"}

    if "all simulations completed" in lower:
        return {"progress": 70, "progress_message": "Simulations finished"}

    extracted = re.search(r"extracted data for\s+(\d+)\s*/\s*(\d+)", lower)
    if extracted:
        cur, tot = int(extracted.group(1)), max(int(extracted.group(2)), 1)
        return {
            "progress": 70 + int(10 * cur / tot),
            "progress_message": f"Extracting results {cur}/{tot}",
        }
    if "signal data extraction complete" in lower:
        return {"progress": 80, "progress_message": "Extracting results"}

    db_exp = re.search(r"database export\s+(\d+)\s*/\s*(\d+)", lower)
    if db_exp:
        cur, tot = int(db_exp.group(1)), max(int(db_exp.group(2)), 1)
        return {
            "progress": 80 + int(10 * cur / tot),
            "progress_message": f"InfluxDB export {cur}/{tot}",
        }
    if "database export complete" in lower:
        return {"progress": 90, "progress_message": "InfluxDB export complete"}

    csv_sim = re.search(r"processing simulation\s+(\d+)\s*/\s*(\d+)", lower)
    if csv_sim:
        cur, tot = int(csv_sim.group(1)), max(int(csv_sim.group(2)), 1)
        return {
            "progress": 90 + int(8 * cur / tot),
            "progress_message": f"Writing CSV {cur}/{tot}",
            "csv_exported": True,
        }
    if "csv export complete" in lower:
        return {"progress": 98, "progress_message": "CSV export complete", "csv_exported": True}

    if "[PROGRESS]" in stripped:
        return {"progress_message": stripped[:200]}
    return None

