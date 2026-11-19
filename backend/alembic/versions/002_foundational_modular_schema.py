"""Foundational 16-table modular schema with pgvector support.

Revision ID: 002_foundational_modular_schema
Revises: 001_initial_schema
Create Date: 2026-11-19 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision: str = "002_foundational_modular_schema"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    inspector = Inspector.from_engine(bind)
    existing_tables = inspector.get_table_names()

    # 1. Enable pgvector extension on PostgreSQL
    if dialect_name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # 2. Users Table
    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("email", sa.String(255), nullable=False, unique=True),
            sa.Column("username", sa.String(50), nullable=False, unique=True),
            sa.Column("full_name", sa.String(100), nullable=True),
            sa.Column("hashed_password", sa.String(255), nullable=False),
            sa.Column("avatar_url", sa.String(255), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_users_id", "users", ["id"])
        op.create_index("ix_users_email", "users", ["email"])
        op.create_index("ix_users_username", "users", ["username"])

    # 3. Organizations Table
    if "organizations" not in existing_tables:
        op.create_table(
            "organizations",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("slug", sa.String(100), nullable=False, unique=True),
            sa.Column("avatar_url", sa.String(255), nullable=True),
            sa.Column("plan", sa.String(50), nullable=False, server_default="team"),
            sa.Column("max_repos", sa.Integer(), nullable=False, server_default="50"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_organizations_id", "organizations", ["id"])
        op.create_index("ix_organizations_slug", "organizations", ["slug"])

    # Ensure a default organization exists for linking
    op.execute(
        "INSERT OR IGNORE INTO organizations (id, name, slug, plan, max_repos, created_at, updated_at) "
        "VALUES ('default-org', 'Default Team', 'default-team', 'team', 50, datetime('now'), datetime('now'))"
        if dialect_name == "sqlite"
        else "INSERT INTO organizations (id, name, slug, plan, max_repos, created_at, updated_at) "
        "VALUES ('default-org', 'Default Team', 'default-team', 'team', 50, now(), now()) ON CONFLICT DO NOTHING"
    )

    # 4. Organization Members Table
    if "organization_members" not in existing_tables:
        op.create_table(
            "organization_members",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("role", sa.String(30), nullable=False, server_default="reviewer"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_organization_members_id", "organization_members", ["id"])
        op.create_index("ix_organization_members_organization_id", "organization_members", ["organization_id"])
        op.create_index("ix_organization_members_user_id", "organization_members", ["user_id"])

    # 5. GitHub Installations Table
    if "github_installations" not in existing_tables:
        op.create_table(
            "github_installations",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("installation_id", sa.Integer(), nullable=False, unique=True),
            sa.Column("account_login", sa.String(100), nullable=False),
            sa.Column("account_type", sa.String(50), nullable=False, server_default="User"),
            sa.Column("permissions_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_github_installations_id", "github_installations", ["id"])
        op.create_index("ix_github_installations_organization_id", "github_installations", ["organization_id"])
        op.create_index("ix_github_installations_installation_id", "github_installations", ["installation_id"])

    # Add organization_id and installation_id to repositories if missing
    repo_cols = [c["name"] for c in inspector.get_columns("repositories")]
    if "organization_id" not in repo_cols:
        op.add_column("repositories", sa.Column("organization_id", sa.String(36), nullable=False, server_default="default-org"))
        op.create_index("ix_repositories_organization_id", "repositories", ["organization_id"])
    if "installation_id" not in repo_cols:
        op.add_column("repositories", sa.Column("installation_id", sa.String(36), nullable=True))
        op.create_index("ix_repositories_installation_id", "repositories", ["installation_id"])

    # 6. Repository Indexes Table
    if "repository_indexes" not in existing_tables:
        op.create_table(
            "repository_indexes",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("repository_id", sa.String(36), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False),
            sa.Column("branch", sa.String(100), nullable=False, server_default="main"),
            sa.Column("commit_sha", sa.String(40), nullable=False),
            sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
            sa.Column("total_files", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_chunks", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_symbols", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_repository_indexes_id", "repository_indexes", ["id"])
        op.create_index("ix_repository_indexes_repository_id", "repository_indexes", ["repository_id"])
        op.create_index("ix_repository_indexes_commit_sha", "repository_indexes", ["commit_sha"])

    # 7. Code Chunks Table (Vector embedding support)
    if "code_chunks" not in existing_tables:
        embedding_col = (
            sa.Column("embedding", sa.Text(), nullable=True)
            if dialect_name == "sqlite"
            else sa.Column("embedding", sa.NullType(), nullable=True)  # Or Vector(1536) in raw postgresql
        )
        op.create_table(
            "code_chunks",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("index_id", sa.String(36), sa.ForeignKey("repository_indexes.id", ondelete="CASCADE"), nullable=False),
            sa.Column("file_path", sa.String(500), nullable=False),
            sa.Column("start_line", sa.Integer(), nullable=False),
            sa.Column("end_line", sa.Integer(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            embedding_col,
            sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        if dialect_name == "postgresql":
            op.execute("ALTER TABLE code_chunks ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector")
        op.create_index("ix_code_chunks_id", "code_chunks", ["id"])
        op.create_index("ix_code_chunks_index_id", "code_chunks", ["index_id"])
        op.create_index("ix_code_chunks_file_path", "code_chunks", ["file_path"])

    # 8. Code Symbols Table
    if "code_symbols" not in existing_tables:
        op.create_table(
            "code_symbols",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("index_id", sa.String(36), sa.ForeignKey("repository_indexes.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("kind", sa.String(50), nullable=False),
            sa.Column("file_path", sa.String(500), nullable=False),
            sa.Column("line_number", sa.Integer(), nullable=False),
            sa.Column("end_line_number", sa.Integer(), nullable=True),
            sa.Column("signature", sa.Text(), nullable=True),
            sa.Column("docstring", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_code_symbols_id", "code_symbols", ["id"])
        op.create_index("ix_code_symbols_index_id", "code_symbols", ["index_id"])
        op.create_index("ix_code_symbols_name", "code_symbols", ["name"])
        op.create_index("ix_code_symbols_file_path", "code_symbols", ["file_path"])

    # 9. Review Agents Table
    if "review_agents" not in existing_tables:
        op.create_table(
            "review_agents",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("review_id", sa.String(36), sa.ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False),
            sa.Column("agent_name", sa.String(100), nullable=False),
            sa.Column("role", sa.String(100), nullable=False),
            sa.Column("status", sa.String(30), nullable=False, server_default="idle"),
            sa.Column("model_name", sa.String(100), nullable=True),
            sa.Column("reasoning_summary", sa.Text(), nullable=True),
            sa.Column("confidence_score", sa.Float(), nullable=True),
            sa.Column("findings_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("execution_time_ms", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_review_agents_id", "review_agents", ["id"])
        op.create_index("ix_review_agents_review_id", "review_agents", ["review_id"])
        op.create_index("ix_review_agents_agent_name", "review_agents", ["agent_name"])

    # 10. Findings Table
    if "findings" not in existing_tables:
        op.create_table(
            "findings",
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
            sa.Column("agent_name", sa.String(100), nullable=True),
            sa.Column("confidence_score", sa.Float(), nullable=True),
            sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("github_comment_id", sa.String(100), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_findings_id", "findings", ["id"])
        op.create_index("ix_findings_review_id", "findings", ["review_id"])
        op.create_index("ix_findings_file_path", "findings", ["file_path"])
        op.create_index("ix_findings_category", "findings", ["category"])
        op.create_index("ix_findings_severity", "findings", ["severity"])

    # 11. Agent Discussions Table
    if "agent_discussions" not in existing_tables:
        op.create_table(
            "agent_discussions",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("review_id", sa.String(36), sa.ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False),
            sa.Column("finding_id", sa.String(36), sa.ForeignKey("findings.id", ondelete="SET NULL"), nullable=True),
            sa.Column("agent_name", sa.String(100), nullable=False),
            sa.Column("message_type", sa.String(50), nullable=False, server_default="proposal"),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("file_context", sa.String(500), nullable=True),
            sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_agent_discussions_id", "agent_discussions", ["id"])
        op.create_index("ix_agent_discussions_review_id", "agent_discussions", ["review_id"])
        op.create_index("ix_agent_discussions_finding_id", "agent_discussions", ["finding_id"])
        op.create_index("ix_agent_discussions_agent_name", "agent_discussions", ["agent_name"])

    # 12. Patches Table
    if "patches" not in existing_tables:
        op.create_table(
            "patches",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("finding_id", sa.String(36), sa.ForeignKey("findings.id", ondelete="CASCADE"), nullable=False),
            sa.Column("original_code", sa.Text(), nullable=False),
            sa.Column("proposed_code", sa.Text(), nullable=False),
            sa.Column("diff_content", sa.Text(), nullable=False),
            sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
            sa.Column("applied_by_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("commit_sha", sa.String(40), nullable=True),
            sa.Column("rejection_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_patches_id", "patches", ["id"])
        op.create_index("ix_patches_finding_id", "patches", ["finding_id"])
        op.create_index("ix_patches_status", "patches", ["status"])

    # 13. Test Runs Table
    if "test_runs" not in existing_tables:
        op.create_table(
            "test_runs",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("patch_id", sa.String(36), sa.ForeignKey("patches.id", ondelete="CASCADE"), nullable=False),
            sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
            sa.Column("test_framework", sa.String(50), nullable=False, server_default="pytest"),
            sa.Column("total_tests", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("passed_tests", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("failed_tests", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("skipped_tests", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("execution_time_seconds", sa.Float(), nullable=True),
            sa.Column("stdout_log", sa.Text(), nullable=True),
            sa.Column("stderr_log", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_test_runs_id", "test_runs", ["id"])
        op.create_index("ix_test_runs_patch_id", "test_runs", ["patch_id"])

    # 14. Audit Logs Table
    if "audit_logs" not in existing_tables:
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("action", sa.String(100), nullable=False),
            sa.Column("resource_type", sa.String(50), nullable=False),
            sa.Column("resource_id", sa.String(100), nullable=False),
            sa.Column("metadata_json", sa.Text(), nullable=True),
            sa.Column("ip_address", sa.String(45), nullable=True),
            sa.Column("user_agent", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_audit_logs_id", "audit_logs", ["id"])
        op.create_index("ix_audit_logs_organization_id", "audit_logs", ["organization_id"])
        op.create_index("ix_audit_logs_action", "audit_logs", ["action"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("test_runs")
    op.drop_table("patches")
    op.drop_table("agent_discussions")
    op.drop_table("findings")
    op.drop_table("review_agents")
    op.drop_table("code_symbols")
    op.drop_table("code_chunks")
    op.drop_table("repository_indexes")
    op.drop_table("github_installations")
    op.drop_table("organization_members")
    op.drop_table("organizations")
    op.drop_table("users")
