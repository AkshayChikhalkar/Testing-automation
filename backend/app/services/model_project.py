"""Inspect a MATLAB model project directory by layout, not folder name."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

_SKIP_DIRS = {".git", "slprj", "__pycache__", "node_modules", ".venv", "venv", "uploads"}


def _read_run_config(root: Path) -> Dict[str, Any]:
    path = root / "run_config.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {"__invalid_json__": True}


def _find_startup_script(root: Path) -> Optional[Path]:
    """Prefer MODEL_*/startup*.m, then any startup*.m under the project."""
    found: List[Path] = []
    model_found: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
        rel_parts = Path(dirpath).relative_to(root).parts
        in_model_folder = any(part.upper().startswith("MODEL") for part in rel_parts)
        for name in filenames:
            if name.lower().startswith("startup") and name.lower().endswith(".m"):
                path = Path(dirpath) / name
                if in_model_folder:
                    model_found.append(path)
                else:
                    found.append(path)
    if model_found:
        return sorted(model_found)[0]
    if found:
        return sorted(found)[0]
    return None


def inspect_model_project(directory_path: str) -> Dict[str, Any]:
    """Return layout info and a valid flag for a model project root."""
    errors: List[str] = []
    raw = (directory_path or "").strip()
    if not raw:
        return {
            "valid": False,
            "errors": ["Directory path is required"],
            "root": None,
            "has_run_simulation": False,
            "has_run_config": False,
            "startup_script": None,
            "model_name": None,
            "model_folder": None,
            "param_roots": [],
        }

    root = Path(raw).expanduser()
    try:
        root = root.resolve()
    except OSError:
        pass

    if not root.exists():
        return {
            "valid": False,
            "errors": [f"Directory does not exist: {raw}"],
            "root": str(root),
            "has_run_simulation": False,
            "has_run_config": False,
            "startup_script": None,
            "model_name": None,
            "model_folder": None,
            "param_roots": [],
        }
    if not root.is_dir():
        return {
            "valid": False,
            "errors": [f"Path is not a directory: {raw}"],
            "root": str(root),
            "has_run_simulation": False,
            "has_run_config": False,
            "startup_script": None,
            "model_name": None,
            "model_folder": None,
            "param_roots": [],
        }

    cfg = _read_run_config(root)
    has_run_config = (root / "run_config.json").is_file()
    if cfg.get("__invalid_json__"):
        errors.append("run_config.json exists but is not valid JSON")
        cfg = {}

    has_runner = (root / "run_simulation.py").is_file()
    if not has_runner:
        errors.append("Missing run_simulation.py at the project root")

    startup: Optional[Path] = None
    startup_rel = cfg.get("startup_script")
    if isinstance(startup_rel, str) and startup_rel.strip():
        candidate = root / startup_rel
        if candidate.is_file():
            startup = candidate
        else:
            errors.append(f"run_config.json startup_script not found: {startup_rel}")

    if startup is None:
        startup = _find_startup_script(root)

    if startup is None:
        errors.append(
            "No startup_*.m found. Add run_config.json with startup_script, "
            "or a MODEL_*/startup_*.m file."
        )

    model_folder = cfg.get("model_folder")
    if not model_folder:
        model_dirs = sorted(
            p.name for p in root.iterdir() if p.is_dir() and p.name.upper().startswith("MODEL")
        )
        model_folder = model_dirs[0] if model_dirs else None

    valid = has_runner and startup is not None and not errors
    return {
        "valid": valid,
        "errors": errors,
        "root": str(root),
        "has_run_simulation": has_runner,
        "has_run_config": has_run_config,
        "startup_script": str(startup) if startup else None,
        "model_name": cfg.get("model_name"),
        "model_folder": model_folder,
        "param_roots": cfg.get("param_roots") or [],
    }
