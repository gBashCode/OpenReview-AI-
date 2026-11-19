"""Review ORM Model."""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.pull_requests.models import PullRequest
    from app.findings.models import Finding
    from app.agents.models import ReviewAgent, AgentDiscussion


class Review(Base, UUIDMixin, TimestampMixin):
    """Represents an autonomous multi-agent code review pass on a pull request."""

    __tablename__ = "reviews"

    pull_request_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("pull_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    commit_sha: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
        index=True,
    )  # pending, analyzing, debating, completed, failed
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Overall quality score 0-100
    security_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    performance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    findings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    pull_request: Mapped["PullRequest"] = relationship("PullRequest", back_populates="reviews")
    findings: Mapped[List["Finding"]] = relationship(
        "Finding",
        back_populates="review",
        cascade="all, delete-orphan",
    )
    agents: Mapped[List["ReviewAgent"]] = relationship(
        "ReviewAgent",
        back_populates="review",
        cascade="all, delete-orphan",
    )
    discussions: Mapped[List["AgentDiscussion"]] = relationship(
        "AgentDiscussion",
        back_populates="review",
        cascade="all, delete-orphan",
    )
