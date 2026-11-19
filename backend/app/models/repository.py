"""Repository ORM Model."""

from typing import List, TYPE_CHECKING
from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.pull_request import PullRequest


class Repository(Base, UUIDMixin, TimestampMixin):
    """Represents a connected GitHub code repository."""

    __tablename__ = "repositories"

    github_repo_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    owner: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    default_branch: Mapped[str] = mapped_column(String(100), default="main", nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    clone_url: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationships
    pull_requests: Mapped[List["PullRequest"]] = relationship(
        "PullRequest",
        back_populates="repository",
        cascade="all, delete-orphan",
    )
