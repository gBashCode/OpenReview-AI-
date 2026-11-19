"""Review Comment ORM Model."""

from typing import Optional, TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.review import Review


class ReviewComment(Base, UUIDMixin, TimestampMixin):
    """Represents an atomic finding or suggestion posted by AI review agents."""

    __tablename__ = "review_comments"

    review_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    line_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_line_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    side: Mapped[str] = mapped_column(String(10), default="RIGHT", nullable=False)  # LEFT, RIGHT
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # security, performance, bug, style, architecture
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # info, warning, error, critical
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_patch: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    github_comment_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    review: Mapped["Review"] = relationship("Review", back_populates="comments")
