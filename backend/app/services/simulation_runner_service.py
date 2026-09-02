"""
Simulation Runner Service - wraps run_simulation.py from simulationsmodelle.

Runs MATLAB models via subprocess (matlab -batch) like the simulationsmodelle CLI.
Supports: project directory, params file (CSV/JSON), batch mode, db mode.
"""

import os
import json
import re
import subprocess
import sys
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
import structlog

from app.core.config import settings

logger = structlog.get_logger()


def _extract_simulation_error(output: str, return_code: int) -> str:
    """Pick a useful MATLAB/Python error line from captured output."""
    markers = (
        "Unrecognized function or variable",
        "Unable to resolve the name",
        "[ERROR]",
        "ERROR: MATLAB",
        "Error in runBatchSimulations",
        "Error in temp_batch_simulation",
        "Error in batch processing",
        "Error running MATLAB",
        "Simulation failed",
        "Neither STAB1 nor STAB",
        "No parameter roots from run_config",
        "Cannot resolve parameter path",
    )
    for line in (output or "").splitlines():
        stripped = line.strip()
        if any(marker in stripped for marker in markers):
            return stripped[:500]
    return f"Simulation exited with code {return_code}"


def _extract_db_export_warning(output: str) -> Optional[str]:
    """If CSV/sim succeeded but InfluxDB export failed, return a short warning."""
    match = re.search(
        r"Database export complete! \((\d+) successful, (\d+) failed\)",
        output or "",
    )
    if match and int(match.group(2)) > 0:
        return match.group(0)
    for line in (output or "").splitlines():
        stripped = line.strip()
        if "Database export failed" in stripped or "Database write failed" in stripped:
            return stripped[:500]
    return None


def find_project_root(project_dir: Path) -> Path:
    """Prefer a directory that contains run_config.json or run_simulation.py."""
    project_dir = Path(project_dir).resolve()
    for candidate in (project_dir, project_dir.parent):
        if (candidate / "run_config.json").exists() or (candidate / "run_simulation.py").exists():
            return candidate
    return project_dir


def load_run_config(project_dir: Path) -> Dict[str, Any]:
    """Load optional per-model run_config.json."""
    root = find_project_root(project_dir)
    path = root / "run_config.json"
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f) or {}
        logger.info("Loaded run_config.json", path=str(path))
        return data
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Could not read run_config.json", path=str(path), error=str(exc))
        return {}


