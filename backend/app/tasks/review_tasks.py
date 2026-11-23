"""Workload-Aware Review Task Dispatcher & Celery Worker Execution."""

import asyncio
from typing import Any, Dict, Optional
from app.analyzer.workload_classifier import WorkloadTier
from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("openreview.tasks.reviews")
settings = get_settings()


def get_queue_for_tier(tier: str) -> str:
    """Maps WorkloadTier to the corresponding AutoScaleX Celery queue."""
    t = (tier or "standard").lower()
    if t == WorkloadTier.FAST.value or t == "fast":
        return settings.CELERY_QUEUE_FAST
    elif t == WorkloadTier.HEAVY.value or t == "heavy":
        return settings.CELERY_QUEUE_HEAVY
    return settings.CELERY_QUEUE_STANDARD


def get_timeout_for_tier(tier: str) -> int:
    """Returns soft time limit ceiling in seconds based on workload tier."""
    t = (tier or "standard").lower()
    if t == WorkloadTier.FAST.value or t == "fast":
        return 20
    elif t == WorkloadTier.HEAVY.value or t == "heavy":
        return 120
    return 60


async def _run_review_in_session(review_id: str, custom_diff: Optional[str] = None):
    """Executes review workflow inside an isolated database session."""
    from app.database.session import AsyncSessionLocal
    from app.orchestration.service import ReviewOrchestrationService

    async with AsyncSessionLocal() as session:
        orchestrator = ReviewOrchestrationService(session)
        await orchestrator.execute_review(review_id, custom_diff=custom_diff)


@celery_app.task(
    bind=True,
    name="app.tasks.review_tasks.execute_autonomous_review",
    max_retries=2,
    default_retry_delay=5,
)
def execute_autonomous_review(
    self,
    review_id: str,
    custom_diff: Optional[str] = None,
    workload_tier: str = "standard",
) -> Dict[str, Any]:
    """Celery background worker entrypoint executing LangGraph multi-agent conference."""
    logger.info(
        f"[Worker Task] Starting review {review_id} on worker process "
        f"(tier={workload_tier}, task_id={self.request.id})"
    )
    try:
        # Run async review orchestration synchronously inside Celery worker thread
        asyncio.run(_run_review_in_session(review_id, custom_diff=custom_diff))
        logger.info(f"[Worker Task] Review {review_id} completed successfully.")
        return {
            "status": "success",
            "review_id": review_id,
            "task_id": self.request.id,
            "workload_tier": workload_tier,
        }
    except Exception as exc:
        logger.error(f"[Worker Task] Review {review_id} failed: {exc}", exc_info=True)
        # Retry with exponential backoff on transient errors
        raise self.retry(exc=exc)


def dispatch_review_task(
    review_id: str,
    tier: str = "standard",
    custom_diff: Optional[str] = None,
    execute_in_process: bool = False,
) -> Dict[str, Any]:
    """Workload-aware dispatcher routing reviews to specialized Redis priority queues.

    Gracefully falls back to local async dispatch or pending queue if Celery/Redis is disabled or unreachable.
    """
    target_queue = get_queue_for_tier(tier)
    timeout_limit = get_timeout_for_tier(tier)

    logger.info(
        f"AutoScaleX Dispatcher: Routing review [{review_id}] to queue [{target_queue}] "
        f"(tier={tier}, timeout={timeout_limit}s, celery_enabled={settings.CELERY_ENABLED})"
    )

    if settings.CELERY_ENABLED:
        try:
            # Attempt asynchronous Celery dispatch with workload-specific routing
            async_result = execute_autonomous_review.apply_async(
                args=[review_id],
                kwargs={
                    "custom_diff": custom_diff,
                    "workload_tier": tier,
                },
                queue=target_queue,
                routing_key=target_queue,
                time_limit=timeout_limit + 10,
                soft_time_limit=timeout_limit,
                retry=False,
            )

            return {
                "dispatched": True,
                "mode": "celery",
                "task_id": async_result.id,
                "queue": target_queue,
                "tier": tier,
            }
        except Exception as dispatch_err:
            # Fallback when Redis or Celery broker is offline
            logger.warning(
                f"Celery broker unavailable ({dispatch_err}). "
                f"Falling back to local dispatch mode for review {review_id}."
            )

    # Local development / test fallback
    if execute_in_process:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_run_review_in_session(review_id, custom_diff=custom_diff))
            fallback_mode = "in_process_async"
        except RuntimeError:
            fallback_mode = "queued_pending"
    else:
        fallback_mode = "queued_pending"

    return {
        "dispatched": True,
        "mode": fallback_mode,
        "task_id": None,
        "queue": target_queue,
        "tier": tier,
    }
