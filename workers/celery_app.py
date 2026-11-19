"""Celery distributed task queue configuration."""

import os
import sys
from pathlib import Path
from celery import Celery

# Add project root and backend to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "openreview_workers",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["workers.tasks.code_review"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,  # 30 minutes max per multi-agent review run
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

if __name__ == "__main__":
    celery_app.start()
