"""SQLAlchemy models central registry for OpenReview AI.

This module exports all 16 foundational domain models so that Alembic migrations
and metadata reflections discover the complete database schema.
"""

from app.database.base import Base, CompatibleVector, TimestampMixin, UUIDMixin
from app.users.models import User
from app.organizations.models import Organization, OrganizationMember
from app.github.models import GitHubInstallation
from app.repositories.models import Repository
from app.indexing.models import RepositoryIndex, CodeChunk, CodeSymbol
from app.pull_requests.models import PullRequest
from app.reviews.models import Review
from app.findings.models import Finding
from app.agents.models import ReviewAgent, AgentDiscussion
from app.autofix.models import Patch
from app.verification.models import TestRun
from app.analytics.models import AuditLog

__all__ = [
    "Base",
    "UUIDMixin",
    "TimestampMixin",
    "CompatibleVector",
    "User",
    "Organization",
    "OrganizationMember",
    "GitHubInstallation",
    "Repository",
    "RepositoryIndex",
    "CodeChunk",
    "CodeSymbol",
    "PullRequest",
    "Review",
    "Finding",
    "ReviewAgent",
    "AgentDiscussion",
    "Patch",
    "TestRun",
    "AuditLog",
]
