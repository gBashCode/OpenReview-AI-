"""Celery tasks for AutoFix patch generation and ephemeral container sandbox execution."""

import asyncio
from workers.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger("openreview.worker.autofix")


@celery_app.task(
    bind=True,
    name="tasks.generate_autofix",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
)
def generate_autofix(self, finding_id: str, regression_test_code: str = None):
    """Executes the 14-step AutoFix pipeline and runs tests in an isolated ephemeral sandbox."""
    logger.info(
        f"Starting AutoFix generation for finding {finding_id} - Attempt {self.request.retries + 1}/3"
    )

    try:
        from app.database.session import AsyncSessionLocal
        from app.autofix.service import AutofixService

        async def _run():
            async with AsyncSessionLocal() as session:
                service = AutofixService(session)
                patch = await service.generate_autofix_for_finding(
                    finding_id=finding_id,
                    regression_test_code=regression_test_code,
                )
                return {
                    "patch_id": patch.id,
                    "status": patch.status,
                    "diff_length": len(patch.diff_content or ""),
                }

        result = asyncio.run(_run())
        logger.info(f"AutoFix patch generated: {result}")
        return result

    except Exception as exc:
        logger.error(f"Error generating AutoFix for finding {finding_id}: {exc}")
        raise self.retry(exc=exc)
