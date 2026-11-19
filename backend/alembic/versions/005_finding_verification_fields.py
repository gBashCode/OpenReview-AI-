"""Finding verification fields: verification_status, root_cause, impact, actionability_score, is_publishable, rejection_reason.

Revision ID: 005_finding_verification_fields
Revises: 004_conference_enhancements
Create Date: 2026-11-19
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "005_finding_verification_fields"
down_revision: Union[str, None] = "004_conference_enhancements"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("findings"):
        cols = [c["name"] for c in inspector.get_columns("findings")]
        if "verification_status" not in cols:
            op.add_column(
                "findings",
                sa.Column("verification_status", sa.String(50), nullable=False, server_default="Confirmed"),
            )
        if "root_cause" not in cols:
            op.add_column("findings", sa.Column("root_cause", sa.Text(), nullable=True))
        if "impact" not in cols:
            op.add_column("findings", sa.Column("impact", sa.Text(), nullable=True))
        if "actionability_score" not in cols:
            op.add_column("findings", sa.Column("actionability_score", sa.Float(), nullable=True))
        if "is_publishable" not in cols:
            op.add_column(
                "findings",
                sa.Column("is_publishable", sa.Boolean(), nullable=False, server_default="1"),
            )
        if "rejection_reason" not in cols:
            op.add_column("findings", sa.Column("rejection_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect != "sqlite":
        op.drop_column("findings", "rejection_reason")
        op.drop_column("findings", "is_publishable")
        op.drop_column("findings", "actionability_score")
        op.drop_column("findings", "impact")
        op.drop_column("findings", "root_cause")
        op.drop_column("findings", "verification_status")
