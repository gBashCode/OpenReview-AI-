"""Indexing metadata enhancements: file_hashes and summary_json on repository_indexes.

Revision ID: 003_indexing_enhancements
Revises: 002_foundational_modular_schema
Create Date: 2026-11-19
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003_indexing_enhancements"
down_revision: Union[str, None] = "002_foundational_modular_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = [c["name"] for c in inspector.get_columns("repository_indexes")]
    if "file_hashes" not in cols:
        op.add_column("repository_indexes", sa.Column("file_hashes", sa.JSON(), nullable=True))
    if "summary_json" not in cols:
        op.add_column("repository_indexes", sa.Column("summary_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect != "sqlite":
        op.drop_column("repository_indexes", "summary_json")
        op.drop_column("repository_indexes", "file_hashes")
