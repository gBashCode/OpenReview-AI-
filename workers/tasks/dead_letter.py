"""Celery tasks for dead-letter queue (DLQ) processing and failed-job triage."""

import asyncio
from datetime import datetime, timezone
from workers.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger("openreview.worker.dead_letter")


@celery_app.task(name="tasks.handle_dead_letter")
def handle_dead_letter(task_id: str, task_name: str, error_message: str, args: list, kwargs: dict):
    """Processes unrecoverable failed jobs from the DLQ and persists diagnostic records."""
    logger.critical(
        f"[DEAD LETTER QUEUE] Unrecoverable failure in task {task_name}[{task_id}]: {error_message}",
        extra={
            "task_id": task_id,
            "task_name": task_name,
            "error": error_message,
            "args": str(args),
            "kwargs": str(kwargs),
        },
    )

    try:
        from app.database.session import AsyncSessionLocal
        from app.analytics.models import AuditLog

        async def _record_dlq():
            async with AsyncSessionLocal() as session:
                log_entry = AuditLog(
                    action=f"task_failure_dlq:{task_name}",
                    entity_type="celery_task",
                    entity_id=task_id,
                    metadata_json={
                        "task_name": task_name,
                        "error": error_message,
                        "args": str(args)[:500],
                        "kwargs": str(kwargs)[:500],
                        "failed_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
                session.add(log_entry)
                await session.commit()

        asyncio.run(_record_dlq())
        logger.info(f"Recorded DLQ entry for task {task_id} into audit_logs.")

    except Exception as db_err:
        logger.error(f"Could not persist DLQ record to audit log: {db_err}")

    return {
        "status": "dlq_recorded",
        "task_id": task_id,
        "task_name": task_name,
    }
