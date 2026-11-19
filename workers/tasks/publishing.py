"""Celery tasks for GitHub review publishing and status checks synchronization."""

import asyncio
from workers.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger("openreview.worker.publishing")


@celery_app.task(
    bind=True,
    name="tasks.publish_github_review",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 5},
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def publish_github_review(self, review_id: str, custom_summary: str = None):
    """Publishes verified findings, check-runs, and review comments to GitHub Pull Request."""
    logger.info(
        f"Starting GitHub publishing for review {review_id} - Attempt {self.request.retries + 1}/5"
    )

    try:
        from app.database.session import AsyncSessionLocal
        from app.reviews.service import ReviewService
        from app.github.publishing_engine import GitHubReviewPublishingEngine

        async def _run():
            async with AsyncSessionLocal() as session:
                review_service = ReviewService(session)
                review = await review_service.get_by_id(review_id)
                pr = review.pull_request
                repo = pr.repository

                engine = GitHubReviewPublishingEngine(
                    owner=repo.owner,
                    repo=repo.name,
                    token=repo.github_token if hasattr(repo, "github_token") else None,
                )
                result = await engine.publish_review(
                    pr=pr,
                    findings=review.findings,
                    head_sha=review.commit_sha,
                    custom_summary=custom_summary or review.summary,
                )
                return {
                    "review_id": review_id,
                    "review_url": result.review_url,
                    "published_comments": len(result.published_comments),
                    "check_run_id": result.check_run_id,
                }

        result = asyncio.run(_run())
        logger.info(f"Published review {review_id} to GitHub: {result}")
        return result

    except Exception as exc:
        logger.error(f"GitHub publishing failed for review {review_id}: {exc}")
        raise self.retry(exc=exc)
