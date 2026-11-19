"""Multi-Agent Conference enhancements: evidence, position, source_reference, final_decision.

Revision ID: 004_conference_enhancements
Revises: 003_indexing_enhancements
Create Date: 2026-11-19
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004_conference_enhancements"
down_revision: Union[str, None] = "003_indexing_enhancements"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 1. Update agent_discussions table
    if inspector.has_table("agent_discussions"):
        disc_cols = [c["name"] for c in inspector.get_columns("agent_discussions")]
        if "evidence" not in disc_cols:
            op.add_column("agent_discussions", sa.Column("evidence", sa.Text(), nullable=True))
        if "source_reference" not in disc_cols:
            op.add_column("agent_discussions", sa.Column("source_reference", sa.String(500), nullable=True))
        if "position" not in disc_cols:
            op.add_column("agent_discussions", sa.Column("position", sa.String(50), nullable=False, server_default="proposal"))
        if "final_decision" not in disc_cols:
            op.add_column("agent_discussions", sa.Column("final_decision", sa.String(50), nullable=True))
        if "round_number" not in disc_cols:
            op.add_column("agent_discussions", sa.Column("round_number", sa.Integer(), nullable=False, server_default="1"))

    # 2. Update findings table
    if inspector.has_table("findings"):
        finding_cols = [c["name"] for c in inspector.get_columns("findings")]
        if "discussion_state" not in finding_cols:
            op.add_column("findings", sa.Column("discussion_state", sa.String(50), nullable=False, server_default="Accepted"))
        if "evidence" not in finding_cols:
            op.add_column("findings", sa.Column("evidence", sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect != "sqlite":
        op.drop_column("findings", "evidence")
        op.drop_column("findings", "discussion_state")
        op.drop_column("agent_discussions", "round_number")
        op.drop_column("agent_discussions", "final_decision")
        op.drop_column("agent_discussions", "position")
        op.drop_column("agent_discussions", "source_reference")
        op.drop_column("agent_discussions", "evidence")
