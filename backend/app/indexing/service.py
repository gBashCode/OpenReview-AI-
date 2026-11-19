"""Repository Indexing, Search, and Intelligence Service."""

from dataclasses import asdict
import os
from typing import Any, Dict, List, Optional
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.indexing.context_retriever import ContextRetriever
from app.indexing.dependency_graph import DependencyGraph
from app.indexing.models import CodeChunk, CodeSymbol, RepositoryIndex
from app.indexing.repository_indexer import RepositoryIndexer
from app.indexing.schemas import (
    ArchitectureSummaryResponse,
    CallerEvidenceDTO,
    ChangedFileItem,
    DocEvidenceDTO,
    ImportEvidenceDTO,
    PRContextEvidenceResponse,
    RelatedFilesResponse,
    RepositoryIndexCreate,
    SemanticSearchResult,
    SymbolEvidenceDTO,
    SymbolSearchResult,
    TestEvidenceDTO,
)
from app.repositories.models import Repository


class IndexingService:
    """Provides high-level repository indexing, symbol querying, semantic search, and PR context retrieval."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.indexer = RepositoryIndexer(session)
        self.retriever = ContextRetriever(session)

    async def list_by_repository(self, repository_id: str) -> List[RepositoryIndex]:
        """Lists all indexing passes for a repository."""
        stmt = (
            select(RepositoryIndex)
            .where(RepositoryIndex.repository_id == repository_id)
            .order_by(RepositoryIndex.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, index_id: str) -> RepositoryIndex:
        """Retrieves a specific index pass by UUID."""
        stmt = select(RepositoryIndex).where(RepositoryIndex.id == index_id)
        index = (await self.session.execute(stmt)).scalar_one_or_none()
        if not index:
            raise NotFoundError("RepositoryIndex", index_id)
        return index

    async def trigger_index(self, data: RepositoryIndexCreate) -> RepositoryIndex:
        """Triggers full or incremental semantic indexing for a repository."""
        stmt_repo = select(Repository).where(Repository.id == data.repository_id)
        repo = (await self.session.execute(stmt_repo)).scalar_one_or_none()
        if not repo:
            raise NotFoundError("Repository", data.repository_id)

        # Determine target path to index
        root_path = data.local_path
        if not root_path or not os.path.isdir(root_path):
            # Check if repository root exists in workspace
            workspace_candidate = os.path.abspath(".")
            root_path = workspace_candidate

        index_record = await self.indexer.index_repository(
            repository_id=repo.id,
            root_path=root_path,
            branch=data.branch or repo.default_branch or "main",
            commit_sha=data.commit_sha or "HEAD",
            incremental=data.incremental,
        )
        return index_record

    async def search_symbols(
        self,
        repository_id: str,
        query: str,
        kind: Optional[str] = None,
        file_path: Optional[str] = None,
        limit: int = 20,
    ) -> List[SymbolSearchResult]:
        """Fast exact and prefix symbol search."""
        # Find latest completed index
        idx_stmt = (
            select(RepositoryIndex)
            .where(
                RepositoryIndex.repository_id == repository_id,
                RepositoryIndex.status == "completed",
            )
            .order_by(RepositoryIndex.created_at.desc())
        )
        index = (await self.session.execute(idx_stmt)).scalars().first()
        if not index:
            return []

        stmt = select(CodeSymbol).where(
            CodeSymbol.index_id == index.id,
            or_(
                CodeSymbol.name == query,
                CodeSymbol.name.ilike(f"{query}%"),
                CodeSymbol.name.ilike(f"%{query}%"),
            ),
        )
        if kind:
            stmt = stmt.where(CodeSymbol.kind == kind)
        if file_path:
            stmt = stmt.where(CodeSymbol.file_path == file_path)

        stmt = stmt.limit(limit)
        symbols = (await self.session.execute(stmt)).scalars().all()

        return [
            SymbolSearchResult(
                id=s.id,
                name=s.name,
                kind=s.kind,
                file_path=s.file_path,
                line_number=s.line_number,
                end_line_number=s.end_line_number,
                signature=s.signature,
                docstring=s.docstring,
            )
            for s in symbols
        ]

    async def search_semantic(
        self,
        repository_id: str,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.2,
    ) -> List[SemanticSearchResult]:
        """Performs vector similarity search across repository chunks."""
        results = await self.retriever.search_semantic(
            repository_id=repository_id,
            query=query,
            top_k=top_k,
            min_similarity=min_similarity,
        )
        return [
            SemanticSearchResult(
                file_path=r.file_path,
                start_line=r.start_line,
                end_line=r.end_line,
                content=r.content,
                similarity=r.similarity,
            )
            for r in results
        ]

    async def retrieve_pr_context(
        self,
        repository_id: str,
        changed_files: List[ChangedFileItem],
        top_k_semantic: int = 5,
    ) -> PRContextEvidenceResponse:
        """Executes hybrid context retrieval for a pull request."""
        raw_items = [item.model_dump() for item in changed_files]
        evidence = await self.retriever.retrieve_pr_context(
            repository_id=repository_id,
            changed_files=raw_items,
            top_k_semantic=top_k_semantic,
        )

        return PRContextEvidenceResponse(
            repository_id=evidence.repository_id,
            commit_sha=evidence.commit_sha,
            changed_symbols=[
                SymbolEvidenceDTO(
                    name=s.name,
                    kind=s.kind,
                    file_path=s.file_path,
                    line_number=s.line_number,
                    end_line_number=s.end_line_number,
                    signature=s.signature,
                    docstring=s.docstring,
                    source_code=s.source_code,
                )
                for s in evidence.changed_symbols
            ],
            enclosing_classes=[
                SymbolEvidenceDTO(
                    name=s.name,
                    kind=s.kind,
                    file_path=s.file_path,
                    line_number=s.line_number,
                    end_line_number=s.end_line_number,
                    signature=s.signature,
                    docstring=s.docstring,
                )
                for s in evidence.enclosing_classes
            ],
            function_callers=[
                CallerEvidenceDTO(
                    caller_name=c.caller_name,
                    callee_name=c.callee_name,
                    file_path=c.file_path,
                    line_number=c.line_number,
                    signature=c.signature,
                )
                for c in evidence.function_callers
            ],
            imported_modules=[
                ImportEvidenceDTO(
                    module=m.module,
                    file_path=m.file_path,
                    imported_symbols=m.imported_symbols,
                )
                for m in evidence.imported_modules
            ],
            related_tests=[
                TestEvidenceDTO(
                    test_file_path=t.test_file_path,
                    target_file_path=t.target_file_path,
                    test_cases=t.test_cases,
                )
                for t in evidence.related_tests
            ],
            relevant_docs=[
                DocEvidenceDTO(
                    file_path=d.file_path,
                    title=d.title,
                    snippet=d.snippet,
                    line_number=d.line_number,
                )
                for d in evidence.relevant_docs
            ],
            semantic_matches=[
                SemanticSearchResult(
                    file_path=sm.file_path,
                    start_line=sm.start_line,
                    end_line=sm.end_line,
                    content=sm.content,
                    similarity=sm.similarity,
                )
                for sm in evidence.semantic_matches
            ],
        )

    async def get_architecture_summary(self, repository_id: str) -> ArchitectureSummaryResponse:
        """Retrieves latest architectural summary of the repository."""
        idx_stmt = (
            select(RepositoryIndex)
            .where(
                RepositoryIndex.repository_id == repository_id,
                RepositoryIndex.status == "completed",
            )
            .order_by(RepositoryIndex.created_at.desc())
        )
        index = (await self.session.execute(idx_stmt)).scalars().first()
        if not index or not index.summary_json or "architecture" not in index.summary_json:
            raise NotFoundError("ArchitectureSummary", repository_id)

        arch = index.summary_json["architecture"]
        return ArchitectureSummaryResponse(
            total_files=arch.get("total_files", 0),
            total_lines_of_code=arch.get("total_lines_of_code", 0),
            primary_language=arch.get("primary_language", "unknown"),
            language_breakdown=arch.get("language_breakdown", {}),
            detected_frameworks=arch.get("detected_frameworks", []),
            entry_points=arch.get("entry_points", []),
            core_modules=arch.get("core_modules", []),
            key_configurations=arch.get("key_configurations", []),
            test_files_count=arch.get("test_files_count", 0),
            test_coverage_ratio=arch.get("test_coverage_ratio", 0.0),
            project_type=arch.get("project_type", "Repository"),
        )

    async def get_related_files(self, repository_id: str, file_path: str) -> RelatedFilesResponse:
        """Retrieves related imports, dependents, and tests for a file."""
        idx_stmt = (
            select(RepositoryIndex)
            .where(
                RepositoryIndex.repository_id == repository_id,
                RepositoryIndex.status == "completed",
            )
            .order_by(RepositoryIndex.created_at.desc())
        )
        index = (await self.session.execute(idx_stmt)).scalars().first()
        if not index or not index.summary_json or "dependencies" not in index.summary_json:
            raise NotFoundError("DependencyGraph", repository_id)

        dep_graph = DependencyGraph.from_dict(index.summary_json["dependencies"])
        return RelatedFilesResponse(
            file_path=file_path,
            imported_modules=dep_graph.get_dependencies(file_path),
            dependent_files=dep_graph.get_dependents(file_path),
            related_tests=dep_graph.get_related_tests(file_path),
        )
