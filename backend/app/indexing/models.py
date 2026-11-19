"""Semantic Indexing ORM Models: RepositoryIndex, CodeChunk (Vector), and CodeSymbol."""

from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, CompatibleVector, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.repositories.models import Repository


class RepositoryIndex(Base, UUIDMixin, TimestampMixin):
    """Tracks indexing passes and commit SHA semantic sync status."""

    __tablename__ = "repository_indexes"

    repository_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    branch: Mapped[str] = mapped_column(String(100), default="main", nullable=False)
    commit_sha: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
    )  # pending, indexing, completed, failed
    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_chunks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_symbols: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    indexed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", back_populates="indexes")


class CodeChunk(Base, UUIDMixin, TimestampMixin):
    """Vectorized code hunk stored with 1,536-dimensional pgvector embeddings."""

    __tablename__ = "code_chunks"

    repository_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(String(500), index=True, nullable=False)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    embedding: Mapped[Optional[Any]] = mapped_column(CompatibleVector(1536), nullable=True)

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", back_populates="code_chunks")


class CodeSymbol(Base, UUIDMixin, TimestampMixin):
    """Extracted abstract syntax tree (AST) symbol (function, class, interface, method)."""

    __tablename__ = "code_symbols"

    repository_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(String(500), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # function, class, method, variable, interface
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    docstring: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", back_populates="code_symbols")
