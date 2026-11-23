"""Celery Application and Workload-Aware Task Dispatcher Configuration."""

from celery import Celery
from kombu import Exchange, Queue
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("openreview.celery")
settings = get_settings()

celery_app = Celery(
    "openreview",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.review_tasks"],
)

# Multi-tier exchange & queue definitions for AutoScaleX
default_exchange = Exchange("openreview", type="direct")

task_queues = [
    Queue(
        settings.CELERY_QUEUE_FAST,
        default_exchange,
        routing_key=settings.CELERY_QUEUE_FAST,
        queue_arguments={"x-max-priority": 10},
    ),
    Queue(
        settings.CELERY_QUEUE_STANDARD,
        default_exchange,
        routing_key=settings.CELERY_QUEUE_STANDARD,
        queue_arguments={"x-max-priority": 5},
    ),
    Queue(
        settings.CELERY_QUEUE_HEAVY,
        default_exchange,
        routing_key=settings.CELERY_QUEUE_HEAVY,
        queue_arguments={"x-max-priority": 1},
    ),
]

celery_app.conf.update(
    task_default_queue=settings.CELERY_TASK_DEFAULT_QUEUE,
    task_default_exchange="openreview",
    task_default_routing_key=settings.CELERY_TASK_DEFAULT_QUEUE,
    task_queues=task_queues,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Worker fairness optimizations for uneven AI review workloads
    task_acks_late=True,                 # Re-queue task if worker pod is preempted or terminated
    worker_prefetch_multiplier=1,        # Only pull 1 task at a time per worker process
    task_track_started=True,             # Track when worker starts executing
    result_expires=3600,                 # Keep results in Redis for 1 hour
    worker_send_task_events=True,        # Telemetry events for monitoring
    broker_connection_retry_on_startup=False,
    broker_connection_timeout=0.2,
    broker_transport_options={
        "socket_timeout": 0.2,
        "socket_connect_timeout": 0.2,
    },
)
