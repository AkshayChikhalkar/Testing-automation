"""Analytics / Grafana embed configuration."""

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.security import get_current_user
from app.models.test_run import TestRun
from app.services.job_dispatcher import grafana_url_for
from app.services.simulation_ids import from_test_run as simulation_id_for

router = APIRouter()


@router.get("/grafana")
async def grafana_embed(
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """URL for the Analytics iframe, scoped to the latest run when possible."""
    query = select(TestRun).order_by(TestRun.created_at.desc())
    if not current_user.is_superuser:
        query = query.where(TestRun.user_id == current_user.id)
    query = query.limit(20)
    result = await db.execute(query)
    runs = result.scalars().all()

    latest_id: Optional[str] = None
    latest_run_id: Optional[int] = None
    for run in runs:
        sid = simulation_id_for(run) or run.simulation_id
        if sid:
            latest_id = sid
            latest_run_id = run.id
            break

    # Select the latest simulation so Grafana is not stuck on an older dashboard default.
    url = grafana_url_for(latest_id, from_time="now-7d", to_time="now")
    return {
        "url": url,
        "simulation_id": latest_id,
        "test_run_id": latest_run_id,
    }
