"""Resolve the Influx/Grafana simulation_id for a test run."""

import os
import re
from typing import Any, Optional

SIM_ID_RE = re.compile(r"\d{8}_\d{6}")
SIM_ID_IN_TEXT = re.compile(r"Simulation ID:\s*(\d{8}_\d{6})")
SIMOUT_NAME = re.compile(r"simOut_(?:sweep_)?(\d{8}_\d{6})\.csv", re.IGNORECASE)


def from_text(raw_output: Optional[str]) -> Optional[str]:
    if not raw_output:
        return None
    matches = SIM_ID_IN_TEXT.findall(raw_output)
    return matches[-1] if matches else None


def from_output_dir(output_directory: Optional[str]) -> Optional[str]:
    """Latest simOut_YYYYMMDD_HHMMSS.csv in the model output folder."""
    if not output_directory or not os.path.isdir(output_directory):
        return None
    ids = []
    try:
        for name in os.listdir(output_directory):
            match = SIMOUT_NAME.match(name)
            if match:
                ids.append(match.group(1))
    except OSError:
        return None
    return max(ids) if ids else None


def preferred_simulation_id(
    stored: Optional[str] = None,
    output_data: Optional[dict] = None,
    raw_output: Optional[str] = None,
) -> Optional[str]:
    """Pick the newest valid simulation_id from stored value, logs, and CSV names.

    Older runs stored the first (oldest) simOut_*.csv in the shared output
    folder, which pointed Grafana at a previous run.
    """
    data = output_data if isinstance(output_data, dict) else {}
    candidates = []
    for value in (
        stored,
        from_text(raw_output),
        from_text(data.get("output_tail")),
        from_text(data.get("output")),
        from_output_dir(data.get("output_directory")),
    ):
        if value and SIM_ID_RE.fullmatch(value):
            candidates.append(value)
    return max(candidates) if candidates else None


def from_test_run(test_run: Any) -> Optional[str]:
    raw_output = None
    try:
        from app.services.run_logs import read_log_text

        raw_output = read_log_text(getattr(test_run, "id", 0) or 0)
    except Exception:
        raw_output = None
    return preferred_simulation_id(
        stored=getattr(test_run, "simulation_id", None),
        output_data=getattr(test_run, "output_data", None),
        raw_output=raw_output,
    )
