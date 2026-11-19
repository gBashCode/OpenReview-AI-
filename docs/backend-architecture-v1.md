# OpenReview AI — Foundational Backend Architecture

## 1. Architectural Overview

OpenReview AI utilizes a **modular monolith** backend built on **FastAPI**, **SQLAlchemy 2.0 (async)**, **Pydantic v2**, and **Alembic**, designed for enterprise autonomy, multi-agent debates, and multi-tenant isolation.

```
backend/app/
├── api/
│   └── v1/
│       ├── endpoints/
│       │   ├── analytics.py
│       │   ├── auth.py
│       │   ├── autofix.py
│       │   ├── findings.py
│       │   ├── health.py
│       │   ├── organizations.py
│       │   ├── pull_requests.py
│       │   ├── repositories.py
│       │   ├── reviews.py
│       │   └── users.py
│       └── router.py
├── core/
│   ├── config.py
│   ├── dependencies.py
│   ├── exceptions.py
│   ├── logging.py
│   └── security.py
├── database/
│   ├── base.py
│   └── session.py
├── auth/
│   ├── schemas.py
│   └── service.py
├── users/
│   ├── models.py
│   └── schemas.py
├── organizations/
│   ├── models.py
│   ├── schemas.py
│   └── service.py
├── github/
│   ├── models.py
│   └── schemas.py
├── repositories/
│   ├── models.py
│   ├── schemas.py
│   └── service.py
├── indexing/
│   ├── models.py
│   ├── schemas.py
│   └── service.py
├── pull_requests/
│   ├── models.py
│   ├── schemas.py
│   └── service.py
├── reviews/
│   ├── models.py
│   ├── schemas.py
│   └── service.py
├── findings/
│   ├── models.py
│   ├── schemas.py
│   └── service.py
├── agents/
│   ├── models.py
│   ├── schemas.py
│   └── service.py
├── autofix/
│   ├── models.py
│   ├── schemas.py
│   └── service.py
├── verification/
│   ├── models.py
│   └── schemas.py
└── analytics/
    ├── models.py
    ├── schemas.py
    └── service.py
```

---

## 2. Relational Database Tables (16 Entities)

| # | Table Name | Key Columns | Relationships |
|---|------------|-------------|---------------|
| 1 | `users` | `id` (UUID), `email`, `username`, `hashed_password`, `is_active`, `is_superuser` | 1-to-many `organization_members`, `audit_logs` |
| 2 | `organizations` | `id` (UUID), `name`, `slug`, `plan`, `max_repos` | 1-to-many `organization_members`, `repositories`, `github_installations`, `audit_logs` |
| 3 | `organization_members` | `id` (UUID), `organization_id` (FK), `user_id` (FK), `role` | Many-to-1 `organizations`, `users` |
| 4 | `github_installations` | `id` (UUID), `organization_id` (FK), `installation_id`, `account_login` | Many-to-1 `organizations`, 1-to-many `repositories` |
| 5 | `repositories` | `id` (UUID), `organization_id` (FK), `github_repo_id`, `full_name`, `default_branch` | Many-to-1 `organizations`, 1-to-many `pull_requests`, `repository_indexes`, `code_chunks`, `code_symbols` |
| 6 | `repository_indexes` | `id` (UUID), `repository_id` (FK), `commit_sha`, `branch`, `status`, `total_chunks` | Many-to-1 `repositories` |
| 7 | `code_chunks` | `id` (UUID), `repository_id` (FK), `file_path`, `content`, `embedding` (Vector 1536) | Many-to-1 `repositories` |
| 8 | `code_symbols` | `id` (UUID), `repository_id` (FK), `name`, `kind`, `file_path`, `signature`, `docstring` | Many-to-1 `repositories` |
| 9 | `pull_requests` | `id` (UUID), `repository_id` (FK), `pr_number`, `head_sha`, `base_sha`, `title` | Many-to-1 `repositories`, 1-to-many `reviews` |
| 10 | `reviews` | `id` (UUID), `pull_request_id` (FK), `commit_sha`, `status`, `score`, `security_score` | Many-to-1 `pull_requests`, 1-to-many `findings`, `review_agents`, `agent_discussions` |
| 11 | `review_agents` | `id` (UUID), `review_id` (FK), `agent_name`, `role`, `status`, `confidence_score` | Many-to-1 `reviews` |
| 12 | `findings` | `id` (UUID), `review_id` (FK), `file_path`, `line_number`, `category`, `severity`, `title` | Many-to-1 `reviews`, 1-to-many `patches`, `agent_discussions` |
| 13 | `agent_discussions` | `id` (UUID), `review_id` (FK), `finding_id` (FK), `agent_name`, `message_type`, `content` | Many-to-1 `reviews`, `findings` |
| 14 | `patches` | `id` (UUID), `finding_id` (FK), `original_code`, `proposed_code`, `diff_content`, `status` | Many-to-1 `findings`, 1-to-many `test_runs` |
| 15 | `test_runs` | `id` (UUID), `patch_id` (FK), `status`, `test_framework`, `passed_tests`, `stdout_log` | Many-to-1 `patches` |
| 16 | `audit_logs` | `id` (UUID), `organization_id` (FK), `user_id` (FK), `action`, `resource_type` | Many-to-1 `organizations`, `users` |

---

## 3. Security, Authentication & Multi-Tenancy

- **Password Hashing**: Salted `bcrypt` hashing with work factor 12.
- **JWT Bearer Authentication**: Signed JWT tokens (`HS256`) carrying `sub` (User ID), email, and username, verified via `get_current_user` dependency.
- **Tenant Data Isolation**: All critical data queries (`Repository`, `PullRequest`, `Review`, `AuditLog`) are scoped to the authenticated tenant organization via `X-Organization-ID` header or user membership.
- **Role-Based Access Control (RBAC)**:
  - `admin`: Full configuration, member invitations, deletion privileges.
  - `maintainer`: Repository settings, patch approvals, test verification.
  - `reviewer`: Code reviews, discussion comments, finding resolutions.
  - `auditor`: Read-only telemetry, reports, and enterprise audit logs.

---

## 4. Vector Search & Codebase Semantic Indexing

- **Dialect Compatibility**:
  - PostgreSQL uses the native `pgvector` extension with 1,536-dimensional float vector embeddings and IVFFlat index acceleration.
  - SQLite uses a custom `CompatibleVector` TypeDecorator that transparently serializes vectors for frictionless testing in CI/CD without local C-extension binaries.
- **Code Symbols**: AST parser extracts declarations (functions, methods, classes, interfaces) with docstrings and signatures.

---

## 5. Verification & Test Suite

The test suite validates the entire API and database layer across 21 integration tests:
```bash
$env:PYTHONPATH="backend"
.\.venv\Scripts\pytest -v tests
```
- `tests/test_auth.py`: Registration, duplicate rejection, login, token validation, `/me` profile.
- `tests/test_organizations.py`: Multi-tenant organization creation, membership, RBAC role updates.
- `tests/test_repositories.py`: Tenant-scoped repository CRUD, conflict protection, semantic indexing.
- `tests/test_pull_requests.py`: PR ingestion, lifecycle management, branch tracking.
- `tests/test_reviews.py`: Review triggers, 5-agent spawning, multi-agent conference debate messages, simulated AI review passes.
- `tests/test_autofix.py`: Diff generation, patch proposals, sandbox test runs, human approve/reject workflow.
- `tests/test_analytics.py`: Organization metrics, audit logging.
- `tests/test_health.py`: Liveness, readiness, PostgreSQL, and Redis connectivity probes.
