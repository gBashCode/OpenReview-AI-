"""Repository Semantic Indexing Orchestrator with Incremental Updates and Stale Pruning."""

from dataclasses import asdict
from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException, NotFoundError
from app.core.logging import get_logger
from app.indexing.architecture_summarizer import ArchitectureSummarizer
from app.indexing.ast_parser import ParsedImport, ParsedSymbol, TreeSitterASTParser
from app.indexing.chunker import CodeChunkItem, SemanticChunker
from app.indexing.dependency_graph import DependencyGraph
from app.indexing.embeddings import BaseEmbeddingProvider, get_embedding_provider
from app.indexing.file_discovery import DiscoveredFile, FileCategory, FileDiscoveryService, Language
from app.indexing.models import CodeChunk, CodeSymbol, RepositoryIndex
from app.repositories.models import Repository

logger = get_logger("openreview.indexing.indexer")


class RepositoryIndexer:
    """Orchestrates secure file discovery, AST extraction, chunking, embeddings, and persistence."""

    def __init__(
        self,
        session: AsyncSession,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
    ):
        self.session = session
        self.ast_parser = TreeSitterASTParser()
        self.chunker = SemanticChunker()
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.summarizer = ArchitectureSummarizer()
        self.discovery_service = FileDiscoveryService()

    async def index_repository(
        self,
        repository_id: str,
        root_path: str,
        branch: str = "main",
        commit_sha: str = "HEAD",
        incremental: bool = True,
    ) -> RepositoryIndex:
        """Executes complete or incremental indexing of a repository commit."""
        # 1. Validate repository existence
        repo_stmt = select(Repository).where(Repository.id == repository_id)
        repo = (await self.session.execute(repo_stmt)).scalar_one_or_none()
        if not repo:
            raise NotFoundError("Repository", repository_id)

        # 2. Discover repository files
        discovered_files = self.discovery_service.discover_repository(root_path)
        current_hashes: Dict[str, str] = {
            f.relative_path: f.sha256_hash for f in discovered_files if not f.is_binary
        }

        # 3. Check for previous completed index for incremental diff
        prev_index_stmt = (
            select(RepositoryIndex)
            .where(
                RepositoryIndex.repository_id == repository_id,
                RepositoryIndex.status == "completed",
            )
            .order_by(RepositoryIndex.created_at.desc())
        )
        prev_index = (await self.session.execute(prev_index_stmt)).scalars().first()

        # 4. Create new Index record
        index_record = RepositoryIndex(
            repository_id=repository_id,
            branch=branch,
            commit_sha=commit_sha,
            status="indexing",
            total_files=len(discovered_files),
        )
        self.session.add(index_record)
        await self.session.flush()

        # 5. Determine files to parse (incremental vs initial)
        files_to_parse: List[DiscoveredFile] = []
        unchanged_files: Set[str] = set()

        if incremental and prev_index and prev_index.file_hashes:
            prev_hashes = prev_index.file_hashes
            for f in discovered_files:
                if f.is_binary:
                    continue
                prev_hash = prev_hashes.get(f.relative_path)
                if prev_hash and prev_hash == f.sha256_hash:
                    unchanged_files.add(f.relative_path)
                else:
                    files_to_parse.append(f)

            logger.info(
                f"Incremental index: {len(unchanged_files)} unchanged, {len(files_to_parse)} added/modified files."
            )
        else:
            files_to_parse = [f for f in discovered_files if not f.is_binary]
            logger.info(f"Full index: parsing {len(files_to_parse)} files.")

        try:
            # 6. Parse symbols, imports, and generate chunks for modified/added files
            parsed_symbols: List[ParsedSymbol] = []
            parsed_imports: List[ParsedImport] = []
            all_chunks: List[CodeChunkItem] = []
            dep_graph = DependencyGraph()

            for d_file in files_to_parse:
                try:
                    with open(d_file.full_path, "r", encoding="utf-8", errors="ignore") as src_f:
                        content = src_f.read()
                except Exception as read_err:
                    logger.warning(f"Failed to read {d_file.relative_path}: {read_err}")
                    continue

                # AST Parsing (only for supported code languages)
                file_syms: List[ParsedSymbol] = []
                file_imps: List[ParsedImport] = []
                if d_file.language in (
                    Language.PYTHON,
                    Language.JAVASCRIPT,
                    Language.TYPESCRIPT,
                    Language.JAVA,
                    Language.GO,
                ):
                    file_syms, file_imps = self.ast_parser.parse_file(
                        d_file.relative_path, content, d_file.language
                    )
                    parsed_symbols.extend(file_syms)
                    parsed_imports.extend(file_imps)
                    dep_graph.add_symbols(d_file.relative_path, file_syms)
                    dep_graph.add_imports(d_file.relative_path, file_imps)

                # Chunking
                chunks = self.chunker.chunk_file(
                    d_file.relative_path,
                    content,
                    symbols=file_syms,
                    language=d_file.language,
                )
                all_chunks.extend(chunks)

            # 7. Carry over unchanged symbols and chunks from previous index if incremental
            if unchanged_files and prev_index:
                # Copy symbols from prev_index
                prev_sym_stmt = select(CodeSymbol).where(
                    CodeSymbol.index_id == prev_index.id,
                    CodeSymbol.file_path.in_(unchanged_files),
                )
                prev_symbols = (await self.session.execute(prev_sym_stmt)).scalars().all()
                for ps in prev_symbols:
                    new_sym = CodeSymbol(
                        index_id=index_record.id,
                        file_path=ps.file_path,
                        name=ps.name,
                        kind=ps.kind,
                        line_number=ps.line_number,
                        end_line_number=ps.end_line_number,
                        signature=ps.signature,
                        docstring=ps.docstring,
                    )
                    self.session.add(new_sym)

                # Copy chunks from prev_index
                prev_chk_stmt = select(CodeChunk).where(
                    CodeChunk.index_id == prev_index.id,
                    CodeChunk.file_path.in_(unchanged_files),
                )
                prev_chunks = (await self.session.execute(prev_chk_stmt)).scalars().all()
                for pc in prev_chunks:
                    new_chk = CodeChunk(
                        index_id=index_record.id,
                        file_path=pc.file_path,
                        start_line=pc.start_line,
                        end_line=pc.end_line,
                        content=pc.content,
                        token_count=pc.token_count,
                        embedding=pc.embedding,
                    )
                    self.session.add(new_chk)

            # 8. Generate Embeddings in batches for new chunks
            chunk_contents = [c.content for c in all_chunks]
            embeddings: List[List[float]] = []
            if chunk_contents:
                embeddings = await self.embedding_provider.embed_texts(chunk_contents)

            # 9. Persist newly parsed symbols
            for sym in parsed_symbols:
                db_symbol = CodeSymbol(
                    index_id=index_record.id,
                    file_path=sym.file_path,
                    name=sym.name,
                    kind=sym.kind,
                    line_number=sym.line_number,
                    end_line_number=sym.end_line_number,
                    signature=sym.signature,
                    docstring=sym.docstring,
                )
                self.session.add(db_symbol)

            # 10. Persist newly generated chunks
            for chk, emb in zip(all_chunks, embeddings):
                db_chunk = CodeChunk(
                    index_id=index_record.id,
                    file_path=chk.file_path,
                    start_line=chk.start_line,
                    end_line=chk.end_line,
                    content=chk.content,
                    token_count=chk.token_count,
                    embedding=emb,
                )
                self.session.add(db_chunk)

            # 11. Cross-reference dependency relationships and architecture summary
            dep_graph.resolve_relationships(discovered_files)
            arch_summary = self.summarizer.summarize(discovered_files, dep_graph)

            # 12. Finalize Index metadata
            total_symbols_count = len(parsed_symbols) + (len(prev_symbols) if unchanged_files and prev_index else 0)
            total_chunks_count = len(all_chunks) + (len(prev_chunks) if unchanged_files and prev_index else 0)

            total_files_count = len(discovered_files)
            index_record.status = "completed"
            index_record.total_chunks = total_chunks_count
            index_record.total_symbols = total_symbols_count
            index_record.file_hashes = current_hashes
            index_record.summary_json = {
                "architecture": asdict(arch_summary),
                "dependencies": dep_graph.to_dict(),
            }
            index_record.indexed_at = datetime.now(timezone.utc)

            await self.session.commit()
            await self.session.refresh(index_record)
            logger.info(
                f"Successfully indexed repo {repository_id}: {total_files_count} files, {total_chunks_count} chunks, {total_symbols_count} symbols."
            )
            return index_record

        except Exception as exc:
            await self.session.rollback()
            logger.error(f"Repository indexing failed for {repository_id}: {exc}", exc_info=True)
            index_record.status = "failed"
            index_record.error_message = str(exc)
            await self.session.commit()
            raise AppException(f"Repository indexing failed: {str(exc)}", status_code=500)
