"""Hybrid Context Retrieval Engine for Pull Request Multi-Agent Reviews."""

from dataclasses import dataclass, field
import json
import math
from typing import Any, Dict, List, Optional, Set
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.indexing.dependency_graph import DependencyGraph
from app.indexing.embeddings import BaseEmbeddingProvider, get_embedding_provider
from app.indexing.models import CodeChunk, CodeSymbol, RepositoryIndex

logger = get_logger("openreview.indexing.retriever")


@dataclass
class SymbolEvidence:
    name: str
    kind: str
    file_path: str
    line_number: int
    end_line_number: int
    signature: Optional[str]
    docstring: Optional[str]
    source_code: Optional[str] = None


@dataclass
class CallerEvidence:
    caller_name: str
    callee_name: str
    file_path: str
    line_number: int
    signature: Optional[str]


@dataclass
class ImportEvidence:
    module: str
    file_path: str
    imported_symbols: List[str] = field(default_factory=list)


@dataclass
class TestEvidence:
    test_file_path: str
    target_file_path: str
    test_cases: List[str] = field(default_factory=list)


@dataclass
class DocEvidence:
    file_path: str
    title: str
    snippet: str
    line_number: int


@dataclass
class ChunkEvidence:
    file_path: str
    start_line: int
    end_line: int
    content: str
    similarity: float


@dataclass
class PRContextEvidence:
    """Consolidated authentic repository context for AI review agents."""

    repository_id: str
    commit_sha: str
    changed_symbols: List[SymbolEvidence]
    enclosing_classes: List[SymbolEvidence]
    function_callers: List[CallerEvidence]
    imported_modules: List[ImportEvidence]
    related_tests: List[TestEvidence]
    relevant_docs: List[DocEvidence]
    semantic_matches: List[ChunkEvidence]


