"""Celery distributed task queue configuration for OpenReview AI.

Configures isolated task queues, exponential backoff retries,
dead-letter queue routing, and failure handling.
"""

import sys
from pathlib import Path
from celery import Celery
from celery.signals import task_failure, task_retry
from kombu import Exchange, Queue

# Add project root and backend to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger("openreview.celery")

# Define AMQP Exchanges and Queues
default_exchange = Exchange("openreview", type="direct")

task_queues = [
    Queue("default", default_exchange, routing_key="default"),
    Queue("reviews", default_exchange, routing_key="reviews"),
    Queue("indexing", default_exchange, routing_key="indexing"),
    Queue("autofix", default_exchange, routing_key="autofix"),
    Queue("publishing", default_exchange, routing_key="publishing"),
    Queue("dead_letter", default_exchange, routing_key="dead_letter"),
]

task_routes = {
    "tasks.execute_code_review": {"queue": "reviews", "routing_key": "reviews"},
    "tasks.orchestrate_review": {"queue": "reviews", "routing_key": "reviews"},
    "tasks.index_repository": {"queue": "indexing", "routing_key": "indexing"},
    "tasks.generate_autofix": {"queue": "autofix", "routing_key": "autofix"},
    "tasks.publish_github_review": {"queue": "publishing", "routing_key": "publishing"},
    "tasks.handle_dead_letter": {"queue": "dead_letter", "routing_key": "dead_letter"},
}

celery_app = Celery(
    "openreview_workers",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "workers.tasks.code_review",
        "workers.tasks.indexing",
        "workers.tasks.autofix",
        "workers.tasks.publishing",
        "workers.tasks.dead_letter",
    ],
)

celery_app.conf.update(
    task_queues=task_queues,
    task_routes=task_routes,
    task_default_queue="default",
    task_default_exchange="openreview",
    task_default_routing_key="default",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,  # Hard timeout: 30 minutes max
    task_soft_time_limit=1500,  # Soft timeout: 25 minutes
    task_acks_late=True,  # Acknowledge only after successful task execution
    worker_prefetch_multiplier=1,  # Fair distribution among workers
    worker_cancel_long_running_tasks_on_connection_loss=True,
    broker_connection_retry_on_startup=True,
    result_expires=86400,  # Cache task results for 24 hours
)


# Global Failure & Dead-Letter Handling
@task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **other):
    """Intercepts unrecoverable task failures, logs diagnostic traces, and routes to Dead-Letter Queue."""
    task_name = sender.name if sender else "unknown_task"
    logger.error(
        f"Task {task_name}[{task_id}] failed critically: {exception}. Routing to dead-letter queue for forensic triage.",
        extra={"task_id": task_id, "task_name": task_name, "error": str(exception)},
    )

    try:
        # Route unrecoverable failure details to dead letter queue
        celery_app.send_task(
            "tasks.handle_dead_letter",
            args=[task_id, task_name, str(exception), args, kwargs],
            queue="dead_letter",
        )
    except Exception as dispatch_err:
        logger.critical(f"Failed to route task {task_id} to dead-letter queue: {dispatch_err}")


@task_retry.connect
def handle_task_retry(sender=None, request=None, reason=None, einfo=None, **other):
    """Logs task retry events with backoff telemetry."""
    task_name = sender.name if sender else "unknown_task"
    task_id = request.id if request else "unknown_id"
    retries = request.retries if request else 0
    logger.warning(
        f"Retrying task {task_name}[{task_id}] (attempt {retries + 1}): reason={reason}"
    )


if __name__ == "__main__":
    celery_app.start()
