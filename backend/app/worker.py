"""Detached worker entrypoint: python -m app.worker <test_run_id>"""

import os
import sys


def _attach_log_file() -> None:
    """Send stdout/stderr to the project logs folder even if spawn redirection fails."""
    log_file = os.environ.get("TEST_RUN_LOG_FILE")
    if not log_file:
        return
    try:
        parent = os.path.dirname(log_file)
        if parent:
            os.makedirs(parent, exist_ok=True)
        handle = open(log_file, "ab", buffering=0)
        os.dup2(handle.fileno(), 1)
        os.dup2(handle.fileno(), 2)
        sys.stdout = open(1, "w", encoding="utf-8", errors="replace", closefd=False, buffering=1)
        sys.stderr = sys.stdout
    except OSError:
        pass


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python -m app.worker <test_run_id>", file=sys.stderr)
        return 2
    test_run_id = int(sys.argv[1])
    _attach_log_file()
    import app.models  # noqa: F401  — register User/Model relationships
    from app.tasks.matlab_tasks import run_test_run_execution

    run_test_run_execution(test_run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
