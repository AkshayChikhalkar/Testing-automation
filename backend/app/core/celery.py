"""
Celery configuration for background tasks
"""

from celery import Celery
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "matlab_automation",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.matlab_tasks",
        "app.tasks.data_tasks",
        "app.tasks.hardware_tasks",
        "app.tasks.report_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    task_routes={
        "app.tasks.matlab_tasks.*": {"queue": "matlab"},
        "app.tasks.data_tasks.*": {"queue": "data"},
        "app.tasks.hardware_tasks.*": {"queue": "hardware"},
        "app.tasks.report_tasks.*": {"queue": "reports"},
    },
    task_annotations={
        "*": {"rate_limit": "10/s"},
        "app.tasks.matlab_tasks.execute_model": {"rate_limit": "5/s"},
    }
)

# Optional configuration for production
if not settings.DEBUG:
    celery_app.conf.update(
        worker_hijack_root_logger=False,
        worker_log_color=False,
    )
