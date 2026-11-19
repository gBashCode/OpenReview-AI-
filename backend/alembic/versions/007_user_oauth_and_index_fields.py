"""Add OAuth and demo fields to users, and indexed_at to repository_indexes.

Revision ID: 007_user_oauth_and_index_fields
Revises: 006_autofix_engine_enhancements
Create Date: 2026-11-20
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "007_user_oauth_and_index_fields"
down_revision: Union[str, None] = "006_autofix_engine_enhancements"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("users"):
        user_cols = [c["name"] for c in inspector.get_columns("users")]
        if "github_id" not in user_cols:
            op.add_column("users", sa.Column("github_id", sa.Integer(), nullable=True))
            op.create_index("ix_users_github_id", "users", ["github_id"], unique=True)
        if "github_access_token" not in user_cols:
            op.add_column("users", sa.Column("github_access_token", sa.String(255), nullable=True))
        if "google_id" not in user_cols:
            op.add_column("users", sa.Column("google_id", sa.String(100), nullable=True))
            op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)
        if "is_demo" not in user_cols:
            op.add_column("users", sa.Column("is_demo", sa.Boolean(), server_default=sa.text("false"), nullable=False))

    if inspector.has_table("repository_indexes"):
        idx_cols = [c["name"] for c in inspector.get_columns("repository_indexes")]
        if "indexed_at" not in idx_cols:
            op.add_column("repository_indexes", sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("repository_indexes"):
        idx_cols = [c["name"] for c in inspector.get_columns("repository_indexes")]
        if "indexed_at" in idx_cols:
            op.drop_column("repository_indexes", "indexed_at")

    if inspector.has_table("users"):
        user_cols = [c["name"] for c in inspector.get_columns("users")]
        if "is_demo" in user_cols:
            op.drop_column("users", "is_demo")
        if "google_id" in user_cols:
            op.drop_index("ix_users_google_id", table_name="users")
            op.drop_column("users", "google_id")
        if "github_access_token" in user_cols:
            op.drop_column("users", "github_access_token")
        if "github_id" in user_cols:
            op.drop_index("ix_users_github_id", table_name="users")
            op.drop_column("users", "github_id")
