"""Initial schema for OpenReview AI.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-19 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Repositories Table
    op.create_table(
        "repositories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("github_repo_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("owner", sa.String(100), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False, unique=True),
        sa.Column("default_branch", sa.String(100), nullable=False, server_default="main"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("clone_url", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_repositories_id", "repositories", ["id"])
    op.create_index("ix_repositories_github_repo_id", "repositories", ["github_repo_id"])
    op.create_index("ix_repositories_owner", "repositories", ["owner"])
    op.create_index("ix_repositories_name", "repositories", ["name"])
    op.create_index("ix_repositories_full_name", "repositories", ["full_name"])

    # 2. Pull Requests Table
    op.create_table(
        "pull_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("repository_id", sa.String(36), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("github_pr_id", sa.Integer(), nullable=True),
        sa.Column("pr_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("head_branch", sa.String(100), nullable=False),
        sa.Column("base_branch", sa.String(100), nullable=False),
        sa.Column("head_sha", sa.String(40), nullable=False),
        sa.Column("base_sha", sa.String(40), nullable=False),
        sa.Column("author_username", sa.String(100), nullable=False),
        sa.Column("state", sa.String(20), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_pull_requests_id", "pull_requests", ["id"])
    op.create_index("ix_pull_requests_repository_id", "pull_requests", ["repository_id"])
    op.create_index("ix_pull_requests_pr_number", "pull_requests", ["pr_number"])
    op.create_index("ix_pull_requests_head_sha", "pull_requests", ["head_sha"])

    # 3. Reviews Table
    op.create_table(
        "reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("pull_request_id", sa.String(36), sa.ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("commit_sha", sa.String(40), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("security_score", sa.Float(), nullable=True),
        sa.Column("performance_score", sa.Float(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("findings_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_reviews_id", "reviews", ["id"])
    op.create_index("ix_reviews_pull_request_id", "reviews", ["pull_request_id"])
    op.create_index("ix_reviews_status", "reviews", ["status"])

    # 4. Review Comments Table
    op.create_table(
        "review_comments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("review_id", sa.String(36), sa.ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=True),
        sa.Column("end_line_number", sa.Integer(), nullable=True),
        sa.Column("side", sa.String(10), nullable=False, server_default="RIGHT"),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("suggested_patch", sa.Text(), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("github_comment_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_review_comments_id", "review_comments", ["id"])
    op.create_index("ix_review_comments_review_id", "review_comments", ["review_id"])
    op.create_index("ix_review_comments_category", "review_comments", ["category"])
    op.create_index("ix_review_comments_severity", "review_comments", ["severity"])


def downgrade() -> None:
    op.drop_table("review_comments")
    op.drop_table("reviews")
    op.drop_table("pull_requests")
    op.drop_table("repositories")