class ContextRetriever:
    """Executes hybrid retrieval: exact symbol, AST graph, dependency resolution, and vector search."""

    def __init__(
        self,
        session: AsyncSession,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
    ):
        self.session = session
        self.embedding_provider = embedding_provider or get_embedding_provider()

    async def retrieve_pr_context(
        self,
        repository_id: str,
        changed_files: List[Dict[str, Any]],
        top_k_semantic: int = 5,
    ) -> PRContextEvidence:
        """Retrieves verified contextual evidence for changed files and functions in a PR."""
        # 1. Fetch latest completed index
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
            logger.warning(f"No completed index found for repository {repository_id}")
            return PRContextEvidence(
                repository_id=repository_id,
                commit_sha="",
                changed_symbols=[],
                enclosing_classes=[],
                function_callers=[],
                imported_modules=[],
                related_tests=[],
                relevant_docs=[],
                semantic_matches=[],
            )

        dep_graph_data = index.summary_json.get("dependencies", {}) if index.summary_json else {}
        dep_graph = DependencyGraph.from_dict(dep_graph_data)

        changed_symbols: List[SymbolEvidence] = []
        enclosing_classes: List[SymbolEvidence] = []
        function_callers: List[CallerEvidence] = []
        imported_modules: List[ImportEvidence] = []
        related_tests: List[TestEvidence] = []
        relevant_docs: List[DocEvidence] = []
        semantic_matches: List[ChunkEvidence] = []

        seen_symbol_names: Set[str] = set()

        # 2. Inspect changed files & resolve changed symbols
        for item in changed_files:
            file_path = item.get("file_path") or item.get("filename") or ""
            changed_lines = set(item.get("changed_lines") or [])
            # If line range passed instead of list
            if item.get("start_line") is not None and item.get("end_line") is not None:
                changed_lines.update(range(item["start_line"], item["end_line"] + 1))

            if not file_path:
                continue

            # A. Fetch all symbols in this file
            sym_stmt = select(CodeSymbol).where(
                CodeSymbol.index_id == index.id,
                CodeSymbol.file_path == file_path,
            )
            file_symbols = (await self.session.execute(sym_stmt)).scalars().all()

            for sym in file_symbols:
                s_end = sym.end_line_number or sym.line_number
                sym_range = set(range(sym.line_number, s_end + 1))
                
                # If symbol overlaps with changed lines or if all lines in file are considered
                is_changed = bool(sym_range.intersection(changed_lines)) if changed_lines else True

                if is_changed and sym.name not in seen_symbol_names:
                    seen_symbol_names.add(sym.name)

                    # Retrieve chunk content for source code
                    chunk_stmt = select(CodeChunk).where(
                        CodeChunk.index_id == index.id,
                        CodeChunk.file_path == file_path,
                        CodeChunk.start_line <= sym.line_number,
                        CodeChunk.end_line >= s_end,
                    )
                    chunk = (await self.session.execute(chunk_stmt)).scalars().first()
                    source_snippet = chunk.content if chunk else None

                    evidence = SymbolEvidence(
                        name=sym.name,
                        kind=sym.kind,
                        file_path=sym.file_path,
                        line_number=sym.line_number,
                        end_line_number=s_end,
                        signature=sym.signature,
                        docstring=sym.docstring,
                        source_code=source_snippet,
                    )
                    changed_symbols.append(evidence)

                    # B. Check for callers of this function
                    callers = dep_graph.get_callers(sym.name)
                    for caller_name in callers:
                        # Find caller symbol definition
                        c_stmt = select(CodeSymbol).where(
                            CodeSymbol.index_id == index.id,
                            CodeSymbol.name == (caller_name.split(".")[-1] if "." in caller_name else caller_name),
                        )
                        c_sym = (await self.session.execute(c_stmt)).scalars().first()
                        if c_sym:
                            function_callers.append(
                                CallerEvidence(
                                    caller_name=caller_name,
                                    callee_name=sym.name,
                                    file_path=c_sym.file_path,
                                    line_number=c_sym.line_number,
                                    signature=c_sym.signature,
                                )
                            )

            # C. Imported modules
            imported_paths = dep_graph.get_dependencies(file_path)
            for imp_mod in imported_paths:
                imported_modules.append(
                    ImportEvidence(
                        module=imp_mod,
                        file_path=file_path,
                    )
                )

            # D. Associated Tests
            test_paths = dep_graph.get_related_tests(file_path)
            for t_path in test_paths:
                # Find test cases in that test file
                t_sym_stmt = select(CodeSymbol).where(
                    CodeSymbol.index_id == index.id,
                    CodeSymbol.file_path == t_path,
                )
                t_syms = (await self.session.execute(t_sym_stmt)).scalars().all()
                related_tests.append(
                    TestEvidence(
                        test_file_path=t_path,
                        target_file_path=file_path,
                        test_cases=[s.name for s in t_syms],
                    )
                )

        # 3. Documentation search
        for sym in changed_symbols[:5]:
            doc_stmt = (
                select(CodeChunk)
                .where(
                    CodeChunk.index_id == index.id,
                    CodeChunk.file_path.ilike("%.md"),
                    CodeChunk.content.ilike(f"%{sym.name}%"),
                )
                .limit(3)
            )
            doc_chunks = (await self.session.execute(doc_stmt)).scalars().all()
            for dc in doc_chunks:
                relevant_docs.append(
                    DocEvidence(
                        file_path=dc.file_path,
                        title=f"Documentation reference: {sym.name}",
                        snippet=dc.content[:300] + "...",
                        line_number=dc.start_line,
                    )
                )

        # 4. Semantic vector similarity search
        query_terms = [s.name for s in changed_symbols]
        if query_terms:
            query_str = " ".join(query_terms)
            semantic_matches = await self.search_semantic(
                repository_id=repository_id,
                query=query_str,
                top_k=top_k_semantic,
                index_id=index.id,
            )

        return PRContextEvidence(
            repository_id=repository_id,
            commit_sha=index.commit_sha,
            changed_symbols=changed_symbols,
            enclosing_classes=enclosing_classes,
            function_callers=function_callers[:10],
            imported_modules=imported_modules[:15],
            related_tests=related_tests[:10],
            relevant_docs=relevant_docs[:5],
            semantic_matches=semantic_matches,
        )

    async def search_semantic(
        self,
        repository_id: str,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.2,
        index_id: Optional[str] = None,
    ) -> List[ChunkEvidence]:
        """Performs vector similarity search across repository code chunks."""
        # 1. Resolve target index
        if not index_id:
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
            index_id = index.id

        # 2. Generate query embedding
        query_vector = await self.embedding_provider.embed_query(query)

        # 3. Fetch candidate chunks
        chk_stmt = select(CodeChunk).where(
            CodeChunk.index_id == index_id,
            CodeChunk.embedding.isnot(None),
        )
        chunks = (await self.session.execute(chk_stmt)).scalars().all()

        # 4. Rank by cosine similarity
        scored_chunks: List[Tuple[float, CodeChunk]] = []
        for chk in chunks:
            raw_emb = chk.embedding
            if isinstance(raw_emb, str):
                try:
                    vec = json.loads(raw_emb)
                except Exception:
                    continue
            elif isinstance(raw_emb, (list, tuple)):
                vec = raw_emb
            else:
                continue

            sim = self._cosine_similarity(query_vector, vec)
            if sim >= min_similarity:
                scored_chunks.append((sim, chk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        return [
            ChunkEvidence(
                file_path=chk.file_path,
                start_line=chk.start_line,
                end_line=chk.end_line,
                content=chk.content,
                similarity=round(score, 4),
            )
            for score, chk in scored_chunks[:top_k]
        ]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculates cosine similarity between two float vectors."""
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)
