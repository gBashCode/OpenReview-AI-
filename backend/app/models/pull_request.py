"""Pull Request ORM Model."""

from typing import List, TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.repository import Repository
    from app.models.review import Review


class PullRequest(Base, UUIDMixin, TimestampMixin):
    """Represents a Pull Request evaluated by OpenReview AI."""

    __tablename__ = "pull_requests"

    repository_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    github_pr_id: Mapped[int] = mapped_column(Integer, index=True, nullable=True)
    pr_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    head_branch: Mapped[str] = mapped_column(String(100), nullable=False)
    base_branch: Mapped[str] = mapped_column(String(100), nullable=False)
    head_sha: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    base_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    author_username: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(20), default="open", nullable=False)  # open, closed, merged

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", back_populates="pull_requests")
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="pull_request",
        cascade="all, delete-orphan",
    )
