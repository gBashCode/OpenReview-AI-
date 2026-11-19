"""GitHub App Installation ORM Model."""

from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.organizations.models import Organization
    from app.repositories.models import Repository


class GitHubInstallation(Base, UUIDMixin, TimestampMixin):
    """Represents an authorized GitHub App installation scoped to an organization."""

    __tablename__ = "github_installations"

    organization_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    installation_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    account_login: Mapped[str] = mapped_column(String(100), nullable=False)
    account_type: Mapped[str] = mapped_column(String(50), default="Organization", nullable=False)
    permissions_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="github_installations")
    repositories: Mapped[List["Repository"]] = relationship(
        "Repository",
        back_populates="installation",
    )
