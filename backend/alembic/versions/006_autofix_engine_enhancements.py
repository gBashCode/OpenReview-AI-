"""AutoFix engine enhancements: rollback_diff, formatter_status, linter_status, sandbox_status, failure_explanation, branch_name, pr_url.

Revision ID: 006_autofix_engine_enhancements
Revises: 005_finding_verification_fields
Create Date: 2026-11-19
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "006_autofix_engine_enhancements"
down_revision: Union[str, None] = "005_finding_verification_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("patches"):
        cols = [c["name"] for c in inspector.get_columns("patches")]
        if "rollback_diff" not in cols:
            op.add_column("patches", sa.Column("rollback_diff", sa.Text(), nullable=True))
        if "formatter_status" not in cols:
            op.add_column("patches", sa.Column("formatter_status", sa.String(30), nullable=True, server_default="passed"))
        if "linter_status" not in cols:
            op.add_column("patches", sa.Column("linter_status", sa.String(30), nullable=True, server_default="passed"))
        if "sandbox_status" not in cols:
            op.add_column("patches", sa.Column("sandbox_status", sa.String(30), nullable=True, server_default="passed"))
        if "regression_status" not in cols:
            op.add_column("patches", sa.Column("regression_status", sa.String(30), nullable=True, server_default="passed"))
        if "failure_explanation" not in cols:
            op.add_column("patches", sa.Column("failure_explanation", sa.Text(), nullable=True))
        if "branch_name" not in cols:
            op.add_column("patches", sa.Column("branch_name", sa.String(100), nullable=True))
        if "pr_url" not in cols:
            op.add_column("patches", sa.Column("pr_url", sa.String(500), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect != "sqlite":
        op.drop_column("patches", "pr_url")
        op.drop_column("patches", "branch_name")
        op.drop_column("patches", "failure_explanation")
        op.drop_column("patches", "regression_status")
        op.drop_column("patches", "sandbox_status")
        op.drop_column("patches", "linter_status")
        op.drop_column("patches", "formatter_status")
        op.drop_column("patches", "rollback_diff")
