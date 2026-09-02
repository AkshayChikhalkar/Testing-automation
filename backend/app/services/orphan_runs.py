"""Mark test runs that were left pending/running after a crash or timeout."""

from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.test_run import TestRun
from app.services.run_state import results_dict

logger = structlog.get_logger()


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def fail_orphaned_runs() -> int:
    """Fail stale pending/running runs. Returns number of rows updated."""
    now = datetime.now(timezone.utc)
    timeout = timedelta(seconds=int(settings.SIMULATION_TIMEOUT_SECONDS or 3600))
    heartbeat_stale = timedelta(minutes=10)
    pending_stale = timedelta(minutes=15)
    updated = 0

    db = SessionLocal()
    try:
        rows = db.execute(
            select(TestRun).where(TestRun.status.in_(("pending", "running")))
        ).scalars().all()
        for run in rows:
            reason = None
            if run.status == "pending":
                created = _aware(run.created_at) if run.created_at else None
                if created and now - created > pending_stale:
                    reason = "Run never started (worker did not pick up the job)"
            else:
                started = _aware(run.start_time) if run.start_time else (
                    _aware(run.created_at) if run.created_at else None
                )
                if started and now - started > timeout:
                    reason = f"Simulation timed out after {int(timeout.total_seconds())} seconds"
                else:
                    hb = results_dict(run).get("heartbeat_at")
                    hb_dt = None
                    if isinstance(hb, str):
                        try:
                            hb_dt = datetime.fromisoformat(hb.replace("Z", "+00:00"))
                        except ValueError:
                            hb_dt = None
                    ref = hb_dt or started
                    if ref and now - _aware(ref) > heartbeat_stale:
                        reason = "Simulation worker stopped sending progress (process likely died)"
            if not reason:
                continue
            run.status = "failed"
            run.end_time = now
            run.error_message = reason
            updated += 1
            logger.warning("Marked orphaned test run failed", test_run_id=run.id, reason=reason)
        if updated:
            db.commit()
        else:
            db.rollback()
    except Exception:
        db.rollback()
        logger.exception("Orphaned-run sweep failed")
        return 0
    finally:
        db.close()
    return updated
