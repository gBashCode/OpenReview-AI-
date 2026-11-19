"""Verification and Sandbox TestRun ORM Model."""

from typing import Optional, TYPE_CHECKING
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.autofix.models import Patch


class TestRun(Base, UUIDMixin, TimestampMixin):
    """Represents a sandbox test execution verifying a generated autofix patch."""

    __tablename__ = "test_runs"

    patch_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
        index=True,
    )  # pending, running, passed, failed, error
    test_framework: Mapped[str] = mapped_column(
        String(50),
        default="pytest",
        nullable=False,
    )  # pytest, jest, go_test, cargo_test
    total_tests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed_tests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_tests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_tests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    execution_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stdout_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stderr_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    patch: Mapped["Patch"] = relationship("Patch", back_populates="test_runs")