class SimulationRunnerService:
    """Service to run MATLAB simulations via simulationsmodelle run_simulation.py"""

    def __init__(self):
        self.simulations_path: Optional[Path] = None
        self._resolve_simulations_path()

    def _resolve_simulations_path(self) -> None:
        """Resolve path to simulationsmodelle project"""
        if settings.SIMULATIONS_PROJECT_PATH:
            p = Path(settings.SIMULATIONS_PROJECT_PATH)
            if p.exists() and (p / "run_simulation.py").exists():
                self.simulations_path = p
                return
        # Try sibling directory (same GitLab parent)
        # backend/app/services -> backend
        backend_dir = Path(__file__).resolve().parent.parent.parent
        # backend -> Testing automation -> GitLab
        gitlab_dir = backend_dir.parent.parent
        for name in ["simulationsmodelle", "simulationsmodelle-main"]:
            candidate = gitlab_dir / name
            if candidate.exists() and (candidate / "run_simulation.py").exists():
                self.simulations_path = candidate
                return
        self.simulations_path = None

    def is_available(self) -> bool:
        """Check if simulationsmodelle project is available"""
        return self.simulations_path is not None

    def run_simulation(
        self,
        project_directory: str,
        params_file: Optional[str] = None,
        params_json: Optional[Dict[str, Any]] = None,
        param_overrides: Optional[List[str]] = None,
        batch_mode: bool = False,
        db_mode: bool = False,
        db_type: str = "influxdb",
        db_host: Optional[str] = None,
        db_port: Optional[int] = None,
        db_token: Optional[str] = None,
        db_org: Optional[str] = None,
        db_bucket: Optional[str] = None,
        startup_script: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Run MATLAB simulation via run_simulation.py.

        Args:
            project_directory: Path to MATLAB project (simulationsmodelle or MODEL_SingleStab_ECU parent)
            params_file: Path to CSV or JSON params file (for batch or single run)
            params_json: Inline JSON params (alternative to file)
            param_overrides: List of "param.path=value" strings
            batch_mode: If True, use CSV batch mode (params_file must be CSV)
            db_mode: Enable database export
            db_type: influxdb or timescaledb
            db_host, db_port, db_token, db_org, db_bucket: DB config
            startup_script: Custom startup script path

        Returns:
            Dict with success, output, error, return_code
        """
        project_dir = Path(project_directory).resolve()
        if not project_dir.exists():
            return {
                "success": False,
                "error": f"Project directory does not exist: {project_directory}",
                "output": "",
                "return_code": -1,
            }
        # Prefer run_simulation.py in project_directory if it exists
        run_script = project_dir / "run_simulation.py"
        if not run_script.exists():
            run_script = (self.simulations_path / "run_simulation.py") if self.simulations_path else None

        if not run_script or not run_script.exists():
            return {
                "success": False,
                "error": "run_simulation.py not found. Ensure project_directory or SIMULATIONS_PROJECT_PATH points to simulationsmodelle.",
                "output": "",
                "return_code": -1,
            }

        # Build command
        cmd = [sys.executable, str(run_script)]

        cfg = load_run_config(project_dir)
        project_root = find_project_root(project_dir)
        # run_config.json wins so the registered model cannot launch the wrong entrypoint
        startup_rel = cfg.get("startup_script") or "MODEL_SingleStab_ECU/startup_MDL.m"
        if cfg.get("startup_script"):
            startup_path = project_root / startup_rel
            if not startup_path.exists():
                startup_path = project_dir / startup_rel
        elif startup_script:
            startup_path = Path(startup_script)
        else:
            startup_path = project_root / startup_rel
            if not startup_path.exists():
                startup_path = project_dir / startup_rel

        if startup_path.exists():
            cmd.extend(["--startup-script", str(startup_path)])

        # Params
        if params_file:
            params_path = Path(params_file)
            if not params_path.exists():
                return {
                    "success": False,
                    "error": f"Params file not found: {params_file}",
                    "output": "",
                    "return_code": -1,
                }
            if batch_mode and params_path.suffix.lower() == ".csv":
                cmd.extend(["--csv", str(params_path)])
            else:
                cmd.extend(["--params", str(params_path)])
        elif params_json:
            # Write temp JSON and pass
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(params_json, f)
                temp_path = f.name
            try:
                cmd.extend(["--params", temp_path])
                cwd = project_dir if (project_dir / "run_simulation.py").exists() else self.simulations_path
                output_dir = startup_path.parent / "output"
                result = self._execute(cmd, cwd, output_dir, db_mode, db_type, db_host, db_port, db_token, db_org, db_bucket)
                return result
            finally:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
        elif param_overrides:
            for p in param_overrides:
                cmd.extend(["--param", p])
        elif batch_mode:
            return {
                "success": False,
                "error": "Batch mode requires a CSV params file (--csv)",
                "output": "",
                "return_code": -1,
            }

        # cwd: use project_dir if it contains run_simulation.py, else simulations_path
        cwd = project_dir if (project_dir / "run_simulation.py").exists() else self.simulations_path
        # Output dir where run_simulation.py writes .mat and .json files
        output_dir = startup_path.parent / "output"
        return self._execute(
            cmd, cwd, output_dir, db_mode, db_type, db_host, db_port, db_token, db_org, db_bucket,
            progress_callback=progress_callback,
        )

    def _execute(
        self,
        cmd: List[str],
        cwd: Path,
        output_dir: Path,
        db_mode: bool,
        db_type: str,
        db_host: Optional[str],
        db_port: Optional[int],
        db_token: Optional[str],
        db_org: Optional[str],
        db_bucket: Optional[str],
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """Execute run_simulation.py subprocess"""
        influx = settings.influx_connection()
        token = db_token or influx.get("token") or os.environ.get("INFLUXDB_TOKEN")
        host = db_host or influx.get("host")
        port = db_port if db_port is not None else influx.get("port")
        org = db_org or influx.get("org")
        bucket = db_bucket or influx.get("bucket")

        if db_mode:
            if not token:
                logger.warning("INFLUXDB_TOKEN not set; skipping database export")
                print("[SIM] INFLUXDB_TOKEN not set; skipping database export (CSV only)\n", flush=True)
            else:
                cmd.extend(["--db-type", db_type])
                if host:
                    cmd.extend(["--db-host", str(host)])
                if port is not None:
                    cmd.extend(["--db-port", str(port)])
                if org:
                    cmd.extend(["--db-org", str(org)])
                if bucket:
                    cmd.extend(["--db-bucket", str(bucket)])

        try:
            logger.info("Running simulation", cmd=cmd, cwd=str(cwd))
            env = {**os.environ, "PYTHONPATH": str(self.simulations_path or "")}
            env["PYTHONUNBUFFERED"] = "1"  # Force unbuffered output from child on Windows
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"
            if token:
                env["INFLUXDB_TOKEN"] = str(token)
            if host:
                env["INFLUXDB_HOST"] = str(host)
            if port is not None:
                env["INFLUXDB_PORT"] = str(port)
            if org:
                env["INFLUXDB_ORG"] = str(org)
            if bucket:
                env["INFLUXDB_BUCKET"] = str(bucket)
            print(f"[SIM] Running: {' '.join(cmd)}\n", flush=True)

            # Capture output while also streaming to terminal
            output_lines: List[str] = []
            output_lock = threading.Lock()

            def read_stream(stream, dest: List[str], out_sys):
                try:
                    for line in iter(stream.readline, ""):
                        with output_lock:
                            dest.append(line)
                        if progress_callback:
                            try:
                                progress_callback(line)
                            except Exception:
                                pass
                        if out_sys:
                            try:
                                out_sys.write(line)
                                out_sys.flush()
                            except UnicodeEncodeError:
                                out_sys.write(line.encode("ascii", errors="replace").decode("ascii"))
                                out_sys.flush()
                except Exception:
                    pass
                finally:
                    try:
                        stream.close()
                    except Exception:
                        pass

            process = subprocess.Popen(
                cmd,
                cwd=str(cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=env,
            )
            timeout_s = int(settings.SIMULATION_TIMEOUT_SECONDS or 3600)
            reader = threading.Thread(
                target=read_stream,
                args=(process.stdout, output_lines, sys.stdout),
                daemon=True,
            )
            reader.start()
            return_code = process.wait(timeout=timeout_s)
            reader.join(timeout=2)
            captured_output = "".join(output_lines)

            success = return_code == 0
            error = None if success else _extract_simulation_error(captured_output, return_code)
            result = {
                "success": success,
                "output": captured_output,
                "error": error,
                "return_code": return_code,
                "output_directory": str(output_dir),
                "db_export_warning": _extract_db_export_warning(captured_output) if success else None,
            }
            return result
        except subprocess.TimeoutExpired as te:
            if hasattr(te, "process") and te.process:
                try:
                    te.process.kill()
                except Exception:
                    pass
            return {
                "success": False,
                "error": f"Simulation timed out after {int(settings.SIMULATION_TIMEOUT_SECONDS or 3600)} seconds",
                "output": "",
                "return_code": -1,
                "output_directory": str(output_dir),
            }
        except Exception as e:
            logger.exception("Simulation execution failed")
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "return_code": -1,
                "output_directory": str(output_dir),
            }
