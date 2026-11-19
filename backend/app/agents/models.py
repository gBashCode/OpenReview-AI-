"""Agents ORM Models."""

from typing import Optional, TYPE_CHECKING
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.reviews.models import Review
    from app.findings.models import Finding


class ReviewAgent(Base, UUIDMixin, TimestampMixin):
    """Represents an autonomous AI agent participating in a pull request review."""

    __tablename__ = "review_agents"

    review_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )  # e.g., Security Sentinel, Performance Guardian, Bug Hunter, Architecture Specialist, Verification Arbiter
    role: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )  # e.g., security_analysis, performance_profiling, code_quality, verification
    status: Mapped[str] = mapped_column(
        String(30),
        default="idle",
        nullable=False,
        index=True,
    )  # idle, running, completed, failed
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # gpt-4o, claude-3-5-sonnet, etc.
    reasoning_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    findings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    review: Mapped["Review"] = relationship("Review", back_populates="agents")


class AgentDiscussion(Base, UUIDMixin, TimestampMixin):
    """Represents debate, cross-examination, and consensus messages between AI agents."""

    __tablename__ = "agent_discussions"

    review_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    finding_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("findings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    message_type: Mapped[str] = mapped_column(
        String(50),
        default="proposal",
        nullable=False,
        index=True,
    )  # proposal, critique, verification, consensus, dissent
    content: Mapped[str] = mapped_column(Text, nullable=False)
    file_context: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_reference: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    position: Mapped[str] = mapped_column(
        String(50),
        default="proposal",
        nullable=False,
        index=True,
    )  # proposal, challenge, rebuttal, context_supply, verdict, concession
    final_decision: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )  # Accepted, Rejected, Needs investigation, Duplicate, Uncertain
    round_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    review: Mapped["Review"] = relationship("Review", back_populates="discussions")
    finding: Mapped[Optional["Finding"]] = relationship("Finding", back_populates="discussions")
