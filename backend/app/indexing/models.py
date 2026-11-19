"""Semantic Indexing ORM Models: RepositoryIndex, CodeChunk (Vector), and CodeSymbol."""

from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
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
    file_hashes: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON, nullable=True)
    summary_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", back_populates="indexes")
    chunks: Mapped[List["CodeChunk"]] = relationship(
        "CodeChunk",
        back_populates="index",
        cascade="all, delete-orphan",
    )
    symbols: Mapped[List["CodeSymbol"]] = relationship(
        "CodeSymbol",
        back_populates="index",
        cascade="all, delete-orphan",
    )


class CodeChunk(Base, UUIDMixin, TimestampMixin):
    """Vectorized code hunk stored with 1,536-dimensional pgvector embeddings."""

    __tablename__ = "code_chunks"

    index_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("repository_indexes.id", ondelete="CASCADE"),
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
    index: Mapped["RepositoryIndex"] = relationship("RepositoryIndex", back_populates="chunks")


class CodeSymbol(Base, UUIDMixin, TimestampMixin):
    """Extracted abstract syntax tree (AST) symbol (function, class, interface, method)."""

    __tablename__ = "code_symbols"

    index_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("repository_indexes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(String(500), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # function, class, method, variable, interface, struct, import
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    docstring: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    index: Mapped["RepositoryIndex"] = relationship("RepositoryIndex", back_populates="symbols")

    def __init__(self, **kwargs):
        if "start_line" in kwargs and "line_number" not in kwargs:
            kwargs["line_number"] = kwargs.pop("start_line")
        if "end_line" in kwargs and "end_line_number" not in kwargs:
            kwargs["end_line_number"] = kwargs.pop("end_line")
        super().__init__(**kwargs)

    @property
    def start_line(self) -> int:
        return self.line_number

    @property
    def end_line(self) -> int:
        return self.end_line_number if self.end_line_number is not None else self.line_number
