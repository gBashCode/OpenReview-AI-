"""Autofix Patch ORM Model."""

from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.findings.models import Finding
    from app.users.models import User
    from app.verification.models import TestRun


class Patch(Base, UUIDMixin, TimestampMixin):
    """Represents an automated code patch generated for a finding."""

    __tablename__ = "patches"

    finding_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("findings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_code: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_code: Mapped[str] = mapped_column(Text, nullable=False)
    diff_content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
        index=True,
    )  # pending, approved, rejected, applied, failed
    applied_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    commit_sha: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    finding: Mapped["Finding"] = relationship("Finding", back_populates="patches")
    applied_by_user: Mapped[Optional["User"]] = relationship("User")
    test_runs: Mapped[List["TestRun"]] = relationship(
        "TestRun",
        back_populates="patch",
        cascade="all, delete-orphan",
    )
