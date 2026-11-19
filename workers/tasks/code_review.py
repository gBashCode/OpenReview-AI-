"""Celery tasks for autonomous code review execution."""

import asyncio
from workers.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger("openreview.worker.review")


@celery_app.task(
    bind=True,
    name="tasks.execute_code_review",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 5},
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def execute_code_review(self, review_id: str, pull_request_id: str):
    """Executes the autonomous multi-agent code review workflow with retry and backoff."""
    logger.info(
        f"Starting Celery code review task for review {review_id} (PR {pull_request_id}) - Attempt {self.request.retries + 1}/5"
    )

    try:
        from app.database.session import AsyncSessionLocal
        from app.reviews.service import ReviewService
        from app.orchestration.service import ReviewOrchestrationService

        async def _run():
            async with AsyncSessionLocal() as session:
                orchestrator = ReviewOrchestrationService(session)
                review = await orchestrator.execute_autonomous_review(review_id)
                return {"status": review.status, "review_id": review.id, "score": review.score}

        result = asyncio.run(_run())
        logger.info(f"Successfully completed code review {review_id}: status={result['status']}")
        return result

    except Exception as exc:
        logger.error(f"Error in review {review_id}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc)
