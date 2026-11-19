"""Celery tasks for repository intelligence and semantic AST indexing."""

import asyncio
from workers.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger("openreview.worker.indexing")


@celery_app.task(
    bind=True,
    name="tasks.index_repository",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
    retry_backoff_max=180,
    retry_jitter=True,
)
def index_repository(self, repository_id: str, commit_sha: str = None):
    """Executes Tree-sitter file discovery, symbol extraction, chunking, and pgvector embedding."""
    logger.info(
        f"Starting repository indexing task for {repository_id} (commit={commit_sha or 'HEAD'}) - Attempt {self.request.retries + 1}/3"
    )

    try:
        from app.database.session import AsyncSessionLocal
        from app.indexing.service import RepositoryIndexingService

        async def _run():
            async with AsyncSessionLocal() as session:
                service = RepositoryIndexingService(session)
                index_run = await service.index_repository(repository_id, commit_sha=commit_sha)
                return {
                    "index_id": index_run.id,
                    "status": index_run.status,
                    "files": index_run.files_indexed,
                    "symbols": index_run.symbols_indexed,
                    "chunks": index_run.chunks_indexed,
                }

        result = asyncio.run(_run())
        logger.info(f"Indexing completed for {repository_id}: {result}")
        return result

    except Exception as exc:
        logger.error(f"Error during repository indexing {repository_id}: {exc}")
        raise self.retry(exc=exc)
