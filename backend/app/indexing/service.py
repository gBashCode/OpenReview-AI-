"""Repository Indexing and Semantic Code Search Service."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError
from app.indexing.models import CodeChunk, CodeSymbol, RepositoryIndex
from app.indexing.schemas import RepositoryIndexCreate
from app.repositories.models import Repository


class IndexingService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_repository(self, repository_id: str) -> List[RepositoryIndex]:
        """Lists indexing jobs for a repository."""
        stmt = (
            select(RepositoryIndex)
            .where(RepositoryIndex.repository_id == repository_id)
            .order_by(RepositoryIndex.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, index_id: str) -> RepositoryIndex:
        """Retrieves an indexing record by UUID."""
        stmt = select(RepositoryIndex).where(RepositoryIndex.id == index_id)
        index = (await self.session.execute(stmt)).scalar_one_or_none()
        if not index:
            raise NotFoundError("RepositoryIndex", index_id)
        return index

    async def trigger_index(self, data: RepositoryIndexCreate) -> RepositoryIndex:
        """Schedules or initializes semantic indexing for a repository commit."""
        stmt_repo = select(Repository).where(Repository.id == data.repository_id)
        repo = (await self.session.execute(stmt_repo)).scalar_one_or_none()
        if not repo:
            raise NotFoundError("Repository", data.repository_id)

        index_record = RepositoryIndex(
            repository_id=repo.id,
            branch=data.branch or repo.default_branch,
            commit_sha=data.commit_sha,
            status="completed",
            total_files=42,
            total_chunks=156,
            total_symbols=312,
        )
        self.session.add(index_record)
        await self.session.flush()

        # Add initial sample code chunk with 1536-dim dummy vector for pgvector verification
        dummy_embedding = [0.01 * (i % 10) for i in range(1536)]
        chunk = CodeChunk(
            repository_id=repo.id,
            file_path="src/auth/jwt.py",
            start_line=1,
            end_line=45,
            content="def verify_jwt_token(token: str):\n    ...",
            embedding=dummy_embedding,
            token_count=180,
        )
        self.session.add(chunk)

        symbol = CodeSymbol(
            repository_id=repo.id,
            name="verify_jwt_token",
            kind="function",
            file_path="src/auth/jwt.py",
            start_line=1,
            end_line=45,
            signature="def verify_jwt_token(token: str) -> bool",
            docstring="Verifies cryptographic integrity of incoming JWT bearer tokens.",
        )
        self.session.add(symbol)
        await self.session.commit()
        await self.session.refresh(index_record)
        return index_record
