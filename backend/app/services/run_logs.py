"""Locations and helpers for test-run log files.

Logs are written to the project-root ``logs/`` folder (the one shown in the
repo), with ``uploads/run_logs/`` kept as a fallback for older runs.
"""

from pathlib import Path
from typing import List, Optional

from app.core.config import settings

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
REPO_ROOT = BACKEND_DIR.parent

MAX_LOG_LINES_IN_API = 400


def _uploads_base() -> Path:
    base = Path(settings.UPLOAD_PATH)
    if not base.is_absolute():
        base = BACKEND_DIR / base
    return base


def log_dir() -> Path:
    path = REPO_ROOT / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def log_path(test_run_id: int) -> Path:
    return log_dir() / f"test_run_{test_run_id}.log"


def legacy_log_path(test_run_id: int) -> Path:
    return _uploads_base() / "run_logs" / f"test_run_{test_run_id}.log"


def resolve_log_path(test_run_id: int) -> Optional[Path]:
    primary = log_path(test_run_id)
    if primary.is_file() and primary.stat().st_size > 0:
        return primary
    legacy = legacy_log_path(test_run_id)
    if legacy.is_file() and legacy.stat().st_size > 0:
        return legacy
    if primary.is_file():
        return primary
    if legacy.is_file():
        return legacy
    return None


def write_run_log(test_run_id: int, text: str, mode: str = "a") -> Path:
    path = log_path(test_run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    with open(path, mode, encoding="utf-8", errors="replace") as handle:
        handle.write(text)
    return path


def ensure_matlab_output_logged(test_run_id: int, raw_output: str) -> None:
    """Make sure captured MATLAB/Python output is in the project logs folder."""
    if not raw_output:
        return
    path = log_path(test_run_id)
    existing = ""
    if path.is_file():
        try:
            existing = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            existing = ""
    snippet = raw_output.strip()[:200]
    if snippet and snippet in existing:
        return
    header = "" if existing.endswith("\n") or not existing else "\n"
    write_run_log(test_run_id, f"{header}----- MATLAB output -----\n{raw_output}", mode="a")


def read_log_text(test_run_id: int) -> str:
    path = resolve_log_path(test_run_id)
    if path:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            pass
    return ""


def read_log_lines(test_run_id: int, output_data: Optional[dict] = None) -> List[str]:
    text = read_log_text(test_run_id)
    if not text and isinstance(output_data, dict):
        text = output_data.get("output_tail") or output_data.get("output") or ""
    if not text:
        return []
    lines = text.splitlines()
    if len(lines) > MAX_LOG_LINES_IN_API:
        omitted = len(lines) - MAX_LOG_LINES_IN_API
        return [f"... ({omitted} earlier lines omitted; download the full log) ..."] + lines[-MAX_LOG_LINES_IN_API:]
    return lines
