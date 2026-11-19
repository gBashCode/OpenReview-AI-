"""Findings ORM Model."""

from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.reviews.models import Review
    from app.autofix.models import Patch
    from app.agents.models import AgentDiscussion


class Finding(Base, UUIDMixin, TimestampMixin):
    """Represents a discrete code issue, vulnerability, or suggestion detected by an AI review agent."""

    __tablename__ = "findings"

    review_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    line_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_line_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    side: Mapped[str] = mapped_column(String(10), default="RIGHT", nullable=False)  # LEFT or RIGHT
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # security, bug, performance, style, architecture
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )  # critical, high, medium, low, info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_patch: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    agent_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    discussion_state: Mapped[str] = mapped_column(
        String(50),
        default="Accepted",
        nullable=False,
        index=True,
    )  # Accepted, Rejected, Needs investigation, Duplicate, Uncertain
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(50),
        default="Confirmed",
        nullable=False,
        index=True,
    )  # Confirmed, High-confidence potential issue, Needs investigation, Rejected
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actionability_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_publishable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    github_comment_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    review: Mapped["Review"] = relationship("Review", back_populates="findings")
    patches: Mapped[List["Patch"]] = relationship(
        "Patch",
        back_populates="finding",
        cascade="all, delete-orphan",
    )
    discussions: Mapped[List["AgentDiscussion"]] = relationship(
        "AgentDiscussion",
        back_populates="finding",
    )
