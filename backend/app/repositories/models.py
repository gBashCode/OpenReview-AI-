"""Repository ORM Model scoped by Organization for Multi-Tenant Isolation."""

from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.organizations.models import Organization
    from app.github.models import GitHubInstallation
    from app.pull_requests.models import PullRequest
    from app.indexing.models import RepositoryIndex, CodeChunk, CodeSymbol


class Repository(Base, UUIDMixin, TimestampMixin):
    """Represents a connected code repository under tenant organization ownership."""

    __tablename__ = "repositories"

    organization_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    installation_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("github_installations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    github_repo_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    owner: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    default_branch: Mapped[str] = mapped_column(String(100), default="main", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    clone_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="repositories")
    installation: Mapped[Optional["GitHubInstallation"]] = relationship("GitHubInstallation", back_populates="repositories")
    pull_requests: Mapped[List["PullRequest"]] = relationship(
        "PullRequest",
        back_populates="repository",
        cascade="all, delete-orphan",
    )
    indexes: Mapped[List["RepositoryIndex"]] = relationship(
        "RepositoryIndex",
        back_populates="repository",
        cascade="all, delete-orphan",
    )
